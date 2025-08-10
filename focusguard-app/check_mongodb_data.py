#!/usr/bin/env python3
"""
MongoDB Data Verification Script for FocusGuard
This script checks if all data is being properly fetched and stored in MongoDB
"""

import asyncio
import motor.motor_asyncio
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MongoDBDataChecker:
    def __init__(self):
        self.mongodb_url = os.getenv("MONGODB_URL")
        if not self.mongodb_url:
            print("❌ MONGODB_URL not set in environment variables")
            return
        
        self.client = motor.motor_asyncio.AsyncIOMotorClient(self.mongodb_url)
        self.db = self.client.focusguard
        
        # Collections
        self.users_collection = self.db.users
        self.sessions_collection = self.db.focus_sessions
        self.plans_collection = self.db.daily_plans
        self.activity_collection = self.db.activity_logs
        self.notifications_collection = self.db.notifications
        self.progress_collection = self.db.progress_tracking

    async def check_connection(self):
        """Check MongoDB connection"""
        try:
            await self.client.admin.command('ping')
            print("✅ MongoDB connection successful")
            return True
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            return False

    async def check_users_collection(self):
        """Check users collection data"""
        print("\n👥 Checking Users Collection...")
        try:
            users = await self.users_collection.find().to_list(length=None)
            print(f"📊 Total users: {len(users)}")
            
            if users:
                print("📋 User details:")
                for user in users:
                    print(f"  - Username: {user.get('username')}")
                    print(f"    ID: {user.get('_id')}")
                    print(f"    Created: {user.get('created_at')}")
                    print(f"    Last Active: {user.get('last_active')}")
                    print(f"    Custom Audio: {user.get('custom_audio_url', 'None')}")
                    print()
            else:
                print("⚠️  No users found in database")
            
            return len(users)
        except Exception as e:
            print(f"❌ Error checking users: {e}")
            return 0

    async def check_sessions_collection(self):
        """Check focus sessions collection data"""
        print("\n⏱️  Checking Focus Sessions Collection...")
        try:
            sessions = await self.sessions_collection.find().to_list(length=None)
            print(f"📊 Total sessions: {len(sessions)}")
            
            if sessions:
                print("📋 Recent sessions:")
                recent_sessions = sessions[-5:]  # Show last 5 sessions
                for session in recent_sessions:
                    print(f"  - Session ID: {session.get('_id')}")
                    print(f"    User: {session.get('username')}")
                    print(f"    Task: {session.get('task_description')}")
                    print(f"    Duration: {session.get('duration_minutes')} minutes")
                    print(f"    Start: {session.get('start_time')}")
                    print(f"    Completed: {session.get('completed')}")
                    print(f"    Distractions: {session.get('distraction_count', 0)}")
                    print()
            else:
                print("⚠️  No focus sessions found")
            
            return len(sessions)
        except Exception as e:
            print(f"❌ Error checking sessions: {e}")
            return 0

    async def check_plans_collection(self):
        """Check daily plans collection data"""
        print("\n📅 Checking Daily Plans Collection...")
        try:
            plans = await self.plans_collection.find().to_list(length=None)
            print(f"📊 Total plans: {len(plans)}")
            
            if plans:
                print("📋 Recent plans:")
                recent_plans = plans[-5:]  # Show last 5 plans
                for plan in recent_plans:
                    print(f"  - Plan ID: {plan.get('_id')}")
                    print(f"    User: {plan.get('username')}")
                    print(f"    Date: {plan.get('date')}")
                    print(f"    Tasks: {len(plan.get('tasks', []))}")
                    print(f"    Reminders: {len(plan.get('reminders', []))}")
                    print(f"    Created: {plan.get('created_at')}")
                    print(f"    Updated: {plan.get('updated_at')}")
                    print()
            else:
                print("⚠️  No daily plans found")
            
            return len(plans)
        except Exception as e:
            print(f"❌ Error checking plans: {e}")
            return 0

    async def check_activity_collection(self):
        """Check activity logs collection data"""
        print("\n📊 Checking Activity Logs Collection...")
        try:
            activities = await self.activity_collection.find().to_list(length=None)
            print(f"📊 Total activity logs: {len(activities)}")
            
            if activities:
                print("📋 Recent activities:")
                recent_activities = activities[-5:]  # Show last 5 activities
                for activity in recent_activities:
                    print(f"  - Activity ID: {activity.get('_id')}")
                    print(f"    User: {activity.get('username')}")
                    print(f"    Window: {activity.get('window_title')}")
                    print(f"    Classification: {activity.get('classification')}")
                    print(f"    Is Distraction: {activity.get('is_distraction')}")
                    print(f"    Timestamp: {activity.get('timestamp')}")
                    print()
            else:
                print("⚠️  No activity logs found")
            
            return len(activities)
        except Exception as e:
            print(f"❌ Error checking activities: {e}")
            return 0

    async def check_notifications_collection(self):
        """Check notifications collection data"""
        print("\n🔔 Checking Notifications Collection...")
        try:
            notifications = await self.notifications_collection.find().to_list(length=None)
            print(f"📊 Total notifications: {len(notifications)}")
            
            if notifications:
                print("📋 Recent notifications:")
                recent_notifications = notifications[-5:]  # Show last 5 notifications
                for notification in recent_notifications:
                    print(f"  - Notification ID: {notification.get('_id')}")
                    print(f"    User: {notification.get('username')}")
                    print(f"    Type: {notification.get('notification_type')}")
                    print(f"    Message: {notification.get('message')}")
                    print(f"    Read: {notification.get('read')}")
                    print(f"    Created: {notification.get('created_at')}")
                    print()
            else:
                print("⚠️  No notifications found")
            
            return len(notifications)
        except Exception as e:
            print(f"❌ Error checking notifications: {e}")
            return 0

    async def check_progress_collection(self):
        """Check progress tracking collection data"""
        print("\n📈 Checking Progress Tracking Collection...")
        try:
            progress_entries = await self.progress_collection.find().to_list(length=None)
            print(f"📊 Total progress entries: {len(progress_entries)}")
            
            if progress_entries:
                print("📋 Recent progress entries:")
                recent_progress = progress_entries[-5:]  # Show last 5 entries
                for progress in recent_progress:
                    print(f"  - Progress ID: {progress.get('_id')}")
                    print(f"    User: {progress.get('username')}")
                    print(f"    Date: {progress.get('date')}")
                    print(f"    Focus Time: {progress.get('focus_time_minutes', 0)} minutes")
                    print(f"    Distractions: {progress.get('distraction_count', 0)}")
                    print(f"    Productivity Score: {progress.get('productivity_score', 0)}")
                    print()
            else:
                print("⚠️  No progress entries found")
            
            return len(progress_entries)
        except Exception as e:
            print(f"❌ Error checking progress: {e}")
            return 0

    async def check_data_integrity(self):
        """Check data integrity and relationships"""
        print("\n🔍 Checking Data Integrity...")
        
        try:
            # Check if users have associated data
            users = await self.users_collection.find().to_list(length=None)
            
            for user in users:
                username = user.get('username')
                print(f"\n👤 Checking data for user: {username}")
                
                # Check sessions
                user_sessions = await self.sessions_collection.find({"username": username}).to_list(length=None)
                print(f"  📊 Sessions: {len(user_sessions)}")
                
                # Check plans
                user_plans = await self.plans_collection.find({"username": username}).to_list(length=None)
                print(f"  📅 Plans: {len(user_plans)}")
                
                # Check activities
                user_activities = await self.activity_collection.find({"username": username}).to_list(length=None)
                print(f"  📈 Activities: {len(user_activities)}")
                
                # Check notifications
                user_notifications = await self.notifications_collection.find({"username": username}).to_list(length=None)
                print(f"  🔔 Notifications: {len(user_notifications)}")
                
                # Check progress
                user_progress = await self.progress_collection.find({"username": username}).to_list(length=None)
                print(f"  📊 Progress entries: {len(user_progress)}")
                
        except Exception as e:
            print(f"❌ Error checking data integrity: {e}")

    async def check_recent_activity(self):
        """Check recent activity (last 24 hours)"""
        print("\n⏰ Checking Recent Activity (Last 24 Hours)...")
        
        try:
            yesterday = datetime.utcnow() - timedelta(days=1)
            
            # Recent sessions
            recent_sessions = await self.sessions_collection.find({
                "start_time": {"$gte": yesterday}
            }).to_list(length=None)
            print(f"📊 Recent sessions: {len(recent_sessions)}")
            
            # Recent activities
            recent_activities = await self.activity_collection.find({
                "timestamp": {"$gte": yesterday}
            }).to_list(length=None)
            print(f"📈 Recent activities: {len(recent_activities)}")
            
            # Recent notifications
            recent_notifications = await self.notifications_collection.find({
                "created_at": {"$gte": yesterday}
            }).to_list(length=None)
            print(f"🔔 Recent notifications: {len(recent_notifications)}")
            
        except Exception as e:
            print(f"❌ Error checking recent activity: {e}")

    async def run_full_check(self):
        """Run complete MongoDB data check"""
        print("🔍 FocusGuard MongoDB Data Verification")
        print("=" * 50)
        
        # Check connection
        if not await self.check_connection():
            return
        
        # Check all collections
        user_count = await self.check_users_collection()
        session_count = await self.check_sessions_collection()
        plan_count = await self.check_plans_collection()
        activity_count = await self.check_activity_collection()
        notification_count = await self.check_notifications_collection()
        progress_count = await self.check_progress_collection()
        
        # Check data integrity
        await self.check_data_integrity()
        
        # Check recent activity
        await self.check_recent_activity()
        
        # Summary
        print("\n📊 SUMMARY")
        print("=" * 50)
        print(f"👥 Users: {user_count}")
        print(f"⏱️  Sessions: {session_count}")
        print(f"📅 Plans: {plan_count}")
        print(f"📈 Activities: {activity_count}")
        print(f"🔔 Notifications: {notification_count}")
        print(f"📊 Progress Entries: {progress_count}")
        
        if user_count > 0:
            print("\n✅ MongoDB data verification completed successfully!")
        else:
            print("\n⚠️  No users found. Consider creating a test user first.")
        
        await self.client.close()

async def main():
    """Main function"""
    checker = MongoDBDataChecker()
    await checker.run_full_check()

if __name__ == "__main__":
    asyncio.run(main())
