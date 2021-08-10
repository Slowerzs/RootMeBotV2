from peewee import *
from database.models.base_model import *


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

