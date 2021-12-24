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



    def keys(self) -> list:
        return ["idx", "title", "category", "description", "score", "difficulty", "date", "validation_number"]

    def __getitem__(self, key) -> dict:
        return {
            "idx": self.idx,
            "title": self.title,
            "category": self.category,
            "description": self.description,
            "score": self.score,
            "difficulty": self.difficulty,
            "date": self.date,
            "validation_number": self.validation_number
            }.get(key)

