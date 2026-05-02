# EnduranceTracker

A comprehensive endurance racing management application that supports both desktop (Tkinter) and web-based interfaces for managing drivers, planning stints, and tracking live race data.

**🌐 NEW: Web Interface Available** - Choose between traditional desktop GUI or modern web-based interface. Both modes support internet collaboration with MongoDB and secure authentication.

---

## Features

### Core Functionality
- **Race Event Management**: Set up events with duration, start time, track, car, and team details
- **Driver Management**: Add drivers with timezone support and availability tracking
- **Stint Planning**: Interactive planning grid with driver availability visualization  
- **Live Race Tracking**: Real-time lap time recording, driver changes, and race monitoring
- **Weather & Conditions**: Track weather and track conditions throughout the race
- **Multi-timezone Support**: Global teams can coordinate across time zones

### Interface Options
- **Desktop Mode (Tkinter)**: Traditional GUI application with CustomTkinter components
- **🆕 Web Mode (Flask)**: Modern browser-based interface with Bootstrap 5.3
  - Responsive design for desktop, tablet, and mobile
  - Real-time updates and modern UI components
  - Theme switching (dark/light mode)
  - RESTful API for all operations

### Communication Modes
- **Local Mode**: Single machine operation with SQLite database
- **Network Mode**: Multi-machine collaboration over local networks
- **🆕 Internet Mode**: Real-time collaboration over the internet with MongoDB
  - Server-client architecture for distributed teams
  - Secure SHA256-hashed passcode authentication
  - Real-time data synchronization
  - Support for cloud or local MongoDB instances
  - See [INTERNET_SETUP.md](INTERNET_SETUP.md) for full setup instructions

---

## Requirements

- Python 3.9+
- Dependencies listed in `requirements.txt`
- **For Internet Mode**: MongoDB (local installation or cloud service like MongoDB Atlas)
- **For Web Mode**: Modern web browser (Chrome, Firefox, Safari, Edge)

---

## Installation

### 1. Clone and Setup

```bash
git clone <repository-url>
cd EnduranceTracker
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv env

# Windows
env\Scripts\activate

# Linux/Mac
source env/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Or use the Makefile shortcut:

```bash
make init
```

---

## Configuration

The application uses a `config.ini` file to store settings and connection parameters. This file is automatically created with default values on first run, but can be customized as needed.

### Configuration Sections

#### `[general]` - Application Settings
- `geometry`: Window size and position (format: `widthxheight+x+y`)
- `dark_mode`: Enable dark theme (`True`/`False`)
- `data_dir`: Local database file path (default: `./endurance_tracker.db`)
- `server`: Enable server mode for network collaboration (`1`/`0`)
- `use_internet`: Enable internet mode with MongoDB (`True`/`False`)

#### `[settings]` - User Preferences
- `times`: Comma-separated list of timezones for driver availability
  - Example: `US/Eastern,US/Central,US/Mountain,US/Pacific`
  - Supports all standard timezone identifiers

#### `[com]` - Network Communication
- `host`: Local network host address (default: `127.0.0.1`)
- `port`: Local network port (default: `65432`)

#### `[internet]` - Internet Collaboration
- `mongodb_uri`: MongoDB connection string
  - Local: `mongodb://localhost:27017/`
  - Atlas: `mongodb+srv://username:password@cluster.mongodb.net/`
- `database_name`: MongoDB database name (default: `endurance_tracker`)
- `passcode`: SHA256-hashed authentication passcode for security
- `server_host`: Internet server host (default: `127.0.0.1`)
- `server_port`: Internet server port (default: `8080`)

### Example Configurations

**Local Only Mode** (default):
```ini
[general]
use_internet = False
server = 0
```

**Network Collaboration Mode**:
```ini
[general]
server = 1
use_internet = False

[com]
host = 192.168.1.100
port = 65432
```

**Internet Mode with MongoDB Atlas**:
```ini
[general]
use_internet = True

[internet]
mongodb_uri = mongodb+srv://username:password@cluster.mongodb.net/
database_name = my_race_team
passcode = your_secure_passcode_here
```

---

## Usage

### Desktop Mode (Traditional Tkinter GUI)

```bash
python -m endurance_tracker
```

- Traditional desktop application with familiar UI
- Lightweight and runs entirely locally
- Full feature support including internet collaboration

### Web Mode (Modern Browser Interface)

```bash
python -m endurance_tracker --web
```

- Modern web interface at `http://localhost:5000`
- Responsive design works on all devices
- Real-time updates and modern UI

#### Web Mode Options

```bash
# Custom host and port
python -m endurance_tracker --web --host 0.0.0.0 --port 8080

# Don't auto-open browser
python -m endurance_tracker --web --no-browser

# Set via environment variable
set ENDURANCE_TRACKER_WEB=true
python -m endurance_tracker
```

---

## Configuration

### Basic Configuration (`config.ini`)

```ini
[general]
geometry = 1200x800+100+100
dark_mode = False
data_dir = ./data
max_driver = 10

[settings]
times = US/Eastern,US/Central,US/Mountain,US/Pacific,Europe/London

[com]
host = localhost
port = 12345
server = False

[internet]
mongodb_uri = mongodb://localhost:27017
database_name = endurance_tracker
passcode = your_secure_passcode
server_host = 0.0.0.0
server_port = 8080
use_internet = False
```

### Internet Mode Setup

For detailed internet mode setup instructions, see **[INTERNET_SETUP.md](INTERNET_SETUP.md)**.

#### Quick Reference — Server Setup
1. Install and start MongoDB
2. Configure `config.ini`:
   ```ini
   [internet]
   mongodb_uri = mongodb://localhost:27017
   database_name = endurance_tracker
   passcode = your_team_passcode
   server_host = 0.0.0.0
   server_port = 8080
   use_internet = True
   ```
3. Run application and start as server in Home tab

#### Quick Reference — Client Setup  
1. Configure `config.ini` with server details:
   ```ini
   [internet]
   server_host = <server_ip_address>
   server_port = 8080
   passcode = your_team_passcode
   use_internet = True
   ```
2. Run application and connect as client

---

## File Structure

```
EnduranceTracker/
├── endurance_tracker/
│   ├── __init__.py              # Package initialization
│   ├── __main__.py              # Entry point with mode detection
│   ├── app.py                   # Tkinter desktop application
│   ├── web_app.py               # Flask web application
│   ├── core.py                  # Core business logic
│   ├── db.py                    # Database abstraction (SQLite/MongoDB)
│   ├── config.py                # Configuration management
│   ├── helpers.py               # Network and utility functions
│   │
│   ├── templates/               # HTML templates (Web Mode)
│   │   ├── base.html           # Base template with Bootstrap
│   │   ├── index.html          # Main dashboard
│   │   ├── home.html           # Event and connection management
│   │   ├── general.html        # Driver and settings management
│   │   ├── planning.html       # Interactive stint planning
│   │   └── race.html           # Live race tracking
│   │
│   ├── static/                  # Web assets
│   │   ├── css/
│   │   │   └── app.css         # Custom styles and themes
│   │   └── js/
│   │       └── app.js          # JavaScript utilities and API client
│   │
│   └── ui/                      # Tkinter UI components
│       ├── __init__.py
│       ├── actions.py          # UI event handlers
│       ├── tabs.py             # Tab implementations
│       └── theme.py            # Theme management
│
├── config.ini                   # Application configuration
├── requirements.txt             # Python dependencies
├── setup.py                     # Package setup
├── Makefile                     # Build automation
├── EnduranceTracker.spec       # PyInstaller spec
├── INTERNET_SETUP.md            # Internet mode setup guide
└── README.md                    # This file
```

---

## Web API Endpoints

The web mode provides a RESTful API for all operations:

### Core Data
- `GET/POST /api/event` - Race event management
- `GET/POST/DELETE /api/drivers` - Driver management  
- `GET/POST/PUT/DELETE /api/tracker` - Stint tracking data

### Race Operations
- `GET/POST /api/race` - Race state management
- `POST /api/race/laps` - Record lap times
- `POST /api/race/driver-change` - Record driver changes
- `POST /api/race/events` - Record race events (pit stops, incidents)

### Connection
- `POST /api/connection` - Internet mode connection control

---

## Development

### Running Tests
```bash
python -m pytest tests/
```

### Building Executable
```bash
python setup.py build
```

### Code Structure
- **Model**: Database layer (`db.py`) with SQLite and MongoDB support
- **View**: Tkinter UI (`ui/`) and Flask templates (`templates/`)
- **Controller**: Business logic (`core.py`) and API routes (`web_app.py`)

---

## Dependencies

### Core Dependencies
- `pandas>=2.0` - Data manipulation and analysis
- `pytz==2025.2` - Timezone support and calculations
- `babel==2.17.0` - Internationalization support

### Desktop UI (Tkinter Mode)
- `customtkinter==5.2.2` - Modern UI components
- `tkcalendar==1.6.1` - Calendar and date picker widgets  
- `darkdetect==0.8.0` - System dark mode detection

### Web UI (Flask Mode)
- `flask>=2.3.0` - Web framework
- `werkzeug>=2.3.0` - WSGI utilities

### Database & Network
- `pymongo>=4.0` - MongoDB connectivity (internet mode)
- Built-in `sqlite3` - Local database (included with Python)

---

## Troubleshooting

### Common Issues

#### Desktop Mode
- **CTkOptionMenu Errors**: Ensure customtkinter version is 5.2.2+
- **Import Errors**: Verify all dependencies installed with `pip install -r requirements.txt`
- **Theme Issues**: Check `darkdetect` installation for automatic theme detection

#### Web Mode  
- **Port Already in Use**: Change port with `--port 8080` or update config.ini
- **Flask Import Error**: Install Flask with `pip install flask>=2.3.0`
- **Browser Not Opening**: Use `--no-browser` flag and manually navigate to URL
- **Static Files Not Loading**: Ensure `static/` directory exists with CSS/JS files

#### Internet Mode
- **Cannot Connect**: Check firewall settings and MongoDB connectivity
- **Invalid Passcode**: Ensure all machines use identical passcode (case-sensitive)
- **MongoDB Errors**: Verify MongoDB service is running and accessible
- **Sync Issues**: Check network latency and MongoDB performance

#### Database Issues
- **SQLite Locked**: Close other instances of the application
- **MongoDB Connection Failed**: Verify connection string and network access
- **Data Not Syncing**: Check internet mode is enabled on all clients

### Performance Tips
- **Large Datasets**: Consider MongoDB indexing for better performance
- **Slow Web Interface**: Check browser developer tools for network issues
- **Memory Usage**: Restart application periodically for long races

### Fallback Options
- If internet mode fails, application automatically falls back to local SQLite
- All data remains accessible locally even without network connectivity
- Desktop mode available if web browser issues occur

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with proper testing
4. Update documentation as needed
5. Submit a pull request with detailed description

### Development Setup
```bash
# Clone and setup development environment
git clone <repository-url>
cd EnduranceTracker
python -m venv dev-env
dev-env/Scripts/activate  # Windows
pip install -r requirements.txt
pip install -e .  # Editable install

# Run tests
python -m pytest tests/

# Test both modes
python -m endurance_tracker          # Desktop mode
python -m endurance_tracker --web    # Web mode
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Support

- **Documentation**: Check this README and inline code comments
- **Configuration**: Review `config.ini` settings for your use case
- **Issues**: Report bugs and feature requests via GitHub issues
- **Internet Setup**: See [INTERNET_SETUP.md](INTERNET_SETUP.md) for MongoDB and network requirements

**Choose Your Interface:**
- **Desktop Mode**: Traditional GUI for local use and familiar interface
- **Web Mode**: Modern browser interface for remote access and mobile support

Both modes provide identical functionality - pick what works best for your team!
