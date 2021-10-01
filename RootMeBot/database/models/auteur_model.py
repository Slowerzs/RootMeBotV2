from sqlalchemy import Table, Column, Integer, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from database.models.base_model import *


class Auteur(Base):
    __tablename__ = 'auteurs'
    idx = Column(Integer, primary_key=True)
    username = Column(Text)
    score = Column(Text)
    rank = Column(Text)
    
    def __str__(self) -> str:
        return f"User {self.username}-{self.idx}: {self.score} points [{self.rank}|{len(self.validations)}]"
