from peewee import *

import asyncio

import database.models.base_model as db
from database.models.challenge_model import Challenge
from database.models.auteur_model import Auteur
from database.models.challenge_auteur_model import ChallengeAuteur

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

        self.db = SqliteDatabase(database_path)
        db.database.initialize(self.db)
        
        self.db.connect()
        self.db.create_tables([Challenge, Auteur, ChallengeAuteur])


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

    async def get_challenge_from_db(self, idx: int) -> ChallengeData:
        """Retreives an ChallengeData from database"""
        chall = Challenge.select().where(Challenge.idx == idx).get()
        challenge_data = ChallengeData(idx, chall.title, chall.category, chall.description, chall.score, chall.difficulty, chall.date, chall.validations)
        return challenge_data       

        
    async def update_challenges(self, init=False) -> None:
        """Retreives all challenges"""

        old_challenges = [chall.idx for chall in Challenge.select()]
        all_challenges = await self.rootme_api.fetch_all_challenges()
        new_challenges = [new_chall for new_chall in all_challenges if new_chall.idx not in old_challenges]

        async def get_new_chall(idx: int):
            try:
                full_chall = await self.rootme_api.get_challenge_by_id(idx)
            except PremiumChallenge:
                print(f"Could not retreive premium challenge {idx}")
                return
            Challenge.create(**full_chall)
            if not init:
                self.notification_manager.add_chall_to_queue(full_chall)
            
        coros = [get_new_chall(chall.idx) for chall in new_challenges]
        await asyncio.gather(*coros)
    
        return

    async def get_all_users_from_db(self) -> list[AuteurData]:
        """Returns all users in database in the form of AuteurData"""
        users = []
        
        for aut in Auteur.select():
            validations = [i.idx for i in aut.validations]
            auteur_data = AuteurData(aut.idx, aut.username, aut.score, aut.rank, validations)
            users.append(auteur_data)

        return users

    async def get_user_from_db(self, idx: int) -> AuteurData:
        """Retreives an AuteurData from database"""
        aut = Auteur.select().where(Auteur.idx == idx).get()
        validations = [i.idx for i in aut.validations]
        auteur_data = AuteurData(aut.idx, aut.username, aut.score, aut.rank, validations)
        return auteur_data

    async def remove_user_from_db(self, idx: int) -> AuteurData:
        """Remove an Auteur from db"""
        try:
            aut = Auteur.select().where(Auteur.idx == idx).get()
            print(f"Auteur to remove : {aut}")
            validations = [i.idx for i in aut.validations]
            auteur_data = AuteurData(aut.idx, aut.username, aut.score, aut.rank, validations)
            aut.delete_instance()
            return auteur_data
        except DoesNotExist:
            return None
        

    async def update_user(self, idx: int) -> None:
        """Tries to update a user to database, if it doesn't exists return nothing"""
        new_solves = []
        try:
            #If the user already exists in our database
            old_auteur = await self.get_user_from_db(idx)
            db_auteur = Auteur.select().where(Auteur.idx == idx).get()

            full_auteur = await self.rootme_api.get_user_by_id(idx)

            
            if not full_auteur:
                return

            print(full_auteur)

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
        except UnknownUser:
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
        
        #25 at a time

        coros = [self.update_user(aut.idx) for aut in Auteur.select()]
        await asyncio.gather(*coros)

        #for aut in Auteur.select():
        #   print(aut)
        #   new_solves = await self.update_user(aut.idx)
        #   all_new_solves += new_solves






