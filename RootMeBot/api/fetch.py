import asyncio
import time
import aiohttp
import json
import functools
import uuid
from datetime import datetime, timedelta

from asyncio.exceptions import TimeoutError
from aiohttp.client_exceptions import ServerDisconnectedError, ClientConnectorError, ClientPayloadError, ClientOSError, ClientOSError 

from api.extract import *

from database.models.auteur_model import Auteur
from database.models.challenge_model import Challenge
from database.models.base_model import Base

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
        self.timeout = aiohttp.ClientTimeout(total=6)
        self.ban = datetime.now()

        self.queue = asyncio.PriorityQueue()

        self.requests = {}

    async def worker(self):
        print(f"Starting worker...")
        while True:
            
            check = False
            
            prio , req = await self.queue.get()

            url, params, key = req

            while not check:
                await asyncio.sleep(4.80)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Treating item in queue : {key} -> {url} + {params} - (Priority {prio})")
                try:
                    async with self.session.get(url, params=params, cookies=cookies_rootme) as r:
                        if r.status == 200:
                            data = await r.json()
                            check = True
                        elif r.status == 401:
                            data = 'PREMIUM'
                            check = True
                        else:
                            print(f'Status : {r.status} - restarting')
                            await asyncio.sleep(15)
                            check = False
                except ClientOSError as e:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Got {e.__class__.__name__}, retrying in 15s...")
                    await asyncio.sleep(15)
                    check = False
                except ServerDisconnectedError as e:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Got {e.__class__.__name__}, retrying...")
                    check = False


            self.requests[key]['result'] = data
            self.requests[key]['event'].set()

            self.queue.task_done()

    async def get(self, url, params, priority=1):
        key = uuid.uuid4().hex

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Request for {url} added to queue -> {key} (Priority {priority})")

        event = asyncio.Event()
        self.requests[key] = {}
        self.requests[key]['event'] = event
        await self.queue.put((priority, (url, params, key)))
        await event.wait()

        result = self.requests[key]['result']
        del self.requests[key]

        return result



    async def get_user_by_id(self, idx: int, priority=1) -> Auteur:
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


        user_data = await self.get(f"{api_base_url}{auteurs_path}/{idx}", params, priority)
        aut = extract_auteur(user_data)
        return aut

    async def search_user_by_name(self, username: str, start: int, priority=1) -> Auteurs:
        """Retreives a list of all matching usernames, possibly none"""

        params = {
            'nom' : username,
            'count': str(start),
            str(int(time.time())): str(int(time.time())),
            'lang': self.lang
            }

        users_data = await self.get(f"{api_base_url}{auteurs_path}", params, priority=0)
        current_users = extract_auteurs_short(users_data)

        if len(current_users) == 50:
            return current_users + await self.search_user_by_name(username, start + 50, priority)

        self.lang = DEFAULT_LANG
        return current_users

    
    async def fetch_all_challenges(self, start=0) -> ChallengeShort:
        """Retrieves all challenges given a starting number"""

        params = {
            str(int(time.time())): str(int(time.time())),
            'debut_challenges': str(start),
            'lang': DEFAULT_LANG
            }
    
        current_challenges = []
        
        if not start:
            print("Fetching all challenges...")
        
        challenges_data = await self.get(f"{api_base_url}{challenges_path}/", params)


        #print(challenges_data)

        current_challenges += extract_page_challenges(challenges_data)

        if challenges_data[-1]['rel'] == 'next':
            return current_challenges + await self.fetch_all_challenges(start=start + (50 - (start % 50)))
        else:
            return current_challenges
        
        return current_challenges
        
    
    async def get_challenge_by_id(self, idx: int) -> Challenge:
        """Retreives all information about a challenge by ID"""

        params = {
            str(int(time.time())): str(int(time.time())),
            'lang': DEFAULT_LANG
            }
        
        challenge_data = await self.get(f"{api_base_url}{challenges_path}/{idx}", params) 
        challenge = extract_challenge(challenge_data, idx)
        return challenge

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



