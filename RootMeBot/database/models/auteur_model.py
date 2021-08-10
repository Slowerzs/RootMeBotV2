from peewee import *
from database.models.base_model import *
from database.models.challenge_model import Challenge

class Auteur(BaseModel):
	idx = IntegerField(primary_key=True)
	username = TextField()
	score = IntegerField()
	rank = IntegerField()
	validations = ManyToManyField(Challenge, backref='solvers')

	def __str__(self) -> str:
		return f"User {self.username}-{self.idx}: {self.score} points [{self.rank}|{len(self.validations)}]"
