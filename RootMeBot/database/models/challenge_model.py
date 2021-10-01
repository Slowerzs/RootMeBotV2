from sqlalchemy import Table, Column, Integer, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from database.models.base_model import *
from database.models.auteur_model import Auteur

association_table = Table('association_auteur_challenge', Base.metadata,
        Column('challenge_id', ForeignKey('challenges.idx'), primary_key = True),
        Column('auteur_id', ForeignKey('auteurs.idx'), primary_key = True)
    )



class Challenge(Base):

    __tablename__ = 'challenges'
    idx = Column(Integer, primary_key=True)
    title = Column(Text)
    category = Column(Text)
    description = Column(Text)
    score = Column(Integer)
    difficulty = Column(Text)
    date = Column(DateTime)
    validations = Column(Text)
    solvers = relationship("Auteur",
            secondary = association_table,
            backref="validations"
    )

    def __str__(self) -> str:
        return f"Challenge {self.title}: {self.category} [{self.score}]"

"""
class Challenge(BaseModel):
    idx = IntegerField(primary_key=True)
    title = TextField()
    category = TextField()
    description = TextField()
    score = IntegerField()
    difficulty = TextField()
    date = DateTimeField()
    validations = IntegerField()

    def __str__(self) -> str:
        return f"Challenge {self.title}: {self.category} [{self.score}]"
"""
