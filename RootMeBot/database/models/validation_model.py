"""Module for the Validation class"""
from database.models.auteur_model import Auteur
from database.models.base_model import Base
from database.models.challenge_model import Challenge
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship


class Validation(Base):
    """Class that represents the link between users and challenges"""

    __tablename__ = 'validations'
    idx = Column(Text, primary_key=True)
    auteur_id = Column(Integer, ForeignKey('auteurs.idx'), nullable=False)
    challenge_id = Column(Integer, ForeignKey('challenges.idx'), nullable=False)
    date = Column(DateTime)

    validation_auteur = relationship(Auteur, backref="validation_aut")
    validation_challenge = relationship(Challenge, backref="validation_chall")

    def __str__(self) -> str:
        return f'Validation : {self.challenge_id} by {self.auteur_id} at {self.date}'


Challenge.solvers = association_proxy("validation_chall", "validation_auteur")
Auteur.solves = association_proxy("validation_aut", "validation_challenge")
