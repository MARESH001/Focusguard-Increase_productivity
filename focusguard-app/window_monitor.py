#!/usr/bin/env python3
"""
Real Windows Window Monitor for FocusGuard
This script actually monitors the currently active window and sends real data to the API.
"""

import asyncio
import aiohttp
import json
import time
import os
from datetime import datetime, timedelta
import win32gui
import win32process
import win32api
import win32con
import psutil
import re
import motor.motor_asyncio

class RealWindowMonitor:
    def __init__(self, api_base_url="http://localhost:8000", username=None):
        self.api_base_url = api_base_url
        self.username = username
        self.session_id = None
        self.is_monitoring = False
        self.last_window_title = ""
        self.last_check_time = 0
        self.check_interval = 2  # Check every 2 seconds for real-time monitoring
        self.last_distracting_window = None
        self.last_distraction_time = None
        self.distraction_repeat_interval = 2  # Repeat notification every 2 seconds for same distraction
        
    async def get_current_user(self):
        """Get the current user from MongoDB"""
        try:
            # Get MongoDB connection from environment
            mongodb_url = os.getenv("MONGODB_URL")
            if not mongodb_url:
                print("⚠️ MONGODB_URL not set, using default username")
                return "cheerful_soul_44"
            
            # Connect to MongoDB
            client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_url)
            db = client.focusguard
            
            # Get the most recent user
            cursor = db.users.find().sort("created_at", -1).limit(1)
            users = await cursor.to_list(length=1)
            
            if users:
                return users[0]["username"]
            else:
                # Fallback to default username if no users found
                return "cheerful_soul_44"
                
        except Exception as e:
            print(f"Error getting current user from MongoDB: {e}")
            return "cheerful_soul_44"  # Fallback - updated to match current user
    
    async def create_session(self):
        """Create a new session for the current user"""
        if not self.username:
            self.username = await self.get_current_user()
            print(f"🔍 Detected current user: {self.username}")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Create user if doesn't exist
                user_data = {"username": self.username}
                async with session.post(
                    f"{self.api_base_url}/users/",
                    json=user_data
                ) as response:
                    if response.status not in [200, 201]:
                        print(f"❌ Failed to create user: {response.status}")
                        return False
                
                # Create session
                session_data = {"task_description": "Real window monitoring session", "keywords": ["monitoring"], "duration_minutes": 30}
                async with session.post(
                    f"{self.api_base_url}/users/{self.username}/sessions/",
                    json=session_data
                ) as response:
                    if response.status == 200:
                        session_info = await response.json()
                        self.session_id = session_info["id"]
                        print(f"✅ Session created: {self.session_id}")
                        return True
                    else:
                        print(f"❌ Failed to create session: {response.status}")
                        return False
                        
        except Exception as e:
            print(f"❌ Error creating session: {e}")
            return False

    def get_active_window_title(self):
        """Get the title of the currently active window"""
        try:
            # Get the handle of the foreground window
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                # Get the window title
                title = win32gui.GetWindowText(hwnd)
                
                # Get the process name
                try:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    process = psutil.Process(pid)
                    process_name = process.name()
                    
                    # Combine process name and window title for better classification
                    if title:
                        full_title = f"{process_name} - {title}"
                    else:
                        full_title = process_name
                        
                    return full_title
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    return title if title else "Unknown Window"
            else:
                return "No Active Window"
        except Exception as e:
            print(f"Error getting window title: {e}")
            return "Error Getting Window"
    
    def get_window_info(self):
        """Get detailed information about the active window"""
        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                title = win32gui.GetWindowText(hwnd)
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                
                try:
                    process = psutil.Process(pid)
                    process_info = {
                        "name": process.name(),
                        "exe": process.exe(),
                        "cmdline": process.cmdline(),
                        "title": title,
                        "full_title": f"{process.name()} - {title}" if title else process.name()
                    }
                    return process_info
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    return {
                        "name": "Unknown",
                        "exe": "Unknown",
                        "cmdline": [],
                        "title": title,
                        "full_title": title if title else "Unknown Window"
                    }
            else:
                return {
                    "name": "None",
                    "exe": "None",
                    "cmdline": [],
                    "title": "No Active Window",
                    "full_title": "No Active Window"
                }
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
        if (self.last_distracting_window and 
            current_title == self.last_distracting_window):
            return True, "Sending data for repeated distraction notification"
        
        return False, "No change needed"

    async def log_real_activity(self, window_title):
        """Log real window activity to the API - this will trigger smart notifications"""
        if not self.session_id:
            print("❌ No active session")
            return False
            
        try:
            async with aiohttp.ClientSession() as session:
                activity_data = {
                    "session_id": self.session_id,
                    "window_title": window_title
                }
                
                # Use the enhanced endpoint to trigger smart notifications for distractions
                async with session.post(
                    f"{self.api_base_url}/sessions/{self.session_id}/activity/enhanced",
                    json=activity_data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        classification = result.get("classification", "unknown")
                        is_distraction = result.get("is_distraction", False)
                        confidence = result.get("confidence", 0.0)
                        sentiment = result.get("sentiment", "unknown")
                        sentiment_score = result.get("sentiment_score", 0.0)
                        reasoning = result.get("reasoning", "No reasoning provided")
                        
                        status_icon = "⚠️" if is_distraction else "✅"
                        status_text = "DISTRACTION" if is_distraction else "PRODUCTIVE"
                        
                        print(f"{status_icon} {status_text}: {window_title}")
                        print(f"   🎯 Classification: {classification} (confidence: {confidence:.2f})")
                        print(f"   😊 Sentiment: {sentiment} (score: {sentiment_score:.2f})")
                        print(f"   💭 Reasoning: {reasoning}")
                        
                        # Track activity and handle notifications
                        if is_distraction:
                            self.last_distracting_window = window_title
                            self.last_distraction_time = time.time()
                            print(f"   📱 Distraction logged - notification sent!")
                        else:
                            # Reset distraction tracking when productive
                            if self.last_distracting_window:
                                print(f"   🎯 Productive content detected - logging activity")
                                self.last_distracting_window = None
                                self.last_distraction_time = None
                        
                        return True
                    else:
                        print(f"❌ Failed to log activity: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Error logging activity: {e}")
            return False

    async def monitor_real_windows(self, duration_minutes=30):
        """Monitor real windows for a specified duration"""
        print(f"🚀 Starting REAL window monitoring for {duration_minutes} minutes...")
        print(f"📊 Monitoring user: {self.username}")
        print(f"⏰ Check interval: {self.check_interval} seconds")
        print(f"🔄 Distraction repeat interval: {self.distraction_repeat_interval} seconds")
        print(f"🎯 API endpoint: {self.api_base_url}")
        print("=" * 60)
        print("📱 NOTIFICATIONS: Will log activity AND send notifications for distractions")
        print("=" * 60)
        
        # Create a focus session
        if not await self.create_session():
            print("❌ Failed to create focus session. Exiting.")
            return
        
        self.is_monitoring = True
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        print("🔍 Monitoring active windows... (Press Ctrl+C to stop)")
        print("=" * 60)
        
        while self.is_monitoring and time.time() < end_time:
            try:
                # Get current window info
                window_info = self.get_window_info()
                current_title = window_info["full_title"]
                current_time = time.time()
                
                # Check if we should send activity data
                should_send, reason = self.should_send_activity(current_title, current_time)
                
                if should_send:
                    print(f"\n🔄 Window: {current_title}")
                    print(f"   Process: {window_info['name']}")
                    print(f"   Time: {datetime.now().strftime('%H:%M:%S')}")
                    print(f"   Reason: {reason}")
                    
                    # Log the activity (this triggers notifications)
                    await self.log_real_activity(current_title)
                    
                    # Update tracking
                    self.last_window_title = current_title
                    self.last_check_time = current_time
                else:
                    # Show current status without logging
                    if current_title != self.last_window_title:
                        print(f"\n👁️  Window: {current_title} (monitoring, no change)")
                        self.last_window_title = current_title
                
                # Wait before next check
                await asyncio.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                print("\n⏹️  Monitoring stopped by user")
                break
            except Exception as e:
                print(f"❌ Error during monitoring: {e}")
                await asyncio.sleep(self.check_interval)
        
        self.is_monitoring = False
        print("=" * 60)
        print("🏁 Real window monitoring completed!")

    async def test_single_window(self):
        """Test the system with current window"""
        print("🧪 Testing with current active window...")
        
        window_info = self.get_window_info()
        current_title = window_info["full_title"]
        
        print(f"Current window: {current_title}")
        print(f"Process: {window_info['name']}")
        print(f"Executable: {window_info['exe']}")
        
        # Create session and test
        if await self.create_session():
            await self.log_real_activity(current_title)
        else:
            print("❌ Failed to create test session")

async def main():
    """Main function to run the real window monitor"""
    print("🎯 FocusGuard REAL Window Monitor")
    print("=" * 40)
    
        # Configuration
    api_url = "http://localhost:8000"
    username = "cheerful_soul_44" # This will be overridden by get_current_user
    duration = 5  # minutes
    
    monitor = RealWindowMonitor(api_url, username)
    
    try:
        # Test with current window first
        await monitor.test_single_window()
        
        print("\n" + "=" * 40)
        
        # Start real monitoring
        await monitor.monitor_real_windows(duration)
        
    except KeyboardInterrupt:
        print("\n⏹️  Monitoring stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
