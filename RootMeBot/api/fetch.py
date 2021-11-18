import asyncio
import time
import aiohttp
import json
import functools
import uuid
from datetime import datetime, timedelta

from asyncio.exceptions import TimeoutError
from aiohttp.client_exceptions import ServerDisconnectedError, ClientConnectorError, ClientPayloadError, ClientOSError

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

class PriorityEntry(object):

    def __init__(self, priority, data):
        self.data = data
        self.priority = priority

    def __lt__(self, other):
        return self.priority < other.priority


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
            
            data = await self.queue.get()

            prio, req = data.priority, data.data

            url, params, key, method = req

            if method == 'GET':
                method_http = self.session.get
            elif method == 'HEAD':
                method_http = self.session.head


            while not check:



                await asyncio.sleep(4.85)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Treating item in queue : {key} -> {url} + {params} - (Priority {prio})")
                try:
                    async with method_http(url, params=params, cookies=cookies_rootme) as r:

                        # HEAD
                        if method == 'HEAD':
                            if r.status == 200:
                                data = '200'
                                check = True
                            elif r.status == 404:
                                data = '404'
                                check = True
                            continue

                        # GET
                        if r.status == 200:
                            data = await r.text()
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
                except (ServerDisconnectedError, ClientPayloadError) as e:
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
        obj = PriorityEntry(priority, (url, params, key, 'GET'))
        await self.queue.put(obj)
        await event.wait()

        result = json.loads(self.requests[key]['result'])
        del self.requests[key]

        return result


    async def head(self, url, priority=1):
        key = uuid.uuid4().hex

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Request for {url} added to queue -> {key} (Priority {priority})")

        event = asyncio.Event()
        self.requests[key] = {}
        self.requests[key]['event'] = event
        obj = PriorityEntry(priority, (url, {}, key, 'HEAD'))
        await self.queue.put(obj)
        await event.wait()

        result = self.requests[key]['result']
        del self.requests[key]

        return result




    async def get_user_by_id(self, idx: int, priority=1) -> Auteur:
        """Retreives an Auteur by id"""
       
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

    async def get_image_png(self, idx: int) -> str:

        url = f'https://www.root-me.org/IMG/auton{idx}.png'

        code = await self.head(url, priority=0)

        if code == '200':
            return url

    async def get_image_jpg(self, idx: int) -> str:

        url = f'https://www.root-me.org/IMG/auton{idx}.jpg'
        code = await self.head(url, priority=0)

        if code == '200':
            return url


