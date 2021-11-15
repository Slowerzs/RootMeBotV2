from sqlalchemy import Table, Column, Integer, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.associationproxy import association_proxy

from database.models.base_model import *
from database.models.auteur_model import Auteur
from database.models.challenge_model import Challenge

class Validation(Base):
    __tablename__ = 'validations'
    idx = Column(Integer, primary_key = True)
    auteur_id = Column(Integer, ForeignKey('auteurs.idx'))
    challenge_id = Column(Integer, ForeignKey('challenges.idx'))
    date = Column(DateTime)
    
    challenge = relationship(Challenge, backref="validations_challenge", lazy='subquery')
    solver = relationship(Auteur, backref="validations_auteur", lazy='subquery')

    def __str__(self) -> str:
        return f'Validation : {self.challenge} by {self.solver}'


Challenge.solvers = association_proxy("validations_auteur", "solver")
Auteur.solves = association_proxy("validations_challenge", "challenge")

