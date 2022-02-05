"""Module for the Auteur class"""
from database.models.base_model import Base
from sqlalchemy import Column, Integer, Text


class Auteur(Base):
    """Class that represent a user"""
    __tablename__ = 'auteurs'
    idx = Column(Integer, primary_key=True)
    username = Column(Text)
    score = Column(Integer)
    rank = Column(Text)

    def __str__(self) -> str:
        return (
            f"User {self.username}-{self.idx}: "
            f"{self.score} points [{self.rank}|{len(self.solves)}]"
        )

    def __repr__(self) -> str:
        return (
            f"User {self.username}-{self.idx}: "
            f"{self.score} points [{self.rank}|{len(self.solves)}]"
        )
    