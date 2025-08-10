#!/usr/bin/env python3
"""
Test script for integrated monitoring functionality
"""

import asyncio
import aiohttp
import json
import time

async def test_integrated_monitoring():
    """Test the integrated monitoring endpoints"""
    base_url = "http://localhost:8000"
    username = "cheerful_soul_44"
    
    print("🧪 Testing Integrated Monitoring Functionality")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        try:
            # Test 1: Check monitoring status
            print("1. Checking monitoring status...")
            async with session.get(f"{base_url}/monitoring/status") as response:
                if response.status == 200:
                    status = await response.json()
                    print(f"   ✅ Status: {status}")
                else:
                    print(f"   ❌ Failed: {response.status}")
            
            # Test 2: Get current window
            print("\n2. Getting current window...")
            async with session.get(f"{base_url}/monitoring/current-window") as response:
                if response.status == 200:
                    window = await response.json()
                    print(f"   ✅ Current window: {window}")
                else:
                    print(f"   ❌ Failed: {response.status}")
            
            # Test 3: Start monitoring
            print(f"\n3. Starting monitoring for {username}...")
            async with session.post(f"{base_url}/monitoring/start/{username}", json={"duration_minutes": 5}) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"   ✅ Monitoring started: {result}")
                else:
                    print(f"   ❌ Failed: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
            
            # Test 4: Check status again
            print("\n4. Checking monitoring status after start...")
            async with session.get(f"{base_url}/monitoring/status") as response:
                if response.status == 200:
                    status = await response.json()
                    print(f"   ✅ Status: {status}")
                else:
                    print(f"   ❌ Failed: {response.status}")
            
            # Wait a bit
            print("\n⏳ Waiting 10 seconds to see monitoring in action...")
            await asyncio.sleep(10)
            
            # Test 5: Stop monitoring
            print("\n5. Stopping monitoring...")
            async with session.post(f"{base_url}/monitoring/stop") as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"   ✅ Monitoring stopped: {result}")
                else:
                    print(f"   ❌ Failed: {response.status}")
            
            # Test 6: Final status check
            print("\n6. Final status check...")
            async with session.get(f"{base_url}/monitoring/status") as response:
                if response.status == 200:
                    status = await response.json()
                    print(f"   ✅ Final status: {status}")
                else:
                    print(f"   ❌ Failed: {response.status}")
                    
        except Exception as e:
            print(f"❌ Error during testing: {e}")

async def test_simultaneous_setup():
    """Test the simultaneous monitoring setup endpoint"""
    base_url = "http://localhost:8000"
    
    print("\n🧪 Testing Simultaneous Monitoring Setup")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(f"{base_url}/monitoring/setup-simultaneous") as response:
                if response.status == 200:
                    setup = await response.json()
                    print("✅ Setup instructions:")
                    for instruction in setup["instructions"]:
                        print(f"   {instruction}")
                    print(f"\n📋 Integrated monitoring available: {setup['integrated_monitoring']['available']}")
                else:
                    print(f"❌ Failed: {response.status}")
                    
        except Exception as e:
            print(f"❌ Error during setup test: {e}")

if __name__ == "__main__":
    print("🚀 Starting Integrated Monitoring Tests")
    print("Make sure the main.py server is running on http://localhost:8000")
    print("=" * 60)
    
    asyncio.run(test_integrated_monitoring())
    asyncio.run(test_simultaneous_setup())
    
    print("\n✅ Testing completed!")
