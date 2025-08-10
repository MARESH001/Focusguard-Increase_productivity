#!/usr/bin/env python3
"""
Setup Script for FocusGuard Enhanced Features
This script helps set up and configure the enhanced features.
"""

import subprocess
import sys
import os
import json
from pathlib import Path
import asyncio
import aiohttp
from datetime import datetime, timedelta
import motor.motor_asyncio

async def get_current_user():
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

async def setup_test_data(api_base_url="http://localhost:8000"):
    """Setup test data for enhanced features"""
    
    # Get current user dynamically
    username = await get_current_user()
    print(f"🔍 Setting up test data for user: {username}")
    
    test_data = {
        "test_user": {
            "username": username,
            "daily_plan": {
                "date": "2024-01-15",
                "tasks": [
                    {"id": "1", "text": "Complete project documentation", "completed": False, "reminder_time": "14:00"},
                    {"id": "2", "text": "Review code changes", "completed": True, "reminder_time": None},
                    {"id": "3", "text": "Prepare presentation", "completed": False, "reminder_time": "16:00"}
                ],
                "custom_audio_url": "https://example.com/notification.mp3"
            }
        }
    }
    
    # Save test data
    with open("test_data.json", "w") as f:
        json.dump(test_data, f, indent=2)
    
    print("✅ Test data created: test_data.json")
    return True

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required. Current version: {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def install_dependencies():
    """Install required Python dependencies"""
    print("📦 Installing Python dependencies...")
    
    # Check if requirements.txt exists
    if not os.path.exists("requirements.txt"):
        print("❌ requirements.txt not found")
        return False
    
    # Install dependencies
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        return False
    
    # Install additional dependencies for enhanced features
    additional_deps = [
        "websockets==12.0",
        "apscheduler==3.10.4"
    ]
    
    for dep in additional_deps:
        if not run_command(f"pip install {dep}", f"Installing {dep}"):
            return False
    
    return True

def check_mongodb():
    """Check if MongoDB is running"""
    print("🗄️ Checking MongoDB connection...")
    try:
        import motor.motor_asyncio
        import asyncio
        
        async def test_connection():
            try:
                client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
                await client.admin.command('ping')
                print("✅ MongoDB is running and accessible")
                return True
            except Exception as e:
                print(f"❌ MongoDB connection failed: {e}")
                return False
        
        return asyncio.run(test_connection())
    except ImportError:
        print("❌ motor package not installed")
        return False

def create_test_data():
    """Create test data for enhanced features"""
    print("🧪 Creating test data...")
    
    test_data = {
        "test_user": {
            "username": "cheerful_soul_44",
            "daily_plan": {
                "date": "2024-01-15",
                "tasks": [
                    {"id": "1", "text": "Complete project documentation", "completed": False, "reminder_time": "14:00"},
                    {"id": "2", "text": "Review code changes", "completed": True, "reminder_time": None},
                    {"id": "3", "text": "Prepare presentation", "completed": False, "reminder_time": "16:00"}
                ],
                "custom_audio_url": "https://example.com/notification.mp3"
            }
        }
    }
    
    # Save test data
    with open("test_data.json", "w") as f:
        json.dump(test_data, f, indent=2)
    
    print("✅ Test data created: test_data.json")
    return True

def create_config_file():
    """Create configuration file"""
    print("⚙️ Creating configuration file...")
    
    config = {
        "api_base_url": "http://localhost:8000",
        "websocket_url": "ws://localhost:8000",
        "mongodb_url": "mongodb://localhost:27017/focusguard",
        "notification_settings": {
            "default_sound_enabled": True,
            "custom_audio_enabled": True,
            "toast_notifications": True
        },
        "activity_monitoring": {
            "check_interval_seconds": 2,
            "distraction_threshold": 3,
            "enable_notifications": True
        },
        "progress_tracking": {
            "streak_calculation": True,
            "break_detection": True,
            "productivity_scoring": True
        }
    }
    
    with open("config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print("✅ Configuration file created: config.json")
    return True

def run_tests():
    """Run basic tests"""
    print("🧪 Running basic tests...")
    
    # Test imports
    try:
        import fastapi
        import motor
        import websockets
        import apscheduler
        print("✅ All required packages imported successfully")
    except ImportError as e:
        print(f"❌ Import test failed: {e}")
        return False
    
    # Test database connection
    if not check_mongodb():
        print("❌ Database connection test failed")
        return False
    
    print("✅ All tests passed")
    return True

def print_next_steps():
    """Print next steps for the user"""
    print("\n" + "="*50)
    print("🎉 Enhanced Features Setup Complete!")
    print("="*50)
    print("\n📋 Next Steps:")
    print("1. Start the backend server:")
    print("   cd focusguard-app")
    print("   python main.py")
    print("\n2. Start the frontend:")
    print("   cd focusguard-frontend")
    print("   npm run dev")
    print("\n3. Test the activity monitoring:")
    print("   python activity_monitor.py")
    print("\n4. Open the application in your browser:")
    print("   http://localhost:5173")
    print("\n📚 Documentation:")
    print("- Read README_ENHANCED_FEATURES.md for detailed information")
    print("- Check the API endpoints in main.py")
    print("- Review the frontend components")
    print("\n🔧 Configuration:")
    print("- Edit config.json to customize settings")
    print("- Modify test_data.json for different test scenarios")
    print("\n🚀 Features Available:")
    print("✅ Activity monitoring every 2 seconds")
    print("✅ Smart notification system")
    print("✅ Progress tracking with streaks")
    print("✅ Enhanced daily planning with tasks")
    print("✅ Real-time WebSocket notifications")
    print("✅ Custom audio support")
    print("✅ Task reminders")
    print("\n" + "="*50)

def main():
    """Main setup function"""
    print("🚀 FocusGuard Enhanced Features Setup")
    print("="*40)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        sys.exit(1)
    
    # Check MongoDB
    if not check_mongodb():
        print("⚠️ MongoDB is not running. Please start MongoDB and run this script again.")
        print("   On Ubuntu/Debian: sudo systemctl start mongod")
        print("   On macOS: brew services start mongodb-community")
        print("   On Windows: Start MongoDB service from Services")
        sys.exit(1)
    
    # Create configuration files
    create_config_file()
    # create_test_data() # This line is now replaced by the new_code
    
    # Run tests
    if not run_tests():
        print("❌ Tests failed")
        sys.exit(1)
    
    # Print next steps
    print_next_steps()

if __name__ == "__main__":
    main() 