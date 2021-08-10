from peewee import *
from datetime import datetime

class ChallengeShort():
	def __init__(self, idx: int, title: str) -> None:
		self.idx = idx
		self.title = title


class ChallengeData():

	def __init__(self, idx: int, title: str, category: str, description: str, score: int, difficulty: str, date: datetime, validations: int):
		self.idx = idx
		self.title = title
		self.category = category
		self.description = description
		self.score = score
		self.difficulty = difficulty
		self.date = date
		self.validations = validations

	def keys(self) -> list:
		return ["idx", "title", "category", "description", "score", "difficulty", "date", "validations"]
	
	def __getitem__(self, key) -> dict:
		return {
			"idx": self.idx,
			"title": self.title,
			"category": self.category,
			"description": self.description,
			"score": self.score,
			"difficulty": self.difficulty,
			"date": self.date,
			"validations": self.validations
			}[key]
		

	def __str__(self) -> str:
		return f"Challenge {self.title}: {self.category} [{self.score}]"
