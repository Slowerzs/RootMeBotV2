import discord
import aiohttp

from html import unescape
from classes.challenge import ChallengeData
from classes.auteur import AuteurData
from database.manager import DatabaseManager
from discord.channel import TextChannel

from constants import SUCCESS_GREEN, SCOREBOARD_WHITE, NEW_YELLOW, INFO_BLUE, ERROR_RED, PING_ROLE_ROOTME


Auteurs = list[AuteurData]
Challenges = list[ChallengeData]

async def init_start(channel: TextChannel) -> None:
    """First time running message"""

    message_title = f"Welcome ! :smile:"

    message = f'This seems to be the first time running the bot, please wait while the database is being initialized !'

    embed = discord.Embed(color=INFO_BLUE, title=message_title, description=message)
    await channel.send(embed=embed) 


async def init_end(channel: TextChannel) -> None:
    """Initialization complete"""

    message_title = f'All done !'

    message = f'You can now add users ! See !help for more infos'

    embed = discord.Embed(color=INFO_BLUE, title=message_title, description=message)
    await channel.send(embed=embed) 



async def send_new_solve(channel: TextChannel, chall: ChallengeData, aut: AuteurData, above: tuple[str, int], is_blood: bool) -> None:
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

    embed = discord.Embed(color=NEW_YELLOW, title=message_title, description=message)
    
    if above[1]:
        footer = f'{above[1] - aut.score} points to overtake {above[0]}'
        embed.set_footer(text=footer)

    await channel.send(embed=embed)


async def send_new_challenge(channel: TextChannel, chall: ChallengeData) -> None:
    """Posts a new challenge in the right channel"""

    ping = f'<@&{PING_ROLE_ROOTME}>'
    message_title = f'New Challenge ! :open_mouth:'

    message = f' • {unescape(chall.title)} ({chall.score} points)'
    message += f'\n • Category: {chall.category}'
    message += f'\n • Difficulty: {chall.difficulty}'

    embed = discord.Embed(color=NEW_YELLOW, title=message_title, description=message)
    await channel.send(ping, embed=embed)


async def scoreboard(channel: TextChannel, database_manager: DatabaseManager) -> None:


    users = await database_manager.get_all_users_from_db()

    if not users:
        
        embed = discord.Embed(color=0xff0000, title='Error', description='No users in database :frowning:')
    else:
        users = sorted(users, key=lambda x: x.score, reverse=True)
        message_title = f'Scoreboard'
        message = ''
        for user in users:
            message += f' • • • {user.username} --> {user.score} \n'

        embed = discord.Embed(color=SCOREBOARD_WHITE, title=message_title, description=message)

    await channel.send(embed=embed)


async def added_ok(channel: TextChannel, username: str) -> None:
    
    message_title = 'Success'
    message = f'{username} was succesfully added :+1:'

    embed = discord.Embed(color=SUCCESS_GREEN, title=message_title, description=message)
    await channel.send(embed=embed)

async def cant_find_user(channel: TextChannel, data: str) -> None:
    
    message_title = 'Error'
    message = f'Cant find user {data} :frowning:'

    embed = discord.Embed(color=ERROR_RED, title=message_title, description=message)

    await channel.send(embed=embed)

async def cant_find_challenge(channel: TextChannel, data: str) -> None:
    
    message_title = 'Error'
    message = f'Cant find challenge {data} :frowning:'

    embed = discord.Embed(color=ERROR_RED, title=message_title, description=message)

    await channel.send(embed=embed)


async def removed_ok(channel: TextChannel, username: str) -> None:
    
    message_title = 'Success'
    message = f'{username} was succesfully removed :wave:'

    embed = discord.Embed(color=SUCCESS_GREEN, title=message_title, description=message)
    await channel.send(embed=embed)



async def possible_users(channel: TextChannel, auteurs: Auteurs) -> None:

    message_title = 'Possibles users'
    
    message = ''
    for auteur in auteurs:
        message += f' • • • {auteur.username}: {auteur.score} points --> ID {auteur.idx}\n'

    embed = discord.Embed(color=INFO_BLUE, title=message_title, description=message)
    await channel.send(embed=embed)


async def who_solved(channel: TextChannel, auteurs: Auteurs, chall_name: str) -> None:
    
    message_title = f'Solvers of {unescape(chall_name)} :sunglasses:'
    message = ''
    for auteur in auteurs:
        message += f' • • • {auteur.username}\n' 


    embed = discord.Embed(color=INFO_BLUE, title=message_title, description=message)
    await channel.send(embed=embed)


async def multiple_challenges(channel: TextChannel, challenges: Challenges) -> None:

    message_title = f'Multiple challenges found :thinking:'

    embed = discord.Embed(color=ERROR_RED, title=message_title)
    
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

    embed = discord.Embed(color=ERROR_RED, title=message_title)
    
    for aut in auteurs:
        first_column += f'\n{aut.username}'
        second_column +=  f'\n{aut.score}'
        third_column +=  f'\n{aut.idx}'

    embed.add_field(name=f'Username', value=first_column, inline=True)
    embed.add_field(name=f'Score', value=second_column, inline=True)
    embed.add_field(name=f'ID', value=third_column, inline=True)
    await channel.send(embed=embed)


async def profile(channel: TextChannel, auteur: AuteurData, stats_glob: list[int], solves: list[int], image_url: str) -> None:

    message_title = f'Profile of {auteur.username}'
    
    nb_web_client, nb_web_server, nb_app_script, nb_cryptanalyse, nb_programmation, nb_steganographie, nb_cracking, nb_realiste, nb_reseau, nb_forensic, nb_app_systeme = stats_glob
    solves_web_client, solves_web_server, solves_app_script, solves_cryptanalyse, solves_programmation, solves_steganographie, solves_cracking, solves_realiste, solves_reseau, solves_forensic, solves_app_systeme = solves

    first_column = f'**\nWeb Client**'
    first_column += f'\n{solves_web_client}/{nb_web_client}'
    first_column += f'\n**App-Script**'
    first_column += f'\n{solves_app_script}/{nb_app_script}'
    first_column += f'\n**Programmation**'
    first_column += f'\n{solves_programmation}/{nb_programmation}'
    first_column += f'\n**Cracking**'
    first_column += f'\n{solves_cracking}/{nb_cracking}'
    first_column += f'\n**Reseau**'
    first_column += f'\n{solves_reseau}/{nb_reseau}'
    first_column += f'\n**App-Système**'
    first_column += f'\n{solves_app_systeme}/{nb_app_systeme}'

    second_column = f'**\nWeb Serveur**'
    second_column += f'\n{solves_web_server}/{nb_web_server}'
    second_column += f'\n**Cryptanalyse**'
    second_column += f'\n{solves_cryptanalyse}/{nb_cryptanalyse}'
    second_column += f'\n**Steganographie**'
    second_column += f'\n{solves_steganographie}/{nb_steganographie}'
    second_column += f'\n**Realiste**'
    second_column += f'\n{solves_realiste}/{nb_realiste}'
    second_column += f'\n**Forensic**'
    second_column += f'\n{solves_forensic}/{nb_forensic}'

    embed = discord.Embed(color=INFO_BLUE, title=message_title)

    embed.add_field(name=f'Score: {auteur.score}', value=first_column, inline=True)
    embed.add_field(name=f'**\n**', value=f'**\n**', inline=True)
    embed.add_field(name=f'Rank: {auteur.rank}', value=second_column, inline=True)

    embed.set_thumbnail(url=image_url)
        

    await channel.send(embed=embed)



async def usage(channel: TextChannel) -> None:


    message_title = f'Error'
    message = f'Incorrect usage, see !help'

    embed = discord.Embed(color=ERROR_RED, title=message_title, description=message)
    await channel.send(embed=embed)

async def lang(channel: TextChannel, lang: str) -> None:

    message_title = f"Lang changed"
    message = f'The lang for the next search has been updated ! :flag_{lang}:'
    embed = discord.Embed(color=SUCCESS_GREEN, title=message_title, description=message)
    await channel.send(embed=embed)

async def unknown_lang(channel: TextChannel, lang: str) -> None:
    message_title = f"Unknown lang"
    message = f'Can\'t find lang {lang}. Available languages are : "en", "fr", "de", "es", "ru"'
    embed = discord.Embed(color=ERROR_RED, title=message_title, description=message)
    await channel.send(embed=embed)





