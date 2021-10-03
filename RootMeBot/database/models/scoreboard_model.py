from sqlalchemy import Table, Column, Integer, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship, backref
from database.models.base_model import *
from database.models.auteur_model import Auteur

association_table = Table('association_auteur_scoreboard', Base.metadata,
        Column('scoreboard_id', ForeignKey('scoreboards.idx'), primary_key=True),
        Column('auteur_id', ForeignKey('auteurs.idx'), primary_key=True)
    )

class Scoreboard(Base):
    __tablename__ = 'scoreboards'
    idx = Column(Integer, primary_key=True)
    name = Column(Text)
    users = relationship("Auteur",
            secondary = association_table,
            backref=backref("scoreboards", lazy='subquery'),
            lazy="subquery"
    )
