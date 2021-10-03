import discord
import aiohttp

from html import unescape

from database.manager import DatabaseManager
from discord.channel import TextChannel

from classes.enums import Color, Stats
from classes.views import ScoreboardView

from database.models.auteur_model import Auteur
from database.models.scoreboard_model import Scoreboard
from database.models.challenge_model import Challenge

Auteurs = list[Auteur]
Challenges = list[Challenge]

async def init_start(channel: TextChannel) -> None:
    """First time running message"""

    message_title = f"Welcome ! :smile:"

    message = f'This seems to be the first time running the bot, please wait while the database is being initialized !'

    embed = discord.Embed(color=Color.INFO_BLUE.value, title=message_title, description=message)
    await channel.send(embed=embed) 

async def incorrect_usage(channel: TextChannel) -> None:

    message_title = 'Error :frowning:'
    message = f'See !help'
    embed = discord.Embed(color=Color.ERROR_RED.value, title=message_title, description=message)
    await channel.send(embed=embed) 


async def init_end(channel: TextChannel) -> None:
    """Initialization complete"""

    message_title = f'All done !'

    message = f'You can now add users ! See !help for more infos'

    embed = discord.Embed(color=Color.INFO_BLUE.value, title=message_title, description=message)
    await channel.send(embed=embed) 



async def send_new_solve(channel: TextChannel, chall: Challenge, aut: Auteur, above: tuple[str, int], is_blood: bool) -> None:
    """Posts a new solve in the right channel"""

    if is_blood:
        emoji = ':drop_of_blood:'
    elif chall.difficulty == "Très difficile":
        emoji = ':fire:'
    else:
        emoji = ':partying_face:'

    message_title = f'New challenge solved by {aut.username} {emoji}'
    
    message = f' • {unescape(chall.title)} ({chall.score} points)'
    message += f'\n • Category: {chall.category}'
    message += f'\n • Difficulty: {chall.difficulty}'
    message += f'\n • New score: {aut.score}'
    message += f'\n • Validations: {chall.validations}'

    embed = discord.Embed(color=Color.NEW_YELLOW.value, title=message_title, description=message)
    
    if above[1]:
        footer = f'{above[1] - aut.score} points to overtake {above[0]}'
        embed.set_footer(text=footer)

    await channel.send(embed=embed)


async def send_new_challenge(channel: TextChannel, chall: Challenge) -> None:
    """Posts a new challenge in the right channel"""

    ping = f'<@&{Color.PING_ROLE_ROOTME}>'
    message_title = f'New Challenge ! :open_mouth:'

    message = f' • {unescape(chall.title)} ({chall.score} points)'
    message += f'\n • Category: {chall.category}'
    message += f'\n • Difficulty: {chall.difficulty}'

    embed = discord.Embed(color=Color.NEW_YELLOW.value, title=message_title, description=message)
    await channel.send(ping, embed=embed)


async def scoreboard(channel: TextChannel, database_manager: DatabaseManager) -> None:

   users = await database_manager.get_all_users_from_db()

   if not users:
       embed = discord.Embed(color=0xff0000, title='Error', description='No users in database :frowning:')

   else:
       users.sort(key=lambda x: x.score, reverse=True)
       message_title = f'Scoreboard'
       message = ''
       for user in users:
           message += f' • • • {user.username} --> {user.score} \n'

       embed = discord.Embed(color=Color.SCOREBOARD_WHITE.value, title=message_title, description=message)

   await channel.send(embed=embed)


async def added_ok(channel: TextChannel, username: str) -> None:
    
    message_title = 'Success'
    message = f'{username} was succesfully added :+1:'

    embed = discord.Embed(color=Color.SUCCESS_GREEN.value, title=message_title, description=message)
    await channel.send(embed=embed)

async def cant_find_user(channel: TextChannel, data: str) -> None:
    
    message_title = 'Error'
    message = f'Cant find user {data} :frowning:'

    embed = discord.Embed(color=Color.ERROR_RED.value, title=message_title, description=message)

    await channel.send(embed=embed)

async def cant_find_challenge(channel: TextChannel, data: str) -> None:
    
    message_title = 'Error'
    message = f'Cant find challenge {data} :frowning:'

    embed = discord.Embed(color=Color.ERROR_RED.value, title=message_title, description=message)

    await channel.send(embed=embed)

async def cant_find_scoreboard(channel: TextChannel, data: str) -> None:
    
    message_title = 'Error'
    message = f'Cant find scoreboard {data} :frowning:'

    embed = discord.Embed(color=Color.ERROR_RED.value, title=message_title, description=message)

    await channel.send(embed=embed)



async def removed_ok(channel: TextChannel, username: str) -> None:
    
    message_title = 'Success'
    message = f'{username} was succesfully removed :wave:'

    embed = discord.Embed(color=Color.SUCCESS_GREEN.value, title=message_title, description=message)
    await channel.send(embed=embed)



async def possible_users(channel: TextChannel, auteurs: Auteurs) -> None:

    message_title = 'Possibles users'
    
    message = ''
    for auteur in auteurs:
        message += f' • • • {auteur.username}: {auteur.score} points --> ID {auteur.idx}\n'

    embed = discord.Embed(color=Color.INFO_BLUE.value, title=message_title, description=message)
    await channel.send(embed=embed)


async def who_solved(channel: TextChannel, chall: Challenge) -> None:
    
    message_title = f'Solvers of {unescape(chall.title)} :sunglasses:'
    message = ''
    for auteur in chall.solvers:
        message += f' • • • {auteur.username}\n' 


    embed = discord.Embed(color=Color.INFO_BLUE.value, title=message_title, description=message)
    await channel.send(embed=embed)


async def multiple_challenges(channel: TextChannel, challenges: Challenges) -> None:

    message_title = f'Multiple challenges found :thinking:'

    embed = discord.Embed(color=Color.ERROR_RED.value, title=message_title)
    
    first_column = ''
    second_column = ''
    for chall in challenges:
        first_column += f'\n{unescape(chall.title)}'
        second_column += f'\n{chall.idx}'

    embed.add_field(name=f'Title', value=first_column, inline=True)
    embed.add_field(name=f'ID', value=second_column, inline=True)

    await channel.send(embed=embed)



async def multiple_users(channel: TextChannel, auteurs: Auteurs) -> None:
    message_title = f'Multiple users match :thinking:'
    first_column = ''
    second_column = ''
    third_column = ''

    embed = discord.Embed(color=Color.ERROR_RED.value, title=message_title)
    
    for aut in auteurs:
        first_column += f'\n{aut.username}'
        second_column +=  f'\n{aut.score}'
        third_column +=  f'\n{aut.idx}'

    embed.add_field(name=f'Username', value=first_column, inline=True)
    embed.add_field(name=f'Score', value=second_column, inline=True)
    embed.add_field(name=f'ID', value=third_column, inline=True)
    await channel.send(embed=embed)


async def profile(channel: TextChannel, auteur: Auteur, stats_glob: list[int], image_url: str) -> None:

    message_title = f'Profile of {auteur.username}'
    
    solves = {
            Stats.WEB_CLIENT : len([i for i in auteur.validations if i.category == 'Web - Client']),
            Stats.APP_SCRIPT : len([i for i in auteur.validations if i.category == 'App - Script']),
            Stats.PROGRAMMING : len([i for i in auteur.validations if i.category == 'Programmation']),
            Stats.CRACKING : len([i for i in auteur.validations if i.category == 'Cracking']),
            Stats.NETWORK : len([i for i in auteur.validations if i.category == 'Réseau']),
            Stats.APP_SYSTEM : len([i for i in auteur.validations if i.category == 'App - Système']),
            Stats.WEB_SERVER : len([i for i in auteur.validations if i.category == 'Web - Serveur']),
            Stats.CRYPTANALYSIS : len([i for i in auteur.validations if i.category == 'Cryptanalyse']),
            Stats.STEGANOGRAPHY : len([i for i in auteur.validations if i.category == 'Stéganographie']),
            Stats.REALIST : len([i for i in auteur.validations if i.category == 'Réaliste']),
            Stats.FORENSICS : len([i for i in auteur.validations if i.category == 'Forensic'])
            }

    first_column = f'**\nWeb Client**'
    first_column += f'\n{solves[Stats.WEB_CLIENT]}/{stats_glob[Stats.WEB_CLIENT]}'
    first_column += f'\n**App-Script**'
    first_column += f'\n{solves[Stats.APP_SCRIPT]}/{stats_glob[Stats.APP_SCRIPT]}'
    first_column += f'\n**Programmation**'
    first_column += f'\n{solves[Stats.PROGRAMMING]}/{stats_glob[Stats.PROGRAMMING]}'
    first_column += f'\n**Cracking**'
    first_column += f'\n{solves[Stats.CRACKING]}/{stats_glob[Stats.CRACKING]}'
    first_column += f'\n**Reseau**'
    first_column += f'\n{solves[Stats.NETWORK]}/{stats_glob[Stats.NETWORK]}'
    first_column += f'\n**App-Système**'
    first_column += f'\n{solves[Stats.APP_SYSTEM]}/{stats_glob[Stats.APP_SYSTEM]}'

    second_column = f'**\nWeb Serveur**'
    second_column += f'\n{solves[Stats.WEB_SERVER]}/{stats_glob[Stats.WEB_SERVER]}'
    second_column += f'\n**Cryptanalyse**'
    second_column += f'\n{solves[Stats.CRYPTANALYSIS]}/{stats_glob[Stats.CRYPTANALYSIS]}'
    second_column += f'\n**Steganographie**'
    second_column += f'\n{solves[Stats.STEGANOGRAPHY]}/{stats_glob[Stats.STEGANOGRAPHY]}'
    second_column += f'\n**Realiste**'
    second_column += f'\n{solves[Stats.REALIST]}/{stats_glob[Stats.REALIST]}'
    second_column += f'\n**Forensic**'
    second_column += f'\n{solves[Stats.FORENSICS]}/{stats_glob[Stats.FORENSICS]}'

    embed = discord.Embed(color=Color.INFO_BLUE.value, title=message_title)

    embed.add_field(name=f'Score: {auteur.score}', value=first_column, inline=True)
    embed.add_field(name=f'**\n**', value=f'**\n**', inline=True)
    embed.add_field(name=f'Rank: {auteur.rank}', value=second_column, inline=True)

    embed.set_thumbnail(url=image_url)
        

    await channel.send(embed=embed)



async def usage(channel: TextChannel) -> None:


    message_title = f'Error'
    message = f'Incorrect usage, see !help'

    embed = discord.Embed(color=Color.ERROR_RED.value, title=message_title, description=message)
    await channel.send(embed=embed)

async def lang(channel: TextChannel, lang: str) -> None:

    message_title = f"Lang changed"
    message = f'The lang for the next search has been updated ! :flag_{lang}:'
    embed = discord.Embed(color=Color.SUCCESS_GREEN.value, title=message_title, description=message)
    await channel.send(embed=embed)

async def unknown_lang(channel: TextChannel, lang: str) -> None:
    message_title = f"Unknown lang"
    message = f'Can\'t find lang {lang}. Available languages are : "en", "fr", "de", "es", "ru"'
    embed = discord.Embed(color=Color.ERROR_RED.value, title=message_title, description=message)
    await channel.send(embed=embed)


async def add_scoreboard(channel: TextChannel, sc: Scoreboard) -> None:
    message_title = f"Scoreboard Created"
    message = f'Scoreboard {sc.name} was successfully created (id {sc.idx}) :+1:'
    embed = discord.Embed(color=Color.SUCCESS_GREEN.value, title=message_title, description=message)
    await channel.send(embed=embed)

async def manage_user(channel: TextChannel, db_manager: DatabaseManager, auteur: Auteur) -> None:
    message_title = 'Edit user'
    message = f'Choose the scoreboards {auteur.username} is part of'
    view = ScoreboardView(db_manager, auteur)
    embed = discord.Embed(color=Color.SCOREBOARD_WHITE.value, title=message_title, description=message)
    await channel.send(embed=embed, view=view)



