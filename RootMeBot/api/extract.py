from classes.auteur import *
from classes.challenge import *
from datetime import datetime

def extract_auteur(user_data: dict) -> AuteurData:
	"""Parses data to create an Auteur"""
	idx, user_name, user_score = int(user_data['id_auteur']), user_data['nom'], int(user_data['score'])
	
	try:
		user_rank = int(user_data['position'])
	except ValueError:
		#If the user's score is 0, the rank is not specified
		user_rank = 0

	user_validations = []
	for validation in user_data['validations']:
		user_validations.append(int(validation['id_challenge']))
	
	return AuteurData(idx, user_name, user_score, user_rank, user_validations)


def extract_auteurs_short(users_data: list) -> list[AuteurShort]:
	"""Parses data to create a list of AuteurShort"""

	users = []

	users_data = users_data[0]
	
	for user_pos in range(min(len(users_data), 49)):
		users.append(AuteurShort(int(users_data[str(user_pos)]['id_auteur']), users_data[str(user_pos)]['nom']))
	
	return users

def extract_challenge(challenge_data: dict, idx) -> ChallengeData:
	"""Parses data to create a Challenge"""
	titre = challenge_data['titre']
	category = challenge_data['rubrique']
	description = challenge_data['soustitre']
	score = int(challenge_data['score'])
	difficulty = challenge_data['difficulte']
	date = challenge_data['date_publication']
	validations = int(challenge_data['validations'])
	format_date = "%Y-%m-%d %H:%M:%S"

	date_time = datetime.strptime(date, format_date) 
	challenge = ChallengeData(idx, titre, category, description, score, difficulty, date_time, validations)
	

	return challenge

def extract_page_challenges(data: list) -> list[ChallengeShort]:
	"""Parses data to create a list of ChallengeShort"""
	challs = []
	for chall in data[0].values():
		idx = int(chall['id_challenge'])
		title = chall['titre']

		current_chall = ChallengeShort(idx, title)
		challs.append(current_chall)

	return challs



