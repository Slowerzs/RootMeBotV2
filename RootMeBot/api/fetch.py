import asyncio
import aiohttp
import json
import functools
import time

from aiohttp.client_exceptions import ServerDisconnectedError

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
		self.session = aiohttp.ClientSession()
		self.semaphore = asyncio.Semaphore(25)


		

	@async_request
	async def get_user_by_id(self, idx: int, session: aiohttp.ClientSession) -> AuteurData:
		"""Retreives an Auteur by id"""
		
		if idx == 0:
			raise UnknownUser(idx)
	
	
		params = {str(int(time.time())): str(int(time.time()))}
		try:
			async with session.get(f"{api_base_url}{auteurs_path}/{idx}", params=params, cookies=cookies_rootme) as r:
				if r.status == 404:
					raise UnknownUser(idx)
		
				elif r.status == 200:
					try:
						user_data = await r.json()
					except aiohttp.client_exceptions.ClientPayloadError:
						await asyncio.sleep(0.05)
						return await self.get_user_by_id(idx)		
		
			
					aut = extract_auteur(user_data)
					return aut 

		except ServerDisconnectedError:
			await asyncio.sleep(0.2)
			return await self.get_user_by_id(idx)
	
	
	@async_request
	async def search_user_by_name(self, username: str, start: int, session: aiohttp.ClientSession) -> Auteurs:
		"""Retreives a list of all matching usernames, possibly none"""
	
		params = {
			'nom' : username,
			'count': str(start),
			str(int(time.time())): str(int(time.time()))
			}
		try:
			async with session.get(f"{api_base_url}{auteurs_path}",params=params, cookies=cookies_rootme) as r:
				if r.status == 404:
					raise UnknownUser(username)
		
				elif r.status == 200:
					users_data = await r.json()
					
					current_users = extract_auteurs_short(users_data)
					if len(current_users) == 50:
						return current_users + await self.search_user_by_name(username, start + 50)
					else:
						return current_users
		except ServerDisconnectedError:
			await asyncio.sleep(0.2)
			return await self.search_user_by_name(username, start)
		
			
	
	@async_request
	async def fetch_all_challenges(self, session: aiohttp.ClientSession, start=0) -> ChallengeShort:
		"""Retrieves all challenges given a starting number"""
	
		params = {
			str(int(time.time())): str(int(time.time())),
			'debut_challenges': str(start)
			}
	
		current_challenges = []
		await asyncio.sleep(0.1)
		try:
			async with session.get(f"{api_base_url}{challenges_path}", params=params, cookies=cookies_rootme) as r:
				if r.status == 200:
					challenges_data = await r.json()
		
					current_challenges += extract_page_challenges(challenges_data)
					
					if challenges_data[-1]['rel'] == 'next':
						return current_challenges + await self.fetch_all_challenges(start=start + (50 - (start % 50)))
					else:
						return current_challenges
		except ServerDisconnectedError:
			await asyncio.sleep(0.2)
			return await self.fetch_all_challenges(idx, start=start)
		
		return current_challenges
		
	
	
	@async_request
	async def get_challenge_by_id(self, idx: int, session: aiohttp.ClientSession) -> ChallengeData:
		"""Retreives all information about a challenge by ID"""
	
		params = {str(int(time.time())): str(int(time.time()))}
		try:		
			async with session.get(f"{api_base_url}{challenges_path}{idx}", params=params, cookies=cookies_rootme) as r:
				
				if r.status == 401:
					raise PremiumChallenge(idx)
		
				elif r.status == 404:
					raise UnknownChallenge(idx)
				
				elif r.status == 200:
					challenge_data = await r.json()
					challenge = extract_challenge(challenge_data, idx)
					print(challenge)
					return challenge
	
		except ServerDisconnectedError:
			await asyncio.sleep(0.2)
			return await self.get_challenge_by_id(username)
	
	@async_request
	async def get_image_url(self, idx: int, session: aiohttp.ClientSession) -> str:
		url = f'https://www.root-me.org/IMG/auton{idx}.png'
		try:
			async with session.head(url) as resp:
				if resp.status == 200:
					return url
		
		except ServerDisconnectedError:
			await asyncio.sleep(0.2)
			return await self.get_image_url(username, start)
		
		url = f'https://www.root-me.org/IMG/auton{idx}.jpg'
		try:
			async with session.head(url) as resp:
				if resp.status == 200:
					return url
		except ServerDisconnectedError:
			await asyncio.sleep(0.2)
			return await self.get_image_url(idx)
		
		return 'https://www.root-me.org/IMG/auton0.png'	






	
