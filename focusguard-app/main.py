from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import motor.motor_asyncio
from bson import ObjectId
from textblob import TextBlob
import re
import json
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import uuid
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB configuration
MONGODB_URL = os.getenv("MONGODB_URL")

app = FastAPI(title="FocusGuard API", version="1.0.0")

# CORS middleware
origins = [
    "https://thefocusguard.netlify.app",
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
if not MONGODB_URL:
    print("❌ MONGODB_URL environment variable is not set")
    print("Please create a .env file with: MONGODB_URL=your_mongodb_connection_string")
    client = None
    db = None
else:
    try:
        client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
        db = client.focusguard
        print("✅ MongoDB connected successfully")
    except Exception as e:
        print(f"⚠️ MongoDB connection failed: {e}")
        print("Please check your MONGODB_URL in the .env file")
        client = None
        db = None

# Collections
users_collection = db.users
sessions_collection = db.focus_sessions
plans_collection = db.daily_plans
activity_collection = db.activity_logs
notifications_collection = db.notifications
progress_collection = db.progress_tracking

# WebSocket connections for real-time notifications
active_connections: Dict[str, WebSocket] = {}

# Scheduler for reminders
scheduler = AsyncIOScheduler()

# Enhanced notification tracking system
user_distraction_tracking: Dict[str, Dict[str, Any]] = {}
# Structure: {username: {"count": int, "session_id": str, "last_reset": datetime}}

@app.on_event("startup")
async def startup_event():
    """Initialize scheduler on startup"""
    try:
        scheduler.start()
        print("✅ Scheduler started successfully")
    except Exception as e:
        print(f"⚠️ Scheduler start failed: {e}")

class SmartContentClassifier:
    def __init__(self):
        self.entertainment_keywords = {
            'youtube', 'netflix', 'spotify', 'instagram', 'facebook', 'twitter', 'tiktok',
            'reddit', 'twitch', 'discord', 'snapchat', 'pinterest', 'tumblr', 'vine',
            'game', 'gaming', 'play', 'movie', 'music', 'video', 'stream', 'live',
            'entertainment', 'fun', 'funny', 'meme', 'joke', 'comedy', 'drama',
            'reality', 'show', 'series', 'episode', 'season', 'trailer', 'preview'
        }
        
        self.educational_keywords = {
            'focusguard','course', 'tutorial', 'learn', 'study', 'education', 'academic', 'university',
            'college', 'school', 'lecture', 'lesson', 'assignment', 'homework', 'exam',
            'test', 'quiz', 'research', 'paper', 'thesis', 'dissertation', 'documentation',
            'guide', 'manual', 'book', 'textbook', 'reference', 'library', 'scholar',
            'professor', 'teacher', 'instructor', 'student', 'learning', 'knowledge'
        }
        
        self.productive_keywords = {
            'work', 'project', 'task', 'job', 'business', 'office', 'meeting', 'presentation',
            'report', 'analysis', 'data', 'code', 'programming', 'development', 'design',
            'planning', 'strategy', 'management', 'admin', 'dashboard', 'tool', 'software',
            'application', 'system', 'database', 'server', 'network', 'security',
            'finance', 'accounting', 'marketing', 'sales', 'customer', 'client',
            'product', 'service', 'quality', 'efficiency', 'productivity', 'performance'
        }
        
    def classify_with_patterns(self, title):
        """Pattern-based classification using regex and keyword matching"""
        title_lower = title.lower()
        
        # Entertainment patterns
        entertainment_patterns = [
            r'\b(youtube|netflix|spotify|instagram|facebook|twitter|tiktok|reddit|twitch|discord)\b',
            r'\b(game|gaming|play|movie|music|video|stream|live)\b',
            r'\b(entertainment|fun|funny|meme|joke|comedy|drama)\b',
            r'\b(reality|show|series|episode|season|trailer|preview)\b'
        ]
        
        # Educational patterns
        educational_patterns = [
            r'\b(course|tutorial|learn|study|education|academic|university|college|school)\b',
            r'\b(lecture|lesson|assignment|homework|exam|test|quiz|research|paper)\b',
            r'\b(thesis|dissertation|documentation|guide|manual|book|textbook)\b',
            r'\b(reference|library|scholar|professor|teacher|instructor|student)\b'
        ]
        
        # Productive patterns
        productive_patterns = [
            r'\b(work|project|task|job|business|office|meeting|presentation|report)\b',
            r'\b(analysis|data|code|programming|development|design|planning|strategy)\b',
            r'\b(management|admin|dashboard|tool|software|application|system)\b',
            r'\b(database|server|network|security|finance|accounting|marketing)\b',
            r'\b(sales|customer|client|product|service|quality|efficiency)\b'
        ]
        
        # Count matches
        entertainment_matches = sum(len(re.findall(pattern, title_lower)) for pattern in entertainment_patterns)
        educational_matches = sum(len(re.findall(pattern, title_lower)) for pattern in educational_patterns)
        productive_matches = sum(len(re.findall(pattern, title_lower)) for pattern in productive_patterns)
        
        # Determine classification
        if entertainment_matches > educational_matches and entertainment_matches > productive_matches:
            return "entertainment", min(0.9, 0.5 + entertainment_matches * 0.1)
        elif educational_matches > entertainment_matches and educational_matches > productive_matches:
            return "educational", min(0.9, 0.5 + educational_matches * 0.1)
        elif productive_matches > entertainment_matches and productive_matches > educational_matches:
            return "productive", min(0.9, 0.5 + productive_matches * 0.1)
        else:
            return "neutral", 0.5
    
    def classify_with_linguistic_features(self, title):
        """Classification using linguistic features"""
        try:
            blob = TextBlob(title)
            
            # Analyze sentiment
            sentiment = blob.sentiment.polarity
            
            # Analyze subjectivity
            subjectivity = blob.sentiment.subjectivity
            
            # Entertainment tends to be more subjective and positive
            if subjectivity > 0.6 and sentiment > 0.2:
                return "entertainment", 0.7
            # Educational content tends to be more objective
            elif subjectivity < 0.4:
                return "educational", 0.6
            # Productive content is often neutral to slightly positive
            elif -0.2 <= sentiment <= 0.3:
                return "productive", 0.8
            else:
                return "neutral", 0.5
                
        except Exception as e:
            print(f"Linguistic classification error: {e}")
            return self.classify_with_patterns(title)
    
    def ensemble_classify(self, title):
        """Ensemble classification combining multiple methods"""
        if not title or len(title.strip()) < 3:
            return "neutral", 0.5, False
        
        # Get classifications from different methods
        pattern_class, pattern_conf = self.classify_with_patterns(title)
        linguistic_class, linguistic_conf = self.classify_with_linguistic_features(title)
        
        # Simple voting system
        classifications = [pattern_class, linguistic_class]
        confidences = [pattern_conf, linguistic_conf]
        
        # Count votes
        vote_counts = {}
        for class_name in classifications:
            vote_counts[class_name] = vote_counts.get(class_name, 0) + 1
        
        # Get the most voted classification
        most_voted = max(vote_counts, key=vote_counts.get)
        
        # Calculate average confidence for the winning classification
        winning_confidences = [conf for class_name, conf in zip(classifications, confidences) if class_name == most_voted]
        avg_confidence = sum(winning_confidences) / len(winning_confidences) if winning_confidences else 0.5
        
        # Determine if it's a distraction
        is_distraction = most_voted in ["entertainment"]
        
        return most_voted, avg_confidence, is_distraction

# Initialize classifier
classifier = SmartContentClassifier()

# Pydantic models
class UserCreate(BaseModel):
    username: str

class UserResponse(BaseModel):
    id: str
    username: str
    created_at: datetime
    last_active: datetime

class FocusSessionCreate(BaseModel):
    task_description: str
    keywords: List[str]
    duration_minutes: int

class FocusSessionUpdate(BaseModel):
    completed: Optional[bool] = None
    distraction_count: Optional[int] = None
    productivity_score: Optional[float] = None
    end_time: Optional[datetime] = None

class FocusSessionResponse(BaseModel):
    id: str
    username: str
    task_description: str
    keywords: List[str]
    duration_minutes: int
    start_time: datetime
    end_time: Optional[datetime]
    completed: bool
    distraction_count: int
    productivity_score: float

class ActivityLogCreate(BaseModel):
    window_title: str

class ActivityLogResponse(BaseModel):
    id: str
    username: str
    session_id: str
    window_title: str
    classification: str
    confidence: float
    is_distraction: bool
    timestamp: datetime

# FIXED: Updated NotificationResponse model with required sound_type field
class NotificationResponse(BaseModel):
    id: str
    username: str
    message: str
    notification_type: str
    sound_type: str  # REQUIRED field that was missing
    custom_audio_url: Optional[str] = None
    created_at: datetime
    read: bool  # Added read status

# Enhanced notification system - FIXED logic
async def send_distraction_notification(username: str, window_title: str, session_id: str):
    """Send distraction notification with proper sound system"""
    
    # Initialize or get user tracking
    if username not in user_distraction_tracking:
        user_distraction_tracking[username] = {
            "count": 0,
            "session_id": session_id,
            "last_reset": datetime.utcnow()
        }
    
    # Reset counter if new session or after 1 hour
    current_tracking = user_distraction_tracking[username]
    time_since_reset = datetime.utcnow() - current_tracking["last_reset"]
    
    if (current_tracking["session_id"] != session_id or 
        time_since_reset > timedelta(hours=1)):
        current_tracking["count"] = 0
        current_tracking["session_id"] = session_id
        current_tracking["last_reset"] = datetime.utcnow()
    
    # Increment distraction count
    current_tracking["count"] += 1
    count = current_tracking["count"]
    
    # FIXED: Proper sound type logic as requested
    if count <= 2:
        sound_type = "default"
        message = f"⚠️ Distracting activity detected: {window_title}"
    else:
        sound_type = "custom"  # Will use custom audio if available
        message = f"🚨 Multiple distractions detected! Stay focused on: {window_title}"
    
    # Create notification data with ALL required fields
    notification_data = {
        "_id": ObjectId(),  # Generate ObjectId for proper insertion
        "id": str(uuid.uuid4()),
        "username": username,
        "message": message,
        "notification_type": "distraction",
        "sound_type": sound_type,  # REQUIRED field
        "custom_audio_url": None,  # You can add custom audio URL logic here
        "created_at": datetime.utcnow(),
        "read": False,
        "session_id": session_id,
        "window_title": window_title,
        "distraction_count": count
    }
    
    # Store notification in database
    try:
        result = await notifications_collection.insert_one(notification_data)
        notification_data["id"] = str(notification_data["_id"])
        print(f"✅ Notification stored in DB for {username}")
    except Exception as e:
        print(f"❌ Database error storing notification: {e}")
        return None
    
    # Send via WebSocket if connected
    if username in active_connections:
        try:
            websocket_message = {
                "type": "distraction_notification",
                "data": {
                    "id": notification_data["id"],
                    "message": notification_data["message"],
                    "notification_type": notification_data["notification_type"],
                    "sound_type": notification_data["sound_type"],
                    "custom_audio_url": notification_data["custom_audio_url"],
                    "created_at": notification_data["created_at"].isoformat(),
                    "window_title": window_title,
                    "distraction_count": count,
                    "read": False
                }
            }
            
            await active_connections[username].send_text(json.dumps(websocket_message, default=str))
            print(f"✅ WebSocket notification sent to {username}: {message}")
        except Exception as e:
            print(f"❌ Error sending WebSocket notification: {e}")
            # Remove broken connection
            if username in active_connections:
                del active_connections[username]
    else:
        print(f"⚠️ No active WebSocket connection for {username}")
    
    return notification_data

# Helper functions
async def get_user_by_username(username: str):
    return await users_collection.find_one({"username": username})

async def create_user(username: str):
    user_data = {
        "username": username,
        "created_at": datetime.utcnow(),
        "last_active": datetime.utcnow()
    }
    result = await users_collection.insert_one(user_data)
    user_data["id"] = str(result.inserted_id)
    return user_data

@app.get("/")
async def root():
    return {"message": "FocusGuard API is running!"}

@app.post("/users/", response_model=UserResponse)
async def create_or_get_user(user: UserCreate):
    # Check if user exists
    existing_user = await get_user_by_username(user.username)
    if existing_user:
        # Update last_active
        await users_collection.update_one(
            {"username": user.username},
            {"$set": {"last_active": datetime.utcnow()}}
        )
        existing_user["id"] = str(existing_user["_id"])
        return existing_user
    
    # Create new user
    new_user = await create_user(user.username)
    return new_user

@app.post("/users/{username}/sessions/", response_model=FocusSessionResponse)
async def create_focus_session(username: str, session: FocusSessionCreate):
    # Get or create user
    user = await get_user_by_username(username)
    if not user:
        user = await create_user(username)
    
    session_data = {
        "user_id": str(user["_id"]),
        "username": username,
        "task_description": session.task_description,
        "keywords": session.keywords,
        "duration_minutes": session.duration_minutes,
        "start_time": datetime.utcnow(),
        "end_time": None,
        "completed": False,
        "distraction_count": 0,
        "productivity_score": 0.0,
        "created_at": datetime.utcnow()
    }
    
    result = await sessions_collection.insert_one(session_data)
    session_data["id"] = str(result.inserted_id)
    
    # Reset distraction tracking for new session
    if username in user_distraction_tracking:
        user_distraction_tracking[username]["count"] = 0
        user_distraction_tracking[username]["session_id"] = str(result.inserted_id)
        user_distraction_tracking[username]["last_reset"] = datetime.utcnow()
    
    return session_data

@app.get("/users/{username}/sessions/", response_model=List[FocusSessionResponse])
async def get_focus_sessions(username: str):
    user = await get_user_by_username(username)
    if not user:
        user = await create_user(username)
    
    sessions = await sessions_collection.find({"username": username}).sort("created_at", -1).to_list(length=100)
    for session in sessions:
        session["id"] = str(session["_id"])
    return sessions

# FIXED: Add the missing endpoint that frontend is calling
@app.post("/sessions/{session_id}/activity/enhanced", response_model=ActivityLogResponse)
async def monitor_activity_enhanced(session_id: str, activity_log: ActivityLogCreate):
    """Enhanced activity monitoring endpoint that frontend is calling"""
    return await monitor_activity_realtime(session_id, activity_log)

# MAIN ENHANCEMENT: Real-time activity monitoring endpoint
@app.post("/sessions/{session_id}/monitor-activity", response_model=ActivityLogResponse)
async def monitor_activity_realtime(session_id: str, activity_log: ActivityLogCreate):
    """Monitor user activity in real-time and send instant notifications for distractions"""
    
    # Validate ObjectId
    if not ObjectId.is_valid(session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID")
    
    # Find session
    session = await sessions_collection.find_one({"_id": ObjectId(session_id)})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    username = session["username"]
    
    # Classify the activity using AI
    classification, confidence, is_distraction = classifier.ensemble_classify(activity_log.window_title)
    
    # Create activity log entry
    activity_data = {
        "user_id": session["user_id"],
        "username": username,
        "session_id": session_id,
        "window_title": activity_log.window_title,
        "classification": classification,
        "confidence": confidence,
        "is_distraction": is_distraction,
        "timestamp": datetime.utcnow(),
        "created_at": datetime.utcnow()
    }
    
    result = await activity_collection.insert_one(activity_data)
    activity_data["id"] = str(result.inserted_id)
    
    # If it's a distraction, send immediate notification
    if is_distraction:
        print(f"🚨 DISTRACTION DETECTED for {username}: {activity_log.window_title}")
        
        # Send distraction notification
        notification = await send_distraction_notification(username, activity_log.window_title, session_id)
        
        if notification:
            # Update session distraction count
            await sessions_collection.update_one(
                {"_id": ObjectId(session_id)},
                {"$inc": {"distraction_count": 1}}
            )
            
            print(f"✅ Notification sent and session updated for {username}")
        else:
            print(f"❌ Failed to send notification for {username}")
    
    return activity_data

# FIXED: Add missing PUT endpoint for sessions
@app.put("/sessions/{session_id}", response_model=dict)
async def update_session(session_id: str, session_update: FocusSessionUpdate):
    """Update session details"""
    if not ObjectId.is_valid(session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID")
    
    session = await sessions_collection.find_one({"_id": ObjectId(session_id)})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    update_data = {}
    if session_update.completed is not None:
        update_data["completed"] = session_update.completed
    if session_update.distraction_count is not None:
        update_data["distraction_count"] = session_update.distraction_count
    if session_update.productivity_score is not None:
        update_data["productivity_score"] = session_update.productivity_score
    if session_update.end_time is not None:
        update_data["end_time"] = session_update.end_time
    
    if update_data:
        await sessions_collection.update_one(
            {"_id": ObjectId(session_id)},
            {"$set": update_data}
        )
    
    return {"message": "Session updated successfully"}

# FIXED: Add missing time_spent endpoint
@app.get("/users/{username}/activity/time_spent")
async def get_time_spent(username: str, start_date: str, end_date: str):
    """Get time spent data for user"""
    user = await get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        # Parse dates
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # Get activity logs in date range
        activities = await activity_collection.find({
            "username": username,
            "timestamp": {
                "$gte": start_dt,
                "$lte": end_dt
            }
        }).to_list(length=1000)
        
        # Calculate time spent by category
        time_data = {
            "productive": 0,
            "educational": 0,
            "entertainment": 0,
            "neutral": 0
        }
        
        for activity in activities:
            classification = activity.get("classification", "neutral")
            if classification in time_data:
                time_data[classification] += 1  # Simple count for now
        
        return time_data
        
    except Exception as e:
        print(f"Error getting time spent: {e}")
        return {
            "productive": 0,
            "educational": 0,
            "entertainment": 0,
            "neutral": 0
        }

# WebSocket endpoint for real-time notifications
@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await websocket.accept()
    active_connections[username] = websocket
    print(f"✅ WebSocket connected for user: {username}")
    
    try:
        while True:
            # Keep connection alive and listen for any messages
            data = await websocket.receive_text()
            
            # Handle incoming messages
            try:
                message = json.loads(data)
                if message.get("type") == "heartbeat":
                    await websocket.send_text(json.dumps({"type": "heartbeat_response", "status": "ok"}))
                elif message.get("type") == "test_notification":
                    # Test notification for debugging
                    await websocket.send_text(json.dumps({
                        "type": "distraction_notification",
                        "data": {
                            "id": str(uuid.uuid4()),
                            "message": "Test notification",
                            "notification_type": "distraction",
                            "sound_type": "default",
                            "custom_audio_url": None,
                            "created_at": datetime.utcnow().isoformat(),
                            "window_title": "Test",
                            "distraction_count": 1,
                            "read": False
                        }
                    }))
            except json.JSONDecodeError:
                pass  # Ignore malformed messages
                
    except WebSocketDisconnect:
        if username in active_connections:
            del active_connections[username]
            print(f"❌ WebSocket disconnected for user: {username}")
    except Exception as e:
        print(f"⚠️ WebSocket error for {username}: {e}")
        if username in active_connections:
            del active_connections[username]

@app.get("/users/{username}/notifications/", response_model=List[NotificationResponse])
async def get_notifications(username: str):
    """Get user's notification history"""
    user = await get_user_by_username(username)
    if not user:
        user = await create_user(username)
    
    # Get user's notifications (last 50)
    notifications = await notifications_collection.find({
        "username": username
    }).sort("created_at", -1).to_list(length=50)
    
    # FIXED: Ensure all required fields are present
    for notification in notifications:
        notification["id"] = str(notification["_id"])
        # Add missing fields if they don't exist
        if "sound_type" not in notification:
            notification["sound_type"] = "default"
        if "read" not in notification:
            notification["read"] = False
    
    return notifications

@app.get("/users/{username}/active-session")
async def get_active_session(username: str):
    """Get user's currently active session"""
    user = await get_user_by_username(username)
    if not user:
        user = await create_user(username)
    
    # Find active session (not completed and within last 24 hours)
    twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
    
    active_session = await sessions_collection.find_one({
        "username": username,
        "completed": False,
        "start_time": {"$gte": twenty_four_hours_ago}
    })
    
    if active_session:
        active_session["id"] = str(active_session["_id"])
        return {"active_session": active_session}
    
    return {"active_session": None}

@app.put("/sessions/{session_id}/complete")
async def complete_session(session_id: str):
    """Mark a session as completed"""
    if not ObjectId.is_valid(session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID")
    
    session = await sessions_collection.find_one({"_id": ObjectId(session_id)})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Update session as completed
    await sessions_collection.update_one(
        {"_id": ObjectId(session_id)},
        {
            "$set": {
                "completed": True,
                "end_time": datetime.utcnow()
            }
        }
    )
    
    # Reset distraction tracking for the user
    username = session["username"]
    if username in user_distraction_tracking:
        user_distraction_tracking[username]["count"] = 0
        user_distraction_tracking[username]["last_reset"] = datetime.utcnow()
    
    return {"message": "Session completed successfully"}

@app.get("/users/{username}/distraction-stats")
async def get_distraction_stats(username: str):
    """Get current distraction statistics for the user"""
    user = await get_user_by_username(username)
    if not user:
        user = await create_user(username)
    
    current_stats = user_distraction_tracking.get(username, {
        "count": 0,
        "session_id": None,
        "last_reset": datetime.utcnow()
    })
    
    return {
        "username": username,
        "current_distraction_count": current_stats["count"],
        "current_session_id": current_stats.get("session_id"),
        "last_reset": current_stats["last_reset"],
        "next_sound_type": "default" if current_stats["count"] < 2 else "custom"
    }

# DEBUGGING: Add test endpoint
@app.post("/test-notification/{username}")
async def test_notification(username: str):
    """Test notification system"""
    if username in active_connections:
        try:
            test_notification = {
                "type": "distraction_notification",
                "data": {
                    "id": str(uuid.uuid4()),
                    "message": "🧪 Test notification - your notification system is working!",
                    "notification_type": "distraction",
                    "sound_type": "default",
                    "custom_audio_url": None,
                    "created_at": datetime.utcnow().isoformat(),
                    "window_title": "Test Window",
                    "distraction_count": 1,
                    "read": False
                }
            }
            
            await active_connections[username].send_text(json.dumps(test_notification))
            return {"message": f"Test notification sent to {username}"}
        except Exception as e:
            return {"error": f"Failed to send test notification: {e}"}
    else:
        return {"error": f"No active WebSocket connection for {username}"}

if __name__ == "__main__":
    import uvicorn
    if db is None:
        print("❌ Cannot start server without MongoDB connection")
        exit(1)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
