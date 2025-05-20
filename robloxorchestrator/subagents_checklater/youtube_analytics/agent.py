"""
YouTube Analytics Agent for Roblox Economy Intelligence
Tracks Roblox-related content, creator activity, and viral trends
"""

from google.adk.agents import Agent
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional

from .tools import (
    get_trending_roblox_content,
    track_roblox_creators,
    analyze_economy_videos,
    detect_viral_roblox_content,
    create_content_summary_report,
    analyze_video_comments,
    discover_top_creators,
    analyze_top_video_comments
)
from .instructions import return_instructions_youtube

# Set up logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("youtube_agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("youtube_agent")

# YouTube Analytics Agent
youtube_agent = Agent(
    name="youtube_analytics_system",
    model="gemini-2.0-flash-exp",
    description="Monitors YouTube for Roblox economy content, creator trends, and viral videos",
    instruction=return_instructions_youtube(),
    tools=[
        get_trending_roblox_content,
        track_roblox_creators,
        analyze_economy_videos,
        detect_viral_roblox_content,
        create_content_summary_report,
        analyze_video_comments,
        discover_top_creators,
        analyze_top_video_comments  # Add the new function here
    ]
)

logger.info("YouTube Analytics Agent initialized")
