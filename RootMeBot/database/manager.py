import asyncio

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

import database.models.base_model as db
from database.models.challenge_model import Challenge
from database.models.auteur_model import Auteur
from database.models.base_model import Base

from classes.challenge import ChallengeData, ChallengeShort
from classes.auteur import AuteurData, AuteurShort
from classes.error import *

from api.fetch import ApiRootMe
from constants import database_path

from notify.manager import NotificationManager

Solves = list[tuple[AuteurData, ChallengeData]]
Challenges = list[ChallengeData]
Auteurs = list[AuteurData]

class DatabaseManager():

    def __init__(self, rootme_api: ApiRootMe, notification_manager: NotificationManager) -> None:

        self.rootme_api = rootme_api
        self.notification_manager = notification_manager

        self.engine = create_engine(f"sqlite://{database_path}")
        Base.metadata.create_all(bind=self.engine)
       
        self.Session = sessionmaker(self.engine)
        

    def count_challenges(self) -> int:
        """Counts number of challenges, used for initialization"""

        with self.Session.begin() as session:
            res = session.query(Challenge.idx).count()

        return res

    async def add_challenge_to_db(self, idx: int) -> ChallengeData:
        """Adds a Challenge to db from api"""

        try:
            challenge = await self.rootme_api.get_challenge_by_id(idx)
        
        except PremiumChallenge:
            return None
        try:
            Challenge.update(**challenge)
        except DoesNotExist:
            Challenge.create(**challenge)
        return challenge

    async def get_challenge_from_db(self, idx: int) -> Challenge:
        """Retreives an Challenge from database"""
        
        with self.Session.begin() as session:
            chall = session.query(Challenge).filter(Challenge.idx == idx).one()
        return chall

        
    async def update_challenges(self, init=False) -> None:
        """Retreives all challenges
        For all new challenges (not """


        with self.Session.begin() as session:
            old_challs = session.query(Challenge).all()
            old_ids = [c.idx for c in old_challs]
            all_challenges = await self.rootme_api.fetch_all_challenges()    
            new_challenges = [new_chall for new_chall in all_challenges if new_chall.idx not in old_ids]



        async def get_new_chall(idx: int):
            try:
                full_chall = await self.rootme_api.get_challenge_by_id(idx)
            except PremiumChallenge:
                print(f"Could not retreive premium challenge {idx}")
                return

            with self.Session.begin() as session:
                if temp_chall := session.query(Challenge.idx).filter(Challenge.idx == full_chall.idx).one_or_none():
                    if temp_chall.score != full_chall.score:
                        #In case of an update from Root-Me
                        temp_chall.update(full_chall)
                else:
                    session.add(full_chall)

            if not init:
                self.notification_manager.add_chall_to_queue(full_chall)


        for chall in new_challenges:
            await asyncio.sleep(0.90)
            await get_new_chall(chall.idx)

    
        return

    async def get_all_users_from_db(self) -> list[Auteur]:
        """Returns all users in database in the form of Auteur"""
        
        with self.Session.begin() as session:
            users = session.query(Auteur).all()

        return users

    async def get_user_from_db(self, idx: int) -> AuteurData:
        """Retreives an Auteur from database"""

        with self.Session.begin() as session:
            auteur = session.query(Auteur).where(Auteur.idx == idx).one_or_none()
        return auteur

    async def remove_user_from_db(self, idx: int) -> AuteurData:
        """Remove an Auteur from db"""
        with self.Session.begin() as session:
            session.select(Auteur).filter(Auteur.idx == idx).delete()

        

    async def update_user(self, idx: int) -> None:
        """Tries to update a user to database, if it doesn't exists return nothing"""
        new_solves = []
        try:
            #If the user already exists in our database
            old_auteur = await self.get_user_from_db(idx)

            full_auteur = await self.rootme_api.get_user_by_id(idx)
            if not full_auteur:
                return
    
            for validation in full_auteur.validations:
                if validation not in old_auteur.validations:
                    try:
                        chall = await self.rootme_api.get_challenge_by_id(validation)
                        if chall:
                            Challenge.update(**chall)
                    except DoesNotExist:
                        chall = await self.add_challenge_to_db(validation)
                    except PremiumChallenge:
                        continue
                    if chall:
                        #Send notification
                        new_solves.append((full_auteur, chall))
                        #Saves the new solve to the auteur
                        db_auteur.validations.add(Challenge.select().where(Challenge.idx == validation))
                        #Update score
                        db_auteur.score = full_auteur.score
                        db_auteur.rank = full_auteur.rank
                        db_auteur.save()

            for solve in new_solves:
                try:
                    user_above = Auteur.select().where(Auteur.score > solve[0].score).order_by(Auteur.score.asc()).get()
                    above = (user_above.username, user_above.score)
                except DoesNotExist:
                    #First person in scoreboard
                    above = ("", 0)

                if solve[1]:
                    #Premium challenge are None, we can't notify them :(
                    self.notification_manager.add_solve_to_queue(solve, above)

        except DoesNotExist:
            return 

    async def search_user(self, username: str) -> Auteurs:
        full_auteurs = []
        try:
            auteurs = await self.rootme_api.search_user_by_name(username, 0)
        except UnknownUser:
            #No user matches the username
            return []

        for aut in auteurs:
            try:
                full_auteur = await self.rootme_api.get_user_by_id(aut.idx)
                full_auteurs.append(full_auteur)
            except UnknownUser:
                #User might be banned, he still shows up in search but we can't get his profile
                continue
        return full_auteurs


    async def add_user(self, idx: int) -> AuteurData:

        try:
            aut = await self.get_user_from_db(idx)
            return aut
        except DoesNotExist:
            pass

        try:    
            full_auteur = await self.rootme_api.get_user_by_id(idx)
        except:
            return None     

        #We check if we have all the user's solves in our db, otherwise add to it
        for validation in full_auteur.validations:
            try:
                await self.get_challenge_from_db(validation)
            except DoesNotExist:
                await self.add_challenge_to_db(validation)

        Auteur.create(**full_auteur)        
        return full_auteur


    async def update_users(self) -> None:

        all_new_solves = []
        
        with self.Session.begin() as session:
            for aut in session.query(Auteur).all():
                print(aut)
                await self.update_user(aut.idx)
                await asyncio.sleep(0.90)






