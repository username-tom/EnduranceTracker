"""Configuration constants and config-file helpers for EnduranceTracker."""

import configparser as cp
import os

# Locate config.ini relative to the project root (two levels up from this file)
_PACKAGE_DIR = os.path.dirname(__file__)
_PROJECT_ROOT = os.path.abspath(os.path.join(_PACKAGE_DIR, '..'))
_CONFIG_PATH = os.path.join(_PROJECT_ROOT, 'config.ini')

config = cp.ConfigParser()
config.read(_CONFIG_PATH)


def get_config(section, key):
    return config.get(section, key)


def set_config(section, key, value):
    if not config.has_section(section):
        config.add_section(section)
    config.set(section, key, str(value))
    with open(_CONFIG_PATH, 'w') as configfile:
        config.write(configfile)


GEOMETRY = get_config('general', 'geometry')
STATUS_TIMES = get_config('settings', 'times')
DARK_MODE = get_config('general', 'dark_mode').lower() == 'true'
DATA_DIR = get_config('general', 'data_dir')
IS_SERVER = get_config('general', 'server').lower() == 'true'
USE_INTERNET = get_config('general', 'use_internet').lower() == 'true'
HOST = get_config('com', 'host')
PORT = int(get_config('com', 'port'))

# Internet/MongoDB configuration
MONGODB_URI = get_config('internet', 'mongodb_uri')
DATABASE_NAME = get_config('internet', 'database_name')
PASSCODE = get_config('internet', 'passcode')
SHOW_PASSWORD = get_config('internet', 'show_password').lower() == 'true'
SERVER_HOST = get_config('internet', 'server_host')
SERVER_PORT = int(get_config('internet', 'server_port'))

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
BUTTON_BG = '#f0f0f0'
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

# Maps human-readable field names to snake_case DB keys
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
    "theoretical stint time": "theoretical_stint_time",
    "average stint time": "average_stint_time",
}

# Canonical column names for the tracker DataFrame
TRACKER_COLUMNS = [
    'Overall Time Slots',
    'Driver',
    'Theoretical Stints #',
    'Actual Stints #',
    'Actual Driver',
    'Est. Chance of Rain (%)',
    'Act. Weather at Time',
    'Notes',
]
