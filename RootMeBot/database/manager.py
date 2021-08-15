from peewee import *

import database.models.base_model as db

from database.models.challenge_model import Challenge
from database.models.auteur_model import Auteur
from database.models.challenge_auteur_model import ChallengeAuteur

from classes.challenge import ChallengeData, ChallengeShort
from classes.auteur import AuteurData, AuteurShort
from classes.error import *

from api.fetch import *
from constants import database_path

Solves = list[tuple[AuteurData, ChallengeData]]
Challenges = list[ChallengeData]
Auteurs = list[AuteurData]

class DatabaseManager():
	def __init__(self):
		self.db = SqliteDatabase(database_path)

		db.database.initialize(self.db)

		self.db.connect()
		self.db.create_tables([Challenge, Auteur, ChallengeAuteur])


	async def add_challenge_to_db(self, idx: int) -> ChallengeData:
		"""Adds a Challenge to db from api"""

		try:
			challenge = await get_challenge_by_id(idx)
		
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

		
	async def update_challenges(self) -> Challenges:
		"""Retreives all challenges"""

		old_challenges = [chall.idx for chall in Challenge.select()]
		all_challenges = await fetch_all_challenges()
		new_challenges = [new_chall for new_chall in all_challenges if new_chall.idx not in old_challenges]

		challenges = []

		for chall in new_challenges:
			await asyncio.sleep(2)
			try:
				full_chall = await get_challenge_by_id(chall.idx)
			except PremiumChallenge:
				print(f"Could not retreive premium challenge {chall.idx}")
				continue
			challenges.append(full_chall)
			Challenge.create(**full_chall)

		return challenges

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
			validations = [i.idx for i in aut.validations]
			auteur_data = AuteurData(aut.idx, aut.username, aut.score, aut.rank, validations)
			aut.delete_instance()
			return auteur_data
		except DoesNotExist:
			return None
		

	async def update_user(self, idx: int) -> Solves:
		"""Tries to update a user to database, if it doesn't exists return nothing"""
		new_solves = []
		try:
			#If the user already exists in our database
			old_auteur = await self.get_user_from_db(idx)
			db_auteur = Auteur.select().where(Auteur.idx == idx).get()

			full_auteur = await get_user_by_id(idx)


			if not full_auteur:
				return []

			for validation in full_auteur.validations:
				if validation not in old_auteur.validations:
					try:
						chall = await get_challenge_by_id(validation)
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

			return new_solves					

		except DoesNotExist:
			await self.add_user(idx)
			return []

	async def search_user(self, username: str) -> Auteurs:
		full_auteurs = []
		try:
			auteurs = await search_user_by_name(username, 0)
		except UnknownUser:
			#No user matches the username
			return []

		for aut in auteurs:
			try:
				await asyncio.sleep(2)
				full_auteur = await get_user_by_id(aut.idx)
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
			full_auteur = await get_user_by_id(idx)
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


	async def update_users(self) -> Solves:

		all_new_solves = []

		for aut in Auteur.select():
			await asyncio.sleep(1.5)
			print(aut)
			new_solves = await self.update_user(aut.idx)
			all_new_solves += new_solves

		return all_new_solves





