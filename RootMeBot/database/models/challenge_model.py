"""Module for the challenge class"""
from database.models.base_model import Base
from sqlalchemy import Column, DateTime, Integer, Text


class Challenge(Base):
    """Class that represents each challenge on the platform"""

    __tablename__ = 'challenges'
    idx = Column(Integer, primary_key=True)
    title = Column(Text)
    category = Column(Text)
    description = Column(Text)
    score = Column(Integer)
    difficulty = Column(Text)
    date = Column(DateTime)

    def __repr__(self) -> str:
        return f"Challenge {self.title}: {self.category} [{self.score}]"
    def __str__(self) -> str:
        return f"Challenge {self.title}: {self.category} [{self.score}]"



    def keys(self) -> list:
        """Lists keys"""
        return ["idx", "title", "category", "description", "score", "difficulty", "date"]

    def __getitem__(self, key) -> dict:
        item = {
            "idx": self.idx,
            "title": self.title,
            "category": self.category,
            "description": self.description,
            "score": self.score,
            "difficulty": self.difficulty,
            "date": self.date,
            }.get(key)

        assert item is not None, "Error unknown Key"

        return item
