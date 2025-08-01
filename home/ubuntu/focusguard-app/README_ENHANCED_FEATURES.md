# FocusGuard Enhanced Features

This document describes the new enhanced features added to FocusGuard, including activity monitoring, notifications, progress tracking, and enhanced daily planning.

## 🚀 New Features Overview

### 1. Activity Monitoring & Notifications
- **Real-time Activity Checking**: Monitors user activity every 2 seconds
- **Smart Notification System**: 
  - First 2 distraction notifications: Default sound
  - 3rd distraction notification: Custom audio (if set) or default
- **WebSocket Integration**: Real-time notifications via WebSocket connections
- **Audio Notifications**: Custom audio support with fallback to default sounds

### 2. Progress Tracking with Streaks
- **Focus Streak System**: Tracks consecutive days of focus activity
- **Progress Graphs**: Visual representation of focus time and productivity
- **Streak Breaks**: Graph breaks when user skips using the app
- **Streak Analytics**: Current streak, longest streak, and streak history

### 3. Enhanced Daily Planning
- **Task-based Planning**: Replace text descriptions with checkboxes
- **Reminder System**: Set time-based reminders for individual tasks
- **Custom Audio URLs**: Set custom notification sounds for distraction alerts
- **Task Management**: Add, edit, remove, and mark tasks as complete

## 📋 API Endpoints

### New Backend Endpoints

#### WebSocket
- `GET /ws/{username}` - WebSocket connection for real-time notifications

#### Enhanced Daily Plans
- `POST /users/{username}/plans/enhanced/` - Create enhanced daily plan with tasks
- `GET /users/{username}/plans/enhanced/{date}` - Get enhanced daily plan
- `PUT /users/{username}/plans/enhanced/{date}` - Update enhanced daily plan

#### Notifications
- `GET /users/{username}/notifications/` - Get user notifications
- `PUT /notifications/{notification_id}/read` - Mark notification as read

#### Progress Tracking
- `GET /users/{username}/progress/` - Get user progress data with streaks
- `GET /users/{username}/stats/weekly` - Get weekly statistics

#### Enhanced Activity Logging
- `POST /sessions/{session_id}/activity/enhanced` - Log activity with notifications

## 🎯 Feature Details

### Activity Monitoring System

The activity monitoring system works as follows:

1. **Activity Detection**: Every 2 seconds, the system checks the current window/application
2. **Classification**: Uses AI to classify activities as productive, educational, or entertainment
3. **Notification Logic**:
   - Entertainment activities trigger distraction notifications
   - First 2 notifications: Default notification sound
   - 3rd notification: Custom audio (if set in daily plan) or default sound
   - Counter resets after 3rd notification

```python
# Example notification flow
if classification == "entertainment":
    notification_count += 1
    if count <= 2:
        send_notification(message, "distraction")  # Default sound
    elif count == 3:
        custom_audio = get_user_custom_audio()
        send_notification(message, "distraction", custom_audio)
        notification_count = 0  # Reset counter
```

### Progress Tracking & Streaks

The progress tracking system includes:

1. **Daily Progress**: Tracks focus time, distractions, and productivity per day
2. **Streak Calculation**: 
   - Current streak: Consecutive days with focus activity
   - Longest streak: Best streak achieved
   - Streak breaks: Days without any focus sessions
3. **Visual Indicators**: 
   - Graph breaks when no focus activity is detected
   - Streak status badges and progress indicators

### Enhanced Daily Planning

The new daily planning system features:

1. **Task Management**:
   - Individual task items with checkboxes
   - Add/remove tasks dynamically
   - Mark tasks as complete/incomplete

2. **Reminder System**:
   - Set time-based reminders for individual tasks
   - Reminders trigger notifications at specified times
   - Automatic scheduling using APScheduler

3. **Custom Audio**:
   - Set custom notification sound URLs
   - Used for 3rd distraction notification
   - Fallback to default sound if custom audio fails

## 🛠️ Installation & Setup

### Backend Dependencies

Add these to your `requirements.txt`:

```txt
websockets==12.0
apscheduler==3.10.4
```

### Database Collections

The system uses these MongoDB collections:

- `users` - User information
- `focus_sessions` - Focus session data
- `daily_plans` - Enhanced daily plans with tasks
- `activity_logs` - Activity monitoring data
- `notifications` - Notification history
- `progress_tracking` - Progress and streak data

### Frontend Components

New React components:

- `NotificationCenter.jsx` - Real-time notification system
- Enhanced `DailyPlan.jsx` - Task-based planning
- Enhanced `Statistics.jsx` - Progress tracking and streaks

## 🧪 Testing

### Activity Monitor Script

Use the provided `activity_monitor.py` script to test the notification system:

```bash
cd focusguard-app
python activity_monitor.py
```

This script:
- Creates a focus session
- Simulates activity monitoring every 2 seconds
- Randomly generates productive/distracting activities
- Tests the notification system

### Manual Testing

1. **Start the backend**:
   ```bash
   cd focusguard-app
   python main.py
   ```

2. **Start the frontend**:
   ```bash
   cd focusguard-frontend
   npm run dev
   ```

3. **Test notifications**:
   - Create a daily plan with custom audio URL
   - Start a focus session
   - Run the activity monitor script
   - Check for notifications in the frontend

## 🔧 Configuration

### WebSocket Configuration

The WebSocket connection is automatically established when the NotificationCenter component loads. It will:

- Connect to `ws://localhost:8000/ws/{username}`
- Automatically reconnect if disconnected
- Handle real-time notifications

### Notification Settings

Users can:
- Mute/unmute notifications
- Set custom audio URLs for distraction alerts
- View notification history
- Mark notifications as read

### Reminder Scheduling

Task reminders are automatically scheduled using APScheduler:

- Cron-based scheduling for precise timing
- Automatic cleanup of old reminders
- Error handling for failed reminders

## 📊 Data Models

### Enhanced Daily Plan

```json
{
  "id": "string",
  "username": "string",
  "date": "YYYY-MM-DD",
  "tasks": [
    {
      "id": "string",
      "text": "string",
      "completed": boolean,
      "reminder_time": "HH:MM" // optional
    }
  ],
  "custom_audio_url": "string", // optional
  "completed": boolean,
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Progress Data

```json
{
  "username": "string",
  "current_streak": number,
  "longest_streak": number,
  "total_focus_time": number,
  "average_productivity": number,
  "progress_data": [
    {
      "date": "YYYY-MM-DD",
      "focus_time_minutes": number,
      "distraction_count": number,
      "productivity_score": number,
      "streak_days": number,
      "is_break": boolean
    }
  ]
}
```

### Notification

```json
{
  "id": "string",
  "username": "string",
  "message": "string",
  "notification_type": "distraction|reminder|streak",
  "custom_audio_url": "string", // optional
  "created_at": "datetime",
  "read": boolean
}
```

## 🎨 UI/UX Features

### Notification Center

- Real-time notification bell with unread count
- Mute/unmute functionality
- Connection status indicator
- Toast notifications for new alerts
- Notification history panel

### Enhanced Daily Plan

- Task-based interface with checkboxes
- Time picker for reminders
- Custom audio URL input
- Task completion tracking
- Visual progress indicators

### Progress Dashboard

- Streak status with visual indicators
- Progress graphs with break detection
- Productivity trends
- Streak history and records
- Motivational messaging

## 🔒 Security Considerations

- WebSocket connections are user-specific
- Notification data is scoped to individual users
- Custom audio URLs should be validated
- Reminder scheduling includes user isolation

## 🚀 Future Enhancements

Potential future features:

1. **Advanced Analytics**: More detailed productivity insights
2. **Goal Setting**: Long-term focus goals and milestones
3. **Team Features**: Collaborative focus sessions
4. **Mobile App**: Native mobile application
5. **Integration**: Calendar and task management integrations
6. **AI Insights**: Personalized productivity recommendations

## 📝 Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**:
   - Check if backend is running on port 8000
   - Verify CORS settings
   - Check browser console for errors

2. **Notifications Not Working**:
   - Ensure WebSocket connection is established
   - Check notification permissions in browser
   - Verify audio playback settings

3. **Reminders Not Triggering**:
   - Check APScheduler is running
   - Verify time format (HH:MM)
   - Check server logs for errors

4. **Progress Data Not Updating**:
   - Ensure activity logging is working
   - Check database connections
   - Verify progress calculation logic

### Debug Mode

Enable debug logging by setting environment variables:

```bash
export FOCUSGUARD_DEBUG=1
export FOCUSGUARD_LOG_LEVEL=DEBUG
```

## 📞 Support

For issues or questions about the enhanced features:

1. Check the troubleshooting section
2. Review the API documentation
3. Test with the provided activity monitor script
4. Check server logs for error messages

---

**Note**: These enhanced features require MongoDB to be running and the backend server to be started. Make sure all dependencies are installed and the database is properly configured. 