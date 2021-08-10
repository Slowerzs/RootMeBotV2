from classes.auteur import AuteurData
from classes.challenge import ChallengeData


Solves = list[tuple[AuteurData, ChallengeData]]
Challenges = list[ChallengeData]
Solve = tuple[AuteurData, ChallengeData]


class NotificationManager():

	def __init__(self) -> None:
		self.new_challenges = []
		self.new_solves = []


	def add_solve_to_queue(self, solve: Solve) -> None:
		"""Adds a new solve by someone in the queue"""
		auteur = solve[0]
		challenge = solve[1]

		if not challenge:
			return

		self.new_solves.append((auteur, challenge))
		print(self)

	def get_solve_queue(self) -> Solves:
		"""Returns the currently enqueued solves"""
		queue = [self.new_solves.pop() for i in range(len(self.new_solves))]
		return queue

	def add_chall_to_queue(self, challenge: ChallengeData) -> None:
		"""Adds a new challenge in the queue"""
		self.new_challenges.append(challenge)
		

	def get_chall_queue(self) -> Challenges:
		"""Returns the currently enqueued challenges"""
		queue = [chall for chall in self.new_challenges]
		self.new_challenges = []
		return queue

	def __str__(self) -> str:
		output = f"""Challenge queue : [{', '.join([str(chall.idx) for chall in self.new_challenges])}]\n"""
		output += f"""Solves in queue : [{', '.join([str(chall.idx) + ' by ' + aut.username for aut, chall in self.new_solves])}]"""
		return output



