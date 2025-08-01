from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import motor.motor_asyncio
from bson import ObjectId
import spacy
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

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
    print("✅ Spacy model loaded")
except OSError:
    print("⚠️ Spacy model not found. Run: python -m spacy download en_core_web_sm")
    nlp = None

app = FastAPI(title="FocusGuard API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
        "https://your-app-name.netlify.app",  # Replace with your Netlify domain
        "https://*.netlify.app"  # Allow all Netlify subdomains
    ],
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

# Notification counter for each user
notification_counters: Dict[str, int] = {}

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
        
    def classify_with_ai(self, title):
        """Advanced classification using spaCy and TextBlob"""
        if not nlp:
            return self.classify_with_patterns(title)
        
        try:
            doc = nlp(title.lower())
            
            # Extract key phrases and entities
            entities = [ent.text.lower() for ent in doc.ents]
            tokens = [token.text.lower() for token in doc if not token.is_stop and token.is_alpha]
            
            # Combine all text elements
            all_text = ' '.join(tokens + entities)
            
            # Count keyword matches
            entertainment_score = sum(1 for keyword in self.entertainment_keywords if keyword in all_text)
            educational_score = sum(1 for keyword in self.educational_keywords if keyword in all_text)
            productive_score = sum(1 for keyword in self.productive_keywords if keyword in all_text)
            
            # Determine classification
            if entertainment_score > educational_score and entertainment_score > productive_score:
                return "entertainment", 0.8
            elif educational_score > entertainment_score and educational_score > productive_score:
                return "educational", 0.7
            elif productive_score > entertainment_score and productive_score > educational_score:
                return "productive", 0.9
            else:
                return "neutral", 0.5
                
        except Exception as e:
            print(f"AI classification error: {e}")
            return self.classify_with_patterns(title)
    
    def classify_with_similarity(self, title):
        """Classification using semantic similarity (placeholder)"""
        # This would use sentence transformers or similar
        # For now, fall back to pattern matching
        return self.classify_with_patterns(title)
    
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
            return "neutral", 0.5
        
        # Get classifications from different methods
        ai_class, ai_conf = self.classify_with_ai(title)
        pattern_class, pattern_conf = self.classify_with_patterns(title)
        linguistic_class, linguistic_conf = self.classify_with_linguistic_features(title)
        
        # Simple voting system
        classifications = [ai_class, pattern_class, linguistic_class]
        confidences = [ai_conf, pattern_conf, linguistic_conf]
        
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

class DailyPlanCreate(BaseModel):
    plan_text: str
    date: Optional[str] = None

class DailyPlanUpdate(BaseModel):
    plan_text: Optional[str] = None
    completed: Optional[bool] = None

class DailyPlanResponse(BaseModel):
    id: str
    username: str
    date: str
    plan_text: str
    completed: bool
    created_at: datetime
    updated_at: datetime

class ActivityLogCreate(BaseModel):
    session_id: str
    window_title: str
    classification: str
    confidence: float
    is_distraction: bool
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: int

class ActivityLogResponse(BaseModel):
    id: str
    username: str
    session_id: str
    window_title: str
    classification: str
    confidence: float
    is_distraction: bool
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: int

class DailyStats(BaseModel):
    date: str
    total_sessions: int
    completed_sessions: int
    total_focus_time: int
    average_productivity: float
    total_distractions: int

# New models for enhanced features
class TaskItem(BaseModel):
    id: str
    text: str
    completed: bool = False
    reminder_time: Optional[str] = None  # HH:MM format

class ReminderItem(BaseModel):
    id: str
    text: str
    time: str  # HH:MM format
    completed: bool = False

class DailyPlanEnhancedCreate(BaseModel):
    tasks: List[TaskItem]
    reminders: List[ReminderItem]
    date: Optional[str] = None

class DailyPlanEnhancedUpdate(BaseModel):
    tasks: Optional[List[TaskItem]] = None
    reminders: Optional[List[ReminderItem]] = None
    completed: Optional[bool] = None

class DailyPlanEnhancedResponse(BaseModel):
    id: str
    username: str
    date: str
    tasks: List[TaskItem]
    reminders: List[ReminderItem]
    completed: bool
    created_at: datetime
    updated_at: datetime

class NotificationCreate(BaseModel):
    message: str
    notification_type: str  # "distraction", "reminder", "streak"
    custom_audio_url: Optional[str] = None

class NotificationResponse(BaseModel):
    id: str
    username: str
    message: str
    notification_type: str
    custom_audio_url: Optional[str] = None
    created_at: datetime
    read: bool = False

class ProgressData(BaseModel):
    date: str
    focus_time_minutes: int
    distraction_count: int
    productivity_score: float
    streak_days: int
    is_break: bool = False

class ProgressResponse(BaseModel):
    username: str
    current_streak: int
    longest_streak: int
    total_focus_time: int
    average_productivity: float
    progress_data: List[ProgressData]

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

# New helper functions for enhanced features
async def send_notification(username: str, message: str, notification_type: str, custom_audio_url: Optional[str] = None):
    """Send notification to user via WebSocket"""
    notification_data = {
        "id": str(uuid.uuid4()),
        "username": username,
        "message": message,
        "notification_type": notification_type,
        "custom_audio_url": custom_audio_url,
        "created_at": datetime.utcnow(),
        "read": False
    }
    
    # Store notification in database
    await notifications_collection.insert_one(notification_data)
    
    # Send via WebSocket if connected
    if username in active_connections:
        try:
            await active_connections[username].send_text(json.dumps({
                "type": "notification",
                "data": notification_data
            }))
        except Exception as e:
            print(f"Error sending WebSocket notification: {e}")
    
    return notification_data

async def check_distraction_and_notify(username: str, window_title: str, classification: str):
    """Check if activity is distracting and send notification if needed"""
    if classification == "entertainment":
        # Increment notification counter
        notification_counters[username] = notification_counters.get(username, 0) + 1
        count = notification_counters[username]
        
        if count <= 2:
            # First 2 notifications with default sound
            await send_notification(
                username=username,
                message=f"⚠️ Distracting activity detected: {window_title}",
                notification_type="distraction"
            )
        elif count == 3:
            # Third notification with default sound
            await send_notification(
                username=username,
                message=f"🚨 Multiple distractions detected! Stay focused on: {window_title}",
                notification_type="distraction"
            )
            
            # Reset counter after third notification
            notification_counters[username] = 0

async def update_progress_tracking(username: str, focus_time: int, distraction_count: int, productivity_score: float):
    """Update user's progress tracking data"""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    # Get existing progress data
    existing_progress = await progress_collection.find_one({
        "username": username,
        "date": today
    })
    
    if existing_progress:
        # Update existing progress
        await progress_collection.update_one(
            {"username": username, "date": today},
            {
                "$set": {
                    "focus_time_minutes": existing_progress.get("focus_time_minutes", 0) + focus_time,
                    "distraction_count": existing_progress.get("distraction_count", 0) + distraction_count,
                    "productivity_score": (existing_progress.get("productivity_score", 0) + productivity_score) / 2,
                    "updated_at": datetime.utcnow()
                }
            }
        )
    else:
        # Create new progress entry
        await progress_collection.insert_one({
            "username": username,
            "date": today,
            "focus_time_minutes": focus_time,
            "distraction_count": distraction_count,
            "productivity_score": productivity_score,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })

async def calculate_streak(username: str):
    """Calculate user's current and longest streaks"""
    # Get all progress data sorted by date
    progress_data = await progress_collection.find({
        "username": username
    }).sort("date", -1).to_list(length=100)
    
    if not progress_data:
        return 0, 0
    
    current_streak = 0
    longest_streak = 0
    temp_streak = 0
    
    # Check for consecutive days with focus time
    for i, progress in enumerate(progress_data):
        if progress.get("focus_time_minutes", 0) > 0:
            temp_streak += 1
            if i == 0:  # Most recent day
                current_streak = temp_streak
        else:
            longest_streak = max(longest_streak, temp_streak)
            temp_streak = 0
    
    longest_streak = max(longest_streak, temp_streak)
    
    return current_streak, longest_streak

async def schedule_reminder(username: str, task_id: str, reminder_time: str, task_text: str):
    """Schedule a reminder for a specific task"""
    try:
        # Parse reminder time (HH:MM format)
        hour, minute = map(int, reminder_time.split(':'))
        
        # Schedule the reminder
        job_id = f"{username}_{task_id}_{reminder_time}"
        
        def send_reminder():
            asyncio.create_task(send_notification(
                username=username,
                message=f"⏰ Reminder: {task_text}",
                notification_type="reminder"
            ))
        
        # Remove existing job if any
        try:
            scheduler.remove_job(job_id)
        except:
            pass
        
        # Add new job
        scheduler.add_job(
            send_reminder,
            CronTrigger(hour=hour, minute=minute),
            id=job_id,
            replace_existing=True
        )
        
        return True
    except Exception as e:
        print(f"Error scheduling reminder: {e}")
        return False

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

@app.get("/users/{username}", response_model=UserResponse)
async def get_user(username: str):
    user = await get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user["id"] = str(user["_id"])
    return user

@app.post("/users/{username}/sessions/", response_model=FocusSessionResponse)
async def create_focus_session(username: str, session: FocusSessionCreate):
    # Get or create user
    user = await get_user_by_username(username)
    if not user:
        # Create user automatically if they don't exist
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
    return session_data

@app.get("/users/{username}/sessions/", response_model=List[FocusSessionResponse])
async def get_focus_sessions(username: str):
    # Get or create user
    user = await get_user_by_username(username)
    if not user:
        # Create user automatically if they don't exist
        user = await create_user(username)
    
    sessions = await sessions_collection.find({"username": username}).sort("created_at", -1).to_list(length=100)
    for session in sessions:
        session["id"] = str(session["_id"])
    return sessions

@app.put("/sessions/{session_id}", response_model=FocusSessionResponse)
async def update_focus_session(session_id: str, session_update: FocusSessionUpdate):
    # Validate ObjectId
    if not ObjectId.is_valid(session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID")
    
    # Find session
    session = await sessions_collection.find_one({"_id": ObjectId(session_id)})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Prepare update data
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
    
    # Return updated session
    updated_session = await sessions_collection.find_one({"_id": ObjectId(session_id)})
    updated_session["id"] = str(updated_session["_id"])
    return updated_session

@app.post("/sessions/{session_id}/activity", response_model=ActivityLogResponse)
async def log_activity(session_id: str, activity_log: ActivityLogCreate):
    # Validate ObjectId
    if not ObjectId.is_valid(session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID")
    
    # Find session
    session = await sessions_collection.find_one({"_id": ObjectId(session_id)})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Classify the activity using AI
    classification, confidence, is_distraction = classifier.ensemble_classify(activity_log.window_title)
    
    # Create activity log
    activity_data = {
        "user_id": session["user_id"],
        "username": session["username"],
        "session_id": session_id,
        "window_title": activity_log.window_title,
        "classification": classification,
        "confidence": confidence,
        "is_distraction": is_distraction,
        "start_time": activity_log.start_time,
        "end_time": activity_log.end_time,
        "duration_seconds": activity_log.duration_seconds,
        "created_at": datetime.utcnow()
    }
    
    result = await activity_collection.insert_one(activity_data)
    activity_data["id"] = str(result.inserted_id)
    
    # Update session distraction count if it's a distraction
    if is_distraction:
        await sessions_collection.update_one(
            {"_id": ObjectId(session_id)},
            {"$inc": {"distraction_count": 1}}
        )
    
    return activity_data

@app.get("/users/{username}/plans/", response_model=List[DailyPlanResponse])
async def get_daily_plans(username: str):
    # Get or create user
    user = await get_user_by_username(username)
    if not user:
        # Create user automatically if they don't exist
        user = await create_user(username)
    
    plans = await plans_collection.find({"username": username}).sort("date", -1).to_list(length=100)
    for plan in plans:
        plan["id"] = str(plan["_id"])
    return plans

@app.get("/users/{username}/plans/{date}", response_model=DailyPlanResponse)
async def get_daily_plan(username: str, date: str):
    # Get or create user
    user = await get_user_by_username(username)
    if not user:
        # Create user automatically if they don't exist
        user = await create_user(username)
    
    plan = await plans_collection.find_one({"username": username, "date": date})
    if not plan:
        # Return empty plan instead of 404
        return {
            "id": "",
            "username": username,
            "date": date,
            "plan_text": "",
            "completed": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    
    plan["id"] = str(plan["_id"])
    return plan

@app.post("/users/{username}/plans/", response_model=DailyPlanResponse)
async def create_daily_plan(username: str, daily_plan: DailyPlanCreate):
    # Get or create user
    user = await get_user_by_username(username)
    if not user:
        # Create user automatically if they don't exist
        user = await create_user(username)
    
    # Use provided date or today's date
    if daily_plan.date:
        date = daily_plan.date
    else:
        date = datetime.utcnow().strftime("%Y-%m-%d")
    
    # Check if plan already exists for this date
    existing_plan = await plans_collection.find_one({"username": username, "date": date})
    if existing_plan:
        # Update existing plan
        await plans_collection.update_one(
            {"username": username, "date": date},
            {
                "$set": {
                    "plan_text": daily_plan.plan_text,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        existing_plan["id"] = str(existing_plan["_id"])
        return existing_plan
    
    # Create new plan
    plan_data = {
        "user_id": str(user["_id"]),
        "username": username,
        "date": date,
        "plan_text": daily_plan.plan_text,
        "completed": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await plans_collection.insert_one(plan_data)
    plan_data["id"] = str(result.inserted_id)
    return plan_data

@app.put("/plans/{plan_id}", response_model=DailyPlanResponse)
async def update_daily_plan(plan_id: str, daily_plan_update: DailyPlanUpdate):
    # Validate ObjectId
    if not ObjectId.is_valid(plan_id):
        raise HTTPException(status_code=400, detail="Invalid plan ID")
    
    # Find plan
    plan = await plans_collection.find_one({"_id": ObjectId(plan_id)})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Prepare update data
    update_data = {"updated_at": datetime.utcnow()}
    if daily_plan_update.plan_text is not None:
        update_data["plan_text"] = daily_plan_update.plan_text
    if daily_plan_update.completed is not None:
        update_data["completed"] = daily_plan_update.completed
    
    await plans_collection.update_one(
        {"_id": ObjectId(plan_id)},
        {"$set": update_data}
    )
    
    # Return updated plan
    updated_plan = await plans_collection.find_one({"_id": ObjectId(plan_id)})
    updated_plan["id"] = str(updated_plan["_id"])
    return updated_plan

@app.get("/users/{username}/stats/{date}", response_model=dict)
async def get_daily_stats(username: str, date: str):
    # Get or create user
    user = await get_user_by_username(username)
    if not user:
        # Create user automatically if they don't exist
        user = await create_user(username)
    
    # Get sessions for the date
    start_date = datetime.strptime(date, "%Y-%m-%d")
    end_date = start_date + timedelta(days=1)
    
    sessions = await sessions_collection.find({
        "username": username,
        "start_time": {"$gte": start_date, "$lt": end_date}
    }).to_list(length=100)
    
    # Calculate stats
    total_sessions = len(sessions)
    completed_sessions = sum(1 for session in sessions if session.get("completed", False))
    total_focus_time = sum(session.get("duration_minutes", 0) for session in sessions)
    total_distractions = sum(session.get("distraction_count", 0) for session in sessions)
    
    # Calculate average productivity
    productivity_scores = [session.get("productivity_score", 0.0) for session in sessions]
    average_productivity = sum(productivity_scores) / len(productivity_scores) if productivity_scores else 0.0
    
    return {
        "date": date,
        "total_sessions": total_sessions,
        "completed_sessions": completed_sessions,
        "total_focus_time": total_focus_time,
        "average_productivity": average_productivity,
        "total_distractions": total_distractions
    }

@app.get("/users/{username}/activity/time_spent", response_model=dict)
async def get_time_spent_per_app(username: str, start_date: Optional[str] = None, end_date: Optional[str] = None):
    # Get or create user
    user = await get_user_by_username(username)
    if not user:
        # Create user automatically if they don't exist
        user = await create_user(username)
    
    # Parse dates
    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    else:
        start_dt = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
    else:
        end_dt = start_dt + timedelta(days=1)
    
    # Get activities for the date range
    activities = await activity_collection.find({
        "username": username,
        "start_time": {"$gte": start_dt, "$lt": end_dt}
    }).to_list(length=1000)
    
    # Group by window title and sum duration
    app_time = {}
    for activity in activities:
        window_title = activity.get("window_title", "Unknown")
        duration = activity.get("duration_seconds", 0)
        
        if window_title in app_time:
            app_time[window_title] += duration
        else:
            app_time[window_title] = duration
    
    return app_time

# WebSocket endpoint for real-time notifications
@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await websocket.accept()
    active_connections[username] = websocket
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        if username in active_connections:
            del active_connections[username]

# Enhanced Daily Plan endpoints
@app.post("/users/{username}/plans/enhanced/", response_model=DailyPlanEnhancedResponse)
async def create_enhanced_daily_plan(username: str, daily_plan: DailyPlanEnhancedCreate):
    # Get or create user
    user = await get_user_by_username(username)
    if not user:
        user = await create_user(username)
    
    # Use today's date if not specified
    date = daily_plan.date or datetime.utcnow().strftime("%Y-%m-%d")
    
    # Schedule reminders for reminder items
    for reminder in daily_plan.reminders:
        await schedule_reminder(username, reminder.id, reminder.time, reminder.text)
    
    # Create enhanced plan
    plan_data = {
        "username": username,
        "date": date,
        "tasks": [task.dict() for task in daily_plan.tasks],
        "reminders": [reminder.dict() for reminder in daily_plan.reminders],
        "completed": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await plans_collection.insert_one(plan_data)
    plan_data["id"] = str(result.inserted_id)
    
    return plan_data

@app.get("/users/{username}/plans/enhanced/{date}", response_model=DailyPlanEnhancedResponse)
async def get_enhanced_daily_plan(username: str, date: str):
    # Get or create user
    user = await get_user_by_username(username)
    if not user:
        user = await create_user(username)
    
    # Get enhanced plan for the date
    plan = await plans_collection.find_one({
        "username": username,
        "date": date
    })
    
    if not plan:
        # Return empty plan structure
        return {
            "id": "",
            "username": username,
            "date": date,
            "tasks": [],
            "reminders": [],
            "completed": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    
    plan["id"] = str(plan["_id"])
    return plan

@app.put("/users/{username}/plans/enhanced/{date}", response_model=DailyPlanEnhancedResponse)
async def update_enhanced_daily_plan(username: str, date: str, plan_update: DailyPlanEnhancedUpdate):
    # Get or create user
    user = await get_user_by_username(username)
    if not user:
        user = await create_user(username)
    
    # Prepare update data
    update_data = {"updated_at": datetime.utcnow()}
    
    if plan_update.tasks is not None:
        update_data["tasks"] = [task.dict() for task in plan_update.tasks]
    
    if plan_update.reminders is not None:
        update_data["reminders"] = [reminder.dict() for reminder in plan_update.reminders]
        # Schedule reminders for new reminder items
        for reminder in plan_update.reminders:
            await schedule_reminder(username, reminder.id, reminder.time, reminder.text)
    
    if plan_update.completed is not None:
        update_data["completed"] = plan_update.completed
    
    # Update or create plan
    result = await plans_collection.update_one(
        {"username": username, "date": date},
        {"$set": update_data},
        upsert=True
    )
    
    # Return updated plan
    updated_plan = await plans_collection.find_one({
        "username": username,
        "date": date
    })
    
    updated_plan["id"] = str(updated_plan["_id"])
    return updated_plan

# Notification endpoints
@app.get("/users/{username}/notifications/", response_model=List[NotificationResponse])
async def get_notifications(username: str):
    # Get or create user
    user = await get_user_by_username(username)
    if not user:
        user = await create_user(username)
    
    # Get user's notifications
    notifications = await notifications_collection.find({
        "username": username
    }).sort("created_at", -1).to_list(length=50)
    
    for notification in notifications:
        notification["id"] = str(notification["_id"])
    
    return notifications

@app.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str):
    # Mark notification as read
    await notifications_collection.update_one(
        {"_id": ObjectId(notification_id)},
        {"$set": {"read": True}}
    )
    
    return {"message": "Notification marked as read"}

# Progress tracking endpoints
@app.get("/users/{username}/progress/", response_model=ProgressResponse)
async def get_user_progress(username: str, days: int = 30):
    # Get or create user
    user = await get_user_by_username(username)
    if not user:
        user = await create_user(username)
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get progress data for the date range
    progress_data = await progress_collection.find({
        "username": username,
        "date": {
            "$gte": start_date.strftime("%Y-%m-%d"),
            "$lte": end_date.strftime("%Y-%m-%d")
        }
    }).sort("date", 1).to_list(length=100)
    
    # Calculate streaks
    current_streak, longest_streak = await calculate_streak(username)
    
    # Calculate totals
    total_focus_time = sum(p.get("focus_time_minutes", 0) for p in progress_data)
    productivity_scores = [p.get("productivity_score", 0) for p in progress_data if p.get("productivity_score", 0) > 0]
    average_productivity = sum(productivity_scores) / len(productivity_scores) if productivity_scores else 0
    
    # Format progress data
    formatted_progress = []
    for progress in progress_data:
        formatted_progress.append({
            "date": progress["date"],
            "focus_time_minutes": progress.get("focus_time_minutes", 0),
            "distraction_count": progress.get("distraction_count", 0),
            "productivity_score": progress.get("productivity_score", 0),
            "streak_days": current_streak,  # This would need more complex calculation
            "is_break": progress.get("focus_time_minutes", 0) == 0
        })
    
    return {
        "username": username,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "total_focus_time": total_focus_time,
        "average_productivity": average_productivity,
        "progress_data": formatted_progress
    }

# Enhanced activity logging with notification
@app.post("/sessions/{session_id}/activity/enhanced", response_model=ActivityLogResponse)
async def log_activity_with_notification(session_id: str, activity_log: ActivityLogCreate):
    # Validate ObjectId
    try:
        ObjectId(session_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid session ID")
    
    # Get session to find username
    session = await sessions_collection.find_one({"_id": ObjectId(session_id)})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    username = session["username"]
    
    # Log the activity
    activity_data = {
        "username": username,
        "session_id": session_id,
        "window_title": activity_log.window_title,
        "classification": activity_log.classification,
        "confidence": activity_log.confidence,
        "is_distraction": activity_log.is_distraction,
        "start_time": activity_log.start_time,
        "end_time": activity_log.end_time,
        "duration_seconds": activity_log.duration_seconds,
        "created_at": datetime.utcnow()
    }
    
    result = await activity_collection.insert_one(activity_data)
    activity_data["id"] = str(result.inserted_id)
    
    # Check for distractions and send notifications
    if activity_log.is_distraction:
        await check_distraction_and_notify(username, activity_log.window_title, activity_log.classification)
    
    # Update progress tracking
    await update_progress_tracking(
        username=username,
        focus_time=0,  # This would be calculated from session duration
        distraction_count=1 if activity_log.is_distraction else 0,
        productivity_score=1.0 - (0.3 if activity_log.is_distraction else 0)
    )
    
    return activity_data

# Weekly stats endpoint for progress graph
@app.get("/users/{username}/stats/weekly", response_model=dict)
async def get_weekly_stats(username: str):
    # Get or create user
    user = await get_user_by_username(username)
    if not user:
        user = await create_user(username)
    
    # Calculate date range for the past week
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)
    
    weekly_stats = {}
    
    # Get stats for each day
    for i in range(7):
        date = (end_date - timedelta(days=i)).strftime("%Y-%m-%d")
        
        # Get sessions for this date
        day_start = datetime.strptime(date, "%Y-%m-%d")
        day_end = day_start + timedelta(days=1)
        
        sessions = await sessions_collection.find({
            "username": username,
            "start_time": {"$gte": day_start, "$lt": day_end}
        }).to_list(length=100)
        
        # Calculate stats
        total_sessions = len(sessions)
        completed_sessions = sum(1 for session in sessions if session.get("completed", False))
        total_focus_time = sum(session.get("duration_minutes", 0) for session in sessions)
        total_distractions = sum(session.get("distraction_count", 0) for session in sessions)
        
        # Calculate average productivity
        productivity_scores = [session.get("productivity_score", 0.0) for session in sessions]
        average_productivity = sum(productivity_scores) / len(productivity_scores) if productivity_scores else 0.0
        
        weekly_stats[date] = {
            "total_sessions": total_sessions,
            "completed_sessions": completed_sessions,
            "total_focus_time": total_focus_time,
            "average_productivity": average_productivity,
            "total_distractions": total_distractions
        }
    
    return weekly_stats

if __name__ == "__main__":
    import uvicorn
    if db is None:
        print("❌ Cannot start server without MongoDB connection")
        exit(1)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)


