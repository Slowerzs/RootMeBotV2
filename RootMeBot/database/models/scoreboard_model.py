"""Module for the scoreboard class in discord"""
from database.models.base_model import Base
from sqlalchemy import Column, ForeignKey, Table, Text
from sqlalchemy.orm import backref, relationship

association_table = Table('association_auteur_scoreboard', Base.metadata,
        Column('scoreboard_name', ForeignKey('scoreboards.name'), primary_key=True),
        Column('auteur_id', ForeignKey('auteurs.idx'), primary_key=True)
    )

class Scoreboard(Base):
    """Class that represents a Scoreboard in discord"""
    __tablename__ = 'scoreboards'
    name = Column(Text, primary_key=True)
    users = relationship("Auteur",
            secondary = association_table,
            backref=backref("scoreboards", lazy='subquery'),
            lazy="subquery"
    )
