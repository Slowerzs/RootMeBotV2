"""Module that manages sending notification on discord"""
from classes.auteur import AuteurData
from classes.challenge import ChallengeData


Solves = list[tuple[AuteurData, ChallengeData, int, bool]]
Challenges = list[ChallengeData]
Solve = tuple[AuteurData, ChallengeData]


class NotificationManager():
    """Class that manages sending messages in discord"""

    def __init__(self) -> None:
        self.new_challenges = []
        self.new_solves = []


    def add_solve_to_queue(self, val: Solve, above: tuple[str, int], is_blood: bool) -> None:
        """Adds a new solve by someone in the queue"""
        auteur = val.validation_auteur # type: ignore
        challenge = val.validation_challenge # type: ignore

        if not challenge:
            return

        self.new_solves.append((auteur, challenge, above, is_blood))

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
        output += f"""Solves in queue : [{', '.join([str(chall.idx) + ' by ' + aut.username for aut, chall, _ in self.new_solves])}]"""
        return output
