# EnduranceTracker

A desktop GUI application for planning and tracking endurance races with real-time multi-machine collaboration over the internet. Manage driver stints, record weather and track conditions, and coordinate a team across multiple time zones and locations.

**🌐 NEW: Internet Communication Support** - Multiple machines can now collaborate in real-time over the internet using MongoDB and secure passcode authentication.

---

## Features

### Core Functionality
- Set up race events (duration, start time, track, car, team)
- Assign drivers to time slots with availability tracking  
- Record actual stints, weather conditions, and track status in real time
- Dark mode support
- Multi-timezone support for global teams

### Communication Modes
- **Local Mode**: Single machine operation with SQLite database
- **Network Mode**: Multi-machine collaboration over local networks
- **🆕 Internet Mode**: Real-time collaboration over the internet with MongoDB
  - Server-client architecture for distributed teams
  - Secure passcode authentication
  - Real-time data synchronization
  - Support for cloud or local MongoDB instances

---

## Requirements

- Python 3.9+
- Dependencies listed in `requirements.txt`
- **For Internet Mode**: MongoDB (local installation or cloud service like MongoDB Atlas)

---

## Quick Start

### 1. Installation

```bash
pip install -r requirements.txt
```

Or use the Makefile shortcut:

```bash
make init
```

### 2. Choose Your Setup

**Single Machine (Local Mode)**
```bash
python -m endurance_tracker
```
Default configuration works out of the box with SQLite.

**Multiple Machines (Internet Mode)**
1. Set up MongoDB (see [Internet Setup Guide](INTERNET_SETUP.md))
2. Configure one machine as server, others as clients
3. Share the same passcode across all machines
4. Run the application and use the connection controls in the General tab

---

## Configuration

### Basic Configuration (`config.ini`)

| Section    | Key          | Description                                      |
|------------|--------------|--------------------------------------------------|
| `general`  | `geometry`   | Initial window size and position                 |
| `general`  | `dark_mode`  | `True` or `False`                                |
| `general`  | `data_dir`   | Path to SQLite database (local mode only)       |
| `general`  | `server`     | `True` for server mode, `False` for client      |
| `general`  | `use_internet` | `True` to enable internet mode                 |
| `settings` | `times`      | Comma-separated list of time zones to display   |

### Local Network Configuration

| Section | Key    | Description                              |
|---------|--------|------------------------------------------|
| `com`   | `host` | Host address for local network communication |
| `com`   | `port` | Port for local network communication     |

### Internet Configuration (New)

| Section    | Key           | Description                                 |
|------------|---------------|---------------------------------------------|
| `internet` | `mongodb_uri` | MongoDB connection string                   |
| `internet` | `database_name` | MongoDB database name                     |
| `internet` | `passcode`    | Shared authentication passcode              |
| `internet` | `server_host` | Server IP address (0.0.0.0 for server)     |
| `internet` | `server_port` | HTTP server port (default: 8080)           |

---

## Internet Setup Guide

For detailed instructions on setting up multi-machine internet communication, see **[INTERNET_SETUP.md](INTERNET_SETUP.md)**.

Key steps:
1. **Install MongoDB** (locally or use MongoDB Atlas)
2. **Configure server machine** with internet mode enabled
3. **Connect client machines** using server IP and shared passcode
4. **Start collaborating** in real-time across the internet

---

## Usage Modes

### 🏠 Local Mode (Single Machine)
- Uses SQLite database stored locally
- No network configuration required
- Perfect for individual use or single-machine setups

### 🏢 Network Mode (Local Network)  
- Multiple machines on same local network
- Uses socket communication between machines
- Shared SQLite database on server machine

### 🌐 Internet Mode (Global Collaboration)
- Multiple machines anywhere on the internet
- Uses HTTP API with MongoDB database
- Secure passcode authentication required
- Real-time synchronization across all connected clients

---

## Security Features

- **Passcode Authentication**: All internet communications protected by shared passcode
- **SHA256 Hashing**: Passcodes are securely hashed during transmission
- **API Security**: All data operations require valid authentication
- **Connection Control**: Manual connect/disconnect for secure session management

---

## Development

### Testing
```bash
make test
# or
py.test tests
```

### Building Executable
```bash
make build
# or
pyinstaller EnduranceTracker.spec
```

---

## Dependencies

Core dependencies in `requirements.txt`:
- `pandas>=2.0` - Data manipulation and analysis
- `customtkinter==5.2.2` - Modern UI components  
- `tkcalendar==1.6.1` - Calendar widgets
- `pytz==2025.2` - Timezone support
- `pymongo>=4.0` - MongoDB database connectivity (for internet mode)
- `darkdetect==0.8.0` - System dark mode detection

---

## Troubleshooting

### Connection Issues
- **Cannot connect**: Check firewall settings and network connectivity
- **Invalid passcode**: Ensure all machines use identical passcode
- **MongoDB errors**: Verify MongoDB service is running and accessible

### Performance
- **Slow sync**: Check network latency and MongoDB performance
- **Large datasets**: Consider data cleanup or MongoDB indexing

### Fallback Options
- If internet mode fails, application automatically falls back to local SQLite mode
- All data remains accessible locally even without network connectivity

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

---

### Need Help?

- Check the [Internet Setup Guide](INTERNET_SETUP.md) for detailed configuration instructions
- Review `config.ini` settings for your specific use case  
- Ensure all network requirements are met for internet mode

Please report any issues or feature requests through the project's issue tracker.
