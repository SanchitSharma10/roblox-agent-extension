"""
RSS Feed Monitor Agent for Roblox Economy Intelligence
Tracks gaming news, Roblox updates, and economy-related articles
"""

from google.adk.agents import Agent
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional

from .tools import (
    monitor_roblox_feeds,
    analyze_economy_news,
    track_update_announcements,
    detect_policy_changes,
    get_competitor_news,
    create_news_summary_report
)
from .instructions import return_instructions_rss

# Set up logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("rss_agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("rss_agent")

# RSS Monitor Agent
rss_monitor_agent = Agent(
    name="rss_monitor_system",
    model="gemini-2.0-flash-exp",
    description="Monitors RSS feeds for Roblox economy news, updates, and policy changes",
    instruction=return_instructions_rss(),
    tools=[
        monitor_roblox_feeds,
        analyze_economy_news,
        track_update_announcements,
        detect_policy_changes,
        get_competitor_news,
        create_news_summary_report
    ]
)

logger.info("RSS Monitor Agent initialized")
