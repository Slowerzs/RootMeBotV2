"""Module for the discord bot"""
import asyncio

import discord
import utils.messages as utils
from classes.error import *
from constants import BOT_PREFIX
from database.manager import DatabaseManager
from discord import Embed
from discord.ext import commands
from discord.ext.commands.context import Context
from notify.manager import NotificationManager


class RootMeBot():
    """Main class for the discord bot"""

    def __init__(self, database_manager: DatabaseManager, notification_manager: NotificationManager, *args, **kwargs) -> None:


        self.intents = discord.Intents.default()
        self.description = """A discord bot to keep up with your progression on www.root-me.org"""
        self.bot = commands.Bot(command_prefix=BOT_PREFIX, description=self.description, intents=self.intents)

        self.notification_manager = notification_manager
        self.database_manager = database_manager

        self.init_done = False


    async def after_init(self, func):
        """Ensures that the init is done"""
        return self.init_done

    def check_channel(self):
        """Ensures that the message is in the correct channel"""
        async def predicate(context):
            if context.message.channel.id == self.BOT_CHANNEL:
                return True
            print(f"Check channel not OK : {context.message.channel.id} - {self.BOT_CHANNEL}")
            return False
        return commands.check(predicate)

    def get_command_args(self, context: commands.context.Context) -> list[str]:
        """Returns args from message"""
        return context.message.content.strip().split()[1:]

    async def init_db(self) -> None:
        """Checks if the database seems populated or not (first run)"""
        await self.bot.wait_until_ready()
        print("Starting...")
        channel = self.bot.get_channel(self.BOT_CHANNEL)

        await self.database_manager.create_scoreboard('global')

        if self.database_manager.count_challenges() < 500:

            await utils.init_start(channel)
            await self.database_manager.update_challenges(init=True)
            await utils.init_end(channel)

        print("Init DB done")
        self.init_done = True


    async def cron_display(self) -> None:
        """Checks if there are new enqueued solves or challenges, and posts them in the right channel"""

        await self.bot.wait_until_ready()

        while not self.init_done:
            await asyncio.sleep(1)

        channel = self.bot.get_channel(self.BOT_CHANNEL)

        while True:

            for aut, chall, score_above, is_blood in self.notification_manager.get_solve_queue():
                if chall:
                    await utils.send_new_solve(channel, chall, aut, score_above, is_blood)


            for chall in self.notification_manager.get_chall_queue():
                await utils.send_new_challenge(channel, chall)

            await asyncio.sleep(1)

    async def cron_check_challs(self) -> None:
        """Checks for new challs"""

        await self.bot.wait_until_ready()

        while not self.init_done:
            await asyncio.sleep(1)

        #while True:

            #await self.database_manager.update_challenges()
            #await asyncio.sleep(3600)

        print("OK challs")


    async def cron_check_solves(self) -> None:
        """Checks for new solves"""
        await self.bot.wait_until_ready()

        while not self.init_done:
            await asyncio.sleep(1)

        print("OK solves")

        while True:
            await self.database_manager.update_users()

    def catch(self):
        """Catch discord event"""
        @self.bot.event
        async def on_ready():
                    for server in self.bot.guilds:
                        print(f'RootMeBot is starting on the following server: "{server.name}" !')



        @self.bot.command(description='Remove user by ID', pass_context=True)
        @commands.check(self.after_init)
        @self.check_channel()
        async def remove_user(context: Context):
            """<id or username>"""

            args = self.get_command_args(context)
            if len(args) < 1:
                await utils.usage(context.message.channel)
                return
            args = str(' '.join(args))

            try:
                idx = int(args)

                username = await self.database_manager.remove_user_from_db(idx)
                if aut:
                    await utils.removed_ok(context.message.channel, username)
                else:
                    #Case where username is full numbers
                    args = str(args)
                    raise ValueError()

            except ValueError:
                auteurs = await self.database_manager.remove_user_from_db_by_name(args)
                if len(auteurs) > 1:
                    await utils.multiple_users(context.message.channel, auteurs)
                elif len(auteurs) == 0:
                    await utils.cant_find_user(context.message.channel, args)
                else:
                    await utils.removed_ok(context.message.channel, args)


        @self.bot.command(description='Show scoreboard')
        @commands.check(self.after_init)
        @self.check_channel()
        async def scoreboard(context: Context) -> None:
            """ """

            args = self.get_command_args(context)
            if len(args) < 1:
                await utils.scoreboard_choice(context.message.channel, self.database_manager)
                return
            else:
                name = ' '.join(args)
                await utils.scoreboard(context.message.channel, self.database_manager, name)

        @self.bot.command(description='Add user by ID')
        @commands.check(self.after_init)
        @self.check_channel()
        async def add_user_id(context: Context) -> None:
            """<id>"""
            args = self.get_command_args(context)
            if len(args) < 1:
                await utils.usage(context.message.channel)
                return

            try:
                idx = int(args[0])
            except ValueError:
                await utils.incorrect_usage(context.message.channel, args[0])
                return

            aut = await self.database_manager.add_user(idx)
            if aut:
                await utils.added_ok(context.message.channel, aut.username)
            else:
                await utils.cant_find_user(context.message.channel, idx)

        @self.bot.command(description='Add user by name')
        @commands.check(self.after_init)
        @self.check_channel()
        async def add_user(context: Context) -> None:
            """<username>"""
            username = ' '.join(self.get_command_args(context))
            auteurs = await self.database_manager.search_user(username)
            if len(auteurs) > 25:
                await utils.many_users(context.message.channel, auteurs)

            elif len(auteurs) > 1:
                await utils.possible_users(context.message.channel, self.database_manager, auteurs)

            elif len(auteurs) == 1:
                aut = await self.database_manager.add_user(auteurs[0].idx)
                await utils.added_ok(context.message.channel, aut.username)
            else:
                await utils.cant_find_user(context.message.channel, username)


        @self.bot.command(description='Create a new scoreboard')
        @commands.check(self.after_init)
        @self.check_channel()
        async def add_scoreboard(context: Context) -> None:
            """<scoreboard name>"""

            args = ' '.join(self.get_command_args(context))

            scoreboard = await self.database_manager.get_scoreboard(args)
            if not scoreboard:
                scoreboard = await self.database_manager.create_scoreboard(args)

            await utils.add_scoreboard(context.message.channel, scoreboard)


        @self.bot.command(description='Deletes a scoreboard')
        @commands.check(self.after_init)
        @self.check_channel()
        async def remove_scoreboard(context: Context) -> None:
            """<scoreboard name>"""

            args = ' '.join(self.get_command_args(context))

            res = await self.database_manager.remove_scoreboard(args)
            if not res:
               await utils.cant_find_scoreboard(context.message.channel, args)
            else:
                await utils.removed_ok(context.message.channel, args)





        @self.bot.command(description='Change the lang for the next search')
        @commands.check(self.after_init)
        @self.check_channel()
        async def user_lang(context: Context) -> None:
            """<lang>"""
            args = self.get_command_args(context)

            if len(args) < 1:
                await utils.usage(context.message.channel)
                return

            lang = args[0].lower()

            if lang in ["en", "fr", "es", "ru", "de"]:
                self.database_manager.rootme_api.lang = lang

                #Send OK message
                if lang == "en":
                    lang = "gb"

                await utils.lang(context.message.channel, lang)
                return
            else:
                await utils.unknown_lang(context.message.channel, lang)



        @self.bot.command(description='Search user by username')
        @commands.check(self.after_init)
        @self.check_channel()
        async def search_user(context: Context) -> None:
            """<username>"""

            args = self.get_command_args(context)
            if len(args) < 1:
                await utils.usage(context.message.channel)
                return
            search = str(' '.join(args))

            auteurs = await self.database_manager.search_user(search)
            print(auteurs)

            if auteurs:
                await utils.many_users(context.message.channel, auteurs)
            else:
                await utils.cant_find_user(context.message.channel, search)


        @self.bot.command(description='Shows stats of a user')
        @commands.check(self.after_init)
        @self.check_channel()
        async def profile(context: Context) -> None:
            """<id or username>"""

            args = self.get_command_args(context)
            if len(args) < 1:
                await utils.usage(context.message.channel)
                return

            search = str(' '.join(args))

            try:
                search_id = int(search)
                auteur = await self.database_manager.get_user_from_db(search_id)
                if not auteur:
                    await utils.cant_find_user(context.message.channel, search)
                    return

            except ValueError:
                auteurs = await self.database_manager.search_user_from_db(search)

                if len(auteurs) == 0:
                    await utils.cant_find_user(context.message.channel, search)
                    return
                elif len(auteurs) > 1:
                    await utils.multiple_users(context.message.channel, auteurs)
                    return
                else:
                    auteur = auteurs[0]


            image_profile = await self.database_manager.rootme_api.get_image_png(auteur.idx)

            if not image_profile:
                image_profile = await self.database_manager.rootme_api.get_image_jpg(auteur.idx)
            if not image_profile:
                image_profile = 'https://www.root-me.org/IMG/auton0.png'

            stats_glob = await self.database_manager.get_stats()
            stats_auteur = await self.database_manager.get_stats_auteur(auteur)
            data = (auteur.username, auteur.score, auteur.rank)

            await utils.profile(context.message.channel, data, stats_auteur, stats_glob, image_profile)



        @self.bot.command(description='Shows the view to manage a user')
        @commands.check(self.after_init)
        @self.check_channel()
        async def manage_user(context: Context) -> None:
            """<username>"""
            args = self.get_command_args(context)
            if len(args) < 1:
                await utils.usage(context.message.channel)
                return

            search = str(' '.join(args))

            try:
                search_id = int(search)
                auteur = await self.database_manager.get_user_from_db(search_id)
                if not auteur:
                    await utils.cant_find_user(context.message.channel, search)
                    return

            except ValueError:
                auteurs = await self.database_manager.search_user_from_db(search)

                if len(auteurs) == 0:
                    await utils.cant_find_user(context.message.channel, search)
                    return
                elif len(auteurs) > 1:
                    await utils.multiple_users(context.message.channel, auteurs)
                    return
                else:
                    auteur = auteurs[0]



                await utils.manage_user(context.message.channel, self.database_manager, auteur)




        @self.bot.command(description='Shows who solved a challenge')
        @commands.check(self.after_init)
        @self.check_channel()
        async def who_solved(context: Context) -> None:
            """<challenge name or id>"""

            args = self.get_command_args(context)
            if len(args) < 1:
                await utils.usage(context.message.channel)
                return
            search = str(' '.join(args))

            try:
                #Search by id
                search_id = int(search)

                chall = await self.database_manager.get_challenge_from_db(search_id)

                if chall:
                    await utils.who_solved(context.message.channel, chall, self.database_manager.session_maker)
                else:
                    await utils.cant_find_challenge(context.message.channel, search)

            except ValueError:
                #Search by name
                results = await self.database_manager.search_challenge_from_db(search)
                if len(results) > 25:
                    await utils.many_challenges(context.message.channel, results)

                elif len(results) > 1:
                    await utils.multiple_challenges(context.message.channel, results, self.database_manager.session_maker)

                elif len(results) == 1:
                    chall = results[0]
                    await utils.who_solved(context.message.channel, chall, self.database_manager.session_maker)

                else:
                    await utils.cant_find_challenge(context.message.channel, search)

    def start(self, TOKEN, BOT_CHANNEL):
        """Starts the bot"""

        self.BOT_CHANNEL = BOT_CHANNEL
        print("START")
        self.catch()

        self.database_manager.loop = self.bot.loop

        self.bot.loop.create_task(self.init_db())

        self.worker = self.bot.loop.create_task(self.database_manager.rootme_api.worker())
        self.check_solves = self.bot.loop.create_task(self.cron_check_solves())
        self.check_challs = self.bot.loop.create_task(self.cron_check_challs())

        self.bot.loop.create_task(self.cron_display())


        self.bot.run(TOKEN)
