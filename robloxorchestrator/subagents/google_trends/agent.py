#!/usr/bin/env python3
"""
Google Trends Agent for Roblox Economy Intelligence
Tracks search trends for Roblox-related terms and correlates with market movements
"""

from google.adk.agents import Agent
from .tools import (
    get_roblox_search_trends,
    analyze_item_search_patterns,
    track_seasonal_trends,
    compare_game_trends,
    detect_viral_events,
    get_regional_trend_analysis,
    analyze_regional_growth_markets,
    create_trends_report
)
from .instructions import return_instructions_trends


def setup_before_agent_call(callback_context):
    """Setup the Google Trends agent."""
    
    # Configure trend tracking parameters
    callback_context.state["trends_config"] = {
        "tracked_keywords": [
            "roblox", "robux", "roblox limiteds", "roblox trading",
            "roblox marketplace", "dominus", "roblox economy",
            "roblox rare items", "roblox investing", "rolimons"
        ],
        "item_keywords": [
            "dominus empyreus", "dominus frigidus", "dominus astra",
            "shaggy super saiyan", "workclock shades", "fedora"
        ],
        "game_keywords": [
            "adopt me roblox", "tower of hell", "brookhaven roblox",
            "arsenal roblox", "murder mystery 2"
        ],
        "regions": ["US", "GB", "CA", "AU", "BR", "KR", "JP"],
        "timeframes": ["1d", "7d", "30d", "3m", "12m"],
        "categories": [8, 13]  # Games category (8), Hobbies & Leisure (13)
    }
    
    # Set analysis parameters
    callback_context.state["analysis_scope"] = {
        "correlation_threshold": 0.7,
        "trend_significance": 20,  # Minimum search volume increase to consider significant
        "seasonal_analysis": True,
        "regional_comparison": True,
        "predictive_modeling": True
    }

# Google Trends Agent
google_trends_agent = Agent(
    name="google_trends_system",
    model="gemini-2.0-flash-exp",
    description="Analyzes Google search trends to predict and correlate with Roblox economy movements",
    instruction=return_instructions_trends(),
    tools=[
        get_roblox_search_trends,
        analyze_item_search_patterns,
        track_seasonal_trends,
        compare_game_trends,
        detect_viral_events,
        get_regional_trend_analysis,
        analyze_regional_growth_markets,
        create_trends_report
    ],
    output_key="trends_results"
)
