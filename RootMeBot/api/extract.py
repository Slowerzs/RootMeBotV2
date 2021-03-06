import code

from classes.auteur import *
from classes.challenge import *
from datetime import datetime

from database.models.auteur_model import Auteur
from database.models.challenge_model import Challenge
from database.models.validation_model import Validation
from database.models.base_model import Base


def extract_auteur(user_data: dict) -> Auteur:
    """Parses data to create an Auteur"""
    idx, user_name, user_score = int(user_data['id_auteur']), user_data['nom'], int(user_data['score'])

    try:
        user_rank = int(user_data['position'])
    except ValueError:
        #If the user's score is 0, the rank is not specified
        user_rank = 0

    aut = Auteur(idx=idx, username=user_name, score=user_score, rank=user_rank)

    for validation in user_data['validations']:

        c = Challenge(idx=int(validation['id_challenge']))
        d = datetime.strptime(validation["date"], "%Y-%m-%d %H:%M:%S")

        v_idx = str(aut.idx) + "-" + validation['id_challenge']

        v = Validation(idx = v_idx, date=d)
        v.validation_auteur = aut
        v.validation_challenge = c


    return aut

def extract_auteurs_short(users_data: list) -> list[AuteurShort]:
    """Parses data to create a list of AuteurShort"""

    users = []
    if users_data:

        users_data = users_data[0]

        for user_pos in range(min(len(users_data), 49)):
            users.append(AuteurShort(int(users_data[str(user_pos)]['id_auteur']), users_data[str(user_pos)]['nom']))

    return users

def extract_challenge(challenge_data: dict, idx) -> Challenge:
    """Parses data to create a Challenge"""

    if challenge_data == 404:
        # To fix
        return None


    #some challenges are list of 1 elements for some reason...
    if type(challenge_data) == list:
        challenge_data = challenge_data[0]


    titre = challenge_data['titre']
    category = challenge_data['rubrique']
    description = challenge_data['soustitre']
    score = int(challenge_data['score'])
    difficulty = challenge_data['difficulte']
    date = challenge_data['date_publication']
    format_date = "%Y-%m-%d %H:%M:%S"

    date_time = datetime.strptime(date, format_date)
    challenge = Challenge(idx=idx, title=titre, category=category, description=description, score=score, difficulty=difficulty, date=date_time)


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



