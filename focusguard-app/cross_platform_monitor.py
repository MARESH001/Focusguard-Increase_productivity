#!/usr/bin/env python3
"""
Cross-Platform Window Monitor for FocusGuard
This script monitors active windows on both Windows and Linux systems.
Works with the FocusGuard API to send real-time activity data.
"""

import asyncio
import aiohttp
import json
import time
import os
import platform
import subprocess
import psutil
from datetime import datetime
import motor.motor_asyncio

class CrossPlatformMonitor:
    def __init__(self, api_base_url="http://localhost:8000", username=None):
        self.api_base_url = api_base_url
        self.username = username
        self.session_id = None
        self.is_monitoring = False
        self.last_window_title = ""
        self.last_check_time = 0
        self.check_interval = 2
        self.system = platform.system()
        
        # Initialize platform-specific capabilities
        self._init_platform_capabilities()
        
    def _init_platform_capabilities(self):
        """Initialize platform-specific window monitoring capabilities"""
        self.windows_available = False
        self.linux_available = False
        
        if self.system == "Windows":
            try:
                import win32gui
                import win32process
                self.windows_available = True
                print("✅ Windows window monitoring available")
            except ImportError:
                print("⚠️ Windows window monitoring not available (pywin32 not installed)")
        
        elif self.system == "Linux":
            self.linux_available = True
            # Check for Linux window manager tools
            try:
                result = subprocess.run(['which', 'xdotool'], capture_output=True, text=True)
                self.xdotool_available = result.returncode == 0
                if self.xdotool_available:
                    print("✅ xdotool available for Linux window monitoring")
                else:
                    print("⚠️ xdotool not found")
            except:
                self.xdotool_available = False
            
            try:
                result = subprocess.run(['which', 'wmctrl'], capture_output=True, text=True)
                self.wmctrl_available = result.returncode == 0
                if self.wmctrl_available:
                    print("✅ wmctrl available for Linux window monitoring")
                else:
                    print("⚠️ wmctrl not found")
            except:
                self.wmctrl_available = False
            
            if not self.xdotool_available and not self.wmctrl_available:
                print("⚠️ No Linux window monitoring tools available")
        
        print(f"🎯 System: {self.system}")
        print(f"🖥️  Platform: {platform.platform()}")
    
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
    
    def get_active_window_title(self):
        """Get the title of the currently active window - works on Windows and Linux"""
        try:
            if self.system == "Windows" and self.windows_available:
                return self._get_windows_active_window()
            elif self.system == "Linux" and self.linux_available:
                return self._get_linux_active_window()
            else:
                return self._get_fallback_window_info()
        except Exception as e:
            print(f"Error getting active window: {e}")
            return "Unknown Window"
    
    def _get_windows_active_window(self):
        """Get active window on Windows"""
        try:
            import win32gui
            import win32process
            
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
            if self.xdotool_available:
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
            if self.wmctrl_available:
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
                session_data = {"task_description": "Cross-platform window monitoring session", "keywords": ["monitoring"], "duration_minutes": 30}
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

    async def log_activity(self, window_title):
        """Log window activity to the API"""
        if not self.session_id:
            print("❌ No active session")
            return False
            
        try:
            async with aiohttp.ClientSession() as session:
                activity_data = {
                    "window_title": window_title
                }
                
                # Use the enhanced endpoint to trigger smart notifications for distractions
                async with session.post(
                    f"{self.api_base_url}/sessions/{self.session_id}/monitor-activity",
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
                        
                        if is_distraction:
                            print(f"   📱 Distraction logged - notification sent!")
                        
                        return True
                    else:
                        print(f"❌ Failed to log activity: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Error logging activity: {e}")
            return False

    async def monitor_windows(self, duration_minutes=30):
        """Monitor active windows for a specified duration"""
        print(f"🚀 Starting cross-platform window monitoring for {duration_minutes} minutes...")
        print(f"📊 Monitoring user: {self.username}")
        print(f"⏰ Check interval: {self.check_interval} seconds")
        print(f"🎯 API endpoint: {self.api_base_url}")
        print(f"🖥️  System: {self.system}")
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
                # Get current window
                current_title = self.get_active_window_title()
                current_time = time.time()
                
                # Check if window has changed
                if current_title != self.last_window_title:
                    print(f"\n🔄 Window changed: {current_title}")
                    print(f"   Time: {datetime.now().strftime('%H:%M:%S')}")
                    
                    # Log the activity (this triggers notifications)
                    await self.log_activity(current_title)
                    
                    # Update tracking
                    self.last_window_title = current_title
                    self.last_check_time = current_time
                else:
                    # Show current status without logging
                    print(f"\r👁️  Current: {current_title} (monitoring...)", end="", flush=True)
                
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
        print("🏁 Cross-platform window monitoring completed!")

    async def test_single_window(self):
        """Test the system with current window"""
        print("🧪 Testing with current active window...")
        
        current_title = self.get_active_window_title()
        print(f"Current window: {current_title}")
        print(f"System: {self.system}")
        
        # Create session and test
        if await self.create_session():
            await self.log_activity(current_title)
        else:
            print("❌ Failed to create test session")

async def main():
    """Main function to run the cross-platform monitor"""
    print("🎯 FocusGuard Cross-Platform Window Monitor")
    print("=" * 50)
    
    # Configuration
    api_url = "http://localhost:8000"
    username = "cheerful_soul_44"  # This will be overridden by get_current_user
    duration = 5  # minutes
    
    monitor = CrossPlatformMonitor(api_url, username)
    
    try:
        # Test with current window first
        await monitor.test_single_window()
        
        print("\n" + "=" * 50)
        
        # Start monitoring
        await monitor.monitor_windows(duration)
        
    except KeyboardInterrupt:
        print("\n⏹️  Monitoring stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
