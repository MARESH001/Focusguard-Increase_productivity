# Cross-Platform Window Monitoring System

## Overview

The FocusGuard application now includes a **cross-platform window monitoring system** that works on both **Windows** and **Linux** systems. This system can detect the currently active window, classify it as productive or distracting, and send real-time notifications when users switch to distracting content.

## Features

✅ **Cross-Platform Support**: Works on Windows and Linux  
✅ **Real-Time Monitoring**: Detects window changes every 2 seconds  
✅ **AI-Powered Classification**: Uses BERT models to classify content  
✅ **Smart Notifications**: Sends notifications only for distractions  
✅ **Session Integration**: Works with existing FocusGuard sessions  
✅ **Fallback Support**: Graceful degradation when tools aren't available  

## System Requirements

### Windows
- Python 3.7+
- `pywin32` library (automatically installed with requirements.txt)
- Windows 10/11 (tested)

### Linux
- Python 3.7+
- `xdotool` or `wmctrl` (installed automatically on Render)
- X11 display server
- Any modern Linux distribution

## How It Works

### 1. Window Detection
The system uses platform-specific methods to detect the active window:

**Windows:**
- Uses `win32gui` and `win32process` libraries
- Gets foreground window handle and title
- Extracts process information

**Linux:**
- Primary: Uses `xdotool` for window detection
- Fallback: Uses `wmctrl` for window management
- Final fallback: System information and environment variables

### 2. Content Classification
Once a window is detected, the system:

1. **Extracts window title** (e.g., "chrome - YouTube")
2. **Classifies content** using BERT AI models
3. **Determines if it's distracting** (entertainment, social media, gaming)
4. **Sends notifications** if classified as distracting

### 3. Notification System
- **Real-time notifications** via WebSocket
- **Smart throttling** to avoid spam
- **Custom audio support** for notifications
- **Distraction counting** and tracking

## API Endpoints

The system adds several new endpoints to the FocusGuard API:

### 1. Window Monitor Status
```http
GET /window-monitor/status
```
Returns the status of the window monitoring system.

### 2. Get Current Window
```http
GET /window-monitor/current-window
```
Returns information about the currently active window.

### 3. Start Monitoring
```http
POST /window-monitor/start-monitoring/{username}
```
Starts monitoring for a specific user with a session ID.

### 4. Check Window
```http
POST /window-monitor/check-window/{username}
```
Checks the current window and logs activity if needed.

### 5. System Information
```http
GET /window-monitor/system-info
```
Returns detailed system information for debugging.

## Usage

### 1. Standalone Monitoring Script

Run the cross-platform monitor directly:

```bash
# Test the system
python test_cross_platform_monitor.py

# Start monitoring
python cross_platform_monitor.py
```

### 2. API Integration

Use the API endpoints from your frontend or other applications:

```javascript
// Check if window monitoring is available
const status = await fetch('/window-monitor/status');
const statusData = await status.json();

// Get current window
const window = await fetch('/window-monitor/current-window');
const windowData = await window.json();

// Start monitoring for a user
const monitoring = await fetch('/window-monitor/start-monitoring/username', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ session_id: 'your-session-id' })
});
```

### 3. Frontend Integration

The frontend can periodically check for window changes:

```javascript
// Check window every 2 seconds
setInterval(async () => {
  const response = await fetch('/window-monitor/check-window/username', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: 'your-session-id' })
  });
  
  const result = await response.json();
  if (result.window_changed) {
    console.log('Window changed:', result.current_window.title);
    if (result.notification_sent) {
      console.log('Distraction notification sent!');
    }
  }
}, 2000);
```

## Deployment

### Render (Linux)
The system is automatically configured for Render deployment:

1. **System dependencies** are installed in `render.yaml`
2. **Linux tools** (`xdotool`, `wmctrl`) are available
3. **Cross-platform code** handles Linux environment
4. **Fallback mechanisms** ensure graceful operation

### Local Development

#### Windows
```bash
# Install dependencies
pip install -r requirements.txt

# Test the system
python test_cross_platform_monitor.py

# Start monitoring
python cross_platform_monitor.py
```

#### Linux
```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install xdotool wmctrl x11-utils

# Install Python dependencies
pip install -r requirements.txt

# Test the system
python test_cross_platform_monitor.py

# Start monitoring
python cross_platform_monitor.py
```

## Configuration

### Environment Variables
- `MONGODB_URL`: MongoDB connection string
- `DISPLAY`: X11 display (Linux only)
- `USER`: Current username (fallback)

### Monitoring Settings
- **Check interval**: 2 seconds (configurable)
- **Notification throttle**: 2 seconds between notifications
- **Session timeout**: 24 hours
- **Distraction tracking**: Per-session basis

## Troubleshooting

### Common Issues

#### 1. "Window monitoring not available"
**Solution**: Check if required tools are installed:
- Windows: `pip install pywin32`
- Linux: `sudo apt-get install xdotool wmctrl`

#### 2. "No active window found"
**Solution**: 
- Ensure you have an active window
- Check display server (Linux)
- Verify permissions

#### 3. "API connection failed"
**Solution**:
- Ensure FocusGuard backend is running
- Check API URL configuration
- Verify network connectivity

#### 4. "Linux tools not found"
**Solution**:
- Install missing tools: `sudo apt-get install xdotool wmctrl`
- Check PATH environment variable
- Verify X11 display server

### Debug Mode

Enable debug logging by setting environment variables:

```bash
export FOCUSGUARD_DEBUG=1
export WINDOW_MONITOR_DEBUG=1
```

### Testing

Run the comprehensive test suite:

```bash
# Test all components
python test_cross_platform_monitor.py

# Test specific platform
python -c "from cross_platform_monitor import CrossPlatformMonitor; print(CrossPlatformMonitor().get_active_window_title())"
```

## Security Considerations

1. **Window titles** may contain sensitive information
2. **Process information** is logged for classification
3. **User consent** should be obtained before monitoring
4. **Data privacy** - window titles are stored in MongoDB
5. **Access control** - monitoring requires valid session

## Performance

- **Memory usage**: ~50MB additional
- **CPU usage**: Minimal (2-second intervals)
- **Network**: Only when window changes detected
- **Storage**: Activity logs in MongoDB

## Future Enhancements

- [ ] macOS support
- [ ] Browser tab monitoring
- [ ] Application usage analytics
- [ ] Custom classification rules
- [ ] Privacy-preserving monitoring
- [ ] Real-time dashboard integration

## Support

For issues or questions:
1. Check the troubleshooting section
2. Run the test script
3. Check system requirements
4. Review API documentation
5. Check FocusGuard logs

---

**Note**: This system is designed to help users stay focused and productive. Always respect user privacy and obtain consent before monitoring activity.
