from os import getenv

### API COOKIE ###

API_KEY = getenv("API_KEY")
cookies_rootme = { "api_key": f"{API_KEY}" }

### API PATH ####

api_base_url = "https://api.www.root-me.org/"
challenges_path = "challenges"
auteurs_path = "auteurs"

### API LANG ####

DEFAULT_LANG = "fr"

### DATABASE ####

database_path = "/opt/db/rootme.db"
LOG_PATH = "/opt/db/log.txt"

### BOT CONSTANTS ###

PING_ROLE_ROOTME = getenv("PING_ROLE_ROOTME")
BOT_PREFIX = "!"
