#!/usr/bin/env python3
"""
Test script for cross-platform window monitoring functionality.
This script tests the CrossPlatformWindowMonitor class to ensure it works
correctly on both Windows and Linux systems.
"""

import asyncio
import platform
import sys
import time
from datetime import datetime

# Add the current directory to Python path to import from main.py
sys.path.append('.')

try:
    from main import CrossPlatformWindowMonitor
    print("✅ Successfully imported CrossPlatformWindowMonitor from main.py")
except ImportError as e:
    print(f"❌ Failed to import CrossPlatformWindowMonitor: {e}")
    sys.exit(1)

def test_window_monitor():
    """Test the CrossPlatformWindowMonitor functionality"""
    print(f"\n🔍 Testing Cross-Platform Window Monitor")
    print(f"🌐 Platform: {platform.system()}")
    print(f"🏗️ Architecture: {platform.machine()}")
    print(f"🐍 Python Version: {platform.python_version()}")
    
    # Initialize the monitor
    try:
        monitor = CrossPlatformWindowMonitor()
        print("✅ CrossPlatformWindowMonitor initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize CrossPlatformWindowMonitor: {e}")
        return False
    
    # Test getting current window
    print("\n📱 Testing current window detection...")
    try:
        window_info = monitor.get_window_info()
        print(f"✅ Current window: {window_info['title']}")
        print(f"📊 Process: {window_info['process']}")
        print(f"🆔 PID: {window_info['pid']}")
        print(f"🔧 Platform: {window_info['platform']}")
    except Exception as e:
        print(f"❌ Failed to get current window: {e}")
        return False
    
    # Test multiple window checks
    print("\n🔄 Testing multiple window checks...")
    for i in range(3):
        try:
            window_info = monitor.get_window_info()
            print(f"Check {i+1}: {window_info['title'][:50]}...")
            time.sleep(1)
        except Exception as e:
            print(f"❌ Failed on check {i+1}: {e}")
            return False
    
    # Test should_send_activity logic
    print("\n⏰ Testing activity sending logic...")
    try:
        current_time = datetime.now()
        should_send = monitor.should_send_activity("Test Window", current_time)
        print(f"✅ Should send activity: {should_send}")
    except Exception as e:
        print(f"❌ Failed to test activity logic: {e}")
        return False
    
    print("\n🎉 All tests passed! Cross-platform window monitoring is working correctly.")
    return True

def test_system_info():
    """Test system information gathering"""
    print(f"\n💻 System Information:")
    print(f"OS: {platform.system()}")
    print(f"Release: {platform.release()}")
    print(f"Version: {platform.version()}")
    print(f"Machine: {platform.machine()}")
    print(f"Processor: {platform.processor()}")
    
    # Test Linux-specific tools if on Linux
    if platform.system() == "Linux":
        print("\n🐧 Linux-specific tools:")
        import subprocess
        
        tools = ['xdotool', 'wmctrl']
        for tool in tools:
            try:
                result = subprocess.run([tool, '--version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    print(f"✅ {tool}: Available")
                else:
                    print(f"⚠️ {tool}: Not available")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                print(f"❌ {tool}: Not found")

async def main():
    """Main test function"""
    print("🚀 Starting Cross-Platform Window Monitor Tests")
    print("=" * 50)
    
    # Test system info
    test_system_info()
    
    # Test window monitor
    success = test_window_monitor()
    
    if success:
        print("\n✅ All tests completed successfully!")
        print("🎯 Cross-platform window monitoring is ready for deployment.")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
