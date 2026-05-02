"""Web-based EnduranceTracker application using Flask."""

import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.serving import make_server
import threading
import webbrowser
from datetime import datetime
import json

from .config import (
    GEOMETRY, DATA_DIR, USE_INTERNET, MONGODB_URI, DATABASE_NAME, 
    PASSCODE, SHOW_PASSWORD, SERVER_HOST, SERVER_PORT, IS_SERVER
)
from .db import Database, MongoDatabase
from .helpers import InternetTrackerClient, InternetTrackerServer

app = Flask(__name__)
app.secret_key = 'endurance_tracker_secret_key'

# Global variables
db = None
server = None
client = None
web_server = None
web_thread = None

def init_database():
    """Initialize the database based on configuration."""
    global db, server, client
    
    if USE_INTERNET:
        try:
            db = MongoDatabase(MONGODB_URI, DATABASE_NAME)
            server = InternetTrackerServer(SERVER_HOST, SERVER_PORT, db=db, passcode=PASSCODE)
            client = InternetTrackerClient(SERVER_HOST, SERVER_PORT, db=db, passcode=PASSCODE)
            print(f"Internet mode enabled - MongoDB: {MONGODB_URI}/{DATABASE_NAME}")
        except Exception as e:
            print(f"Failed to initialize internet mode: {e}")
            print("Falling back to local mode...")
            db = Database(DATA_DIR)
    else:
        db = Database(DATA_DIR)

@app.route('/')
def index():
    """Main dashboard."""
    return render_template('index.html')

@app.route('/home')
def home():
    """Connection and server management."""
    return render_template('home.html', 
                         use_internet=USE_INTERNET,
                         is_server=IS_SERVER,
                         server_host=SERVER_HOST,
                         server_port=SERVER_PORT,
                         show_password=SHOW_PASSWORD)

@app.route('/general')
def general():
    """Event and general settings."""
    event_data = db.get_event_data() if db else {}
    drivers = db.get_drivers() if db else []
    return render_template('general.html', 
                         event_data=event_data,
                         drivers=drivers)

@app.route('/planning')
def planning():
    """Driver planning and availability."""
    drivers = db.get_drivers() if db else []
    tracker_slots = db.get_tracker_slots() if db else []
    return render_template('planning.html',
                         drivers=drivers,
                         tracker_slots=tracker_slots)

@app.route('/race')
def race():
    """Live race tracking."""
    tracker_slots = db.get_tracker_slots() if db else []
    return render_template('race.html',
                         tracker_slots=tracker_slots)

# API Routes
@app.route('/api/event', methods=['GET', 'POST'])
def api_event():
    """Event data API."""
    if request.method == 'GET':
        return jsonify(db.get_event_data() if db else {})
    
    elif request.method == 'POST':
        data = request.json
        for key, value in data.items():
            if db:
                db.set_event_field(key, value)
        return jsonify({'success': True})

@app.route('/api/drivers', methods=['GET', 'POST', 'DELETE'])
def api_drivers():
    """Drivers API."""
    if request.method == 'GET':
        return jsonify(db.get_drivers() if db else [])
    
    elif request.method == 'POST':
        data = request.json
        action = data.get('action')
        
        if action == 'add':
            name = data.get('name', '')
            timezone = data.get('timezone', '')
            if db and name:
                db.add_driver(name, timezone)
                return jsonify({'success': True})
        
        elif action == 'update_slots':
            name = data.get('name', '')
            available = data.get('available', [])
            maybe = data.get('maybe', [])
            unavailable = data.get('unavailable', [])
            if db and name:
                db.update_driver_slots(name, available, maybe, unavailable)
                return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        name = request.json.get('name', '')
        if db and name:
            db.remove_driver(name)
            return jsonify({'success': True})
    
    return jsonify({'success': False})

@app.route('/api/tracker', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_tracker():
    """Tracker slots API."""
    if request.method == 'GET':
        return jsonify(db.get_tracker_slots() if db else [])
    
    elif request.method == 'POST':
        slot = request.json
        if db:
            db.add_tracker_slot(slot)
            return jsonify({'success': True})
    
    elif request.method == 'PUT':
        data = request.json
        time_slot = data.get('time_slot', '')
        slot = data.get('slot', {})
        if db and time_slot:
            db.update_tracker_slot(time_slot, slot)
            return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        time_slot = request.json.get('time_slot', '')
        if db and time_slot:
            db.delete_tracker_slot(time_slot)
            return jsonify({'success': True})
    
    return jsonify({'success': False})

@app.route('/api/connection', methods=['POST'])
def api_connection():
    """Connection management API."""
    global server, client
    
    data = request.json
    action = data.get('action')
    
    if action == 'connect':
        try:
            if data.get('is_server', False):
                # Start server
                if server and hasattr(server, 'start'):
                    server.start()
                    return jsonify({'success': True, 'status': 'Server started'})
            else:
                # Connect client
                if client and hasattr(client, 'connect'):
                    if client.connect():
                        return jsonify({'success': True, 'status': 'Connected to server'})
                    else:
                        return jsonify({'success': False, 'error': 'Failed to connect'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    elif action == 'disconnect':
        try:
            if data.get('is_server', False):
                # Stop server
                if server and hasattr(server, 'stop'):
                    server.stop()
                    return jsonify({'success': True, 'status': 'Server stopped'})
            else:
                # Disconnect client
                if client and hasattr(client, 'disconnect'):
                    client.disconnect()
                    return jsonify({'success': True, 'status': 'Disconnected'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    return jsonify({'success': False, 'error': 'Invalid action'})

@app.route('/api/race', methods=['GET', 'POST'])
def api_race():
    """Race state management."""
    try:
        if request.method == 'POST':
            # Update race state
            data = request.get_json()
            # Store race state (would typically use database)
            return jsonify({'success': True})
        else:
            # Get current race state
            return jsonify({
                'isRunning': False,
                'startTime': None,
                'currentLap': 0,
                'currentDriver': None,
                'lapTimes': [],
                'bestLap': None,
                'lastLap': None
            })
    except Exception as e:
        logger.error(f"Race API error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/race/laps', methods=['POST'])
def api_race_laps():
    """Record lap times."""
    try:
        data = request.get_json()
        # Store lap data (would typically use database)
        logger.info(f"Recorded lap: {data}")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Lap recording error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/race/driver-change', methods=['POST'])
def api_race_driver_change():
    """Record driver changes."""
    try:
        data = request.get_json()
        # Store driver change (would typically use database)
        logger.info(f"Driver change: {data}")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Driver change error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/race/events', methods=['POST'])
def api_race_events():
    """Record race events (pit stops, incidents, etc.)."""
    try:
        data = request.get_json()
        # Store event (would typically use database)
        logger.info(f"Race event: {data}")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Race event error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def start_web_server(host='127.0.0.1', port=5000, open_browser=True):
    """Start the Flask web server."""
    global web_server, web_thread
    
    # Initialize database
    init_database()
    
    # Configure Flask app
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    
    app.template_folder = template_dir
    app.static_folder = static_dir
    
    # Create server
    web_server = make_server(host, port, app, threaded=True)
    
    # Start server in background thread
    web_thread = threading.Thread(target=web_server.serve_forever, daemon=True)
    web_thread.start()
    
    print(f"EnduranceTracker web server started at http://{host}:{port}")
    
    # Open browser
    if open_browser:
        webbrowser.open(f"http://{host}:{port}")
    
    return web_server

def stop_web_server():
    """Stop the Flask web server."""
    global web_server
    if web_server:
        web_server.shutdown()
        web_server = None
        print("Web server stopped")

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)