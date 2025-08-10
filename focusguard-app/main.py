from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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
import shutil
import platform
import subprocess
import psutil
import time

# Advanced BERT-based Content Classification
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    from sentence_transformers import SentenceTransformer
    import torch
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
    BERT_AVAILABLE = True
    print("✅ BERT libraries imported successfully")
except ImportError as e:
    print(f"⚠️ BERT libraries not available: {e}")
    BERT_AVAILABLE = False

# Cross-platform window monitoring imports
try:
    import platform
    import subprocess
    import psutil
    
    # Windows-specific imports (only on Windows)
    if platform.system() == "Windows":
        try:
            import win32gui
            import win32process
            import win32api
            import win32con
            WINDOWS_AVAILABLE = True
            print("✅ Windows window monitoring libraries available")
        except ImportError:
            WINDOWS_AVAILABLE = False
            print("⚠️ Windows window monitoring not available (pywin32 not installed)")
    else:
        WINDOWS_AVAILABLE = False
        print("ℹ️ Not on Windows - Windows window monitoring disabled")
    
    # Linux-specific imports
    if platform.system() == "Linux":
        import os
        import re
        LINUX_AVAILABLE = True
        print("✅ Linux window monitoring available")
    else:
        LINUX_AVAILABLE = False
        
    WINDOW_MONITORING_AVAILABLE = True
    print("✅ Cross-platform window monitoring available")
except ImportError as e:
    print(f"⚠️ Window monitoring not available: {e}")
    WINDOW_MONITORING_AVAILABLE = False
    WINDOWS_AVAILABLE = False
    LINUX_AVAILABLE = False

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

# Create custom audio directory if it doesn't exist
CUSTOM_AUDIO_DIR = "custom_audio"
if not os.path.exists(CUSTOM_AUDIO_DIR):
    os.makedirs(CUSTOM_AUDIO_DIR)
    print(f"✅ Created custom audio directory: {CUSTOM_AUDIO_DIR}")

# Mount static files for custom audio
app.mount("/custom_audio", StaticFiles(directory=CUSTOM_AUDIO_DIR), name="custom_audio")

# Collections
users_collection = db.users
sessions_collection = db.focus_sessions
plans_collection = db.daily_plans
activity_collection = db.activity_logs
notifications_collection = db.notifications
progress_collection = db.progress_tracking
feedback_collection = db.feedback

# WebSocket connections for real-time notifications
active_connections: Dict[str, WebSocket] = {}

# Scheduler for reminders
scheduler = AsyncIOScheduler()

# Enhanced notification tracking system with throttling
user_distraction_tracking: Dict[str, Dict[str, Any]] = {}
# Structure: {username: {"count": int, "session_id": str, "last_reset": datetime, "last_distraction_active": bool, "last_distracting_window": str, "notification_sent_at": datetime, "repeated_notification_count": int, "last_notification_time": datetime}}

# Notification throttling settings
NOTIFICATION_THROTTLE_SECONDS = 2  # Allow notifications every 2 seconds
REPEATED_NOTIFICATION_INTERVAL = 2  # Allow repeated notifications every 2 seconds for same window

@app.on_event("startup")
async def startup_event():
    """Initialize scheduler on startup"""
    try:
        # Start the scheduler
        scheduler.start()
        print("✅ Scheduler started successfully")
        
        # Add the reminder check job
        scheduler.add_job(
            check_and_send_reminders,
            CronTrigger(minute="*"),  # Run every minute
            id="reminder_check",
            replace_existing=True
        )
        print("✅ Reminder check job added to scheduler")
        
        # Print scheduler status
        print(f"📅 Scheduler running: {scheduler.running}")
        print(f"📋 Active jobs: {len(scheduler.get_jobs())}")
        
    except Exception as e:
        print(f"❌ Error starting scheduler: {e}")

# Advanced BERT-based Content Classification
class AdvancedContentClassifier:
    def __init__(self):
        """Initialize BERT-based classifier with pre-trained models"""
        self.fallback_mode = False
        
        if not BERT_AVAILABLE:
            print("⚠️ BERT libraries not available, using fallback classifier")
            self.fallback_mode = True
            self._init_fallback_classifier()
            return
            
        try:
            print("🚀 Initializing BERT-based classifier...")
            
            # Check if we're in a deployment environment
            is_deployment = os.getenv('RENDER', False) or os.getenv('HEROKU', False)
            
            # Initialize BERT models for different tasks
            device = -1  # Always use CPU for deployment compatibility
            if not is_deployment and torch.cuda.is_available():
                device = 0
                print("🚀 Using GPU for BERT processing")
            else:
                print("💻 Using CPU for BERT processing (deployment mode)")
            
            try:
                self.sentiment_analyzer = pipeline(
                    "sentiment-analysis",
                    model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                    device=device
                )
                print("✅ Sentiment analyzer initialized")
            except Exception as e:
                print(f"⚠️ Sentiment analyzer failed: {e}")
                self.sentiment_analyzer = None
            
            try:
                # Use a general-purpose BERT model for text understanding
                self.text_model = SentenceTransformer('all-MiniLM-L6-v2')
                print("✅ Text model initialized")
            except Exception as e:
                print(f"⚠️ Text model failed: {e}")
                self.text_model = None
            
            # Define category embeddings for classification
            if self.text_model:
                self.category_embeddings = self._create_category_embeddings()
            else:
                self.category_embeddings = {}
            
            # Category weights for classification
            self.category_weights = {
                'educational': 1.0,
                'work': 1.0,
                'entertainment': 0.8,
                'social_media': 0.9,
                'gaming': 0.7,
                'streaming': 0.8,
                'neutral': 0.5
            }
            
            if self.sentiment_analyzer or self.text_model:
                print("✅ BERT classifier initialized successfully!")
            else:
                print("⚠️ BERT models failed to load, using fallback classifier")
                self.fallback_mode = True
                self._init_fallback_classifier()
            
        except Exception as e:
            print(f"⚠️ BERT initialization failed, falling back to basic classifier: {e}")
            self.fallback_mode = True
            self._init_fallback_classifier()
    
    def _create_category_embeddings(self):
        """Create embeddings for different content categories"""
        categories = {
            'educational': [
                'course tutorial learn study education academic university college school',
                'lecture lesson assignment homework exam test quiz research paper',
                'thesis dissertation documentation guide manual book textbook',
                'reference library scholar professor teacher instructor student',
                'science math physics chemistry biology history geography',
                'programming coding development engineering technology',
                'language grammar vocabulary writing reading analysis'
            ],
            'work': [
                'work project task job business office meeting presentation',
                'report analysis data code programming development design',
                'planning strategy management admin dashboard tool software',
                'application system database server network security',
                'finance accounting marketing sales customer client',
                'product service quality efficiency productivity performance',
                'email calendar schedule deadline goal target objective'
            ],
            'entertainment': [
                'movie film video entertainment fun funny comedy drama',
                'show series episode season trailer preview review',
                'music song album playlist artist band concert',
                'game gaming play player level score win lose',
                'stream live broadcast channel viewer audience'
            ],
            'social_media': [
                'facebook instagram twitter tiktok snapchat pinterest',
                'social media post share like comment follow',
                'profile friend message chat conversation',
                'trending viral hashtag story reel'
            ],
            'gaming': [
                'game gaming play player level score win lose',
                'steam epic origin battle.net launcher',
                'multiplayer online competitive tournament',
                'rpg fps strategy puzzle adventure'
            ],
            'streaming': [
                'youtube netflix hulu disney+ prime video',
                'stream watch video content creator',
                'channel subscription playlist favorite',
                'live broadcast vod on-demand'
            ]
        }
        
        embeddings = {}
        for category, texts in categories.items():
            # Create embeddings for each category's representative texts
            category_embeddings = []
            for text in texts:
                embedding = self.text_model.encode(text)
                category_embeddings.append(embedding)
            
            # Average the embeddings for the category
            embeddings[category] = np.mean(category_embeddings, axis=0)
        
        return embeddings
    
    def _init_fallback_classifier(self):
        """Initialize fallback classifier if BERT fails"""
        self.entertainment_keywords = {
            'youtube', 'netflix', 'spotify', 'instagram', 'facebook', 'twitter', 'tiktok',
            'reddit', 'twitch', 'discord', 'snapchat', 'pinterest', 'tumblr', 'vine',
            'game', 'gaming', 'play', 'movie', 'music', 'video', 'stream', 'live',
            'entertainment', 'fun', 'funny', 'meme', 'joke', 'comedy', 'drama',
            'reality', 'show', 'series', 'episode', 'season', 'trailer', 'preview'
        }
        
        self.educational_keywords = {
            'course', 'tutorial', 'learn', 'study', 'education', 'academic', 'university',
            'college', 'school', 'lecture', 'lesson', 'assignment', 'homework', 'exam',
            'test', 'quiz', 'research', 'paper', 'thesis', 'dissertation', 'documentation',
            'guide', 'manual', 'book', 'textbook', 'reference', 'library', 'scholar',
            'programming', 'coding', 'development', 'engineering', 'technology', 'computer',
            'science', 'math', 'physics', 'chemistry', 'biology', 'history', 'geography',
            'language', 'grammar', 'vocabulary', 'writing', 'reading', 'analysis',
            'algorithm', 'data structure', 'database', 'web development', 'mobile app',
            'machine learning', 'ai', 'artificial intelligence', 'neural network',
            'statistics', 'calculus', 'algebra', 'geometry', 'trigonometry'
        }
        
        self.productive_keywords = {
            'work', 'project', 'task', 'job', 'business', 'office', 'meeting', 'presentation',
            'report', 'analysis', 'data', 'code', 'programming', 'development', 'design',
            'planning', 'strategy', 'management', 'admin', 'dashboard', 'tool', 'software'
        }
    
    def analyze_sentiment(self, text):
        """Analyze sentiment using BERT-based model"""
        try:
            if hasattr(self, 'fallback_mode') and self.fallback_mode:
                # Fallback to TextBlob
                from textblob import TextBlob
                blob = TextBlob(text)
                sentiment_score = blob.sentiment.polarity
                if sentiment_score > 0.1:
                    return "positive", sentiment_score
                elif sentiment_score < -0.1:
                    return "negative", sentiment_score
                else:
                    return "neutral", sentiment_score
            
            # Use BERT for sentiment analysis
            result = self.sentiment_analyzer(text[:512])[0]  # Limit text length
            label = result['label']
            score = result['score']
            
            # Map labels to sentiment
            if label == 'LABEL_0':
                return "negative", 1 - score
            elif label == 'LABEL_1':
                return "neutral", score
            else:  # LABEL_2
                return "positive", score
                
        except Exception as e:
            print(f"Sentiment analysis error: {e}")
            return "neutral", 0.5
    
    def classify_content(self, title):
        """Classify content using BERT embeddings and similarity with smart tab content analysis"""
        try:
            if hasattr(self, 'fallback_mode') and self.fallback_mode:
                return self._fallback_classify(title)
            
            if not title or len(title.strip()) < 3:
                return "neutral", 0.5, False
            
            # SMART TAB CONTENT ANALYSIS - Look at the actual content, not just process name
            title_lower = title.lower()
            
            # Extract tab content (after the process name and dash)
            tab_content = title
            if " - " in title:
                # Split by " - " and take the meaningful part
                parts = title.split(" - ")
                if len(parts) >= 2:
                    # Skip process name, focus on tab content
                    tab_content = " - ".join(parts[1:])
                    print(f"🔍 Tab content extracted: '{tab_content}' from title: '{title}'")
            else:
                print(f"🔍 No dash found, using full title: '{title}'")
            
            # FORCE FALLBACK CLASSIFIER FOR CHROME TABS - BERT is not working well for tab content
            if "chrome" in title_lower:
                print(f"🔄 Chrome tab detected, using fallback classifier for better accuracy")
                return self._fallback_classify(title)
            
            # Special handling for Cursor/VS Code - always productive for development
            if "cursor" in title_lower or "code" in title_lower or "visual studio" in title_lower:
                if any(dev_word in title_lower for dev_word in 
                       ['.py', '.js', '.jsx', '.ts', '.tsx', '.html', '.css', '.java', '.cpp', '.c']):
                    return "work", 0.95, False  # Development work
                else:
                    return "work", 0.9, False  # General work
            
            # Create embedding for the input title
            title_embedding = self.text_model.encode(title)
            
            # Calculate similarity with all categories
            similarities = {}
            for category, category_embedding in self.category_embeddings.items():
                similarity = cosine_similarity(
                    [title_embedding], 
                    [category_embedding]
                )[0][0]
                similarities[category] = similarity * self.category_weights.get(category, 1.0)
            
            # Find the best matching category
            best_category = max(similarities, key=similarities.get)
            confidence = similarities[best_category]
            
            # Determine if it's a distraction
            is_distraction = best_category in ['entertainment', 'social_media', 'gaming', 'streaming']
            
            # Special handling for educational content - never mark as distracting
            if best_category == 'educational':
                is_distraction = False
                confidence = max(confidence, 0.8)  # Boost confidence for educational content
            
            # Special handling for work content - never mark as distracting
            if best_category == 'work':
                is_distraction = False
                confidence = max(confidence, 0.8)  # Boost confidence for work content
            
            return best_category, confidence, is_distraction
            
        except Exception as e:
            print(f"BERT classification error: {e}")
            if hasattr(self, 'fallback_mode') and self.fallback_mode:
                return self._fallback_classify(title)
            return "neutral", 0.5, False
    
    def _fallback_classify(self, title):
        """Fallback classification using keyword matching with smart tab analysis"""
        title_lower = title.lower()
        
        # Extract tab content (after the process name and dash)
        tab_content = title
        if " - " in title:
            parts = title.split(" - ")
            if len(parts) >= 2:
                tab_content = " - ".join(parts[1:])
                print(f"🔄 Fallback: Tab content extracted: '{tab_content}' from title: '{title}'")
        else:
            print(f"🔄 Fallback: No dash found, using full title: '{title}'")
        
        # Smart Chrome tab analysis
        if "chrome" in title_lower:
            if "new tab" in title_lower:
                return "neutral", 0.9, False
            
            if "youtube" in title_lower:
                print(f"🔍 YouTube detected, analyzing: '{tab_content}'")
                if any(edu_word in tab_content.lower() for edu_word in 
                       ['educational', 'tutorial', 'course', 'learn', 'study', 'lecture']):
                    print(f"📚 Educational YouTube detected: {tab_content}")
                    return "educational", 0.9, False
                elif any(ent_word in tab_content.lower() for ent_word in 
                        ['music', 'song', 'movie', 'game', 'funny', 'comedy', 'entertainment', 'video', 'official', 'ft.', 'feat']):
                    print(f"🎵 Entertainment YouTube detected: {tab_content}")
                    return "entertainment", 0.8, True
                # Check for song patterns (artist names, song titles, music-related patterns)
                elif any(pattern in tab_content.lower() for pattern in 
                        ['ft.', 'feat', 'official', 'video', 'song', 'music', 'album', 'track', 'remix', 'cover']):
                    print(f"🎵 Music pattern detected: {tab_content}")
                    return "entertainment", 0.85, True  # Music/Entertainment YouTube
                # Check for movie/show patterns
                elif any(pattern in tab_content.lower() for pattern in 
                        ['full hd', 'hd video', 'movie', 'film', 'episode', 'season', 'series']):
                    print(f"🎬 Movie pattern detected: {tab_content}")
                    return "entertainment", 0.85, True  # Movie/Show YouTube
                else:
                    print(f"📺 General YouTube streaming: {tab_content}")
                    return "streaming", 0.7, True
            
            # Analyze entertainment and gaming sites
            if any(ent_site in tab_content.lower() for ent_site in 
                   ['movierulz', 'movie', 'film', 'watch online', 'full movie', 'hd video', 'video song']):
                print(f"🎬 Entertainment site detected: {tab_content}")
                return "entertainment", 0.85, True
            
            if any(gaming_site in tab_content.lower() for gaming_site in 
                   ['bc.game', 'casino', 'gambling', 'slot games', 'crypto casino', 'game']):
                print(f"🎮 Gaming site detected: {tab_content}")
                return "gaming", 0.9, True
            
            if any(edu_site in tab_content.lower() for edu_site in 
                   ['stack overflow', 'github', 'documentation', 'tutorial']):
                return "educational", 0.9, False
            
            if any(work_site in tab_content.lower() for work_site in 
                   ['gmail', 'google docs', 'sheets', 'slides']):
                return "work", 0.9, False
            
            # Analyze development/project work - recognize when working on development projects
            if any(dev_keyword in tab_content.lower() for dev_keyword in 
                   ['focusguard', 'focus guard', 'development', 'project', 'app', 'application', 
                    'code', 'programming', 'software', 'web app', 'react', 'python', 'javascript',
                    'html', 'css', 'api', 'backend', 'frontend', 'database', 'server', 'git',
                    'terminal', 'console', 'debug', 'test', 'build', 'deploy', 'config',
                    'package.json', 'requirements.txt', 'docker', 'kubernetes', 'aws', 'azure']):
                return "work", 0.95, False  # Development work is highly productive
            
            # Special case: If the tab contains project-related keywords in the title, it's likely work
            if any(project_keyword in title_lower for project_keyword in 
                   ['focusguard', 'focus guard', 'productivity', 'timer', 'dashboard', 'stats',
                    'monitor', 'track', 'session', 'plan', 'goal', 'task', 'work', 'study']):
                return "work", 0.9, False  # Project-related work
            
            # Whitelist for known productive applications and projects
            productive_apps = [
                'focusguard', 'focus guard', 'productivity tracker', 'focus timer',
                'pomodoro', 'time tracker', 'task manager', 'project manager',
                'notion', 'trello', 'asana', 'jira', 'confluence', 'slack',
                'teams', 'zoom', 'meet', 'webex'
            ]
            if any(app in title_lower for app in productive_apps):
                return "work", 0.9, False  # Known productive application
            
            # Special handling for FocusGuard project - always productive
            if 'focusguard' in title_lower or 'focus guard' in title_lower:
                return "work", 0.95, False  # FocusGuard project is always productive
            
            # Additional check for productivity-related content
            productivity_keywords = [
                'productivity', 'focus', 'concentration', 'work', 'study', 'learning',
                'development', 'coding', 'programming', 'design', 'analysis', 'research',
                'documentation', 'planning', 'organization', 'management', 'collaboration'
            ]
            if any(keyword in title_lower for keyword in productivity_keywords):
                return "work", 0.85, False  # Productivity-related content
        
        # Smart Cursor/VS Code analysis - MUST come before entertainment check
        if "cursor" in title_lower or "code" in title_lower:
            # Cursor.exe is always a development tool - classify as work
            if "cursor.exe" in title_lower:
                return "work", 0.95, False
            # Check for development file extensions
            elif any(dev_word in title_lower for dev_word in 
                   ['.py', '.js', '.jsx', '.ts', '.tsx', '.html', '.css']):
                return "work", 0.95, False
            else:
                return "work", 0.9, False
        
        # Check for educational content
        if any(keyword in title_lower for keyword in self.educational_keywords):
            return "educational", 0.8, False
        
        # Check for productive content
        if any(keyword in title_lower for keyword in self.productive_keywords):
            return "work", 0.8, False
        
        # Check for entertainment
        if any(keyword in title_lower for keyword in self.entertainment_keywords):
            return "entertainment", 0.7, True
        
        return "neutral", 0.5, False
    
    def get_detailed_analysis(self, title):
        """Get comprehensive analysis including sentiment and classification"""
        if not title or len(title.strip()) < 3:
            return {
                "classification": "neutral",
                "confidence": 0.5,
                "is_distraction": False,
                "sentiment": "neutral",
                "sentiment_score": 0.0,
                "reasoning": "Title too short for analysis"
            }
        
        # Get classification
        category, confidence, is_distraction = self.classify_content(title)
        
        # Get sentiment
        sentiment, sentiment_score = self.analyze_sentiment(title)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(title, category, confidence, sentiment)
        
        return {
            "classification": category,
            "confidence": confidence,
            "is_distraction": is_distraction,
            "sentiment": sentiment,
            "sentiment_score": sentiment_score,
            "reasoning": reasoning
        }
    
    def _generate_reasoning(self, title, category, confidence, sentiment):
        """Generate human-readable reasoning for classification with smart tab analysis"""
        title_lower = title.lower()
        
        # Extract tab content for better reasoning
        tab_content = title
        if " - " in title:
            parts = title.split(" - ")
            if len(parts) >= 2:
                tab_content = " - ".join(parts[1:])
        
        if category == "educational":
            if "youtube" in title_lower:
                if any(edu_word in tab_content.lower() for edu_word in 
                       ['educational', 'tutorial', 'course', 'learn', 'study', 'lecture']):
                    return f"Educational YouTube content: '{tab_content}' contains learning keywords"
                else:
                    return f"YouTube tab analyzed: '{tab_content}' - classified as educational based on context"
            elif "stack overflow" in title_lower or "github" in title_lower:
                return f"Educational development resource: '{tab_content}' - programming documentation/help"
            elif "course" in title_lower or "tutorial" in title_lower:
                return f"Educational content: '{tab_content}' - course/tutorial material"
            else:
                return f"Educational content identified: '{tab_content}' contains learning keywords"
        
        elif category == "work":
            if "cursor" in title_lower or "code" in title_lower:
                if any(dev_word in title_lower for dev_word in 
                       ['.py', '.js', '.jsx', '.ts', '.tsx', '.html', '.css']):
                    return f"Development work: '{tab_content}' - coding in {title_lower.split('.')[-1]} files"
                else:
                    return f"Development work: '{tab_content}' - using {title_lower.split('.')[0]} editor"
            elif "gmail" in title_lower or "google docs" in title_lower:
                return f"Work productivity: '{tab_content}' - email/document management"
            elif "excel" in title_lower or "word" in title_lower:
                return f"Office productivity: '{tab_content}' - document/spreadsheet work"
            else:
                return f"Work content: '{tab_content}' contains productivity keywords"
        
        elif category == "entertainment":
            if "youtube" in title_lower:
                if any(ent_word in tab_content.lower() for ent_word in 
                       ['music', 'song', 'movie', 'game', 'funny', 'comedy']):
                    return f"Entertainment YouTube: '{tab_content}' - leisure content detected"
                else:
                    return f"YouTube entertainment: '{tab_content}' - classified as leisure based on context"
            elif "movie" in title_lower or "film" in title_lower:
                return f"Entertainment media: '{tab_content}' - movie/film content"
            elif "music" in title_lower or "song" in title_lower:
                return f"Music entertainment: '{tab_content}' - audio content"
            else:
                return f"Entertainment content: '{tab_content}' - leisure activity detected"
        
        elif category == "social_media":
            if "facebook" in title_lower or "instagram" in title_lower:
                return f"Social media: '{tab_content}' - social networking platform"
            elif "twitter" in title_lower or "reddit" in title_lower:
                return f"Social media: '{tab_content}' - discussion/social platform"
            else:
                return f"Social media content: '{tab_content}' - social interaction detected"
        
        elif category == "gaming":
            return f"Gaming content: '{tab_content}' - game-related activity detected"
        
        elif category == "streaming":
            if "youtube" in title_lower:
                if any(edu_word in tab_content.lower() for edu_word in 
                       ['educational', 'tutorial', 'course', 'learn', 'study']):
                    return f"Educational streaming: '{tab_content}' - learning content on YouTube"
                else:
                    return f"General streaming: '{tab_content}' - video content on YouTube"
            elif "netflix" in title_lower:
                return f"Streaming entertainment: '{tab_content}' - Netflix content"
            else:
                return f"Streaming content: '{tab_content}' - video/media streaming"
        
        elif category == "neutral":
            if "new tab" in title_lower:
                return f"Neutral: '{tab_content}' - empty/new browser tab"
            else:
                return f"Neutral content: '{tab_content}' - insufficient context for specific classification"
        
        else:
            return f"Content analysis: '{tab_content}' - classified as {category} with {confidence:.2f} confidence"

# Initialize the advanced classifier
try:
    classifier = AdvancedContentClassifier()
    print("🎯 Using Advanced BERT-based Content Classifier")
except Exception as e:
    print(f"⚠️ Failed to initialize BERT classifier: {e}")
    print("🔄 Falling back to basic keyword classifier")
    classifier = AdvancedContentClassifier()  # This will trigger fallback mode

# Cross-platform Window Monitoring System
class CrossPlatformWindowMonitor:
    """Cross-platform window monitoring system that works on both Windows and Linux"""
    
    def __init__(self):
        self.system = platform.system()
        self.last_window_title = ""
        self.last_check_time = 0
        self.check_interval = 2
        
    def get_active_window_title(self):
        """Get the title of the currently active window - works on Windows and Linux"""
        try:
            if self.system == "Windows" and WINDOWS_AVAILABLE:
                return self._get_windows_active_window()
            elif self.system == "Linux" and LINUX_AVAILABLE:
                return self._get_linux_active_window()
            else:
                return self._get_fallback_window_info()
        except Exception as e:
            print(f"Error getting active window: {e}")
            return "Unknown Window"
    
    def _get_windows_active_window(self):
        """Get active window on Windows"""
        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                title = win32gui.GetWindowText(hwnd)
                try:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    process = psutil.Process(pid)
                    process_name = process.name()
                    return f"{process_name} - {title}" if title else process_name
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    return title if title else "Unknown Window"
            return "No Active Window"
        except Exception as e:
            print(f"Windows window detection error: {e}")
            return "Windows Error"
    
    def _get_linux_active_window(self):
        """Get active window on Linux using xdotool or wmctrl"""
        try:
            # Try xdotool first (more reliable)
            try:
                result = subprocess.run(
                    ['xdotool', 'getactivewindow', 'getwindowname'],
                    capture_output=True, text=True, timeout=2
                )
                if result.returncode == 0:
                    window_title = result.stdout.strip()
                    if window_title:
                        # Get process name
                        try:
                            result_pid = subprocess.run(
                                ['xdotool', 'getactivewindow', 'getwindowpid'],
                                capture_output=True, text=True, timeout=2
                            )
                            if result_pid.returncode == 0:
                                pid = result_pid.stdout.strip()
                                if pid.isdigit():
                                    process = psutil.Process(int(pid))
                                    process_name = process.name()
                                    return f"{process_name} - {window_title}"
                        except:
                            pass
                        return window_title
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # Fallback to wmctrl
            try:
                result = subprocess.run(
                    ['wmctrl', '-a', ':ACTIVE:', '-v'],
                    capture_output=True, text=True, timeout=2
                )
                if result.returncode == 0:
                    # Parse wmctrl output
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if 'Window title:' in line:
                            window_title = line.split('Window title:')[1].strip()
                            return window_title
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # Final fallback - try to get from environment
            display = os.environ.get('DISPLAY')
            if display:
                return f"Linux Desktop - {display}"
            else:
                return "Linux System"
                
        except Exception as e:
            print(f"Linux window detection error: {e}")
            return "Linux Error"
    
    def _get_fallback_window_info(self):
        """Fallback window info when platform-specific methods fail"""
        try:
            # Get basic system info
            system_info = {
                "system": self.system,
                "hostname": platform.node(),
                "username": os.environ.get('USER', os.environ.get('USERNAME', 'Unknown')),
                "display": os.environ.get('DISPLAY', 'No Display'),
                "terminal": os.environ.get('TERM', 'Unknown')
            }
            
            # Try to get current working directory as context
            try:
                cwd = os.getcwd()
                system_info["working_directory"] = cwd
            except:
                system_info["working_directory"] = "Unknown"
            
            # Create a meaningful window title from system info
            if self.system == "Linux":
                return f"Linux Terminal - {system_info['username']}@{system_info['hostname']}"
            elif self.system == "Windows":
                return f"Windows System - {system_info['username']}"
            else:
                return f"{self.system} System - {system_info['username']}"
                
        except Exception as e:
            print(f"Fallback window info error: {e}")
            return f"{self.system} System"
    
    def get_window_info(self):
        """Get detailed information about the active window"""
        try:
            title = self.get_active_window_title()
            
            # Get process info if possible
            process_info = {
                "name": "Unknown",
                "exe": "Unknown",
                "cmdline": [],
                "title": title,
                "full_title": title
            }
            
            try:
                if self.system == "Windows" and WINDOWS_AVAILABLE:
                    hwnd = win32gui.GetForegroundWindow()
                    if hwnd:
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        process = psutil.Process(pid)
                        process_info.update({
                            "name": process.name(),
                            "exe": process.exe(),
                            "cmdline": process.cmdline()
                        })
                elif self.system == "Linux" and LINUX_AVAILABLE:
                    # Try to get process info on Linux
                    try:
                        result = subprocess.run(
                            ['xdotool', 'getactivewindow', 'getwindowpid'],
                            capture_output=True, text=True, timeout=2
                        )
                        if result.returncode == 0 and result.stdout.strip().isdigit():
                            pid = int(result.stdout.strip())
                            process = psutil.Process(pid)
                            process_info.update({
                                "name": process.name(),
                                "exe": process.exe(),
                                "cmdline": process.cmdline()
                            })
                    except:
                        pass
            except:
                pass
            
            return process_info
            
        except Exception as e:
            print(f"Error getting window info: {e}")
            return {
                "name": "Error",
                "exe": "Error",
                "cmdline": [],
                "title": "Error Getting Window",
                "full_title": "Error Getting Window"
            }
    
    def should_send_activity(self, current_title, current_time):
        """Determine if we should send activity data based on smart rules"""
        
        # Always send if window has changed
        if current_title != self.last_window_title:
            return True, "Window changed"
        
        # If we're on a distraction, send data every 2 seconds for repeated notifications
        if (hasattr(self, 'last_distracting_window') and 
            self.last_distracting_window and 
            current_title == self.last_distracting_window):
            return True, "Sending data for repeated distraction notification"
        
        return False, "No change needed"

# Initialize the cross-platform window monitor
try:
    window_monitor = CrossPlatformWindowMonitor()
    print(f"✅ Cross-platform window monitor initialized for {window_monitor.system}")
except Exception as e:
    print(f"⚠️ Failed to initialize window monitor: {e}")
    window_monitor = None

# Pydantic models
class UserCreate(BaseModel):
    username: str

class UserResponse(BaseModel):
    id: str
    username: str
    created_at: datetime
    last_active: datetime
    original_username: Optional[str] = None
    username_modified: Optional[bool] = False
    message: Optional[str] = None
    custom_audio_url: Optional[str] = None

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
    sentiment: str
    sentiment_score: float
    reasoning: str
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
            "last_reset": datetime.utcnow(),
            "last_distraction_active": False,
            "last_distracting_window": window_title,
            "notification_sent_at": datetime.utcnow(),
            "repeated_notification_count": 0,
            "last_notification_time": datetime.utcnow() # Initialize last_notification_time
        }
    
    # Reset counter if new session or after 1 hour
    current_tracking = user_distraction_tracking[username]
    time_since_reset = datetime.utcnow() - current_tracking["last_reset"]
    
    if (current_tracking["session_id"] != session_id or 
        time_since_reset > timedelta(hours=1)):
        current_tracking["count"] = 0
        current_tracking["session_id"] = session_id
        current_tracking["last_reset"] = datetime.utcnow()
        current_tracking["repeated_notification_count"] = 0
        current_tracking["last_notification_time"] = datetime.utcnow() # Reset last_notification_time
    
    # Increment distraction count
    current_tracking["count"] += 1
    count = current_tracking["count"]
    
    # Check if user has custom audio
    user = await get_user_by_username(username)
    custom_audio_url = user.get("custom_audio_url") if user else None
    
    print(f"🔊 Audio check for {username}: custom_audio_url = {custom_audio_url}")
    
    # Determine sound type and message based on distraction count and custom audio availability
    if custom_audio_url:
        sound_type = "custom"
        print(f"🎵 Using CUSTOM audio for {username}: {custom_audio_url}")
        if count <= 2:
            message = f"⚠️ Distracting activity detected: {window_title}"
        else:
            message = f"🚨 Multiple distractions detected! Stay focused on: {window_title}"
    else:
        sound_type = "default"
        print(f"🔊 Using DEFAULT audio for {username} (no custom audio found)")
        if count <= 2:
            message = f"⚠️ Distracting activity detected: {window_title}"
        else:
            message = f"🚨 Multiple distractions detected! Stay focused on: {window_title}"
    
    # Create notification data with ALL required fields
    notification_data = {
        "_id": ObjectId(),  # Generate ObjectId for proper insertion
        "id": str(uuid.uuid4()),
        "username": username,
        "message": message,
        "notification_type": "distraction",
        "sound_type": sound_type,  # REQUIRED field
        "custom_audio_url": custom_audio_url,  # Use user's custom audio if available
        "created_at": datetime.utcnow(),
        "read": False,
        "session_id": session_id,
        "window_title": window_title,
        "distraction_count": count,
        "repeated_notification_count": current_tracking.get("repeated_notification_count", 0)
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
    print(f"🔍 Checking WebSocket connection for {username}")
    print(f"🔍 Active connections count: {len(active_connections)}")
    print(f"🔍 Active users: {list(active_connections.keys())}")
    print(f"🔍 Username in active_connections: {username in active_connections}")
    
    if username in active_connections:
        try:
            websocket_message = {
                "type": "notification",  # Changed from "distraction_notification" to match frontend
                "data": {
                    "id": notification_data["id"],
                    "message": notification_data["message"],
                    "notification_type": notification_data["notification_type"],
                    "sound_type": notification_data["sound_type"],
                    "custom_audio_url": notification_data["custom_audio_url"],
                    "created_at": notification_data["created_at"].isoformat(),
                    "window_title": window_title,
                    "distraction_count": count,
                    "repeated_notification_count": current_tracking.get("repeated_notification_count", 0),
                    "read": False
                }
            }
            
            print(f"🔊 WebSocket message sound_type: {notification_data['sound_type']}")
            print(f"🔊 WebSocket message custom_audio_url: {notification_data['custom_audio_url']}")
            
            await active_connections[username].send_text(json.dumps(websocket_message, default=str))
            print(f"✅ WebSocket notification sent to {username}: {message}")
        except Exception as e:
            print(f"❌ Error sending WebSocket notification: {e}")
            # Remove broken connection
            if username in active_connections:
                del active_connections[username]
                print(f"🔍 Removed broken connection for {username}")
                print(f"🔍 Active connections count: {len(active_connections)}")
                print(f"🔍 Active users: {list(active_connections.keys())}")
    else:
        print(f"⚠️ No active WebSocket connection for {username}")
        print(f"🔍 Available users: {list(active_connections.keys())}")
    
    return notification_data

# Reminder notification system
async def check_and_send_reminders():
    """Check for due reminders and send notifications"""
    try:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        current_time = datetime.utcnow().strftime("%H:%M")
        
        print(f"🔍 Checking reminders for {today} at {current_time}")
        
        # Find all plans for today
        cursor = plans_collection.find({"date": today})
        plan_count = 0
        reminder_count = 0
        
        async for plan in cursor:
            plan_count += 1
            username = plan.get("username")
            reminders = plan.get("reminders", [])
            
            print(f"📋 Found plan for {username} with {len(reminders)} reminders")
            
            for reminder in reminders:
                reminder_count += 1
                reminder_time = reminder.get("time", "")
                reminder_text = reminder.get("text")
                is_completed = reminder.get("completed", False)
                
                # Clean and validate time format
                if reminder_time:
                    # Remove any extra characters and ensure HH:MM format
                    cleaned_time = reminder_time.strip()
                    if len(cleaned_time) > 5:
                        # If time has extra digits, truncate to HH:MM
                        cleaned_time = cleaned_time[:5]
                    
                    # Validate time format
                    try:
                        # Test if it's a valid time format
                        datetime.strptime(cleaned_time, "%H:%M")
                        reminder_time = cleaned_time
                    except ValueError:
                        print(f"❌ Invalid time format for reminder '{reminder_text}': {reminder_time}")
                        continue
                
                print(f"⏰ Reminder: {reminder_text} at {reminder_time} (completed: {is_completed})")
                
                if not is_completed and reminder_time == current_time:
                    print(f"🚨 Sending reminder notification for {username}: {reminder_text}")
                    # Send reminder notification
                    await send_reminder_notification(username, reminder)
                else:
                    print(f"⏭️ Skipping reminder: completed={is_completed}, time={reminder_time} vs current={current_time}")
        
        print(f"✅ Reminder check completed: {plan_count} plans, {reminder_count} reminders checked")
                    
    except Exception as e:
        print(f"❌ Error checking reminders: {e}")

async def send_reminder_notification(username: str, reminder: dict):
    """Send reminder notification to user"""
    try:
        # Create notification data
        notification_data = {
            "_id": ObjectId(),
            "id": str(uuid.uuid4()),
            "username": username,
            "message": f"⏰ Reminder: {reminder.get('text', 'Time for your reminder!')}",
            "notification_type": "reminder",
            "sound_type": "default",
            "custom_audio_url": None,
            "created_at": datetime.utcnow(),
            "read": False,
            "reminder_id": reminder.get("id"),
            "reminder_time": reminder.get("time")
        }
        
        # Store notification in database
        await notifications_collection.insert_one(notification_data)
        notification_data["id"] = str(notification_data["_id"])
        
        # Send via WebSocket if connected
        if username in active_connections:
            try:
                websocket_message = {
                    "type": "notification",
                    "data": {
                        "id": notification_data["id"],
                        "message": notification_data["message"],
                        "notification_type": notification_data["notification_type"],
                        "sound_type": notification_data["sound_type"],
                        "custom_audio_url": notification_data["custom_audio_url"],
                        "created_at": notification_data["created_at"].isoformat(),
                        "reminder_id": notification_data["reminder_id"],
                        "reminder_time": notification_data["reminder_time"],
                        "read": False
                    }
                }
                
                await active_connections[username].send_text(json.dumps(websocket_message, default=str))
                print(f"✅ Reminder notification sent to {username}: {reminder.get('text')}")
                
            except Exception as e:
                print(f"❌ Error sending reminder WebSocket notification: {e}")
                if username in active_connections:
                    del active_connections[username]
        else:
            print(f"⚠️ No active WebSocket connection for {username} - reminder notification not sent")
            
    except Exception as e:
        print(f"❌ Error sending reminder notification: {e}")

# Schedule reminder checks every minute
scheduler.add_job(
    check_and_send_reminders,
    CronTrigger(minute="*"),  # Run every minute
    id="reminder_checker",
    replace_existing=True
)

# Helper functions
async def get_user_by_username(username: str):
    return await users_collection.find_one({"username": username})

async def create_user(username: str):
    """Create a new user with duplicate username handling"""
    try:
        # Check if username already exists
        existing_user = await users_collection.find_one({"username": username})
        
        if existing_user:
            # Username exists, suggest alternatives
            base_username = username
            counter = 1
            new_username = f"{base_username}_{counter}"
            
            # Keep trying until we find an available username
            while await users_collection.find_one({"username": new_username}):
                counter += 1
                new_username = f"{base_username}_{counter}"
            
            # Create user with modified username
            user_data = {
                "username": new_username,
                "original_username": username,  # Store the original username for reference
                "created_at": datetime.utcnow(),
                "last_active": datetime.utcnow(),
                "custom_audio_url": None
            }
            
            result = await users_collection.insert_one(user_data)
            user_data["id"] = str(result.inserted_id)
            
            print(f"⚠️ Username '{username}' already exists. Created user with username: '{new_username}'")
            return user_data
        else:
            # Username is available, create normally
            user_data = {
                "username": username,
                "created_at": datetime.utcnow(),
                "last_active": datetime.utcnow(),
                "custom_audio_url": None
            }
            
            result = await users_collection.insert_one(user_data)
            user_data["id"] = str(result.inserted_id)
            
            print(f"✅ Created new user: {username}")
            return user_data
            
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user")

async def cleanup_session_audio(username: str):
    """Clean up custom audio files for a user when session ends"""
    try:
        user_audio_dir = os.path.join(CUSTOM_AUDIO_DIR, username)
        if os.path.exists(user_audio_dir):
            import shutil
            shutil.rmtree(user_audio_dir)
            print(f"🗑️ Cleaned up audio files for {username}")
            
            # Clear custom audio URL from database
            await users_collection.update_one(
                {"username": username},
                {"$unset": {"custom_audio_url": ""}}
            )
            print(f"🗑️ Cleared custom audio URL for {username}")
    except Exception as e:
        print(f"⚠️ Error cleaning up audio files for {username}: {e}")

@app.get("/")
async def root():
    return {"message": "FocusGuard API is running!"}

@app.post("/users/", response_model=UserResponse)
async def create_or_get_user(user: UserCreate):
    """Create or get user with duplicate username handling"""
    try:
        # Check if user exists
        existing_user = await users_collection.find_one({"username": user.username})
        
        if existing_user:
            # User exists, update last_active and return
            await users_collection.update_one(
                {"username": user.username},
                {"$set": {"last_active": datetime.utcnow()}}
            )
            existing_user["id"] = str(existing_user["_id"])
            print(f"✅ User logged in: {user.username}")
            return existing_user
        else:
            # User doesn't exist, create new user
            new_user = await create_user(user.username)
            
            # Check if username was modified
            if new_user.get("original_username"):
                # Username was modified, return with warning
                return {
                    **new_user,
                    "username_modified": True,
                    "original_username": new_user["original_username"],
                    "message": f"Username '{new_user['original_username']}' was already taken. Your username is now '{new_user['username']}'"
                }
            else:
                # Username was not modified
                return {
                    **new_user,
                    "username_modified": False,
                    "message": f"Welcome {new_user['username']}!"
                }
                
    except Exception as e:
        print(f"❌ Error in create_or_get_user: {e}")
        raise HTTPException(status_code=500, detail="Failed to create or get user")

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
        user_distraction_tracking[username]["repeated_notification_count"] = 0
        user_distraction_tracking[username]["last_distracting_window"] = ""
        user_distraction_tracking[username]["notification_sent_at"] = datetime.utcnow()
        user_distraction_tracking[username]["last_notification_time"] = datetime.utcnow() # Reset last_notification_time
    else:
        # Initialize tracking for new user
        user_distraction_tracking[username] = {
            "count": 0,
            "session_id": str(result.inserted_id),
            "last_reset": datetime.utcnow(),
            "last_distraction_active": False,
            "last_distracting_window": "",
            "notification_sent_at": datetime.utcnow(),
            "repeated_notification_count": 0,
            "last_notification_time": datetime.utcnow() # Initialize last_notification_time
        }
    
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

# ENABLED: Enhanced endpoint for notifications on distractions
@app.post("/sessions/{session_id}/activity/enhanced", response_model=ActivityLogResponse)
async def monitor_activity_enhanced(session_id: str, activity_log: ActivityLogCreate):
    """Enhanced activity monitoring endpoint - sends notifications for distractions"""
    return await monitor_activity_realtime(session_id, activity_log)

# NEW: Window monitor endpoint that logs activity without triggering notifications
@app.post("/sessions/{session_id}/activity/log-only", response_model=ActivityLogResponse)
async def log_activity_only(session_id: str, activity_log: ActivityLogCreate):
    """Log activity without triggering notifications - for window monitor use"""
    
    # Validate ObjectId
    if not ObjectId.is_valid(session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID")
    
    # Find session
    session = await sessions_collection.find_one({"_id": ObjectId(session_id)})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    username = session["username"]
    
    # Classify the activity using AI
    classification, confidence, is_distraction = classifier.classify_content(activity_log.window_title)
    
    # Get sentiment analysis
    sentiment, sentiment_score = classifier.analyze_sentiment(activity_log.window_title)
    
    # Generate reasoning
    reasoning = classifier._generate_reasoning(activity_log.window_title, classification, confidence, sentiment)
    
    # Create activity log entry with all required fields
    activity_data = {
        "user_id": session["user_id"],
        "username": username,
        "session_id": session_id,
        "window_title": activity_log.window_title,
        "classification": classification,
        "confidence": confidence,
        "is_distraction": is_distraction,
        "sentiment": sentiment,
        "sentiment_score": sentiment_score,
        "reasoning": reasoning,
        "timestamp": datetime.utcnow(),
        "created_at": datetime.utcnow()
    }
    
    result = await activity_collection.insert_one(activity_data)
    activity_data["id"] = str(result.inserted_id)
    
    # Log the activity but don't trigger notifications
    print(f"📝 Activity logged for {username}: {activity_log.window_title} ({classification})")
    
    return ActivityLogResponse(**activity_data)



# MAIN ENHANCEMENT: Real-time activity monitoring endpoint
@app.post("/sessions/{session_id}/monitor-activity", response_model=ActivityLogResponse)
async def monitor_activity_realtime(session_id: str, activity_log: ActivityLogCreate):
    """Monitor user activity in real-time and send smart notifications for distractions"""
    
    # Validate ObjectId
    if not ObjectId.is_valid(session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID")
    
    # Find session
    session = await sessions_collection.find_one({"_id": ObjectId(session_id)})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    username = session["username"]
    
    # Classify the activity using advanced AI
    detailed_analysis = classifier.get_detailed_analysis(activity_log.window_title)
    classification = detailed_analysis["classification"]
    confidence = detailed_analysis["confidence"]
    is_distraction = detailed_analysis["is_distraction"]
    sentiment = detailed_analysis["sentiment"]
    sentiment_score = detailed_analysis["sentiment_score"]
    reasoning = detailed_analysis["reasoning"]
    
    # Debug logging for classification
    print(f"🔍 Classification for '{activity_log.window_title}': {classification} (confidence: {confidence:.2f}, distraction: {is_distraction})")
    print(f"💭 Reasoning: {reasoning}")
    
    # Create activity log entry with enhanced data
    activity_data = {
        "user_id": session["user_id"],
        "username": username,
        "session_id": session_id,
        "window_title": activity_log.window_title,
        "classification": classification,
        "confidence": confidence,
        "is_distraction": is_distraction,
        "sentiment": sentiment,
        "sentiment_score": sentiment_score,
        "reasoning": reasoning,
        "timestamp": datetime.utcnow(),
        "created_at": datetime.utcnow()
    }
    
    result = await activity_collection.insert_one(activity_data)
    activity_data["id"] = str(result.inserted_id)
    
    # Enhanced distraction notification logic
    # Initialize or get user tracking
    if username not in user_distraction_tracking:
        user_distraction_tracking[username] = {
            "count": 0,
            "session_id": session_id,
            "last_reset": datetime.utcnow(),
            "last_distraction_active": False,
            "last_distracting_window": "",
            "notification_sent_at": datetime.utcnow(),
            "repeated_notification_count": 0,
            "last_notification_time": datetime.utcnow() # Initialize last_notification_time
        }

    current_tracking = user_distraction_tracking[username]
    
    # Check if this is a new session
    if current_tracking["session_id"] != session_id:
        current_tracking["count"] = 0
        current_tracking["session_id"] = session_id
        current_tracking["last_reset"] = datetime.utcnow()
        current_tracking["repeated_notification_count"] = 0
        current_tracking["last_distracting_window"] = ""
        current_tracking["notification_sent_at"] = datetime.utcnow()
        current_tracking["last_notification_time"] = datetime.utcnow() # Reset last_notification_time

    if is_distraction:
        print(f"🚨 DISTRACTION DETECTED for {username}: {activity_log.window_title}")
        
        # Check if window title has changed (new distraction)
        window_changed = current_tracking["last_distracting_window"] != activity_log.window_title
        
        # Check if we should send a notification
        should_send_notification = False
        
        # Throttle notifications based on last_notification_time
        time_since_last_notification = datetime.utcnow() - current_tracking["last_notification_time"]
        
        if time_since_last_notification > timedelta(seconds=NOTIFICATION_THROTTLE_SECONDS):
            if window_changed:
                # New distracting window - always send notification
                should_send_notification = True
                current_tracking["last_distracting_window"] = activity_log.window_title
                current_tracking["repeated_notification_count"] = 0
                current_tracking["notification_sent_at"] = datetime.utcnow()
                current_tracking["last_notification_time"] = datetime.utcnow() # Update last_notification_time
                print(f"📱 New distracting window detected for {username}: {activity_log.window_title}")
            else:
                # Same distracting window - check if we should send repeated notification
                time_since_last_repeated_notification = datetime.utcnow() - current_tracking["last_notification_time"]
                
                # Send repeated notification every 2 seconds if still on distracting content
                if time_since_last_repeated_notification > timedelta(seconds=REPEATED_NOTIFICATION_INTERVAL):
                    should_send_notification = True
                    current_tracking["repeated_notification_count"] += 1
                    current_tracking["notification_sent_at"] = datetime.utcnow()
                    current_tracking["last_notification_time"] = datetime.utcnow() # Update last_notification_time
                    print(f"🔄 Sending repeated notification #{current_tracking['repeated_notification_count']} for {username}")
        
        if should_send_notification:
            # Send distraction notification
            notification = await send_distraction_notification(username, activity_log.window_title, session_id)
            current_tracking["last_distraction_active"] = True
            
            if notification:
                await sessions_collection.update_one(
                    {"_id": ObjectId(session_id)},
                    {"$inc": {"distraction_count": 1}}
                )
                print(f"✅ Notification sent and session updated for {username}")
            else:
                print(f"❌ Failed to send notification for {username}")
        else:
            print(f"⏳ Skipping notification for {username} - too soon since last notification")
            
    else:
        # Not a distraction - user switched to productive content
        if current_tracking["last_distraction_active"]:
            print(f"✅ User {username} switched to productive content: {activity_log.window_title}")
            # Reset distraction tracking since user is now productive
            current_tracking["last_distraction_active"] = False
            current_tracking["repeated_notification_count"] = 0
            current_tracking["last_distracting_window"] = ""
            current_tracking["notification_sent_at"] = datetime.utcnow()
            current_tracking["last_notification_time"] = datetime.utcnow() # Reset last_notification_time

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
    print(f"🔍 Active connections count: {len(active_connections)}")
    print(f"🔍 Active users: {list(active_connections.keys())}")
    
    try:
        while True:
            # Keep connection alive and listen for any messages
            data = await websocket.receive_text()
            
            # Handle incoming messages
            try:
                message = json.loads(data)
                if message.get("type") == "heartbeat":
                    await websocket.send_text(json.dumps({"type": "heartbeat_response", "status": "ok"}))
                    print(f"💓 Heartbeat received from {username}")
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
            print(f"🔍 Active connections count: {len(active_connections)}")
            print(f"🔍 Active users: {list(active_connections.keys())}")
    except Exception as e:
        print(f"⚠️ WebSocket error for {username}: {e}")
        if username in active_connections:
            del active_connections[username]
            print(f"🔍 Active connections count: {len(active_connections)}")
            print(f"🔍 Active users: {list(active_connections.keys())}")

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
    """Mark a session as completed and cleanup resources"""
    if not ObjectId.is_valid(session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID")
    
    session = await sessions_collection.find_one({"_id": ObjectId(session_id)})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Update session as completed
    end_time = datetime.utcnow()
    await sessions_collection.update_one(
        {"_id": ObjectId(session_id)},
        {
            "$set": {
                "completed": True,
                "end_time": end_time
            }
        }
    )
    
    # Clean up custom audio files for this user
    username = session.get("username")
    if username:
        await cleanup_session_audio(username)
    
    return {"message": "Session completed successfully", "session_id": session_id}

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

# Get current distraction status and tracking info
@app.get("/users/{username}/distraction-status")
async def get_distraction_status(username: str):
    """Get current distraction status and tracking information"""
    user = await get_user_by_username(username)
    if not user:
        user = await create_user(username)
    
    current_tracking = user_distraction_tracking.get(username, {
        "count": 0,
        "session_id": None,
        "last_reset": datetime.utcnow(),
        "last_distraction_active": False,
        "last_distracting_window": "",
        "notification_sent_at": datetime.utcnow(),
        "repeated_notification_count": 0
    })
    
    # Check if user has custom audio
    custom_audio_url = user.get("custom_audio_url")
    
    return {
        "username": username,
        "current_distraction_count": current_tracking["count"],
        "current_session_id": current_tracking.get("session_id"),
        "last_reset": current_tracking["last_reset"],
        "last_distraction_active": current_tracking["last_distraction_active"],
        "last_distracting_window": current_tracking["last_distracting_window"],
        "repeated_notification_count": current_tracking["repeated_notification_count"],
        "has_custom_audio": custom_audio_url is not None,
        "custom_audio_url": custom_audio_url,
        "next_sound_type": "custom" if (current_tracking["count"] > 2 and custom_audio_url) else "default",
        "status": "productive" if not current_tracking["last_distraction_active"] else "distracted"
    }

# DEBUGGING: Add test endpoint
@app.post("/test-notification/{username}")
async def test_notification(username: str):
    """Test notification system"""
    if username in active_connections:
        try:
            test_notification = {
                "type": "notification",  # Changed to match frontend expectation
                "data": {
                    "id": str(uuid.uuid4()),
                    "message": "🧪 Test notification - your notification system is working!",
                    "notification_type": "distraction",
                    "sound_type": "default",
                    "custom_audio_url": None,
                    "created_at": datetime.utcnow().isoformat(),
                    "window_title": "Test Window",
                    "distraction_count": 1,
                    "repeated_notification_count": 0,
                    "read": False
                }
            }
            
            await active_connections[username].send_text(json.dumps(test_notification))
            return {"message": f"Test notification sent to {username}"}
        except Exception as e:
            return {"error": f"Failed to send test notification: {e}"}
    else:
        return {"error": f"No active WebSocket connection for {username}"}

# Test endpoint for creating reminder notifications
@app.post("/test-reminder/{username}")
async def test_reminder_notification(username: str):
    """Test reminder notification system"""
    if username in active_connections:
        try:
            reminder_notification = {
                "type": "notification",
                "data": {
                    "id": str(uuid.uuid4()),
                    "message": "⏰ Reminder: Take a short break and stretch!",
                    "notification_type": "reminder",
                    "sound_type": "default",
                    "custom_audio_url": None,
                    "created_at": datetime.utcnow().isoformat(),
                    "reminder_id": "test-reminder",
                    "reminder_time": "now",
                    "read": False
                }
            }
            
            await active_connections[username].send_text(json.dumps(reminder_notification))
            return {"message": f"Reminder notification sent to {username}"}
        except Exception as e:
            return {"error": f"Failed to send reminder notification: {e}"}
    else:
        return {"error": f"No active WebSocket connection for {username}"}

# Test endpoint to trigger reminder check immediately
@app.post("/test-reminder-check")
async def test_reminder_check():
    """Test reminder check system immediately"""
    try:
        await check_and_send_reminders()
        return {"message": "Reminder check completed"}
    except Exception as e:
        return {"error": f"Reminder check failed: {e}"}

# Debug endpoint to check stored reminders
@app.get("/debug/reminders/{username}")
async def debug_reminders(username: str):
    """Debug endpoint to check stored reminders for a user"""
    try:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        current_time = datetime.utcnow().strftime("%H:%M")
        
        plan = await plans_collection.find_one({"username": username, "date": today})
        
        if not plan:
            return {
                "username": username,
                "date": today,
                "current_time": current_time,
                "plan_exists": False,
                "reminders": []
            }
        
        reminders = plan.get("reminders", [])
        
        return {
            "username": username,
            "date": today,
            "current_time": current_time,
            "plan_exists": True,
            "reminders": reminders,
            "reminder_count": len(reminders),
            "active_reminders": [r for r in reminders if not r.get("completed", False)]
        }
        
    except Exception as e:
        return {"error": f"Debug failed: {e}"}

# Cleanup endpoint to fix corrupted reminder times
@app.post("/cleanup/reminders/{username}")
async def cleanup_reminders(username: str):
    """Clean up corrupted reminder times for a user"""
    try:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        
        plan = await plans_collection.find_one({"username": username, "date": today})
        
        if not plan:
            return {"message": "No plan found for today"}
        
        reminders = plan.get("reminders", [])
        cleaned_reminders = []
        fixed_count = 0
        
        for reminder in reminders:
            original_time = reminder.get("time", "")
            cleaned_time = original_time.strip()
            
            # Fix corrupted time format
            if len(cleaned_time) > 5:
                cleaned_time = cleaned_time[:5]
                fixed_count += 1
            
            # Validate time format
            try:
                datetime.strptime(cleaned_time, "%H:%M")
            except ValueError:
                # Skip invalid times
                continue
            
            cleaned_reminder = {
                **reminder,
                "time": cleaned_time
            }
            cleaned_reminders.append(cleaned_reminder)
        
        # Update the plan with cleaned reminders
        await plans_collection.update_one(
            {"username": username, "date": today},
            {
                "$set": {
                    "reminders": cleaned_reminders,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {
            "message": f"Cleaned {fixed_count} corrupted reminder times",
            "original_count": len(reminders),
            "cleaned_count": len(cleaned_reminders)
        }
        
    except Exception as e:
        return {"error": f"Cleanup failed: {e}"}

# Custom audio upload endpoint
@app.post("/users/{username}/upload-custom-audio")
async def upload_custom_audio(username: str, audio_file: UploadFile = File(...)):
    """Upload custom audio file for notifications"""
    
    # Validate user exists
    user = await get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate file type
    if not audio_file.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="File must be an audio file")
    
    # Validate file size (max 5MB)
    if audio_file.size > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be less than 5MB")
    
    try:
        # Create user-specific audio directory
        user_audio_dir = os.path.join(CUSTOM_AUDIO_DIR, username)
        if not os.path.exists(user_audio_dir):
            os.makedirs(user_audio_dir)
        
        # Save audio file
        file_extension = audio_file.filename.split('.')[-1] if '.' in audio_file.filename else 'mp3'
        filename = f"custom_notification.{file_extension}"
        file_path = os.path.join(user_audio_dir, filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
        
        # Update user's custom audio URL in database
        custom_audio_url = f"http://localhost:8000/custom_audio/{username}/{filename}"
        await users_collection.update_one(
            {"username": username},
            {"$set": {"custom_audio_url": custom_audio_url}}
        )
        
        print(f"✅ Custom audio uploaded for {username}: {custom_audio_url}")
        print(f"📁 File saved at: {file_path}")
        
        return {
            "message": "Custom audio uploaded successfully",
            "custom_audio_url": custom_audio_url,
            "filename": filename
        }
        
    except Exception as e:
        print(f"❌ Error uploading custom audio: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload audio file")
    finally:
        audio_file.file.close()

# Get user's custom audio URL
@app.get("/users/{username}/custom-audio")
async def get_custom_audio(username: str):
    """Get user's custom audio URL"""
    user = await get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    custom_audio_url = user.get("custom_audio_url")
    return {
        "username": username,
        "custom_audio_url": custom_audio_url,
        "has_custom_audio": custom_audio_url is not None
    }

@app.get("/debug/websocket-status")
async def get_websocket_status():
    """Debug endpoint to check WebSocket connection status"""
    return {
        "active_connections_count": len(active_connections),
        "active_users": list(active_connections.keys()),
        "connection_details": {
            username: {
                "connected": True,
                "websocket_info": str(websocket)
            } for username, websocket in active_connections.items()
        }
    }

@app.get("/debug/custom-audio/{username}")
async def debug_custom_audio(username: str):
    """Debug endpoint to check custom audio status for a user"""
    try:
        user = await get_user_by_username(username)
        if not user:
            return {"error": "User not found"}
        
        custom_audio_url = user.get("custom_audio_url")
        user_audio_dir = os.path.join(CUSTOM_AUDIO_DIR, username)
        
        # Check if directory exists
        dir_exists = os.path.exists(user_audio_dir)
        
        # Check if files exist in directory
        files_in_dir = []
        if dir_exists:
            try:
                files_in_dir = os.listdir(user_audio_dir)
            except Exception as e:
                files_in_dir = [f"Error listing files: {e}"]
        
        # Check if the specific audio file exists
        audio_file_exists = False
        if custom_audio_url and custom_audio_url.endswith('.mp3'):
            filename = custom_audio_url.split('/')[-1]
            audio_file_path = os.path.join(user_audio_dir, filename)
            audio_file_exists = os.path.exists(audio_file_path)
        
        return {
            "username": username,
            "custom_audio_url": custom_audio_url,
            "has_custom_audio_url": custom_audio_url is not None,
            "audio_directory_exists": dir_exists,
            "audio_directory_path": user_audio_dir,
            "files_in_directory": files_in_dir,
            "audio_file_exists": audio_file_exists,
            "custom_audio_dir": CUSTOM_AUDIO_DIR
        }
    except Exception as e:
        return {"error": f"Debug failed: {e}"}

# Daily Plan Models
class TaskCreate(BaseModel):
    id: Optional[str] = None
    text: str
    completed: bool = False

class ReminderCreate(BaseModel):
    id: Optional[str] = None
    text: str
    time: str
    completed: bool = False

class DailyPlanCreate(BaseModel):
    tasks: List[TaskCreate] = []
    reminders: List[ReminderCreate] = []

class DailyPlanResponse(BaseModel):
    id: str
    username: str
    date: str
    tasks: List[dict]
    reminders: List[dict]
    completed: bool
    created_at: datetime
    updated_at: datetime

# Daily Plan endpoints
@app.get("/users/{username}/plans/enhanced/{date}", response_model=DailyPlanResponse)
async def get_daily_plan(username: str, date: str):
    """Get daily plan for a specific date"""
    user = await get_user_by_username(username)
    if not user:
        user = await create_user(username)
    
    plan = await plans_collection.find_one({"username": username, "date": date})
    if plan:
        plan["id"] = str(plan["_id"])
        return plan
    else:
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

@app.put("/users/{username}/plans/enhanced/{date}", response_model=DailyPlanResponse)
async def update_daily_plan(username: str, date: str, plan_data: DailyPlanCreate):
    """Create or update daily plan"""
    print(f"🔄 Updating plan for {username} on {date}")
    print(f"📊 Received tasks count: {len(plan_data.tasks)}")
    print(f"⏰ Received reminders count: {len(plan_data.reminders)}")
    
    user = await get_user_by_username(username)
    if not user:
        user = await create_user(username)
    
    # Check if plan exists
    existing_plan = await plans_collection.find_one({"username": username, "date": date})
    
    if existing_plan:
        print(f"📋 Found existing plan with {len(existing_plan.get('tasks', []))} tasks and {len(existing_plan.get('reminders', []))} reminders")
    else:
        print("📋 No existing plan found, creating new one")
    
    # Convert tasks and reminders to proper format with generated IDs
    tasks = []
    for task in plan_data.tasks:
        # If task has an existing ID, preserve it; otherwise generate new one
        task_id = task.id if task.id else str(uuid.uuid4())
        task_dict = {
            "id": task_id,
            "text": task.text,
            "completed": task.completed
        }
        tasks.append(task_dict)
    
    reminders = []
    for reminder in plan_data.reminders:
        # If reminder has an existing ID, preserve it; otherwise generate new one
        reminder_id = reminder.id if reminder.id else str(uuid.uuid4())
        
        # Clean the time format
        cleaned_time = reminder.time.strip()
        if len(cleaned_time) > 5:
            cleaned_time = cleaned_time[:5]
        
        reminder_dict = {
            "id": reminder_id,
            "text": reminder.text,
            "time": cleaned_time,
            "completed": reminder.completed
        }
        reminders.append(reminder_dict)
    
    print(f"✅ Processed {len(tasks)} tasks and {len(reminders)} reminders")
    
    if existing_plan:
        # Update existing plan - replace entirely to handle deletions properly
        result = await plans_collection.update_one(
            {"username": username, "date": date},
            {
                "$set": {
                    "tasks": tasks,
                    "reminders": reminders,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        print(f"✅ Updated existing plan: {result.modified_count} documents modified")
        plan = await plans_collection.find_one({"username": username, "date": date})
    else:
        # Create new plan
        plan_data_dict = {
            "username": username,
            "date": date,
            "tasks": tasks,
            "reminders": reminders,
            "completed": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        result = await plans_collection.insert_one(plan_data_dict)
        print(f"✅ Created new plan with ID: {result.inserted_id}")
        plan = await plans_collection.find_one({"_id": result.inserted_id})
    
    plan["id"] = str(plan["_id"])
    return plan

@app.put("/users/{username}/plans/enhanced/{date}/tasks/{task_id}/toggle")
async def toggle_task_completion(username: str, date: str, task_id: str):
    """Toggle task completion status"""
    user = await get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    plan = await plans_collection.find_one({"username": username, "date": date})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Find and toggle the task
    tasks = plan.get("tasks", [])
    task_found = False
    
    for task in tasks:
        if task.get("id") == task_id:
            task["completed"] = not task.get("completed", False)
            task_found = True
            break
    
    if not task_found:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update the plan
    await plans_collection.update_one(
        {"username": username, "date": date},
        {
            "$set": {
                "tasks": tasks,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return {"message": "Task completion toggled successfully"}

# Test endpoint to send a reminder notification immediately
@app.post("/test-reminder/{username}")
async def test_reminder_notification(username: str):
    """Test reminder notification system immediately"""
    try:
        # Create a test reminder
        test_reminder = {
            "id": "test-reminder",
            "text": "Test reminder notification",
            "time": "test",
            "completed": False
        }
        
        print(f"🧪 Sending test reminder notification for {username}")
        await send_reminder_notification(username, test_reminder)
        
        return {"message": f"Test reminder notification sent to {username}"}
    except Exception as e:
        return {"error": f"Test reminder failed: {e}"}

# Debug endpoint to check MongoDB data
@app.get("/debug/mongodb-status")
async def debug_mongodb_status():
    """Debug endpoint to check MongoDB connection and data status"""
    try:
        # Test connection
        await client.admin.command('ping')
        connection_status = "✅ Connected"
    except Exception as e:
        connection_status = f"❌ Connection failed: {e}"
        return {"error": connection_status}
    
    # Get collection counts
    try:
        user_count = await users_collection.count_documents({})
        session_count = await sessions_collection.count_documents({})
        plan_count = await plans_collection.count_documents({})
        activity_count = await activity_collection.count_documents({})
        notification_count = await notifications_collection.count_documents({})
        progress_count = await progress_collection.count_documents({})
        
        return {
            "mongodb_connection": connection_status,
            "collections": {
                "users": user_count,
                "focus_sessions": session_count,
                "daily_plans": plan_count,
                "activity_logs": activity_count,
                "notifications": notification_count,
                "progress_tracking": progress_count
            },
            "total_documents": user_count + session_count + plan_count + activity_count + notification_count + progress_count
        }
    except Exception as e:
        return {"error": f"Failed to get collection counts: {e}"}

# Debug endpoint to check specific user data
@app.get("/debug/user-data/{username}")
async def debug_user_data(username: str):
    """Debug endpoint to check all data for a specific user"""
    try:
        # Get user
        user = await users_collection.find_one({"username": username})
        if not user:
            return {"error": f"User {username} not found"}
        
        # Get user's sessions
        user_sessions = await sessions_collection.find({"username": username}).to_list(length=10)
        
        # Get user's plans
        user_plans = await plans_collection.find({"username": username}).to_list(length=10)
        
        # Get user's activities
        user_activities = await activity_collection.find({"username": username}).to_list(length=10)
        
        # Get user's notifications
        user_notifications = await notifications_collection.find({"username": username}).to_list(length=10)
        
        # Get user's progress
        user_progress = await progress_collection.find({"username": username}).to_list(length=10)
        
        return {
            "user": {
                "username": user.get("username"),
                "created_at": user.get("created_at"),
                "last_active": user.get("last_active"),
                "custom_audio_url": user.get("custom_audio_url")
            },
            "data_counts": {
                "sessions": len(user_sessions),
                "plans": len(user_plans),
                "activities": len(user_activities),
                "notifications": len(user_notifications),
                "progress_entries": len(user_progress)
            },
            "recent_data": {
                "sessions": user_sessions,
                "plans": user_plans,
                "activities": user_activities,
                "notifications": user_notifications,
                "progress": user_progress
            }
        }
    except Exception as e:
        return {"error": f"Failed to get user data: {e}"}

# Debug endpoint to check recent activity
@app.get("/debug/recent-activity")
async def debug_recent_activity():
    """Debug endpoint to check recent activity across all users"""
    try:
        from datetime import datetime, timedelta
        
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        # Recent sessions
        recent_sessions = await sessions_collection.find({
            "start_time": {"$gte": yesterday}
        }).to_list(length=10)
        
        # Recent activities
        recent_activities = await activity_collection.find({
            "timestamp": {"$gte": yesterday}
        }).to_list(length=10)
        
        # Recent notifications
        recent_notifications = await notifications_collection.find({
            "created_at": {"$gte": yesterday}
        }).to_list(length=10)
        
        return {
            "recent_activity": {
                "sessions": len(recent_sessions),
                "activities": len(recent_activities),
                "notifications": len(recent_notifications)
            },
            "data": {
                "sessions": recent_sessions,
                "activities": recent_activities,
                "notifications": recent_notifications
            }
        }
    except Exception as e:
        return {"error": f"Failed to get recent activity: {e}"}

# Debug endpoint to check username availability
@app.get("/debug/check-username/{username}")
async def check_username_availability(username: str):
    """Debug endpoint to check if a username is available and suggest alternatives"""
    try:
        # Check if username exists
        existing_user = await users_collection.find_one({"username": username})
        
        if existing_user:
            # Username exists, suggest alternatives
            base_username = username
            suggestions = []
            
            for i in range(1, 6):  # Suggest 5 alternatives
                suggestion = f"{base_username}_{i}"
                suggestion_exists = await users_collection.find_one({"username": suggestion})
                if not suggestion_exists:
                    suggestions.append(suggestion)
            
            return {
                "username": username,
                "available": False,
                "message": f"Username '{username}' is already taken",
                "suggestions": suggestions,
                "existing_user": {
                    "id": str(existing_user["_id"]),
                    "created_at": existing_user["created_at"],
                    "last_active": existing_user["last_active"]
                }
            }
        else:
            # Username is available
            return {
                "username": username,
                "available": True,
                "message": f"Username '{username}' is available",
                "suggestions": []
            }
            
    except Exception as e:
        return {"error": f"Failed to check username: {e}"}

# Debug endpoint to list all usernames
@app.get("/debug/list-usernames")
async def list_all_usernames():
    """Debug endpoint to list all usernames in the database"""
    try:
        users = await users_collection.find({}, {"username": 1, "created_at": 1, "_id": 0}).to_list(length=None)
        
        return {
            "total_users": len(users),
            "usernames": [user["username"] for user in users],
            "users_with_dates": [
                {
                    "username": user["username"],
                    "created_at": user["created_at"]
                } for user in users
            ]
        }
    except Exception as e:
        return {"error": f"Failed to list usernames: {e}"}

class FeedbackCreate(BaseModel):
    subject: str
    message: str
    category: str = "general"  # general, bug, feature, other
    priority: str = "medium"   # low, medium, high, urgent

class FeedbackResponse(BaseModel):
    id: str
    username: str
    subject: str
    message: str
    category: str
    priority: str
    status: str = "pending"  # pending, reviewed, resolved
    created_at: datetime
    admin_response: Optional[str] = None
    responded_at: Optional[datetime] = None

# Feedback endpoints
@app.post("/users/{username}/feedback", response_model=FeedbackResponse)
async def submit_feedback(username: str, feedback: FeedbackCreate):
    """Submit feedback from a user"""
    try:
        # Verify user exists
        user = await users_collection.find_one({"username": username})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Create feedback document
        feedback_data = {
            "username": username,
            "subject": feedback.subject,
            "message": feedback.message,
            "category": feedback.category,
            "priority": feedback.priority,
            "status": "pending",
            "created_at": datetime.utcnow(),
            "admin_response": None,
            "responded_at": None
        }
        
        result = await feedback_collection.insert_one(feedback_data)
        feedback_data["id"] = str(result.inserted_id)
        
        print(f"📝 Feedback submitted by {username}: {feedback.subject}")
        return feedback_data
        
    except Exception as e:
        print(f"❌ Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")

# NEW: Cross-platform window monitoring endpoints
@app.get("/window-monitor/status")
async def get_window_monitor_status():
    """Get the status of the cross-platform window monitor"""
    if not window_monitor:
        return {
            "available": False,
            "system": "Unknown",
            "message": "Window monitoring not available"
        }
    
    return {
        "available": True,
        "system": window_monitor.system,
        "windows_available": WINDOWS_AVAILABLE,
        "linux_available": LINUX_AVAILABLE,
        "last_window_title": window_monitor.last_window_title,
        "message": f"Window monitoring available for {window_monitor.system}"
    }

@app.get("/window-monitor/current-window")
async def get_current_window():
    """Get the currently active window title"""
    if not window_monitor:
        raise HTTPException(status_code=503, detail="Window monitoring not available")
    
    try:
        window_title = window_monitor.get_active_window_title()
        window_info = window_monitor.get_window_info()
        
        return {
            "window_title": window_title,
            "process_name": window_info["name"],
            "process_exe": window_info["exe"],
            "system": window_monitor.system,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get current window: {e}")

@app.post("/window-monitor/start-monitoring/{username}")
async def start_window_monitoring(username: str, session_id: str):
    """Start monitoring the current user's active windows"""
    if not window_monitor:
        raise HTTPException(status_code=503, detail="Window monitoring not available")
    
    # Validate session
    if not ObjectId.is_valid(session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID")
    
    session = await sessions_collection.find_one({"_id": ObjectId(session_id)})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session["username"] != username:
        raise HTTPException(status_code=403, detail="Session does not belong to user")
    
    try:
        # Get current window and classify it
        window_title = window_monitor.get_active_window_title()
        window_info = window_monitor.get_window_info()
        
        # Classify the activity using AI
        detailed_analysis = classifier.get_detailed_analysis(window_title)
        
        # Create activity log entry
        activity_data = {
            "user_id": session["user_id"],
            "username": username,
            "session_id": session_id,
            "window_title": window_title,
            "classification": detailed_analysis["classification"],
            "confidence": detailed_analysis["confidence"],
            "is_distraction": detailed_analysis["is_distraction"],
            "sentiment": detailed_analysis["sentiment"],
            "sentiment_score": detailed_analysis["sentiment_score"],
            "reasoning": detailed_analysis["reasoning"],
            "timestamp": datetime.utcnow(),
            "created_at": datetime.utcnow()
        }
        
        result = await activity_collection.insert_one(activity_data)
        activity_data["id"] = str(result.inserted_id)
        
        # Handle notifications if it's a distraction
        if detailed_analysis["is_distraction"]:
            await send_distraction_notification(username, window_title, session_id)
        
        return {
            "message": "Window monitoring started",
            "current_window": {
                "title": window_title,
                "process": window_info["name"],
                "classification": detailed_analysis["classification"],
                "is_distraction": detailed_analysis["is_distraction"],
                "confidence": detailed_analysis["confidence"]
            },
            "session_id": session_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start monitoring: {e}")

@app.post("/window-monitor/check-window/{username}")
async def check_current_window(username: str, session_id: str):
    """Check the current window and log activity if needed"""
    if not window_monitor:
        raise HTTPException(status_code=503, detail="Window monitoring not available")
    
    # Validate session
    if not ObjectId.is_valid(session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID")
    
    session = await sessions_collection.find_one({"_id": ObjectId(session_id)})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session["username"] != username:
        raise HTTPException(status_code=403, detail="Session does not belong to user")
    
    try:
        # Get current window
        current_title = window_monitor.get_active_window_title()
        current_time = time.time()
        
        # Check if we should send activity data
        should_send, reason = window_monitor.should_send_activity(current_title, current_time)
        
        if should_send:
            # Classify the activity using AI
            detailed_analysis = classifier.get_detailed_analysis(current_title)
            
            # Create activity log entry
            activity_data = {
                "user_id": session["user_id"],
                "username": username,
                "session_id": session_id,
                "window_title": current_title,
                "classification": detailed_analysis["classification"],
                "confidence": detailed_analysis["confidence"],
                "is_distraction": detailed_analysis["is_distraction"],
                "sentiment": detailed_analysis["sentiment"],
                "sentiment_score": detailed_analysis["sentiment_score"],
                "reasoning": detailed_analysis["reasoning"],
                "timestamp": datetime.utcnow(),
                "created_at": datetime.utcnow()
            }
            
            result = await activity_collection.insert_one(activity_data)
            activity_data["id"] = str(result.inserted_id)
            
            # Handle notifications if it's a distraction
            if detailed_analysis["is_distraction"]:
                await send_distraction_notification(username, current_title, session_id)
            
            # Update tracking
            window_monitor.last_window_title = current_title
            window_monitor.last_check_time = current_time
            
            return {
                "window_changed": True,
                "reason": reason,
                "current_window": {
                    "title": current_title,
                    "classification": detailed_analysis["classification"],
                    "is_distraction": detailed_analysis["is_distraction"],
                    "confidence": detailed_analysis["confidence"],
                    "sentiment": detailed_analysis["sentiment"]
                },
                "activity_logged": True,
                "notification_sent": detailed_analysis["is_distraction"]
            }
        else:
            return {
                "window_changed": False,
                "reason": reason,
                "current_window": {
                    "title": current_title
                },
                "activity_logged": False,
                "notification_sent": False
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check window: {e}")

@app.get("/window-monitor/system-info")
async def get_system_info():
    """Get system information for window monitoring"""
    try:
        system_info = {
            "system": platform.system(),
            "platform": platform.platform(),
            "architecture": platform.architecture(),
            "processor": platform.processor(),
            "hostname": platform.node(),
            "username": os.environ.get('USER', os.environ.get('USERNAME', 'Unknown')),
            "display": os.environ.get('DISPLAY', 'No Display'),
            "terminal": os.environ.get('TERM', 'Unknown'),
            "python_version": platform.python_version(),
            "window_monitoring_available": WINDOW_MONITORING_AVAILABLE,
            "windows_available": WINDOWS_AVAILABLE,
            "linux_available": LINUX_AVAILABLE
        }
        
        # Check for Linux window manager tools
        if system_info["system"] == "Linux":
            try:
                # Check for xdotool
                result = subprocess.run(['which', 'xdotool'], capture_output=True, text=True)
                system_info["xdotool_available"] = result.returncode == 0
            except:
                system_info["xdotool_available"] = False
            
            try:
                # Check for wmctrl
                result = subprocess.run(['which', 'wmctrl'], capture_output=True, text=True)
                system_info["wmctrl_available"] = result.returncode == 0
            except:
                system_info["wmctrl_available"] = False
        
        return system_info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system info: {e}")





if __name__ == "__main__":
    import uvicorn
    if db is None:
        print("❌ Cannot start server without MongoDB connection")
        exit(1)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
