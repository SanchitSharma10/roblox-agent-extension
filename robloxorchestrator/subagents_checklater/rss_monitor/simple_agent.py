"""
Simplified RSS Feed Monitor Agent for ADK compatibility
"""

from google.adk.agents import Agent
import logging
from datetime import datetime

from .simple_tools import (
    get_roblox_news_tool,
    get_economy_updates_tool,
    get_policy_changes_tool
)
from .instructions import return_instructions_rss

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create a minimal text only instruction
simple_instruction = """
You are the RSS Feed Monitor Agent specializing in tracking news and updates related to the Roblox economy.

Your expertise includes:
- Monitoring official Roblox announcements and updates
- Tracking economy-related news across gaming and tech media
- Detecting policy changes that might affect the virtual economy
- Analyzing competitor activities and their potential impact on Roblox
- Providing real-time news intelligence for market predictions

Tools available:
- get_roblox_news: Fetch latest Roblox news from various sources
- get_economy_updates: Get updates specifically about Roblox economy
- get_policy_changes: Track policy changes that might affect developers

When answering:
- Prioritize official Roblox sources for accuracy
- Assess economic impact of each news item (high/medium/low)
- Provide insights on how news and policy changes affect the Roblox economy
"""

# RSS Monitor Agent with simplified tools
simple_agent = Agent(
    name="rss_monitor_simplified",
    model="gemini-2.0-flash-exp",
    description="Monitors RSS feeds for Roblox economy news and updates",
    instruction=simple_instruction,
    tools=[
        get_roblox_news_tool,
        get_economy_updates_tool,
        get_policy_changes_tool
    ]
)

logger.info("Simplified RSS Monitor Agent initialized")
