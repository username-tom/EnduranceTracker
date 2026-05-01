# EnduranceTracker

A desktop GUI application for planning and tracking endurance races. Manage driver stints, record weather and track conditions, and coordinate a team across multiple time zones — all stored locally in a SQLite database.

---

## Features

- Set up race events (duration, start time, track, car, team)
- Assign drivers to time slots with availability tracking
- Record actual stints, weather conditions, and track status in real time
- Dark mode support
- Optional client/server mode for multi-machine use over a local network

---

## Requirements

- Python 3.9+
- Dependencies listed in `requirements.txt` (Tkinter is part of the Python standard library)

---

## Installation

```bash
pip install -r requirements.txt
```

Or use the Makefile shortcut:

```bash
make init
```

---

## Configuration

Edit `config.ini` in the project root before running:

| Section    | Key        | Description                                      |
|------------|------------|--------------------------------------------------|
| `general`  | `geometry` | Initial window size and position                 |
| `general`  | `dark_mode`| `True` or `False`                                |
| `general`  | `data_dir` | Path to the SQLite database file                 |
| `general`  | `server`   | `True` to run as server, `False` for client mode |
| `settings` | `times`    | Comma-separated list of time zones to display    |
| `com`      | `host`     | Host address for client/server communication     |
| `com`      | `port`     | Port for client/server communication             |

---

## Running

```bash
python -m endurance_tracker
```

---

## Testing

```bash
make test
# or
py.test tests
```

---

### Please let me know if you run into any issues
