import discord

from database.models.scoreboard_model import Scoreboard
from database.models.auteur_model import Auteur

from database.manager import DatabaseManager

class ScoreboardButton(discord.ui.Button):
    def __init__(self, sc: Scoreboard, y: int):
        self.sc = sc
        super().__init__(style=discord.ButtonStyle.secondary, label=sc.name, row=y)


    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        
        if self.style == discord.ButtonStyle.secondary: 
            self.view.add_to_sc(self.sc)
            self.style = discord.ButtonStyle.success
        else:
            self.view.remove_from_sc(self.sc)
            self.style = discord.ButtonStyle.secondary


class ScoreboardView(discord.ui.View):
    def __init__(self, db_manager: DatabaseManager, auteur: Auteur):
        super().__init__()
        self.database_manager = db_manager
        self.auteur = auteur

        scoreboards = await self.database_manager.get_all_scoreboards()

        for idx, sc in enumerate(scoreboards):
            #maximum 5 buttons per row
            self.add_item(ScoreboardButton(sc), idx // 5)

    def add_to_sc(self, scoreboard: Scoreboard):
        return self.database_manager.add_to_scoreboard(self.auteur.idx, scoreboard.idx)

    def remove_from_sc(self, scoreboard: Scoreboard):
        return self.database_manager.remove_from_scoreboard(self.auteur.idx, scoreboard.idx)




