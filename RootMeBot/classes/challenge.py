"""Module for challenge classes"""
from datetime import datetime

class ChallengeShort():
    """Class for when we don't have full info on challenge"""
    def __init__(self, idx: int, title: str) -> None:
        self.idx = idx
        self.title = title


class ChallengeData():
    """Class for object not yet saved to db"""
    def __init__(
            self, idx: int,
            title: str,
            category:str,
            description: str,
            score: int,
            difficulty: str,
            date: datetime):

        self.idx = idx
        self.title = title
        self.category = category
        self.description = description
        self.score = score
        self.difficulty = difficulty
        self.date = date

    def keys(self) -> list:
        """Lists available keys"""
        return ["idx", "title", "category", "description", "score", "difficulty", "date"]

    def __getitem__(self, key) -> dict:
        return {
            "idx": self.idx,
            "title": self.title,
            "category": self.category,
            "description": self.description,
            "score": self.score,
            "difficulty": self.difficulty,
            "date": self.date,
            }[key]


    def __str__(self) -> str:
        return f"Challenge {self.title}: {self.category} [{self.score}]"
