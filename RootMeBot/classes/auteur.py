from classes.challenge import *

Validations = list[int]

class AuteurShort():
	def __init__(self, idx: int, username: str) -> None:
		self.idx = idx
		self.username = username

class AuteurData():
	def __init__(self, idx: int, username: str, score: int, rank: int, validations: Validations) -> None:
		self.idx = idx
		self.username = username
		self.score = score
		self.rank = rank
		self.validations = validations

	def keys(self) -> list:
		return ["idx", "username", "score", "rank", "validations"]


	def __getitem__(self, key) -> dict:
		return {
			"idx": self.idx,
			"username": self.username,
			"score": self.score,
			"rank": self.rank,
			"validations": self.validations
			}[key]


	def __str__(self) -> str:
		return f"User {self.username}-{self.idx}: {self.score} points [{self.rank}|{len(self.validations)}]"


	
