from sqlalchemy import Table, Column, Integer, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship, backref

from database.models.base_model import *

class Challenge(Base):

    __tablename__ = 'challenges'
    idx = Column(Integer, primary_key=True)
    title = Column(Text)
    category = Column(Text)
    description = Column(Text)
    score = Column(Integer)
    difficulty = Column(Text)
    date = Column(DateTime)
    validation_number = Column(Integer)

    def __repr__(self) -> str:
        return f"Challenge {self.title}: {self.category} [{self.score}]"
    def __str__(self) -> str:
        return f"Challenge {self.title}: {self.category} [{self.score}]"

