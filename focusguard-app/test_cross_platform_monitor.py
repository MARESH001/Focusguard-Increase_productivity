#!/usr/bin/env python3
"""
Test script for Cross-Platform Window Monitor
This script tests the window monitoring capabilities on the current system.
"""

import asyncio
import platform
import subprocess
import os
from cross_platform_monitor import CrossPlatformMonitor

async def test_window_monitoring():
    """Test the cross-platform window monitoring system"""
    print("🧪 Testing Cross-Platform Window Monitor")
    print("=" * 50)
    
    # Create monitor instance
    monitor = CrossPlatformMonitor()
    
    print(f"🖥️  System: {monitor.system}")
    print(f"📋 Platform: {platform.platform()}")
    print(f"🐍 Python: {platform.python_version()}")
    
    # Test window detection
    print("\n🔍 Testing window detection...")
    try:
        current_window = monitor.get_active_window_title()
        print(f"✅ Current window: {current_window}")
        
        # Test window info
        window_info = monitor.get_window_info()
        print(f"📊 Window info: {window_info}")
        
    except Exception as e:
        print(f"❌ Window detection failed: {e}")
    
    # Test system capabilities
    print("\n🔧 Testing system capabilities...")
    if monitor.system == "Windows":
        print(f"Windows monitoring: {'✅ Available' if monitor.windows_available else '❌ Not available'}")
    elif monitor.system == "Linux":
        print(f"Linux monitoring: {'✅ Available' if monitor.linux_available else '❌ Not available'}")
        print(f"xdotool: {'✅ Available' if monitor.xdotool_available else '❌ Not available'}")
        print(f"wmctrl: {'✅ Available' if monitor.wmctrl_available else '❌ Not available'}")
    
    # Test API connectivity (if backend is running)
    print("\n🌐 Testing API connectivity...")
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/") as response:
                if response.status == 200:
                    print("✅ Backend API is running")
                    
                    # Test window monitor status endpoint
                    async with session.get("http://localhost:8000/window-monitor/status") as status_response:
                        if status_response.status == 200:
                            status_data = await status_response.json()
                            print(f"✅ Window monitor status: {status_data}")
                        else:
                            print(f"⚠️ Window monitor status endpoint returned: {status_response.status}")
                else:
                    print(f"⚠️ Backend API returned: {response.status}")
    except Exception as e:
        print(f"❌ Backend API test failed: {e}")
        print("💡 Make sure the FocusGuard backend is running on http://localhost:8000")
    
    print("\n" + "=" * 50)
    print("🏁 Cross-platform window monitor test completed!")

def test_linux_tools():
    """Test Linux window manager tools availability"""
    if platform.system() != "Linux":
        print("⚠️ This test is only for Linux systems")
        return
    
    print("🔧 Testing Linux window manager tools...")
    
    # Test xdotool
    try:
        result = subprocess.run(['which', 'xdotool'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ xdotool found")
            # Test xdotool functionality
            try:
                result = subprocess.run(['xdotool', 'getactivewindow', 'getwindowname'], 
                                      capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    print(f"✅ xdotool working: {result.stdout.strip()}")
                else:
                    print(f"⚠️ xdotool command failed: {result.stderr.strip()}")
            except subprocess.TimeoutExpired:
                print("⚠️ xdotool command timed out")
        else:
            print("❌ xdotool not found")
    except Exception as e:
        print(f"❌ xdotool test failed: {e}")
    
    # Test wmctrl
    try:
        result = subprocess.run(['which', 'wmctrl'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ wmctrl found")
            # Test wmctrl functionality
            try:
                result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    print("✅ wmctrl working")
                else:
                    print(f"⚠️ wmctrl command failed: {result.stderr.strip()}")
            except subprocess.TimeoutExpired:
                print("⚠️ wmctrl command timed out")
        else:
            print("❌ wmctrl not found")
    except Exception as e:
        print(f"❌ wmctrl test failed: {e}")

def test_windows_tools():
    """Test Windows window monitoring tools availability"""
    if platform.system() != "Windows":
        print("⚠️ This test is only for Windows systems")
        return
    
    print("🔧 Testing Windows window monitoring tools...")
    
    try:
        import win32gui
        import win32process
        print("✅ pywin32 libraries available")
        
        # Test basic functionality
        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                title = win32gui.GetWindowText(hwnd)
                print(f"✅ Windows window detection working: {title}")
            else:
                print("⚠️ No active window found")
        except Exception as e:
            print(f"❌ Windows window detection failed: {e}")
            
    except ImportError:
        print("❌ pywin32 not installed")
        print("💡 Install with: pip install pywin32")

if __name__ == "__main__":
    print("🎯 FocusGuard Cross-Platform Window Monitor Test")
    print("=" * 60)
    
    # Test platform-specific tools
    if platform.system() == "Linux":
        test_linux_tools()
    elif platform.system() == "Windows":
        test_windows_tools()
    
    print("\n" + "=" * 60)
    
    # Run async tests
    asyncio.run(test_window_monitoring())
