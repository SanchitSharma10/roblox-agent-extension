#!/usr/bin/env python3
"""
YouTube Analytics Agent for Roblox Economy Intelligence
Tracks Roblox-related content trends, mentions, and creator dynamics
"""

from google.adk.agents import Agent
from .tools import (
    get_roblox_content_trends,
    analyze_creator_mentions,
    get_viral_roblox_videos,
    track_game_popularity,
    get_youtube_market_sentiment,
    create_youtube_analytics_report
)
from .instructions import return_instructions_youtube


def setup_before_agent_call(callback_context):
    """Setup the YouTube analytics agent."""
    
    # Setting up YouTube API settings in session state
    if "youtube_settings" not in callback_context.state:
        youtube_settings = {
            "api_configured": True,
            "channels_tracked": [
                "UC_jQE8JEpRxY0xR_D2qB-xQ",  # Example: KreekCraft
                "UC-71wbxMHGNL6bvSTzztCFg",  # Example: Flamingo
            ],
            "keywords_tracked": [
                "roblox economy", "roblox trading", "limited items", 
                "robux", "dominus", "roblox marketplace"
            ]
        }
        callback_context.state["youtube_settings"] = youtube_settings
    
    # Set up data collection scope
    callback_context.state["youtube_scope"] = {
        "content_types": ["reviews", "trading_guides", "market_analysis", "game_showcases"],
        "time_range": "7d",  # Default to last 7 days
        "min_views": 1000,   # Filter for content with meaningful reach
        "sentiment_analysis": True
    }

# YouTube Analytics Agent
youtube_agent = Agent(
    name="youtube_analytics_system",
    model="gemini-2.0-flash-exp",
    description="Analyzes YouTube content trends related to Roblox economy, items, and creator sentiment",
    instruction=return_instructions_youtube(),
    tools=[
        get_roblox_content_trends,
        analyze_creator_mentions,
        get_viral_roblox_videos,
        track_game_popularity,
        get_youtube_market_sentiment,
        create_youtube_analytics_report
    ],
    output_key="youtube_results"
)
