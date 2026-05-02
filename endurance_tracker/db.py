"""SQLite database layer replacing the original JSON + Google Sheets storage."""

import sqlite3
import json
from typing import Any

try:
    from pymongo import MongoClient
    from pymongo.errors import ServerSelectionTimeoutError
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False


class Database:
    def __init__(self, path: str):
        self.path = path
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self._init_tables()

    def _init_tables(self):
        c = self.conn.cursor()
        c.executescript("""
            CREATE TABLE IF NOT EXISTS event (
                key   TEXT PRIMARY KEY,
                value TEXT
            );
            CREATE TABLE IF NOT EXISTS drivers (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                name              TEXT UNIQUE,
                timezone          TEXT,
                available_stints  TEXT DEFAULT '[]',
                maybe_stints      TEXT DEFAULT '[]',
                unavailable_stints TEXT DEFAULT '[]'
            );
            CREATE TABLE IF NOT EXISTS tracker (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                time_slot           TEXT UNIQUE,
                planned_driver      TEXT DEFAULT '',
                planned_stint       TEXT DEFAULT '',
                actual_driver       TEXT DEFAULT '',
                actual_stint        TEXT DEFAULT '',
                est_rain            REAL DEFAULT 0,
                act_weather         TEXT DEFAULT '',
                act_track_condition TEXT DEFAULT '',
                notes               TEXT DEFAULT ''
            );
        """)
        self.conn.commit()

    # ------------------------------------------------------------------ event

    def get_event_data(self) -> dict:
        c = self.conn.cursor()
        c.execute("SELECT key, value FROM event")
        return dict(c.fetchall())

    def set_event_field(self, key: str, value: Any) -> None:
        c = self.conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO event (key, value) VALUES (?, ?)",
            (key, str(value) if value is not None else ''),
        )
        self.conn.commit()

    # ----------------------------------------------------------------- drivers

    def get_drivers(self) -> list:
        c = self.conn.cursor()
        c.execute(
            "SELECT name, timezone, available_stints, maybe_stints, unavailable_stints "
            "FROM drivers ORDER BY id"
        )
        result = []
        for row in c.fetchall():
            result.append({
                'name': row[0],
                'timezone': row[1],
                'available': json.loads(row[2]) if row[2] else [],
                'maybe': json.loads(row[3]) if row[3] else [],
                'unavailable': json.loads(row[4]) if row[4] else [],
            })
        return result

    def add_driver(self, name: str, tz: str = '') -> None:
        c = self.conn.cursor()
        c.execute(
            "INSERT OR IGNORE INTO drivers "
            "(name, timezone, available_stints, maybe_stints, unavailable_stints) "
            "VALUES (?, ?, '[]', '[]', '[]')",
            (name, tz),
        )
        self.conn.commit()

    def remove_driver(self, name: str) -> None:
        c = self.conn.cursor()
        c.execute("DELETE FROM drivers WHERE name = ?", (name,))
        self.conn.commit()

    def update_driver_slots(
        self,
        name: str,
        available: list,
        maybe: list,
        unavailable: list,
    ) -> None:
        c = self.conn.cursor()
        c.execute(
            "UPDATE drivers SET available_stints=?, maybe_stints=?, unavailable_stints=? "
            "WHERE name=?",
            (json.dumps(available), json.dumps(maybe), json.dumps(unavailable), name),
        )
        if c.rowcount == 0:
            c.execute(
                "INSERT INTO drivers (name, timezone, available_stints, maybe_stints, unavailable_stints) "
                "VALUES (?, '', ?, ?, ?)",
                (name, json.dumps(available), json.dumps(maybe), json.dumps(unavailable)),
            )
        self.conn.commit()

    # ----------------------------------------------------------------- tracker

    def get_tracker_slots(self) -> list:
        c = self.conn.cursor()
        c.execute(
            "SELECT time_slot, planned_driver, planned_stint, actual_driver, actual_stint, "
            "est_rain, act_weather, act_track_condition, notes FROM tracker ORDER BY id"
        )
        cols = [
            'time_slot', 'planned_driver', 'planned_stint', 'actual_driver',
            'actual_stint', 'est_rain', 'act_weather', 'act_track_condition', 'notes',
        ]
        return [dict(zip(cols, row)) for row in c.fetchall()]

    def add_tracker_slot(self, slot: dict) -> None:
        c = self.conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO tracker "
            "(time_slot, planned_driver, planned_stint, actual_driver, actual_stint, "
            "est_rain, act_weather, act_track_condition, notes) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                slot.get('time_slot', ''),
                slot.get('planned_driver', ''),
                slot.get('planned_stint', ''),
                slot.get('actual_driver', ''),
                slot.get('actual_stint', ''),
                slot.get('est_rain', 0),
                slot.get('act_weather', ''),
                slot.get('act_track_condition', ''),
                slot.get('notes', ''),
            ),
        )
        self.conn.commit()

    def update_tracker_slot(self, time_slot: str, slot: dict) -> None:
        c = self.conn.cursor()
        c.execute(
            "UPDATE tracker SET "
            "planned_driver=?, planned_stint=?, actual_driver=?, actual_stint=?, "
            "est_rain=?, act_weather=?, act_track_condition=?, notes=? "
            "WHERE time_slot=?",
            (
                slot.get('planned_driver', ''),
                slot.get('planned_stint', ''),
                slot.get('actual_driver', ''),
                slot.get('actual_stint', ''),
                slot.get('est_rain', 0),
                slot.get('act_weather', ''),
                slot.get('act_track_condition', ''),
                slot.get('notes', ''),
                time_slot,
            ),
        )
        self.conn.commit()

    def delete_tracker_slot(self, time_slot: str) -> None:
        c = self.conn.cursor()
        c.execute("DELETE FROM tracker WHERE time_slot = ?", (time_slot,))
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()


class MongoDatabase:
    """MongoDB database implementation for internet communication."""
    
    def __init__(self, uri: str, database_name: str):
        if not PYMONGO_AVAILABLE:
            raise ImportError("pymongo is required for MongoDB support")
        
        self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        try:
            # Test connection
            self.client.admin.command('ping')
        except ServerSelectionTimeoutError:
            raise ConnectionError(f"Could not connect to MongoDB at {uri}")
        
        self.db = self.client[database_name]
        self.event_collection = self.db.event
        self.drivers_collection = self.db.drivers
        self.tracker_collection = self.db.tracker

    # ------------------------------------------------------------------ event

    def get_event_data(self) -> dict:
        """Get all event data as a dictionary."""
        result = {}
        for doc in self.event_collection.find():
            result[doc['key']] = doc['value']
        return result

    def set_event_field(self, key: str, value: Any) -> None:
        """Set an event field value."""
        self.event_collection.update_one(
            {'key': key},
            {'$set': {'key': key, 'value': str(value) if value is not None else ''}},
            upsert=True
        )

    # ----------------------------------------------------------------- drivers

    def get_drivers(self) -> list:
        """Get all drivers with their availability data."""
        result = []
        for doc in self.drivers_collection.find().sort('_id', 1):
            result.append({
                'name': doc.get('name', ''),
                'timezone': doc.get('timezone', ''),
                'available': doc.get('available', []),
                'maybe': doc.get('maybe', []),
                'unavailable': doc.get('unavailable', []),
            })
        return result

    def add_driver(self, name: str, tz: str = '') -> None:
        """Add a new driver."""
        existing = self.drivers_collection.find_one({'name': name})
        if not existing:
            self.drivers_collection.insert_one({
                'name': name,
                'timezone': tz,
                'available': [],
                'maybe': [],
                'unavailable': [],
            })

    def remove_driver(self, name: str) -> None:
        """Remove a driver."""
        self.drivers_collection.delete_one({'name': name})

    def update_driver_slots(
        self,
        name: str,
        available: list,
        maybe: list,
        unavailable: list,
    ) -> None:
        """Update driver availability slots."""
        self.drivers_collection.update_one(
            {'name': name},
            {
                '$set': {
                    'available': available,
                    'maybe': maybe,
                    'unavailable': unavailable,
                }
            },
            upsert=True
        )

    # ----------------------------------------------------------------- tracker

    def get_tracker_slots(self) -> list:
        """Get all tracker slots."""
        result = []
        for doc in self.tracker_collection.find().sort('_id', 1):
            result.append({
                'time_slot': doc.get('time_slot', ''),
                'planned_driver': doc.get('planned_driver', ''),
                'planned_stint': doc.get('planned_stint', ''),
                'actual_driver': doc.get('actual_driver', ''),
                'actual_stint': doc.get('actual_stint', ''),
                'est_rain': doc.get('est_rain', 0),
                'act_weather': doc.get('act_weather', ''),
                'act_track_condition': doc.get('act_track_condition', ''),
                'notes': doc.get('notes', ''),
            })
        return result

    def add_tracker_slot(self, slot: dict) -> None:
        """Add or replace a tracker slot."""
        self.tracker_collection.update_one(
            {'time_slot': slot.get('time_slot', '')},
            {'$set': slot},
            upsert=True
        )

    def update_tracker_slot(self, time_slot: str, slot: dict) -> None:
        """Update a tracker slot."""
        update_data = {k: v for k, v in slot.items() if k != 'time_slot'}
        self.tracker_collection.update_one(
            {'time_slot': time_slot},
            {'$set': update_data}
        )

    def delete_tracker_slot(self, time_slot: str) -> None:
        """Delete a tracker slot."""
        self.tracker_collection.delete_one({'time_slot': time_slot})

    def close(self) -> None:
        """Close the MongoDB connection."""
        self.client.close()
