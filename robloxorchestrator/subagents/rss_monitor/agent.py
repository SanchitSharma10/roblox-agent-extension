#!/usr/bin/env python3
"""
RSS Feed Monitor Agent for Roblox Economy Intelligence
Tracks gaming news, Roblox updates, and economy-related articles
"""

from google.adk.agents import Agent
from .tools import (
    monitor_roblox_feeds,
    analyze_economy_news,
    track_update_announcements,
    detect_policy_changes,
    get_competitor_news,
    create_news_summary_report
)
from .instructions import return_instructions_rss


def setup_before_agent_call(callback_context):
    """Setup the RSS feed monitor agent."""
    
    # Configure RSS feed sources
    callback_context.state["rss_sources"] = {
        "official_roblox": [
            "https://blog.roblox.com/feed/",
            "https://devforum.roblox.com/latest.rss"
        ],
        "gaming_news": [
            "https://www.pcgamer.com/rss/",
            "https://www.gamesindustry.biz/rss",
            "https://venturebeat.com/games/feed/"
        ],
        "economy_news": [
            "https://www.coindesk.com/arc/outboundfeeds/rss/",
            "https://cointelegraph.com/rss",
            "https://decrypt.co/feed"
        ],
        "metaverse_news": [
            "https://www.roadtovr.com/feed/",
            "https://uploadvr.com/feed/"
        ]
    }
    
    # Configure monitoring scope
    callback_context.state["monitoring_scope"] = {
        "keywords": [
            "roblox", "robux", "virtual economy", "metaverse economy",
            "digital currency", "in-game economy", "virtual worlds"
        ],
        "update_frequency": "every_hour",
        "priority_sources": ["official_roblox"],
        "sentiment_analysis": True,
        "policy_tracking": True
    }

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
    ],
    output_key="rss_results"
)
