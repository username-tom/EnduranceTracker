'''
Helpers for Server API
'''


import sys
import os
OWD = os.getcwd()
sys.path.append(OWD)
os.chdir(OWD)

from docs.conf import *

class TrackerError(Exception):
    pass

import os.path

from time import sleep
from pandas import DataFrame, to_datetime, concat
from tkinter import messagebox
import numpy as np
from datetime import timedelta
import socket
from threading import Thread
import json
from math import ceil


creds = None

def login():
    global creds


def tz_diff(dt, tz1, tz2):
    date = to_datetime(dt)
    return date.tz_localize(tz1).tz_convert(tz2)


def format_timedelta(t: timedelta):
    return f'{int(t.total_seconds() // 3600):02d}:' \
           f'{int((t.total_seconds() // 60) % 60):02d}:' \
           f'{int(t.total_seconds() % 60):02d}'

def text2time(text, unit='s'):
    t = text.lower().strip()
    if 'h' in t:
        h = t.split('h')[0]
        t = t.split('h')[1]
    if 'm' in t:
        m = t.split('m')[0]
        t = t.split('m')[1]
    if 's' in t:
        s = t.split('s')[0]
        
    if ':' in t:
        t = t.split(':')
        if len(t) == 3:
            h, m, s = t[0], t[1], t[2]
        elif len(t) == 2:
            h, m = t[0], t[1]
            s = 0
        else:
            raise ValueError("Invalid time format")
    
    if unit == 's':
        return int(h) * 3600 + int(m) * 60 + int(s)
    elif unit == 'm':
        return int(h) * 60 + int(m) + int(s) / 60
    elif unit == 'h':
        return int(h) + int(m) / 60 + int(s) / 3600

class Driver:
    def __init__(self, 
                 name='', 
                 tz='US/Pacific',
                 available=None,
                 maybe=None,
                 unavailable=None):
        self.name = name
        self.time_zone = tz
        self.available = available
        self.maybe = maybe
        self.unavailable = unavailable

    def __str__(self):
        return f'{self.name} - {self.team} @ {self.time_zone}'
    
class TrackerSlot:
    def __init__(self, 
                 time_slot='',
                 planned_driver='',
                 planned_stint='',
                 actual_driver='',
                 actual_stint='',
                 est_rain=0,
                 act_weather='',
                 act_track_condition='',
                 notes=''):
        self.time_slot = time_slot
        self.planned_driver = planned_driver
        self.planned_stint = planned_stint
        self.actual_driver = actual_driver
        self.actual_stint = actual_stint
        self.est_rain = est_rain
        self.act_weather = act_weather
        self.act_track_condition = act_track_condition
        self.notes = notes

    def __str__(self):
        return f'{self.time_slot}\n{self.planned_driver}\n\
                 {self.planned_stint}\n{self.actual_driver}\n\
                 {self.actual_stint}\n{self.est_rain}\n\
                 {self.act_weather}\n{self.act_track_condition}\n{self.notes}'


class TrackerClient:
    def __init__(self, host="127.0.0.1", port=65432, data_dir=DATA_DIR):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.buffer_size = 1024
        self.listener = None
        self.listener_interval = 0.1  # seconds
        self.data_raw = None
        self.data = {}
        self.data_dir = data_dir
        self.conn = None
        self.addr = None
        self.status = "disconnected"
        
    def connect(self):
        print(f"Connecting to server at {self.host}:{self.port}...")
        try:
            self.socket.connect((self.host, self.port))
        except socket.error as e:
            print(f"Error connecting to socket: {e}")
            return
        else:
            print(f"Socket connected to {self.host}:{self.port}")

            self.start_listener()
            self.status = "connected"

    def send(self, message):
        try:
            self.socket.sendall(message.encode())
        except socket.error as e:
            print(f"Error sending message: {e}")
            return False
        else:
            print(f"Message sent to {self.host}:{self.port} - {message}")

    def receive(self):
        print(f"Waiting for message from {self.host}:{self.port}...")
        try:
            data = self.socket.recv(self.buffer_size)
        except socket.error as e:
            print(f"Error receiving message: {e}")
            return None
        else:
            print(f"Message received from {self.host}:{self.port} - {data.decode()}")
            return data.decode()

    def start_listener(self):
        self.conn, self.addr = self.socket.accept()
        print(f"Connection accepted from {self.addr}")

        self.listener = Thread(target=self.listening)
        self.listener.start()

    def stop_listener(self):
        if self.listener:
            # self.listener.join()
            self.listener = None
        print("Listener stopped")

    def listening(self):
        while self.listener is not None:
            try:
                msg = self.receive()
                if msg is None:
                    break
                print(f"Received message: {msg}")
                # TODO: Process the received message
            except socket.error as e:
                print(f"Error receiving data: {e}")
                break
            sleep(self.listener_interval)
        
    def disconnect(self):
        print(f"Disconnecting from {self.host}:{self.port}...")
        self.stop_listener()
        try:
            self.socket.close()
        except socket.error as e:
            print(f"Error closing socket: {e}")
            return
        else:
            print(f"Socket disconnected from {self.host}:{self.port}")
            self.status = "disconnected"

    def update_local_data(self):
        self.parse_data()
        try:
            with open(self.data_dir, 'w') as f:
                json.dump(self.data, f)
        except IOError as e:
            print(f"Error updating local data: {e}")
            return
        else:
            print("Local data updated successfully")

    def get_local_data(self):
        try:
            with open(self.data_dir, 'r') as f:
                data = json.load(f)
        except IOError as e:
            print(f"Error reading local data: {e}")
        else:
            print("Local data read successfully")
            self.data_raw = data
            self.process_data()

    def process_data(self):
        for key in DATA_ITEMS:
            if key not in self.data_raw:
                raise TrackerError(f"Missing data item: {key}")
            else:
                self.data[key] = self.data_raw[key]

        if 'drivers' not in self.data_raw:
            raise TrackerError("Missing drivers data")
        if 'trackers' not in self.data_raw:
            raise TrackerError("Missing trackers data")
        
        self.data['drivers'] = {}
        self.data['trackers'] = {}

        for key, value in self.data_raw['drivers'].items():
            driver = Driver(name=value['name'], 
                            tz=value['tz'],
                            available=value['available'],
                            maybe=value['maybe'],
                            unavailable=value['unavailable'])
            self.data['drivers'][value['name']] = driver
        for key, value in self.data_raw['trackers'].items():
            tracker = TrackerSlot(time_slot=value['time_slot'],
                                  planned_driver=value['planned_driver'],
                                  planned_stint=value['planned_stint'],
                                  actual_driver=value['actual_driver'],
                                  actual_stint=value['actual_stint'],
                                  est_rain=value['est_rain'],
                                  act_weather=value['act_weather'],
                                  act_track_condition=value['act_track_condition'],
                                  notes=value['notes'])
            self.data['trackers'][value['time_slot']] = tracker

    def parse_data(self):
        self.data_raw = {}
        for key in DATA_ITEMS:
            if key not in self.data:
                raise TrackerError(f"Missing data item: {key}")
            else:
                self.data_raw[key] = self.data[key] 

        self.data_raw['drivers'] = {}
        self.data_raw['trackers'] = {}

        for key, value in self.data['drivers'].items():
            self.data_raw['drivers'][key] = {
                'name': value.name,
                'tz': value.time_zone,
                'available': value.available,
                'maybe': value.maybe,
                'unavailable': value.unavailable
            }
        for key, value in self.data['trackers'].items():
            self.data_raw['trackers'][key] = {
                'time_slot': value.time_slot,
                'planned_driver': value.planned_driver,
                'planned_stint': value.planned_stint,
                'actual_driver': value.actual_driver,
                'actual_stint': value.actual_stint,
                'est_rain': value.est_rain,
                'act_weather': value.act_weather,
                'act_track_condition': value.act_track_condition,
                'notes': value.notes
            }
        
    def update_value(self, item='', index='', value=None):
        if item not in self.data:
            raise TrackerError(f"Missing data item: {item}")
        if item == 'drivers':
            if index not in self.data[item]:
                raise TrackerError(f"Missing driver: {index}")
            self.data[item][index].__dict__[value] = value
        elif item == 'trackers':
            if index not in self.data[item]:
                raise TrackerError(f"Missing tracker: {index}")
            self.data[item][index].__dict__[value] = value
        else:
            if item not in DATA_ITEMS:
                raise TrackerError(f"Requesting to update: {item} does not exist")
            else:
                self.data[item] = value
                self.update_local_data()

        print(f"Updated {item} - {index} - {value}")

    
    def reset_drivers_time_slots(self):
        for key in self.data['drivers']:
            self.data['drivers'][key].available = []
            self.data['drivers'][key].maybe = []
            self.data['drivers'][key].unavailable = [i for i in range(1, ceil(text2time(self.data['event_duration']) / text2time(self.data['average_stint_time'])))]
        
        self.update_local_data()
        print("Drivers time slots reset")

    def reset_drivers(self):
        self.data['drivers'] = {}

        self.update_local_data()
        print("Drivers reset")

    def generate_message(self, func, *args, **kwargs):
        if func == 'update':
            """
            -update -event
            -update -driver --name 
            """
            message = f"-{func} -{args[0]} --{args[1]} {args[2]}"
        elif func == 'get':
            """
            -get -event
            -get -driver --name
            """
            message = f"-{func} -{args[0]} --{args[1]}"
        elif func == 'reset':
            """
            -reset -event
            -reset driver or -reset tracker
            -reset driver name or -reset tracker time_slot
            """
            message = f"-{func} -{args[0]} {args[1]}"
        elif func == 'add':
            """
            -add driver name or -add tracker time_slot
            update rest of the data
            """
            message = f"-{func} {args[0]} {args[1]}"


class TrackerServer(TrackerClient):
    def __init__(self, host="127.0.0.1", port=65432, data_dir=DATA_DIR):
        super().__init__(host, port, data_dir)
        self.status = "stopped"

    def start(self):
        print(f"Starting server at {self.host}:{self.port}...")
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen()
        except socket.error as e:
            print(f"Error starting server: {e}")
            return
        else:
            print(f"Server started at {self.host}:{self.port}")
            print("Waiting for connection...")

            self.start_listener()
            self.status = "started"

    def start_listener(self):
        self.conn, self.addr = self.socket.accept()
        print(f"Connection accepted from {self.addr}")

        self.listener = Thread(target=self.listening)
        self.listener.start()

    def stop(self):
        if self.listener:
            # self.listener.join()
            self.listener = None
        self.conn.close()
        self.socket.close()
        self.status = "stopped"

    def listening(self):
        while self.listener is not None:
            try:
                data = self.conn.recv(self.buffer_size)
                if not data:
                    break
                print(f"Received data: {data.decode()}")
                # TODO: Process the received data
            except socket.error as e:
                print(f"Error receiving data: {e}")
                break
            sleep(self.listener_interval)
    
    