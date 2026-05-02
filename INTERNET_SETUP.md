# Internet Communication Setup Guide

The EnduranceTracker now supports internet communication allowing multiple machines to share data in real-time using a server-client architecture with passcode authentication.

## Overview

- **Server**: Hosts the data and runs the HTTP API server
- **Clients**: Connect to the server to access and edit shared data
- **Authentication**: All communication is protected by a shared passcode
- **Database**: Uses MongoDB for internet mode, SQLite for local mode

## Setup Instructions

### 1. MongoDB Setup (Required for Internet Mode)

**Option A: Local MongoDB**
1. Download and install MongoDB Community Edition from https://www.mongodb.com/try/download/community
2. Start MongoDB service (usually `mongod` or as a system service)
3. Default connection: `mongodb://localhost:27017/`

**Option B: MongoDB Atlas (Cloud)**
1. Create free account at https://www.mongodb.com/atlas
2. Create a cluster and get connection string
3. Example: `mongodb+srv://username:password@cluster.mongodb.net/`

### 2. Application Configuration

1. **Enable Internet Mode**: Check "Enable Internet Mode" in the General tab
2. **Choose Mode**: 
   - Select "Server" for the machine that will host data
   - Select "Client" for machines that will connect to the server
3. **Server Address**: 
   - Server: Use `0.0.0.0` (listens on all interfaces) or specific IP
   - Clients: Enter the server's IP address or hostname
4. **Port**: Default is 8080 (make sure it's open in firewall)
5. **Passcode**: Set a secure shared passcode (same on server and all clients)

### 3. Network Configuration

**For the Server Machine:**
- Ensure port 8080 (or your chosen port) is open in firewall
- If using router, forward the port to the server machine
- Note the public IP address for clients to connect

**For Client Machines:**
- Ensure outbound connections are allowed
- Use server's public IP address and port

## Usage Workflow

### Starting the Server
1. On the server machine:
   - Enable Internet Mode
   - Select "Server" mode
   - Set Server Address to `0.0.0.0` (or specific IP)
   - Set desired port and passcode
   - Click "Connect" to start server

### Connecting Clients
1. On client machines:
   - Enable Internet Mode  
   - Select "Client" mode
   - Enter server's IP address and port
   - Enter the same passcode as server
   - Click "Connect"

### Data Synchronization
- All changes made on any client are immediately synchronized to the server
- Server acts as the single source of truth for all data
- Data persists in MongoDB database

## Configuration Files

The settings are saved in `config.ini`:

```ini
[general]
use_internet = true
server = true  # or false for client

[internet]
mongodb_uri = mongodb://localhost:27017/
database_name = endurance_tracker
passcode = your_secure_passcode_here
server_host = 0.0.0.0
server_port = 8080
```

## Troubleshooting

### Connection Issues
- Verify MongoDB is running and accessible
- Check firewall settings on both server and client
- Ensure correct IP addresses and ports
- Verify passcode matches on server and clients

### MongoDB Issues
- Make sure MongoDB service is running
- Check connection string format
- Verify database permissions (for cloud databases)
- Install pymongo: `pip install pymongo>=4.0`

### Performance Notes
- First connection may take a few seconds to establish
- Large datasets may take time to sync initially
- Network latency affects real-time updates

## Security Considerations

1. **Passcode**: Use a strong, unique passcode
2. **Network**: Consider using VPN for internet connections
3. **Firewall**: Only open necessary ports
4. **MongoDB**: Secure your MongoDB instance properly
5. **HTTPS**: For production use, consider adding SSL/TLS

## Fallback to Local Mode

If internet mode fails to initialize, the application automatically falls back to local SQLite mode. You can also manually disable internet mode by:

1. Unchecking "Enable Internet Mode" 
2. Restarting the application
3. Or editing `config.ini` to set `use_internet = false`