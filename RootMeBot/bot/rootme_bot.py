import discord
import asyncio
import functools
import traceback
import time

from database.manager import DatabaseManager
from database.models.challenge_model import Challenge
from database.models.auteur_model import Auteur

from notify.manager import NotificationManager

from discord.ext import commands
from discord.ext.commands.context import Context
from discord import Embed

from classes.error import *
from classes.challenge import ChallengeData
from classes.auteur import AuteurData

from constants import BOT_PREFIX, LOG_PATH

import utils.messages as utils



class RootMeBot():

    def __init__(self, database_manager: DatabaseManager, notification_manager: NotificationManager, *args, **kwargs) -> None:

        self.intents = discord.Intents.default()
        self.description = """A discord bot to keep up with your progression on www.root-me.org"""
        self.bot = commands.Bot(command_prefix=BOT_PREFIX, description=self.description, intents=self.intents)
        
        self.notification_manager = notification_manager
        self.database_manager = database_manager
    
        self.init_done = False

    async def banned(self):
        await self.bot.change_presence(status=discord.Status.do_not_disturb, activity=discord.Game(name="Banned 😞"))

    async def unbanned(self):
        await self.bot.change_presence(status=discord.Status.online, activity=discord.Game(name="😎"))


    async def after_init(self, func):
        print("Check OK after_init")
        return self.init_done

    def check_channel(self):
        async def predicate(context):
            return context.message.channel.id == self.BOT_CHANNEL
        return commands.check(predicate)

    def get_command_args(self, context: commands.context.Context) -> list[str]:
        """Returns args from message"""
        return context.message.content.strip().split()[1:]

    async def init_db(self) -> None:
        """Checks if the database seems populated or not (first run)"""
        await self.bot.wait_until_ready()
        await self.unbanned()
        print("Starting...")
        channel = self.bot.get_channel(self.BOT_CHANNEL)

        if self.database_manager.count_challenges() < 300:

            await utils.init_start(channel)
            await self.database_manager.update_challenges(init=True)
            await utils.init_end(channel)

        print("Done")
        self.init_done = True
        print(self.init_done)


    async def cron_display(self) -> None:
        """Checks if there are new enqueued solves or challenges, and posts them in the right channel"""

        await self.bot.wait_until_ready()

        while not self.init_done:
            await asyncio.sleep(1)
        
        channel = self.bot.get_channel(self.BOT_CHANNEL)

        while True:

            for aut, chall, score_above in self.notification_manager.get_solve_queue():
                if chall:
                    db_chall = Challenge.select().where(Challenge.idx == chall.idx).get() 
                    if len(db_chall.solvers) <= 2:
                        is_blood = True
                    else:
                        is_blood = False
                    await utils.send_new_solve(channel, chall, aut, score_above, is_blood)
                    

            for chall in self.notification_manager.get_chall_queue():
                await utils.send_new_challenge(channel, chall)

            await asyncio.sleep(1)

    async def cron_check_challs(self) -> None:
        """Checks for new challs"""
        
        await self.bot.wait_until_ready()

        while not self.init_done:
            await asyncio.sleep(1)

        print("OK challs")
        while True:
            
            await self.database_manager.update_challenges()
            await asyncio.sleep(300)


    async def cron_check_solves(self) -> None:
        """Checks for new solves"""
        await self.bot.wait_until_ready()

        while not self.init_done:
            await asyncio.sleep(1)
        
        print("OK solves")

        while True:

            await self.database_manager.update_users()
            await asyncio.sleep(1)

    def catch(self):
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

                aut = await self.database_manager.remove_user_from_db(idx)  
                if aut:
                    await utils.removed_ok(context.message.channel, aut.username)
                else:
                    #Case where username is full numbers
                    args = str(args)
                    raise ValueError()

            except ValueError:
                auteurs = Auteur.select().where(Auteur.username == args)
                if auteurs.count() > 1:
                    
                    all_auteurs = []
                    for aut in auteurs:
                        validations = [i.idx for i in aut.validations]
                        auteur_data = AuteurData(aut.idx, aut.username, aut.score, aut.rank, validations)

                        all_auteurs.append(auteur_data)

                    await utils.multiple_users(context.message.channel, all_auteurs)
                elif auteurs.count() == 0:
                    await utils.cant_find_user(context.message.channel, args)
                else:
                    await self.database_manager.remove_user_from_db(auteurs[0].idx)
                    await utils.removed_ok(context.message.channel, auteurs[0].username)
    

        @self.bot.command(description='Show scoreboard')
        @commands.check(self.after_init)
        @self.check_channel()
        async def scoreboard(context: Context) -> None:
            """ """

            await utils.scoreboard(context.message.channel, self.database_manager)

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
            if len(auteurs) > 1:
                await utils.possible_users(context.message.channel, [aut[0] for aut in auteurs])
            elif len(auteurs) == 1:
                aut = await self.database_manager.add_user(auteurs[0].idx)
                await utils.added_ok(context.message.channel, aut.username)
            else:
                await utils.cant_find_user(context.message.channel, username)


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
            
            if auteurs:
                await utils.possible_users(context.message.channel, auteurs)
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

            nb_web_client = Challenge.select().where(Challenge.category == 'Web - Client').count()
            nb_web_server = Challenge.select().where(Challenge.category == 'Web - Serveur').count()
            nb_app_script = Challenge.select().where(Challenge.category == 'App - Script').count()
            nb_cryptanalyse = Challenge.select().where(Challenge.category == 'Cryptanalyse').count()
            nb_programmation = Challenge.select().where(Challenge.category == 'Programmation').count()
            nb_steganographie = Challenge.select().where(Challenge.category == 'Stéganographie').count()
            nb_cracking = Challenge.select().where(Challenge.category == 'Cracking').count()
            nb_realiste = Challenge.select().where(Challenge.category == 'Réaliste').count()
            nb_reseau = Challenge.select().where(Challenge.category == 'Réseau').count()
            nb_forensic = Challenge.select().where(Challenge.category == 'Forensic').count()
            nb_app_systeme = Challenge.select().where(Challenge.category == 'App - Système').count()

            values = [nb_web_client, nb_web_server, nb_app_script, nb_cryptanalyse, nb_programmation,
                    nb_steganographie, nb_cracking, nb_realiste, nb_reseau, nb_forensic, nb_app_systeme]

            try:
                search_id = int(search)
                auteurs = Auteur.select().where(Auteur.idx == search_id)
                try:
                    aut = auteurs.get()
                except: #To do change to sqlachemy does not exists
                    raise ValueError()

            except ValueError:
                auteurs = Auteur.select().where(Auteur.username.contains(search))
                if auteurs.count() == 0:
                    await utils.cant_find_user(context.message.channel, search)
                    return
                elif auteurs.count() > 1:
                    all_auteurs = []
                    for aut in auteurs:
                        validations = [i.idx for i in aut.validations]
                        auteur_data = AuteurData(aut.idx, aut.username, aut.score, aut.rank, validations)
                        all_auteurs.append(auteur_data)
                    await utils.multiple_users(context.message.channel, all_auteurs)
                    return
                else:
                    aut = auteurs.get()
            

            #
            validations = [i.idx for i in aut.validations]
                    
                        
            solves_web_client = aut.validations.select().where(Challenge.category == 'Web - Client').count()
            solves_web_server = aut.validations.select().where(Challenge.category == 'Web - Serveur').count()
            solves_app_script = aut.validations.select().where(Challenge.category == 'App - Script').count()
            solves_cryptanalyse = aut.validations.select().where(Challenge.category == 'Cryptanalyse').count()
            solves_programmation = aut.validations.select().where(Challenge.category == 'Programmation').count()
            solves_steganographie = aut.validations.select().where(Challenge.category == 'Stéganographie').count()
            solves_cracking = aut.validations.select().where(Challenge.category == 'Cracking').count()
            solves_realiste = aut.validations.select().where(Challenge.category == 'Réaliste').count()
            solves_reseau = aut.validations.select().where(Challenge.category == 'Réseau').count()
            solves_forensic = aut.validations.select().where(Challenge.category == 'Forensic').count()
            solves_app_systeme = aut.validations.select().where(Challenge.category == 'App - Système').count()

            solves = [solves_web_client, solves_web_server, solves_app_script, solves_cryptanalyse, solves_programmation,
                    solves_steganographie, solves_cracking, solves_realiste, solves_reseau, solves_forensic, solves_app_systeme]

            auteur_data = AuteurData(aut.idx, aut.username, aut.score, aut.rank, validations)
            image_profile = await self.database_manager.rootme_api.get_image_png(aut.idx)
            if not image_profile:
                image_profile = await self.database_manager.rootme_api.get_image_jpg(aut.idx)
            if not image_profile:
                image_profile = 'https://www.root-me.org/IMG/auton0.png'

            await utils.profile(context.message.channel, auteur_data, values, solves, image_profile)




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

                chall = Challenge.select().where(Challenge.idx == search_id).get()
                
                all_solvers = []
                for solver in Challenge.select().where(Challenge.idx == search_id).get().solvers:
                    all_solvers.append(solver)

                await utils.who_solved(context.message.channel, all_solvers, chall.title)

            except ValueError:
                #Search by name
                results = Challenge.select().where(Challenge.title.contains(search))
                if results.count() > 1:

                    challs = []
                    for chall in results:
                        challenge_data = ChallengeData(chall.idx, chall.title, chall.category, 
                                        chall.description, chall.score, chall.difficulty, chall.date, chall.validations)
                        challs.append(challenge_data)
                        
                        
                    await utils.multiple_challenges(context.message.channel, challs)
                elif results.count() == 1:
                    chall = results.get()
                
                    all_solvers = []
                    for solver in chall.solvers:
                        all_solvers.append(solver)

                    await utils.who_solved(context.message.channel, all_solvers, chall.title)   
                else:
                    await utils.cant_find_challenge(context.message.channel, search)

    def start(self, TOKEN, BOT_CHANNEL):
        """Starts the bot"""
        
        self.BOT_CHANNEL = BOT_CHANNEL
        print("START")
        self.catch()
        self.bot.loop.create_task(self.init_db())
        self.check_solves = self.bot.loop.create_task(self.cron_check_solves())
        self.check_challs = self.bot.loop.create_task(self.cron_check_challs())
        self.bot.loop.create_task(self.cron_display())


        self.bot.run(TOKEN)







        
