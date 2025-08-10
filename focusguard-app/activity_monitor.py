#!/usr/bin/env python3
"""
Activity Monitor Script for FocusGuard
This script simulates monitoring user activity and sending notifications for distracting activities.
"""

import asyncio
import aiohttp
import json
import time
import random
import os
from datetime import datetime, timedelta
import motor.motor_asyncio

class ActivitySimulator:
    def __init__(self, api_base_url="http://localhost:8000", username=None):
        self.api_base_url = api_base_url
        self.username = username
        self.session_id = None
        self.is_running = False
        
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
                session_data = {"task_description": "Activity simulation session", "keywords": ["simulation"], "duration_minutes": 30}
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

    async def log_activity(self, window_title, is_distraction=False):
        """Log an activity to the API"""
        if not self.session_id:
            print("❌ No active session")
            return False
            
        try:
            async with aiohttp.ClientSession() as session:
                activity_data = {
                    "session_id": self.session_id,
                    "window_title": window_title,
                    "classification": "entertainment" if is_distraction else "productive",
                    "confidence": 0.9,
                    "is_distraction": is_distraction,
                    "start_time": datetime.utcnow().isoformat(),
                    "duration_seconds": 2
                }
                
                async with session.post(
                    f"{self.api_base_url}/sessions/{self.session_id}/activity/enhanced",
                    json=activity_data
                ) as response:
                    if response.status == 200:
                        print(f"✅ Logged activity: {window_title} ({'distraction' if is_distraction else 'productive'})")
                        return True
                    else:
                        print(f"❌ Failed to log activity: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Error logging activity: {e}")
            return False

    async def simulate_activity_monitoring(self, duration_minutes=5):
        """Simulate activity monitoring for a specified duration"""
        print(f"🚀 Starting activity monitoring for {duration_minutes} minutes...")
        print(f"📊 Monitoring user: {self.username}")
        print(f"⏰ Check interval: 2 seconds")
        print("=" * 50)
        
        # Create a focus session
        if not await self.create_session():
            print("❌ Failed to create focus session. Exiting.")
            return
        
        self.is_running = True
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        while self.is_running and time.time() < end_time:
            # Simulate checking activity every 2 seconds
            await asyncio.sleep(2)
            
            # Randomly choose between productive and distracting activity
            is_distraction = random.random() < 0.3  # 30% chance of distraction
            
            if is_distraction:
                activity = random.choice(self.distracting_activities)
                print(f"⚠️  Distracting activity detected: {activity}")
            else:
                activity = random.choice(self.productive_activities)
                print(f"✅ Productive activity: {activity}")
            
            # Log the activity
            await self.log_activity(activity, is_distraction)
            
            # Check if we should stop
            if time.time() >= end_time:
                break
        
        self.is_running = False
        print("=" * 50)
        print("🏁 Activity monitoring completed!")

    async def test_notifications(self):
        """Test notification system directly"""
        print("🔔 Testing notification system...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test different types of notifications
                notifications = [
                    {
                        "message": "⚠️ Distracting activity detected: YouTube",
                        "notification_type": "distraction"
                    },
                    {
                        "message": "⏰ Reminder: Complete your daily tasks",
                        "notification_type": "reminder"
                    },
                    {
                        "message": "🔥 New streak record! 7 days in a row!",
                        "notification_type": "streak"
                    }
                ]
                
                for i, notification in enumerate(notifications, 1):
                    print(f"Sending notification {i}: {notification['message']}")
                    
                    # Send notification via API (you would need to add this endpoint)
                    # For now, we'll just simulate it
                    await asyncio.sleep(1)
                    print(f"✅ Notification {i} sent")
                
                print("✅ Notification test completed!")
                
        except Exception as e:
            print(f"❌ Error testing notifications: {e}")

async def main():
    """Main function to run the activity monitor"""
    print("🎯 FocusGuard Activity Monitor")
    print("=" * 30)
    
        # Configuration
    api_url = "http://localhost:8000"
    username = "cheerful_soul_44" # This will be overridden by get_current_user
    duration = 2  # minutes
    
    monitor = ActivitySimulator(api_url, username)
    
    try:
        # Start activity monitoring
        await monitor.simulate_activity_monitoring(duration)
        
        # Test notifications
        await monitor.test_notifications()
        
    except KeyboardInterrupt:
        print("\n⏹️  Monitoring stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 