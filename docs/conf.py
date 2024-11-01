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
SHEET_ID = get_config('settings', 'sheet_id')
DARK_MODE = True if get_config('general', 'dark_mode').lower() == 'true' else False

SAMPLE_RANGE_NAME = "A1:Z200"
MAX_DRIVER = 8

A = 0
B = 1
C = 2
D = 3
E = 4
F = 5
G = 6
H = 7
I = 8
J = 9
K = 10
L = 11
M = 12
N = 13
O = 14
P = 15
Q = 16
R = 17
S = 18
T = 19
U = 20
V = 21
W = 22
X = 23
Y = 24
Z = 25

TRACKER_RANGE = 1, 201, D, L


INDEX = {
    "INDEX_EVENT_NAME": (0, B),
    "INDEX_EVENT_TIME_EST": (1, B),
    "INDEX_CAR": (2, B),
    "INDEX_TOTAL_TIME": (3, B),
    "INDEX_CURRENT_POSITION": (4, B),
    "INDEX_TOTAL_DRIVER": (5, B),
    "INDEX_GAP_TO_RACE_START": (7, B),
    "INDEX_PRACTICE_DURATION": (8, B),
    "INDEX_QUALIFY_DURATION": (9, B),
    "INDEX_TIME_TO_GREEN": (10, B),
    "INDEX_TIME_TO_START": (11, B),
    "INDEX_SIM_TIME_START": (12, B),
    "INDEX_THEORETICAL_STINT_TIME": (13, B),
    "INDEX_AVERAGE_STINT_TIME": (14, B),
    "INDEX_WEATHER": (0, Z),
    "INDEX_DRIVER_TIME_SLOTS": (1, Q),
    "INDEX_DRIVER_1": (0, R),
    "INDEX_DRIVER_2": (0, S),
    "INDEX_DRIVER_3": (0, T),
    "INDEX_DRIVER_4": (0, U),
    "INDEX_DRIVER_5": (0, V),
    "INDEX_DRIVER_6": (0, W),
    "INDEX_DRIVER_7": (0, X),
    "INDEX_DRIVER_8": (0, Y),
}
WEATHER_LENGTH = 11
STATUS_BG = "#f0f0f0"
CONTENT_BG = "#fafafa"
STATUS_BG_DARK = "#0A0A0A"
CONTENT_BG_DARK = "#202020"
TAB_BG = "#fafafa"
TAB_BG_ACTIVE = "#dadada"
TAB_BG_DARK = "#050505"
TAB_BG_DARK_ACTIVE = "#252525"
DARK_FG = 'white'
ENTRY_BG = 'white'
ENTRY_FG = 'black'
ENTRY_BG_DARK = '#1A1A1A'
ENTRY_FG_DARK = 'white'
LABEL_FG = 'black'
LABEL_FG_DARK = 'white'
BUTTON_BG = '#f0f0f0'  # A commonly used light grey color for button backgrounds
BUTTON_FG = 'black'
BUTTON_BG_DARK = '#0A0A0A'
BUTTON_FG_DARK = 'white'
HOUR_STINT_FONT = 'TkFixedFont'

