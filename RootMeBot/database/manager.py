"""Module for the DatabaseManager"""
import asyncio
import code

from api.fetch import ApiRootMe
from classes.auteur import AuteurData
from classes.challenge import ChallengeData
from classes.enums import Stats
from classes.error import PremiumChallenge, UnknownUser
from constants import database_path
from notify.manager import NotificationManager
from sqlalchemy import create_engine, func
from sqlalchemy.orm import make_transient, sessionmaker

from database.models.auteur_model import Auteur
from database.models.base_model import Base
from database.models.challenge_model import Challenge
from database.models.scoreboard_model import Scoreboard

Solves = list[tuple[AuteurData, ChallengeData]]
Challenges = list[ChallengeData]
Auteurs = list[AuteurData]

class DatabaseManager():
    """Class that manages the database"""

    def __init__(self, rootme_api: ApiRootMe, notification_manager: NotificationManager) -> None:

        self.rootme_api = rootme_api
        self.notification_manager = notification_manager

        self.engine = create_engine(f"sqlite://{database_path}", connect_args={'timeout': 15})
        Base.metadata.create_all(bind=self.engine)

        self.session_maker = sessionmaker(self.engine, expire_on_commit=False)

    def count_challenges(self) -> int:
        """Counts number of challenges, used for initialization"""

        with self.session_maker.begin() as session: # type: ignore
            res = session.query(Challenge.idx).count()

        return res

    async def add_challenge_to_db(self, idx: int, priority=1) -> Challenge:
        """Adds a Challenge to db from api"""
        try:
            challenge = await self.rootme_api.get_challenge_by_id(idx, priority)
        except PremiumChallenge:
            return Challenge()

        return challenge

    async def get_challenge_from_db(self, idx: int) -> Challenge:
        """Retreives an Challenge from database"""

        with self.session_maker.begin() as session: # type: ignore
            chall = session.query(Challenge).filter(Challenge.idx == idx).one_or_none()
        return chall


    async def update_challenges(self, init=False) -> None:
        """Retreives all challenges"""

        print("Updating all challenges...")

        with self.session_maker.begin() as session: # type: ignore
            old_challs = session.query(Challenge).all()
            old_ids = [c.idx for c in old_challs]
            all_challenges = await self.rootme_api.fetch_all_challenges()

            new_challenges = [new_chall for new_chall in all_challenges if new_chall.idx not in old_ids]


        async def get_new_chall(idx: int):
            try:
                full_chall = await self.rootme_api.get_challenge_by_id(idx, 1)
            except PremiumChallenge:
                print(f"Could not retreive premium challenge {idx}")
                return

            with self.session_maker.begin() as session: # type: ignore
                if temp_chall := session.query(Challenge.idx).filter(Challenge.idx == full_chall.idx).one_or_none():
                    if temp_chall.score != full_chall.score:
                        #In case of an update from Root-Me
                        temp_chall.update(full_chall)
                else:
                    session.add(full_chall)

            if not init:
                self.notification_manager.add_chall_to_queue(full_chall)

        await asyncio.gather(*(get_new_chall(chall.idx) for chall in new_challenges))

        print("Done updating challenges !")

        return

    async def get_all_users_from_db(self) -> list[Auteur]:
        """Returns all users in database in the form of Auteur"""

        with self.session_maker.begin() as session: # type: ignore
            users = session.query(Auteur).all()

        return users

    async def search_user_from_db(self, name: str) -> list[Auteur]:
        """Returns a list of users whose username contains the search"""

        with self.session_maker.begin() as session: # type: ignore
            users = session.query(Auteur).filter(Auteur.username.contains(name)).all()

        return users

    async def get_user_from_db(self, idx: int) -> Auteur:
        """Retreives an Auteur from database"""

        with self.session_maker.begin() as session: # type: ignore
            auteur = session.query(Auteur).where(Auteur.idx == idx).one_or_none()
        return auteur

    async def remove_user_from_db(self, idx: int) -> AuteurData:
        """Remove an Auteur from db by id"""
        with self.session_maker.begin() as session: # type: ignore
            aut = session.query(Auteur).filter(Auteur.idx == idx).one_or_none()
            username = aut.username
            aut.validations = []
            session.delete(aut)
            return username


    async def search_challenge_from_db(self, name: str) -> list[Challenge]:
        """Retreives a list of matching challenges in the db"""
        with self.session_maker.begin() as session: # type: ignore
            challs = session.query(Challenge).filter(Challenge.title.contains(name)).all()

        return challs



    async def remove_user_from_db_by_name(self, name: str) -> list[str]:
        """Remove an Auteur from db by id"""
        with self.session_maker.begin() as session: # type: ignore

            aut = session.query(Auteur).filter(Auteur.username == name)

            if (v := aut.count()) == 1:
                auteur = aut.one()
                username = auteur.username
                auteur.validations = []
                aut.delete()
                ret = [username]
            elif v == 0:
                ret = []
            else:
                ret = aut.all()

        return ret

    async def retreive_user(self, idx: int, priority=1) -> Auteur:
        """Returns a Auteur populated properly"""

        auteur = await self.rootme_api.get_user_by_id(idx, priority)

        return auteur


    async def update_user(self, idx: int) -> None:
        """Tries to update a user to database, if it doesn't exist return nothing"""
        new_vals = []
        #If the user already exists in our database

        with self.session_maker.begin() as session:  # type: ignore

            challs_id = [i[0] for i in session.query(Challenge.idx).all()]
            old_auteur = await self.get_user_from_db(idx)
            old_id = [i.idx for i in session.merge(old_auteur).solves]
            make_transient(old_auteur)

            full_auteur = await self.retreive_user(idx)
            full_auteur = session.merge(full_auteur)

            for validation in full_auteur.validation_aut:
                if validation.validation_challenge.idx not in challs_id:
                    new_c = await self.add_challenge_to_db(validation.validation_challenge.idx, 0)
                    if new_c:
                        chall = session.merge(validation.validation_challenge)
                        session.delete(chall)
                        session.add(new_c)

                if validation.validation_challenge.idx not in old_id:
                    new_vals.append(validation)

            for val in new_vals:
                res = session.query(Auteur.username, Auteur.score).filter(Auteur.score > val.validation_auteur.score).order_by(Auteur.score.asc()).limit(1).one_or_none()
                if res:
                    user_above, user_score = res
                else:
                    #First person in scoreboard
                    user_above, user_score = ("", 0)

                above = (user_above, user_score)

                if val.challenge_id:
                    #Premium challenge are None, we can't notify them :(
                    if len(val.validation_challenge.solvers) <= 3:
                        is_blood = True
                    else:
                        is_blood = False

                    self.notification_manager.add_solve_to_queue(val, above, is_blood)



    async def search_user(self, username: str) -> list[Auteur]:
        """Search user by name"""

        try:
            auteurs = await self.rootme_api.search_user_by_name(username, 0, priority=0)
        except UnknownUser:
            #No user matches the username
            return []


        fulls_auteurs = await asyncio.gather(*[self.rootme_api.get_user_by_id(aut.idx, priority=0) for aut in auteurs])


        return fulls_auteurs # type: ignore


    async def add_user(self, idx: int) -> Auteur:
        """Adds a user from the api if we don't already have it"""

        aut = await self.get_user_from_db(idx)
        if not aut:
            with self.session_maker.begin() as session: # type: ignore
                full_auteur = await self.retreive_user(idx, priority=0)
                full_auteur = session.merge(full_auteur)
                global_scoreboard = session.query(Scoreboard).where(Scoreboard.name == 'global').one()
                full_auteur.scoreboards.append(global_scoreboard)
                session.add(full_auteur)
            return full_auteur
        else:
            return aut


    async def update_users(self) -> None:
        """Updates all users"""

        with self.session_maker.begin() as session: # type: ignore
            await asyncio.gather(*(self.update_user(aut.idx) for aut in session.query(Auteur).all()))

        await asyncio.sleep(1)

    async def get_stats(self) -> dict:
        """Queries db for how many chall per category"""

        with self.session_maker.begin() as session: # type: ignore
            res = session.query(Challenge.category, func.count(Challenge.idx)).group_by(Challenge.category).all()
            stats = {
                Stats.APP_SCRIPT: next(x[1] for x in res if x[0] == 'App - Script'),
                Stats.APP_SYSTEM: next(x[1] for x in res if x[0] == 'App - Système'),
                Stats.CRACKING: next(x[1] for x in res if x[0] == 'Cracking'),
                Stats.WEB_CLIENT: next(x[1] for x in res if x[0] == 'Web - Client'),
                Stats.WEB_SERVER: next(x[1] for x in res if x[0] == 'Web - Serveur'),
                Stats.FORENSICS: next(x[1] for x in res if x[0] == 'Forensic'),
                Stats.REALIST: next(x[1] for x in res if x[0] == 'Réaliste'),
                Stats.CRYPTANALYSIS: next(x[1] for x in res if x[0] == 'Cryptanalyse'),
                Stats.NETWORK: next(x[1] for x in res if x[0] == 'Réseau'),
                Stats.STEGANOGRAPHY: next(x[1] for x in res if x[0] == 'Stéganographie') ,
                Stats.PROGRAMMING: next(x[1] for x in res if x[0] == 'Programmation')
                                    }


        return stats

    async def get_stats_auteur(self, auteur: Auteur) -> dict:
        """Queries db for the stats of a single auteur"""

        with self.session_maker.begin() as session: # type: ignore

            auteur = session.merge(auteur)

            solves = {
                Stats.WEB_CLIENT : len([i for i in auteur.solves if i.category == 'Web - Client']),
                Stats.APP_SCRIPT : len([i for i in auteur.solves if i.category == 'App - Script']),
                Stats.PROGRAMMING : len([i for i in auteur.solves if i.category == 'Programmation']),
                Stats.CRACKING : len([i for i in auteur.solves if i.category == 'Cracking']),
                Stats.NETWORK : len([i for i in auteur.solves if i.category == 'Réseau']),
                Stats.APP_SYSTEM : len([i for i in auteur.solves if i.category == 'App - Système']),
                Stats.WEB_SERVER : len([i for i in auteur.solves if i.category == 'Web - Serveur']),
                Stats.CRYPTANALYSIS : len([i for i in auteur.solves if i.category == 'Cryptanalyse']),
                Stats.STEGANOGRAPHY : len([i for i in auteur.solves if i.category == 'Stéganographie']),
                Stats.REALIST : len([i for i in auteur.solves if i.category == 'Réaliste']),
                Stats.FORENSICS : len([i for i in auteur.solves if i.category == 'Forensic'])
            }

        return solves


    async def get_scoreboard(self, name: str) -> Scoreboard:
        """Retreives a scoreboard from db by name"""

        with self.session_maker.begin() as session: # type: ignore
            scoreboard = session.query(Scoreboard).filter(Scoreboard.name == name).one_or_none()
        return scoreboard

    def get_all_scoreboards(self) -> list[Scoreboard]:
        """Retreives all scoreboards"""
        with self.session_maker.begin() as session: # type: ignore
            scoreboard = session.query(Scoreboard).all()
        return scoreboard

    async def create_scoreboard(self, name: str) -> Scoreboard:
        """Creates a scoreboard """
        with self.session_maker.begin() as session: # type: ignore
            scoreboard = await self.get_scoreboard(name)
            if not scoreboard:
                scoreboard = Scoreboard(name=name)
                session.add(scoreboard)
        return scoreboard

    async def remove_scoreboard(self, name: str) -> bool:
        """Removes a scoreboard"""

        with self.session_maker.begin() as session: # type: ignore
            scoreboard = session.query(Scoreboard).filter(Scoreboard.name == name).one_or_none()
            if not scoreboard:
                res = False
            else:
                res = True
                scoreboard.users = []
                session.delete(scoreboard)
        return res

    async def add_to_scoreboard(self, user_id: int, scoreboard_name: str) -> bool:
        """Adds a user to a scoreboard"""

        with self.session_maker.begin() as session: # type: ignore
            aut = session.query(Auteur).filter(Auteur.idx == user_id).one_or_none()
            scoreboard = session.query(Scoreboard).filter(Scoreboard.name == scoreboard_name).one_or_none()
            if not aut or not scoreboard:
                res = False
            else:
                aut.scoreboards.append(scoreboard)
                res = True

        return res

    async def remove_from_scoreboard(self, user_id: int, scoreboard_name: str) -> bool:
        """Remove a user from a scoreboard"""

        with self.session_maker.begin() as session: # type: ignore
            aut = session.query(Auteur).filter(Auteur.idx == user_id).one_or_none()
            scoreboard = session.query(Scoreboard).filter(Scoreboard.name == scoreboard_name).one_or_none()
            if not aut or not scoreboard:
                res = False
            else:
                if scoreboard.name in [i.name for i in aut.scoreboards]:
                    aut.scoreboards.remove(scoreboard)
                    res = True
                else:
                    res = False
        return res
