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
DARK_MODE = True if get_config('general', 'dark_mode').lower() == 'true' else False
DATA_DIR = get_config('general', 'data_dir')
IS_SERVER = True if get_config('general', 'server').lower() == 'true' else False
HOST = get_config('com', 'host')
PORT = int(get_config('com', 'port'))

MAX_DRIVER = 8

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
WEATHER_CONDITIONS = [
    'Unknown',
    'Clear',
    'Partly Cloudy',
    'Cloudy',
    'Overcast',
    'Fog',
    'Light Rain',
    'Heavy Rain',
    'Moderate Rain',
]
TRACK_CONDITIONS = [
    'Unknown',
    'Full Dry',
    'Dry Line',
    'Damp',
    'Wet',
]

DATA_ITEMS = {
    "event": "event",
    "event date": "event_date",
    "event time": "event_time",
    "event timezone": "event_timezone",
    "car": "car",
    "team": "team",
    "event duration": "event_duration",
    "track": "track",
    "current position": "current_position",
    "total drivers": "total_drivers",
    "gap to race start": "gap_2_start",
    "practice duration": "practice_duration",
    "qualify duration": "qualify_duration",
    "time to green": "time_to_green",
    "time to start": "time_to_start",
    "sim. race start": "sim_time_start",
    "theoretical stint time": "thereotical_stint_time",
    "average stint time": "average_stint_time",
}
