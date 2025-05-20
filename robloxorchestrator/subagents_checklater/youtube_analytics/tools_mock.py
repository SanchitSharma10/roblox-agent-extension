"""
Mock implementation of youtube_analytics tools for orchestrator testing
"""
import asyncio
import random
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta

# Helper functions for generating mock data
def generate_random_video():
    """Generate a random YouTube video"""
    video_titles = [
        "I Spent 24 HOURS in a Roblox Game and THIS Happened...",
        "Buying the Most EXPENSIVE Item in Roblox!",
        "How I Made 100,000 Robux in ONE Day! (Roblox Trading)",
        "The RAREST Items in Roblox That NOBODY Has!",
        "We Found a SECRET Pet in Adopt Me! (INSANE VALUE)",
        "ROBLOX BROOKHAVEN! Going Undercover As A CELEBRITY",
        "THE RICHEST PLAYERS in Roblox! (Top 10)",
        "How To Get FREE ROBUX in 2025! (WORKING)",
        "The ULTIMATE Roblox Trading Guide!",
        "REACTING To The WORST Roblox Games Ever Made!",
        "I Traded From NOTHING To A DOMINUS in Roblox!",
        "Spending 1,000,000 ROBUX In 24 Hours Challenge",
        "Real ROBLOX Admin Caught Me BREAKING Rules...",
        "Playing The MOST EXPENSIVE Roblox Game (Worth It?)",
        "The REAL Story Behind This CREEPY Roblox Game..."
    ]
    
    creators = [
        "RobloxGamer123",
        "AdoptMeKing",
        "TradeNinja",
        "LimitedCollector",
        "RobloxMaster",
        "TheBloxer",
        "RobuxRich",
        "MeepCityPlayer",
        "GameExplorer",
        "BlockStacker"
    ]
    
    # Random date within the last 7 days
    days_ago = random.randint(0, 7)
    upload_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    
    return {
        "title": random.choice(video_titles),
        "creator": random.choice(creators),
        "views": random.randint(10000, 10000000),
        "likes": random.randint(1000, 500000),
        "upload_date": upload_date,
        "trending_score": random.randint(1, 100),
        "video_id": f"yt-{random.randint(10000, 99999)}",
        "thumbnail": f"https://i.ytimg.com/vi/placeholder/{random.randint(1000, 9999)}.jpg"
    }

def generate_random_creator():
    """Generate a random YouTube creator"""
    creator_names = [
        "RobloxGamer123",
        "AdoptMeKing",
        "TradeNinja",
        "LimitedCollector",
        "RobloxMaster",
        "TheBloxer",
        "RobuxRich",
        "MeepCityPlayer",
        "GameExplorer",
        "BlockStacker"
    ]
    
    return {
        "name": random.choice(creator_names),
        "subscribers": random.randint(100000, 10000000),
        "total_views": random.randint(1000000, 100000000),
        "video_count": random.randint(50, 500),
        "trending_score": random.randint(1, 100),
        "channel_id": f"ch-{random.randint(10000, 99999)}"
    }

# Mock YouTube analytics tool functions
async def get_trending_roblox_content(limit=10):
    """Get trending Roblox videos on YouTube."""
    await asyncio.sleep(0.3)
    
    videos = []
    for _ in range(limit):
        video = generate_random_video()
        video["trending_score"] = random.randint(70, 100)  # Higher trending score
        videos.append(video)
    
    return videos

async def track_roblox_creators(limit=10):
    """Track top Roblox content creators on YouTube."""
    await asyncio.sleep(0.3)
    
    creators = []
    for _ in range(limit):
        creators.append(generate_random_creator())
    
    return creators

async def analyze_economy_videos(limit=10):
    """Analyze videos about Roblox economy topics."""
    await asyncio.sleep(0.3)
    
    videos = []
    economy_titles = [
        "How To Make MILLIONS of Robux Trading!",
        "The Secret to Roblox Economy Success",
        "Understanding Roblox Limited Items",
        "Roblox Economy EXPLAINED - How To Get RICH",
        "The Future of Roblox Trading in 2025",
        "How Roblox UGC Creators Make REAL MONEY",
        "Roblox Limited Snipe Tutorial - INSTANT PROFIT",
        "How I Made $10,000 from Roblox Trading",
        "Roblox Economy CRASH Prediction!",
        "The Most VALUABLE Items in Roblox History"
    ]
    
    for _ in range(limit):
        video = generate_random_video()
        video["title"] = random.choice(economy_titles)
        video["category"] = "economy"
        videos.append(video)
    
    return videos

async def detect_viral_roblox_content(limit=10):
    """Detect viral Roblox content on YouTube."""
    await asyncio.sleep(0.3)
    
    videos = []
    for _ in range(limit):
        video = generate_random_video()
        video["views"] = random.randint(1000000, 10000000)  # Higher views
        video["likes"] = random.randint(100000, 1000000)  # Higher likes
        video["viral_factor"] = random.uniform(0.8, 1.0)  # Viral factor
        videos.append(video)
    
    return videos

async def create_content_summary_report():
    """Create a summary report of Roblox content trends."""
    await asyncio.sleep(0.3)
    
    return {
        "total_videos_analyzed": 5000,
        "trending_topics": [
            {"topic": "Trading", "video_count": 856, "avg_views": 450000},
            {"topic": "Adopt Me", "video_count": 723, "avg_views": 620000},
            {"topic": "Limiteds", "video_count": 542, "avg_views": 380000},
            {"topic": "Robux", "video_count": 498, "avg_views": 520000},
            {"topic": "Brookhaven", "video_count": 412, "avg_views": 580000}
        ],
        "top_creators": [
            generate_random_creator(),
            generate_random_creator(),
            generate_random_creator()
        ],
        "content_growth": {
            "daily_new_videos": 120,
            "weekly_growth_percent": 5.2,
            "popular_categories": ["Trading", "Roleplay", "Tycoon"]
        }
    }

async def analyze_video_comments(video_id, limit=20):
    """Analyze comments on a Roblox YouTube video."""
    await asyncio.sleep(0.3)
    
    comments = []
    for _ in range(limit):
        comments.append({
            "text": f"Random comment {random.randint(1, 1000)}",
            "likes": random.randint(0, 1000),
            "sentiment": random.choice(["positive", "neutral", "negative"])
        })
    
    return {
        "video_id": video_id,
        "comment_count": limit,
        "sentiment_analysis": {
            "positive": random.randint(40, 70),
            "neutral": random.randint(10, 30),
            "negative": random.randint(5, 20)
        },
        "comments": comments
    }

async def discover_top_creators(limit=10):
    """Discover top Roblox content creators."""
    await asyncio.sleep(0.3)
    
    return sorted([generate_random_creator() for _ in range(limit)], 
                 key=lambda x: x["subscribers"], 
                 reverse=True)

async def analyze_top_video_comments(video_count=5, comment_count=10):
    """Analyze comments from top Roblox videos."""
    await asyncio.sleep(0.4)
    
    videos = []
    for i in range(video_count):
        video = generate_random_video()
        video["analyzed_comments"] = [
            {
                "text": f"Comment {j} on video {i}",
                "likes": random.randint(0, 500),
                "sentiment": random.choice(["positive", "neutral", "negative"])
            }
            for j in range(comment_count)
        ]
        videos.append(video)
    
    return videos
