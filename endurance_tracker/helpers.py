"""Server/client helpers for EnduranceTracker.

Provides TrackerClient, TrackerServer, Driver, TrackerSlot, and utility
functions used throughout the application.
"""

from .config import DATA_ITEMS
from .db import Database

import socket
import json
import hashlib
import threading
from threading import Thread
from time import sleep
from math import ceil
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
from urllib.request import urlopen
from urllib.error import URLError

from pandas import to_datetime
from datetime import timedelta


class TrackerError(Exception):
    pass


# ──────────────────────────────────────────── utility functions ───────────────

def tz_diff(dt, tz1, tz2):
    date = to_datetime(dt)
    return date.tz_localize(tz1).tz_convert(tz2)


def format_timedelta(t: timedelta) -> str:
    total = int(t.total_seconds())
    h = total // 3600
    m = (total // 60) % 60
    s = total % 60
    return f'{h:02d}:{m:02d}:{s:02d}'


def text2time(text, unit='s'):
    t = text.lower().strip()
    h = m = s = 0
    if ':' in t:
        parts = t.split(':')
        if len(parts) == 3:
            h, m, s = parts
        elif len(parts) == 2:
            h, m = parts
            s = 0
        else:
            raise ValueError("Invalid time format")
    else:
        if 'h' in t:
            h = t.split('h')[0]
            t = t.split('h')[1]
        if 'm' in t:
            m = t.split('m')[0]
            t = t.split('m')[1]
        if 's' in t:
            s = t.split('s')[0]

    h, m, s = int(h), int(m), int(s)
    if unit == 's':
        return h * 3600 + m * 60 + s
    elif unit == 'm':
        return h * 60 + m + s / 60
    elif unit == 'h':
        return h + m / 60 + s / 3600
    raise ValueError(f"Unknown unit: {unit}")


# ──────────────────────────────────────────── data model classes ──────────────

class Driver:
    def __init__(self, name='', tz='US/Pacific', available=None, maybe=None,
                 unavailable=None):
        self.name = name
        self.time_zone = tz
        self.available = available or []
        self.maybe = maybe or []
        self.unavailable = unavailable or []

    def __str__(self):
        return f'{self.name} @ {self.time_zone}'


class TrackerSlot:
    def __init__(self, time_slot='', planned_driver='', planned_stint='',
                 actual_driver='', actual_stint='', est_rain=0,
                 act_weather='', act_track_condition='', notes=''):
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
        return (f'{self.time_slot}\n{self.planned_driver}\n{self.planned_stint}\n'
                f'{self.actual_driver}\n{self.actual_stint}\n{self.est_rain}\n'
                f'{self.act_weather}\n{self.act_track_condition}\n{self.notes}')


# ──────────────────────────────────────────── TrackerClient ───────────────────

class TrackerClient:
    def __init__(self, host="127.0.0.1", port=65432, db: Database = None):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.buffer_size = 1024
        self.listener = None
        self.listener_interval = 0.1
        self.data = {}
        self.db = db
        self.conn = None
        self.addr = None
        self.status = "disconnected"

    # ---------------------------------------------------------------- socket

    def connect(self):
        print(f"Connecting to server at {self.host}:{self.port}...")
        try:
            self.socket.connect((self.host, self.port))
        except socket.error as e:
            print(f"Error connecting to socket: {e}")
            return
        self.start_listener()
        self.status = "connected"
        print(f"Socket connected to {self.host}:{self.port}")

    def send(self, message):
        try:
            self.socket.sendall(message.encode())
        except socket.error as e:
            print(f"Error sending message: {e}")
            return False
        print(f"Message sent to {self.host}:{self.port} - {message}")

    def receive(self):
        print(f"Waiting for message from {self.host}:{self.port}...")
        try:
            data = self.socket.recv(self.buffer_size)
        except socket.error as e:
            print(f"Error receiving message: {e}")
            return None
        msg = data.decode()
        print(f"Message received from {self.host}:{self.port} - {msg}")
        return msg

    def start_listener(self):
        self.conn, self.addr = self.socket.accept()
        print(f"Connection accepted from {self.addr}")
        self.listener = Thread(target=self.listening, daemon=True)
        self.listener.start()

    def stop_listener(self):
        if self.listener:
            self.listener = None
        print("Listener stopped")

    def listening(self):
        while self.listener is not None:
            try:
                msg = self.receive()
                if msg is None:
                    break
                print(f"Received message: {msg}")
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
        self.status = "disconnected"
        print(f"Socket disconnected from {self.host}:{self.port}")

    # --------------------------------------------------------- data / DB ops

    def update_value(self, item='', index='', value=None):
        """Update an event field, driver attribute, or tracker slot."""
        if item in ('drivers', 'trackers'):
            if item not in self.data:
                self.data[item] = {}
            if index and index in self.data[item]:
                obj = self.data[item][index]
                if hasattr(obj, index):
                    setattr(obj, index, value)
        else:
            self.data[item] = value
            if self.db is not None:
                self.db.set_event_field(item, value)
        print(f"Updated {item} - {index} - {value}")

    def update_drivers_time_slots(self, drivers_time_slots: dict) -> None:
        """Persist driver availability slots to the DB."""
        if self.db is None:
            return
        for driver_name, slots in drivers_time_slots.items():
            available = [i + 1 for i, v in enumerate(slots) if v == '1']
            maybe = [i + 1 for i, v in enumerate(slots) if v == '2']
            unavailable = [i + 1 for i, v in enumerate(slots) if v == '0']
            self.db.update_driver_slots(driver_name, available, maybe, unavailable)

    def reset_drivers(self):
        self.data['drivers'] = {}
        if self.db is not None:
            for name in list(self.db.get_drivers()):
                self.db.remove_driver(name['name'])
        print("Drivers reset")



# ──────────────────────────────────────────── TrackerServer ───────────────────

class TrackerServer(TrackerClient):
    def __init__(self, host="127.0.0.1", port=65432, db: Database = None):
        super().__init__(host, port, db)
        self.status = "stopped"

    def start(self):
        print(f"Starting server at {self.host}:{self.port}...")
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen()
        except socket.error as e:
            print(f"Error starting server: {e}")
            return
        print(f"Server started at {self.host}:{self.port}. Waiting for connection...")
        self.start_listener()
        self.status = "started"

    def start_listener(self):
        self.conn, self.addr = self.socket.accept()
        print(f"Connection accepted from {self.addr}")
        self.listener = Thread(target=self.listening, daemon=True)
        self.listener.start()

    def stop(self):
        if self.listener:
            self.listener = None
        try:
            if self.conn:
                self.conn.close()
            self.socket.close()
        except socket.error:
            pass
        self.status = "stopped"

    def listening(self):
        while self.listener is not None:
            try:
                data = self.conn.recv(self.buffer_size)
                if not data:
                    break
                print(f"Received data: {data.decode()}")
            except socket.error as e:
                print(f"Error receiving data: {e}")
                break
            sleep(self.listener_interval)


class InternetTrackerRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for internet-based tracker communication."""
    
    def __init__(self, *args, db=None, passcode=None, **kwargs):
        self.db = db
        self.passcode = passcode
        super().__init__(*args, **kwargs)
    
    def _authenticate(self, provided_passcode):
        """Verify the provided passcode."""
        if not self.passcode or not provided_passcode:
            return False
        # Simple hash comparison for security
        expected_hash = hashlib.sha256(self.passcode.encode()).hexdigest()
        provided_hash = hashlib.sha256(provided_passcode.encode()).hexdigest()
        return expected_hash == provided_hash
    
    def _send_json_response(self, data, status=200):
        """Send a JSON response."""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self._send_json_response({})
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path.startswith('/api/event'):
            self._handle_get_event()
        elif self.path.startswith('/api/drivers'):
            self._handle_get_drivers()
        elif self.path.startswith('/api/tracker'):
            self._handle_get_tracker()
        else:
            self._send_json_response({'error': 'Not found'}, 404)
    
    def do_POST(self):
        """Handle POST requests."""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode()
        try:
            data = json.loads(post_data) if post_data else {}
        except json.JSONDecodeError:
            self._send_json_response({'error': 'Invalid JSON'}, 400)
            return
        
        # Authenticate
        passcode = data.get('passcode', '')
        if not self._authenticate(passcode):
            self._send_json_response({'error': 'Invalid passcode'}, 401)
            return
        
        if self.path.startswith('/api/event'):
            self._handle_update_event(data)
        elif self.path.startswith('/api/drivers'):
            self._handle_update_drivers(data)
        elif self.path.startswith('/api/tracker'):
            self._handle_update_tracker(data)
        else:
            self._send_json_response({'error': 'Not found'}, 404)
    
    def _handle_get_event(self):
        """Handle event data retrieval."""
        try:
            data = self.db.get_event_data()
            self._send_json_response({'success': True, 'data': data})
        except Exception as e:
            self._send_json_response({'error': str(e)}, 500)
    
    def _handle_get_drivers(self):
        """Handle drivers data retrieval."""
        try:
            data = self.db.get_drivers()
            self._send_json_response({'success': True, 'data': data})
        except Exception as e:
            self._send_json_response({'error': str(e)}, 500)
    
    def _handle_get_tracker(self):
        """Handle tracker data retrieval."""
        try:
            data = self.db.get_tracker_slots()
            self._send_json_response({'success': True, 'data': data})
        except Exception as e:
            self._send_json_response({'error': str(e)}, 500)
    
    def _handle_update_event(self, data):
        """Handle event data updates."""
        try:
            event_data = data.get('event', {})
            for key, value in event_data.items():
                self.db.set_event_field(key, value)
            self._send_json_response({'success': True})
        except Exception as e:
            self._send_json_response({'error': str(e)}, 500)
    
    def _handle_update_drivers(self, data):
        """Handle driver data updates."""
        try:
            action = data.get('action')
            driver_data = data.get('driver', {})
            
            if action == 'add':
                name = driver_data.get('name', '')
                timezone = driver_data.get('timezone', '')
                self.db.add_driver(name, timezone)
            elif action == 'remove':
                name = driver_data.get('name', '')
                self.db.remove_driver(name)
            elif action == 'update_slots':
                name = driver_data.get('name', '')
                available = driver_data.get('available', [])
                maybe = driver_data.get('maybe', [])
                unavailable = driver_data.get('unavailable', [])
                self.db.update_driver_slots(name, available, maybe, unavailable)
            
            self._send_json_response({'success': True})
        except Exception as e:
            self._send_json_response({'error': str(e)}, 500)
    
    def _handle_update_tracker(self, data):
        """Handle tracker data updates."""
        try:
            action = data.get('action')
            slot_data = data.get('slot', {})
            
            if action == 'add':
                self.db.add_tracker_slot(slot_data)
            elif action == 'update':
                time_slot = data.get('time_slot', '')
                self.db.update_tracker_slot(time_slot, slot_data)
            elif action == 'delete':
                time_slot = data.get('time_slot', '')
                self.db.delete_tracker_slot(time_slot)
            
            self._send_json_response({'success': True})
        except Exception as e:
            self._send_json_response({'error': str(e)}, 500)


class InternetTrackerServer:
    """HTTP server for internet-based tracker communication."""
    
    def __init__(self, host="0.0.0.0", port=8080, db=None, passcode=None):
        self.host = host
        self.port = port
        self.db = db
        self.passcode = passcode
        self.server = None
        self.server_thread = None
        self.status = "stopped"
    
    def start(self):
        """Start the HTTP server."""
        def handler_factory(*args, **kwargs):
            return InternetTrackerRequestHandler(*args, db=self.db, passcode=self.passcode, **kwargs)
        
        self.server = HTTPServer((self.host, self.port), handler_factory)
        self.server_thread = Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()
        self.status = "started"
        print(f"Internet tracker server started on {self.host}:{self.port}")
    
    def stop(self):
        """Stop the HTTP server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        if self.server_thread:
            self.server_thread.join(timeout=1)
        self.status = "stopped"
        print("Internet tracker server stopped")


class InternetTrackerClient:
    """HTTP client for internet-based tracker communication."""
    
    def __init__(self, host="localhost", port=8080, db=None, passcode=None):
        self.host = host
        self.port = port
        self.db = db
        self.passcode = passcode
        self.base_url = f"http://{host}:{port}/api"
        self.status = "disconnected"
    
    def _make_request(self, endpoint, method="GET", data=None):
        """Make an HTTP request to the server."""
        url = f"{self.base_url}/{endpoint}"
        
        if method == "GET":
            try:
                response = urlopen(url, timeout=10)
                return json.loads(response.read().decode())
            except URLError as e:
                print(f"Error making GET request: {e}")
                return None
        
        elif method == "POST":
            if data is None:
                data = {}
            data['passcode'] = self.passcode
            
            try:
                import urllib.request
                req = urllib.request.Request(
                    url, 
                    data=json.dumps(data).encode(),
                    headers={'Content-Type': 'application/json'}
                )
                response = urlopen(req, timeout=10)
                return json.loads(response.read().decode())
            except URLError as e:
                print(f"Error making POST request: {e}")
                return None
    
    def connect(self):
        """Test connection to server."""
        response = self._make_request("event")
        if response and response.get('success'):
            self.status = "connected"
            print(f"Connected to internet tracker server at {self.host}:{self.port}")
            return True
        else:
            self.status = "disconnected"
            print(f"Failed to connect to server at {self.host}:{self.port}")
            return False
    
    def disconnect(self):
        """Disconnect from server (no-op for HTTP client)."""
        self.status = "disconnected"
        print("Disconnected from internet tracker server")
    
    def update_value(self, item='', index='', value=None):
        """Update an event field value."""
        if item in ('drivers', 'trackers'):
            # Handle driver/tracker updates differently
            return
        
        response = self._make_request("event", "POST", {
            'event': {item: value}
        })
        
        if response and response.get('success'):
            # Also update local DB if available
            if self.db is not None:
                self.db.set_event_field(item, value)
            print(f"Updated {item} = {value}")
        else:
            print(f"Failed to update {item}")
    
    def update_drivers_time_slots(self, drivers_time_slots: dict) -> None:
        """Update driver availability slots."""
        for driver_name, slots in drivers_time_slots.items():
            available = [i + 1 for i, v in enumerate(slots) if v == '1']
            maybe = [i + 1 for i, v in enumerate(slots) if v == '2']
            unavailable = [i + 1 for i, v in enumerate(slots) if v == '0']
            
            response = self._make_request("drivers", "POST", {
                'action': 'update_slots',
                'driver': {
                    'name': driver_name,
                    'available': available,
                    'maybe': maybe,
                    'unavailable': unavailable
                }
            })
            
            if response and response.get('success'):
                # Also update local DB if available
                if self.db is not None:
                    self.db.update_driver_slots(driver_name, available, maybe, unavailable)
                print(f"Updated driver slots for {driver_name}")
            else:
                print(f"Failed to update driver slots for {driver_name}")
    
    def reset_drivers(self):
        """Reset all drivers (not implemented for internet client)."""
        print("Reset drivers not implemented for internet client")
