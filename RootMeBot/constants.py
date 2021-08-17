from os import getenv

### API COOKIE ###

API_KEY = getenv("API_KEY")
cookies_rootme = { "api_key": f"{API_KEY}" }

### API PATH ####

api_base_url = "https://api.www.root-me.org/"
challenges_path = "challenges/"
auteurs_path = "auteurs/"

### DATABASE ####

database_path = "/opt/db/rootme.db"

### COLORS ######

SUCCESS_GREEN = 0x91f723
SCOREBOARD_WHITE = 0xffffff
NEW_YELLOW = 0xffde26
INFO_BLUE = 0x99c0ff
ERROR_RED = 0xff0000

### BOT CONSTANTS ###

BOT_PREFIX = "!"
