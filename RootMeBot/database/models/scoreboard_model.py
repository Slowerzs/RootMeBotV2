from sqlalchemy import Table, Column, Integer, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship, backref
from database.models.base_model import *
from database.models.auteur_model import Auteur

association_table = Table('association_auteur_scoreboard', Base.metadata,
        Column('scoreboard_name', ForeignKey('scoreboards.name'), primary_key=True),
        Column('auteur_id', ForeignKey('auteurs.idx'), primary_key=True)
    )

class Scoreboard(Base):
    __tablename__ = 'scoreboards'
    name = Column(Text, primary_key=True)
    users = relationship("Auteur",
            secondary = association_table,
            backref=backref("scoreboards", lazy='subquery'),
            lazy="subquery"
    )
