import discord
from discord.channel import TextChannel

from database.models.scoreboard_model import Scoreboard
from database.models.auteur_model import Auteur

from database.manager import DatabaseManager

import utils.messages as utils


class ManageButton(discord.ui.Button):
    def __init__(self, sc: Scoreboard, y: int, status: bool):
        self.sc = sc
        if status:
            super().__init__(style=discord.ButtonStyle.success, label=sc.name, row=y)
        else:
            super().__init__(style=discord.ButtonStyle.secondary, label=sc.name, row=y)


    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        
        if self.style == discord.ButtonStyle.secondary: 
            res = await self.view.add_to_sc(self.sc)
            if not res:
                self.disabled = True
            self.style = discord.ButtonStyle.success
        else:
            res = await self.view.remove_from_sc(self.sc)
            if not res:
                self.disabled = True
            self.style = discord.ButtonStyle.secondary

        await interaction.response.edit_message(view=self.view) 


class ManageView(discord.ui.View):

    def __init__(self, db_manager: DatabaseManager, auteur: Auteur):
        super().__init__()
        self.database_manager = db_manager
        self.auteur = auteur

        scoreboards = self.database_manager.get_all_scoreboards()

        for idx, sc in enumerate(scoreboards):
            #maximum 5 buttons per row
            self.add_item(ManageButton(sc, idx // 5, sc.idx in [i.idx for i in self.auteur.scoreboards]))

    async def add_to_sc(self, scoreboard: Scoreboard):
        return await self.database_manager.add_to_scoreboard(self.auteur.idx, scoreboard.name)

    async def remove_from_sc(self, scoreboard: Scoreboard):
        return await self.database_manager.remove_from_scoreboard(self.auteur.idx, scoreboard.name)



class DropdownScoreboard(discord.ui.Select):
    def __init__(self, scoreboards: list[Scoreboard]):

        options = [
            discord.SelectOption(label=i.name, description='') for i in scoreboards
        ]

        super().__init__(placeholder='Choose the scoreboard', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await self.view.show_scoreboard(self.values[0])

class ScoreboardView(discord.ui.View):
    def __init__(self, channel: TextChannel, db_manager: DatabaseManager):
        super().__init__()
        self.database_manager = db_manager
        self.channel = channel

        scoreboards = self.database_manager.get_all_scoreboards()
        
        self.add_item(DropdownScoreboard(scoreboards))

    async def show_scoreboard(self, name: str):
        await utils.scoreboard(self.channel, self.database_manager, name)









