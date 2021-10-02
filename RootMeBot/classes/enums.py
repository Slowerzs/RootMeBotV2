from enum import Enum

### COLORS ######

class Color(Enum):
    SUCCESS_GREEN = 0x91f723
    SCOREBOARD_WHITE = 0xffffff
    NEW_YELLOW = 0xffde26
    INFO_BLUE = 0x99c0ff
    ERROR_RED = 0xff0000

### Stats ####

class Stats(Enum):
    WEB_CLIENT = 0
    WEB_SERVER = 1
    APP_SCRIPT = 2
    CRYPTANALYSIS = 3
    PROGRAMMING = 4
    STEGANOGRAPHY = 5
    CRACKING = 6
    REALIST = 7
    NETWORK = 8
    FORENSICS = 9
    APP_SYSTEM = 10



