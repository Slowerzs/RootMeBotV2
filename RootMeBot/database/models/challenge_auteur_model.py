from peewee import *
from database.models.challenge_model import Challenge
from database.models.auteur_model import Auteur

ChallengeAuteur = Auteur.validations.get_through_model()
