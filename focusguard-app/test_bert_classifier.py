#!/usr/bin/env python3
"""
Test script for the new BERT-based content classifier
This demonstrates how the system intelligently classifies different types of content
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import AdvancedContentClassifier

async def test_classifier():
    """Test the BERT classifier with various window titles"""
    print("🧪 Testing BERT-based Content Classifier")
    print("=" * 60)
    
    # Initialize the classifier
    try:
        classifier = AdvancedContentClassifier()
        print("✅ Classifier initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize classifier: {e}")
        return
    
    # Test cases with different types of content
    test_cases = [
        # Educational content
        "Python Programming Tutorial - Learn Python in 2024",
        "MIT OpenCourseWare: Introduction to Computer Science",
        "Khan Academy: Calculus - Derivatives and Limits",
        "Research Paper: Machine Learning Applications in Healthcare",
        
        # Work/Productive content
        "Excel - Budget_2024.xlsx",
        "Visual Studio Code - project/main.py",
        "Slack - Team Collaboration",
        "Google Calendar - Meeting with Client",
        "Jira - Project Management Dashboard",
        
        # Entertainment content
        "Netflix - Stranger Things Season 4",
        "Spotify - Top Hits 2024 Playlist",
        "YouTube - Funny Cat Videos Compilation",
        "Steam - Call of Duty: Modern Warfare",
        
        # Social Media
        "Facebook - News Feed",
        "Instagram - @username's Profile",
        "Twitter - Trending Topics",
        "TikTok - For You Page",
        
        # Gaming
        "Steam - Counter-Strike 2",
        "Epic Games Launcher - Fortnite",
        "Discord - Gaming Community",
        "Twitch - Live Gaming Stream",
        
        # Streaming
        "YouTube - Educational Programming Course",
        "Netflix - Documentary: Planet Earth",
        "Hulu - News Channel Live",
        "Disney+ - National Geographic Content",
        
        # Mixed/Complex cases
        "YouTube - How to Build a Website (Tutorial)",
        "Facebook - Learning Python Programming Group",
        "Reddit - r/learnprogramming",
        "Discord - Study Group Server"
    ]
    
    print("\n🔍 Testing Classification and Sentiment Analysis:")
    print("=" * 60)
    
    for i, title in enumerate(test_cases, 1):
        print(f"\n📱 Test Case {i}: {title}")
        print("-" * 40)
        
        try:
            # Get detailed analysis
            analysis = classifier.get_detailed_analysis(title)
            
            # Display results
            print(f"🎯 Classification: {analysis['classification']}")
            print(f"📊 Confidence: {analysis['confidence']:.3f}")
            print(f"⚠️  Is Distraction: {analysis['is_distraction']}")
            print(f"😊 Sentiment: {analysis['sentiment']}")
            print(f"📈 Sentiment Score: {analysis['sentiment_score']:.3f}")
            print(f"💭 Reasoning: {analysis['reasoning']}")
            
        except Exception as e:
            print(f"❌ Error analyzing: {e}")
    
    print("\n" + "=" * 60)
    print("✅ BERT Classifier Test Complete!")
    print("\n📋 Summary of Categories:")
    print("• Educational: Learning, courses, tutorials, research")
    print("• Work: Productivity tools, development, business")
    print("• Entertainment: Movies, music, fun content")
    print("• Social Media: Facebook, Instagram, Twitter, etc.")
    print("• Gaming: Video games, gaming platforms")
    print("• Streaming: YouTube, Netflix, Hulu, etc.")
    print("• Neutral: Content that doesn't fit other categories")

if __name__ == "__main__":
    asyncio.run(test_classifier())
