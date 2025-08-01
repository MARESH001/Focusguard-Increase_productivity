#!/usr/bin/env python3
"""
Activity Monitor Script for FocusGuard
This script simulates monitoring user activity and sending notifications for distracting activities.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
import random

class ActivityMonitor:
    def __init__(self, api_base_url="http://localhost:8000", username="testuser"):
        self.api_base_url = api_base_url
        self.username = username
        self.session_id = None
        self.is_monitoring = False
        
        # Sample distracting activities for testing
        self.distracting_activities = [
            "YouTube - Funny Cat Videos",
            "Facebook - Social Media",
            "Instagram - Photo Sharing",
            "Twitter - Social Media",
            "Reddit - Entertainment",
            "Netflix - Movie Streaming",
            "Spotify - Music",
            "TikTok - Short Videos",
            "Discord - Gaming Chat",
            "Twitch - Live Streaming"
        ]
        
        # Sample productive activities
        self.productive_activities = [
            "Visual Studio Code - focusguard-app/main.py",
            "Google Chrome - Stack Overflow",
            "Terminal - git commit",
            "Notion - Project Planning",
            "Slack - Work Communication",
            "Microsoft Teams - Meeting",
            "Zoom - Video Conference",
            "Jira - Task Management",
            "Confluence - Documentation",
            "GitHub - Code Repository"
        ]

    async def create_focus_session(self):
        """Create a focus session for monitoring"""
        try:
            async with aiohttp.ClientSession() as session:
                session_data = {
                    "task_description": "Testing activity monitoring",
                    "keywords": ["test", "monitoring", "focus"],
                    "duration_minutes": 30
                }
                
                async with session.post(
                    f"{self.api_base_url}/users/{self.username}/sessions/",
                    json=session_data
                ) as response:
                    if response.status == 200:
                        session_info = await response.json()
                        self.session_id = session_info["id"]
                        print(f"✅ Created focus session: {self.session_id}")
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
        if not await self.create_focus_session():
            print("❌ Failed to create focus session. Exiting.")
            return
        
        self.is_monitoring = True
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        while self.is_monitoring and time.time() < end_time:
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
        
        self.is_monitoring = False
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
    username = "testuser"
    duration = 2  # minutes
    
    monitor = ActivityMonitor(api_url, username)
    
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