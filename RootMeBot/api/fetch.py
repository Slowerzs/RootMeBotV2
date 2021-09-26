import asyncio
import time
import aiohttp
import json
import functools
from datetime import datetime, timedelta

from asyncio.exceptions import TimeoutError
from aiohttp.client_exceptions import ServerDisconnectedError, ClientConnectorError, ClientPayloadError, ClientOSError, ClientOSError 

from api.extract import *

from classes.auteur import *
from classes.challenge import *
from classes.error import *
from constants import *

Auteurs = list[AuteurShort]
Challenges = list[ChallengeShort]


def async_request(func):
    @functools.wraps(func)
    async def make_request(*args, **kwargs):
        async with args[0].semaphore:
            return await func(*args, args[0].session, **kwargs)

    return make_request
    

class ApiRootMe():

    def __init__(self):
        self.bot = None
        self.semaphore = asyncio.BoundedSemaphore(24)
        self.connector = aiohttp.TCPConnector(limit=24, ttl_dns_cache=300)
        self.session = aiohttp.ClientSession(connector=self.connector)
        self.lang = DEFAULT_LANG
        self.timeout = aiohttp.ClientTimeout(total=3)
        self.ban = datetime.now()

    @async_request
    async def get_user_by_id(self, idx: int, session: aiohttp.ClientSession) -> AuteurData:
        """Retreives an Auteur by id"""
        
        if idx == 0:
            raise UnknownUser(idx)
    
        if datetime.now() < self.ban:
            print(self.ban)
            while datetime.now() < self.ban:
                await asyncio.sleep(1)

            await self.bot.unbanned()


        params = {
            str(int(time.time())): str(int(time.time())),
            }

        try:
            async with session.get(f"{api_base_url}{auteurs_path}/{idx}", params=params, cookies=cookies_rootme, timeout=self.timeout) as r:
                if r.status == 404:
                    self.ban = datetime.now() + timedelta(minutes=0, seconds=10)
                    raise UnknownUser(idx)
        
                elif r.status == 200:
                    user_data = await r.json()
                    aut = extract_auteur(user_data)
                    return aut

                elif r.status == 429:
                    self.ban = datetime.now() + timedelta(minutes=0, seconds=10)

                elif r.status == 403:
                    print("O_o 403")
                    self.ban = datetime.now() + timedelta(minutes=5, seconds=30)
                    await self.bot.banned()

                    return await self.get_user_by_id(idx)

        except (ServerDisconnectedError, ClientConnectorError, ClientPayloadError, ClientOSError):
            self.ban = datetime.now() + timedelta(minutes=5, seconds=30)
            self.session = aiohttp.ClientSession(connector=self.connector)
            await self.bot.banned()
            print(f"Banned {datetime.now()}")

        except TimeoutError:

            await self.bot.banned()
            self.ban = datetime.now() + timedelta(minutes=5, seconds=30)
            print(f"Banned {datetime.now()}")

            return await self.get_user_by_id(idx)


    @async_request
    async def search_user_by_name(self, username: str, start: int, session: aiohttp.ClientSession,) -> Auteurs:
        """Retreives a list of all matching usernames, possibly none"""

        if datetime.now() < self.ban:
            print(self.ban)
            while datetime.now() < self.ban:
                await asyncio.sleep(1)

            self.bot.unbanned()


        params = {
            'nom' : username,
            'count': str(start),
            str(int(time.time())): str(int(time.time())),
            'lang': self.lang
            }
        try:
            async with session.get(f"{api_base_url}{auteurs_path}",params=params, cookies=cookies_rootme, timeout=self.timeout) as r:
                #Reset LANG
                if self.lang != DEFAULT_LANG:
                    self.lang = DEFAULT_LANG

                if r.status == 404:
                    raise UnknownUser(username)
        
                elif r.status == 200:
                    users_data = await r.json()

                    if users_data == [{}]:
                        raise UnknownUser(username)
                    
                    current_users = extract_auteurs_short(users_data)
                    if len(current_users) == 50:
                        return current_users + await self.search_user_by_name(username, start + 50)
                    else:
                        return current_users
                elif r.status == 429:
                    self.ban = datetime.now() + timedelta(minutes=0, seconds=10)

                elif r.status == 403:
                    self.ban = datetime.now() + timedelta(minutes=5, seconds=30)
                    await self.bot.banned()

        except (ServerDisconnectedError, ClientConnectorError, ClientPayloadError, ClientOSError):
            self.ban = datetime.now() + timedelta(minutes=5, seconds=30)
            self.session = aiohttp.ClientSession(connector=self.connector)
            await self.bot.banned()
            print(f"Banned {datetime.now()}")
            return None 
    
    @async_request
    async def fetch_all_challenges(self, session: aiohttp.ClientSession, start=0) -> ChallengeShort:
        """Retrieves all challenges given a starting number"""
        if datetime.now() < self.ban:
            print(self.ban)
            while datetime.now() < self.ban:
                await asyncio.sleep(1)

            await self.bot.unbanned()

        params = {
            str(int(time.time())): str(int(time.time())),
            'debut_challenges': str(start),
            'lang': DEFAULT_LANG
            }
    
        current_challenges = []
        try:
            async with session.get(f"{api_base_url}{challenges_path}", params=params, cookies=cookies_rootme, timeout=self.timeout) as r:
                if r.status == 200:
                    challenges_data = await r.json()
        
                    current_challenges += extract_page_challenges(challenges_data)
                    
                    if challenges_data[-1]['rel'] == 'next':
                        return current_challenges + await self.fetch_all_challenges(start=start + (50 - (start % 50)))
                    else:
                        return current_challenges
                elif r.status == 429:
                    self.ban = datetime.now() + timedelta(minutes=0, seconds=10)

                elif r.status == 403:
                    self.ban = datetime.now() + timedelta(minutes=5, seconds=30)
                    await self.bot.banned()
        except (ServerDisconnectedError, ClientConnectorError, ClientPayloadError, ClientOSError):
            self.ban = datetime.now() + timedelta(minutes=5, seconds=30)
            self.session = aiohttp.ClientSession(connector=self.connector)
            await self.bot.banned()
            print(f"Banned {datetime.now()}")
            return current_challenges
        except TimeoutError:
            
            await self.bot.banned()
            self.ban = datetime.now() + timedelta(minutes=5, seconds=30)
            print(f"Banned {datetime.now()}")
            
            return current_challenges

        return current_challenges
        
    
    
    @async_request
    async def get_challenge_by_id(self, idx: int, session: aiohttp.ClientSession) -> ChallengeData:
        """Retreives all information about a challenge by ID"""
        if datetime.now() < self.ban:
            print(self.ban)
            while datetime.now() < self.ban:
                await asyncio.sleep(1)

            await self.bot.unbanned()

        params = {
            str(int(time.time())): str(int(time.time())),
            'lang': DEFAULT_LANG
            }
        try:        
            async with session.get(f"{api_base_url}{challenges_path}/{idx}", params=params, cookies=cookies_rootme, timeout=self.timeout) as r:
                
                if r.status == 401:
                    self.ban = datetime.now() + timedelta(minutes=0, seconds=10)
                    raise PremiumChallenge(idx)
        
                elif r.status == 404:
                    self.ban = datetime.now() + timedelta(minutes=0, seconds=10)
                    raise UnknownChallenge(idx)
                
                elif r.status == 200:
                    challenge_data = await r.json()
                    challenge = extract_challenge(challenge_data, idx)
                    print(challenge)
                    return challenge
                elif r.status == 429:
                    self.ban = datetime.now() + timedelta(minutes=0, seconds=10)

                elif r.status == 403:
                    self.ban = datetime.now() + timedelta(minutes=5, seconds=30)
                    await self.bot.banned()
    
        except (ServerDisconnectedError, ClientConnectorError, ClientPayloadError, ClientOSError):
            print(f"Banned {datetime.now()}")
            self.ban = datetime.now() + timedelta(minutes=5, seconds=30)
            self.session = aiohttp.ClientSession(connector=self.connector)
            await self.bot.banned()
            return None
        except TimeoutError:

            await self.bot.banned()
            self.ban = datetime.now() + timedelta(minutes=5, seconds=30)
            print(f"Banned {datetime.now()}")

            return await self.get_challenge_by_id(idx)

    @async_request
    async def get_image_png(self, idx: int, session: aiohttp.ClientSession) -> str:

        if datetime.now() < self.ban:
            print(self.ban)
            while datetime.now() < self.ban:
                await asyncio.sleep(1)

            await self.bot.unbanned()

        url = f'https://www.root-me.org/IMG/auton{idx}.png'
        try:
            async with session.head(url, timeout=self.timeout) as r:
                if r.status == 200:
                    return url
                elif r.status == 429:
                    self.ban = datetime.now() + timedelta(minutes=0, seconds=10)

                elif r.status == 403:
                    self.ban = datetime.now() + timedelta(minutes=5, seconds=30)
                    await self.bot.banned()
                else:
                    return None     
        
        except (ServerDisconnectedError, ClientConnectorError, ClientPayloadError, ClientOSError):
            print(f"Banned {datetime.now()}")
            self.ban = datetime.now() + timedelta(minutes=5, seconds=30)
            self.session = aiohttp.ClientSession(connector=self.connector)
            await self.bot.banned()
            return None
        except TimeoutError:

            await self.bot.banned()
            self.ban = datetime.now() + timedelta(minutes=5, seconds=30)
            print(f"Banned {datetime.now()}")
            
            return await self.get_image_png(idx)


    @async_request
    async def get_image_jpg(self, idx: int, session: aiohttp.ClientSession) -> str:

        if datetime.now() < self.ban:
            print(self.ban)
            while datetime.now() < self.ban:
                await asyncio.sleep(1)

            await self.bot.unbanned()

        url = f'https://www.root-me.org/IMG/auton{idx}.jpg'
        try:
            async with session.head(url, timeout=self.timeout) as r:
                if r.status == 200:
                    return url

                elif r.status == 429:
                    self.ban = datetime.now() + timedelta(minutes=0, seconds=10)

                elif r.status == 403:
                    self.ban = datetime.now() + timedelta(minutes=5, seconds=30)
                    await self.bot.banned()

                else:
                    return None         
        except (ServerDisconnectedError, ClientConnectorError, ClientPayloadError, ClientOSError):
            self.ban = datetime.now() + timedelta(minutes=5, seconds=30)
            self.session = aiohttp.ClientSession(connector=self.connector)
            print(f"Banned {datetime.now()}")
            await self.bot.banned()
            return None
        except TimeoutError:

            await self.bot.banned()
            self.ban = datetime.now() + timedelta(minutes=5, seconds=30)
            print(f"Banned {datetime.now()}")
            
            return await self.get_image_jpg(idx)



