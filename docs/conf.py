SAMPLE_SPREADSHEET_ID = "1eT516P2BHNUItpuoz8_aylJNPMPgpFOp2u7DZhhgICo"
SAMPLE_RANGE_NAME = "!A1:Z200"

INDEX = {
    "INDEX_EVENT_NAME": (0, 1),
    "INDEX_EVENT_TIME_EST": (1, 1),
    "INDEX_CAR": (2, 1),
    "INDEX_TOTAL_TIME": (3, 1),
    "INDEX_CURRENT_POSITION": (4, 1),
    "INDEX_TOTAL_DRIVER": (5, 1),
    "INDEX_GAP_TO_RACE_START": (7, 1),
    "INDEX_PRACTICE_DURATION": (8, 1),
    "INDEX_QUALIFY_DURATION": (9, 1),
    "INDEX_TIME_TO_GREEN": (10, 1),
    "INDEX_TIME_TO_START": (11, 1),
    "INDEX_SIM_TIME_START": (12, 1),
    "INDEX_THEORETICAL_STINT_TIME": (13, 1),
    "INDEX_AVERAGE_STINT_TIME": (14, 1),
    "INDEX_WEATHER": (0, 25),
    "INDEX_DRIVER_TIME_SLOTS": (1, 16),
    "INDEX_DRIVER_1": (0, 17),
    "INDEX_DRIVER_2": (0, 18),
    "INDEX_DRIVER_3": (0, 19),
    "INDEX_DRIVER_4": (0, 20),
    "INDEX_DRIVER_5": (0, 21),
    "INDEX_DRIVER_6": (0, 22),
    "INDEX_DRIVER_7": (0, 23),
    "INDEX_DRIVER_8": (0, 24),
}
STATUS_BG = "#f7d6ff"
CONTENT_BG = "#fff9d6"

import configparser as cp
import os
OWD = os.getcwd()
os.chdir(OWD)

config = cp.ConfigParser()
config.read('config.ini')

def get_config(section, key):
    return config.get(section, key)

def set_config(section, key, value):
    config.set(section, key, value)
    with open('config.ini', 'w') as configfile:
        config.write(configfile)

GEOMETRY = get_config('general', 'geometry')
STATUS_TIMES = get_config('settings', 'times')
