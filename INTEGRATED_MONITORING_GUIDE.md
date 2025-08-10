# 🚀 Integrated Monitoring Guide

## Overview

The FocusGuard application now supports **integrated monitoring** directly within `main.py`, eliminating the need to run separate monitoring scripts. The monitoring functionality is built into the main server and can be controlled via API endpoints.

## 🎯 Two Monitoring Options

### Option 1: Integrated Monitoring (Recommended)
- **Single Process**: Everything runs in `main.py`
- **API Control**: Start/stop monitoring via HTTP endpoints
- **Automatic**: No need for separate scripts
- **Platform**: Works on Windows with proper dependencies

### Option 2: Simultaneous Monitoring (Legacy)
- **Multiple Processes**: `main.py` + separate monitoring scripts
- **Manual Control**: Run scripts in separate terminals
- **Flexible**: Can run monitoring scripts independently
- **Platform**: Works on any platform

## 🔧 Integrated Monitoring Setup

### Prerequisites
```bash
# Install Windows monitoring dependencies
pip install psutil pywin32

# Or update requirements.txt and install all dependencies
pip install -r requirements.txt
```

### Starting the Server
```bash
# Start the main server (includes monitoring capability)
python main.py
```

### Using Integrated Monitoring

#### 1. Check Monitoring Status
```bash
curl http://localhost:8000/monitoring/status
```

#### 2. Start Monitoring
```bash
curl -X POST "http://localhost:8000/monitoring/start/cheerful_soul_44?duration_minutes=30"
```

#### 3. Stop Monitoring
```bash
curl -X POST http://localhost:8000/monitoring/stop
```

#### 4. Get Current Window
```bash
curl http://localhost:8000/monitoring/current-window
```

## 📋 API Endpoints

### Monitoring Control Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/monitoring/start/{username}` | POST | Start monitoring for a user |
| `/monitoring/stop` | POST | Stop active monitoring |
| `/monitoring/status` | GET | Get monitoring status |
| `/monitoring/current-window` | GET | Get current active window |
| `/monitoring/setup-simultaneous` | POST | Get setup instructions |

### Parameters

#### Start Monitoring
- `username` (path): The username to monitor
- `duration_minutes` (query): Duration in minutes (default: 30)

#### Response Format
```json
{
  "status": "success",
  "message": "Monitoring started for cheerful_soul_44",
  "duration_minutes": 30,
  "monitoring_active": true
}
```

## 🧪 Testing

### Test Script
Run the included test script to verify functionality:

```bash
python test_integrated_monitoring.py
```

This script will:
1. Check monitoring status
2. Get current window
3. Start monitoring
4. Monitor for 10 seconds
5. Stop monitoring
6. Verify final status

### Manual Testing
```bash
# 1. Start the server
python main.py

# 2. In another terminal, test the endpoints
curl http://localhost:8000/monitoring/status
curl -X POST "http://localhost:8000/monitoring/start/cheerful_soul_44?duration_minutes=5"
curl http://localhost:8000/monitoring/current-window
curl -X POST http://localhost:8000/monitoring/stop
```

## 🔄 Simultaneous Monitoring (Legacy)

If you prefer to run monitoring scripts separately:

### Terminal 1: Start Main Server
```bash
python main.py
```

### Terminal 2: Run Window Monitor
```bash
python window_monitor.py
```

### Terminal 3: Run Activity Monitor (Testing)
```bash
python activity_monitor.py
```

## 🏗️ Architecture

### Integrated Monitoring
```
┌─────────────────────────────────────┐
│           main.py                   │
│  ┌─────────────────────────────┐    │
│  │    FastAPI Server           │    │
│  │  - API Endpoints            │    │
│  │  - WebSocket                │    │
│  │  - BERT Classification      │    │
│  └─────────────────────────────┘    │
│  ┌─────────────────────────────┐    │
│  │  IntegratedWindowMonitor    │    │
│  │  - Window Monitoring        │    │
│  │  - Activity Logging         │    │
│  │  - Notification Triggering  │    │
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘
```

### Simultaneous Monitoring
```
┌─────────────────┐    ┌─────────────────┐
│   main.py       │    │ window_monitor.py│
│  (API Server)   │◄──►│ (Monitoring)    │
└─────────────────┘    └─────────────────┘
        │                       │
        ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│   MongoDB       │    │   Windows API   │
│  (Database)     │    │  (System Calls) │
└─────────────────┘    └─────────────────┘
```

## ⚙️ Configuration

### Environment Variables
```bash
# Required
MONGODB_URL=your_mongodb_connection_string

# Optional
RENDER=true  # For deployment environment
```

### Monitoring Settings
The monitoring behavior can be adjusted in the `IntegratedWindowMonitor` class:

```python
self.check_interval = 2  # Check every 2 seconds
self.distraction_repeat_interval = 2  # Repeat notifications every 2 seconds
```

## 🚨 Troubleshooting

### Common Issues

#### 1. "Windows monitoring not available"
**Cause**: Missing Windows dependencies
**Solution**: Install `pywin32` and `psutil`
```bash
pip install pywin32 psutil
```

#### 2. "Window monitor not initialized"
**Cause**: Server startup issue
**Solution**: Check server logs and restart
```bash
python main.py
```

#### 3. "Monitoring already active"
**Cause**: Monitoring already running
**Solution**: Stop current monitoring first
```bash
curl -X POST http://localhost:8000/monitoring/stop
```

#### 4. Permission Errors
**Cause**: Windows security restrictions
**Solution**: Run as administrator or check Windows security settings

### Debug Endpoints
Use these endpoints to troubleshoot:

```bash
# Check MongoDB status
curl http://localhost:8000/debug/mongodb-status

# Check WebSocket status
curl http://localhost:8000/debug/websocket-status

# Check user data
curl http://localhost:8000/debug/user-data/cheerful_soul_44
```

## 📊 Monitoring Features

### What Gets Monitored
- **Active Window Title**: Current application and window
- **Process Information**: Application name and details
- **Window Changes**: When you switch between applications
- **Distraction Detection**: BERT-based content classification

### What Gets Logged
- **Activity Logs**: All window activity with timestamps
- **Classifications**: Productive vs. distracting content
- **Sentiment Analysis**: Positive/negative content analysis
- **Notifications**: Real-time alerts for distractions

### Real-time Features
- **WebSocket Notifications**: Instant alerts to frontend
- **OS Notifications**: System-level notification cards
- **Custom Audio**: Personalized notification sounds
- **Throttling**: Smart notification frequency control

## 🎯 Best Practices

### For Development
1. Use integrated monitoring for simplicity
2. Test with short durations (5-10 minutes)
3. Monitor server logs for debugging
4. Use the test script for verification

### For Production
1. Ensure all dependencies are installed
2. Monitor server resources
3. Set appropriate monitoring durations
4. Configure proper error handling

### For Users
1. Start monitoring when beginning work
2. Stop monitoring when taking breaks
3. Check notification settings
4. Upload custom audio for personalization

## 🔗 Related Files

- `main.py` - Main server with integrated monitoring
- `window_monitor.py` - Standalone window monitoring script
- `activity_monitor.py` - Activity simulation script
- `test_integrated_monitoring.py` - Testing script
- `requirements.txt` - Dependencies including monitoring libraries

## 📝 Notes

- **Platform Support**: Integrated monitoring works best on Windows
- **Performance**: Monitoring runs in background with minimal impact
- **Security**: Only monitors active windows, no keystroke logging
- **Privacy**: All data stays local unless explicitly sent to server
- **Compatibility**: Works with existing FocusGuard features
