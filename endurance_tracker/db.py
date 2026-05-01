"""SQLite database layer replacing the original JSON + Google Sheets storage."""

import sqlite3
import json
from typing import Any


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
