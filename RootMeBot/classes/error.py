class PremiumChallenge(Exception):
	"""Exeception raised when requesting a premium challenge (not available without a premium API KEY)"""
	def __init__(self, idx) -> None:
		self.idx = idx
	def __str__(self) -> str:
		return f"Premium challenge : {self.idx}"

class UnknownChallenge(Exception):
	"""Exception raised when requesting an unknown challenge id"""
	def __init__(self, idx) -> None:
		self.idx = idx
	def __str__(self) -> str:
		return f"Error unknown challenge : {self.idx}"


class UnknownUser(Exception):
	"""Exception raised when requesting an unknown user"""
	def __init__(self, unknown_usr) -> None:
		self.username = unknown_usr
	def __str__(self) -> str:
		return f"Error unknown username : {self.username}"


class Banned(Exception):
	"""Exception raised when banned"""
	def __init__(self, time) -> None:
		self.time = time
	def __str__(self) -> str:
		return f"Banned at : {self.time}"
