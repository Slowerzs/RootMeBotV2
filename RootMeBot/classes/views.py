"""All views for discord messages"""
import discord
from discord.channel import TextChannel
from discord.utils import escape_markdown

import asyncio

from html import unescape

from database.models.scoreboard_model import Scoreboard
from database.models.auteur_model import Auteur
from database.models.challenge_model import Challenge

from database.manager import DatabaseManager

import utils.messages as utils


class ManageButton(discord.ui.Button):
    """Button to choose which scoreboard"""
    def __init__(self, sc: Scoreboard, y: int, status: bool):
        self.sc = sc
        
        if sc.name == 'global':
            super().__init__(style=discord.ButtonStyle.success, label=sc.name, row=y, disabled=True)
        elif status:
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
    """View to manage scoreboards"""
    def __init__(self, db_manager: DatabaseManager, auteur: Auteur):
        super().__init__()
        self.database_manager = db_manager
        self.auteur = auteur

        scoreboards = self.database_manager.get_all_scoreboards()

        for idx, sc in enumerate(scoreboards):
            #maximum 5 buttons per row
            self.add_item(ManageButton(sc, idx // 5, sc.name in [i.name for i in self.auteur.scoreboards]))

    async def add_to_sc(self, scoreboard: Scoreboard):
        return await self.database_manager.add_to_scoreboard(self.auteur.idx, scoreboard.name)

    async def remove_from_sc(self, scoreboard: Scoreboard):
        return await self.database_manager.remove_from_scoreboard(self.auteur.idx, scoreboard.name)



class DropdownScoreboard(discord.ui.Select):
    """Dropdown to chosse which scoreboard"""
    def __init__(self, scoreboards: list[Scoreboard]):

        options = [
            discord.SelectOption(label=escape_markdown(i.name), description='') for i in scoreboards
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


class MultipleChallButton(discord.ui.Select):
    def __init__(self, challenges: list[Challenge]):

        options = [
            discord.SelectOption(label=unescape(i.title), description=f'{i.category} - {i.score} points - {i.difficulty}', value=str(i.idx)) for i in challenges
        ]

        super().__init__(placeholder='Choose the challenge', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await self.view.show_challenge(self.values[0])

class MultipleChallFoundView(discord.ui.View):
    def __init__(self, channel: TextChannel, challenges: list[Challenge], Session):
        super().__init__()
        self.Session = Session
        self.channel = channel
        self.challenges = challenges

        self.add_item(MultipleChallButton(challenges))

    async def show_challenge(self, idx: str):
        chall = next(filter(lambda x: x.idx == int(idx), self.challenges))
        await utils.who_solved(self.channel, chall, self.Session)

class MultipleUserButton(discord.ui.Select):
    def __init__(self, users: list[Auteur]):

        options = [
                discord.SelectOption(label=escape_markdown(i.username), description=f'{i.score} points - ID {i.idx}', value=str(i.idx)) for i in users
        ]

        super().__init__(placeholder='Which user :', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction): 
        await self.view.add_user(self.values[0])

class MultipleUserFoundView(discord.ui.View):
    def __init__(self, channel: TextChannel, db_manager: DatabaseManager, users: list[Auteur]):
        super().__init__()
        self.channel = channel
        self.database_manager = db_manager
        self.users = users

        self.add_item(MultipleUserButton(users))

    async def add_user(self, idx: str):
        auteur = next(filter(lambda x: x.idx == int(idx), self.users))
        
        asyncio.create_task(self.database_manager.add_user(auteur.idx))

        await utils.added_ok(self.channel, 'User')





