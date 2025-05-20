"""
Tools for the Roblox Economy Orchestrator Agent
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import subagents
from .subagents.marketplace_analytics.agent import marketplace_agent
from .subagents.youtube_analytics.agent import youtube_agent
from .subagents.google_trends.agent import google_trends_agent
from .subagents.rss_monitor.agent import rss_monitor_agent
async def check_agent_status() -> Dict[str, str]:
    """
    Check the status of all subagents
    
    Returns:
        Dict with subagent status information
    """
    statuses = {}
    
    # Check marketplace agent
    try:
        if hasattr(marketplace_agent.root_agent, "get_status"):
            status = await marketplace_agent.root_agent.get_status()
            statuses["marketplace_analytics"] = status
        else:
            statuses["marketplace_analytics"] = "available"
    except Exception as e:
        logger.error(f"Error checking marketplace agent: {str(e)}")
        statuses["marketplace_analytics"] = "error"
    
    # Check YouTube agent
    try:
        if hasattr(youtube_agent.root_agent, "get_status"):
            status = await youtube_agent.root_agent.get_status()
            statuses["youtube_analytics"] = status
        else:
            statuses["youtube_analytics"] = "available"
    except Exception as e:
        logger.error(f"Error checking YouTube agent: {str(e)}")
        statuses["youtube_analytics"] = "error"
    
    # Check Google Trends agent
    try:
        if hasattr(google_trends_agent.root_agent, "get_status"):
            status = await google_trends_agent.root_agent.get_status()
            statuses["google_trends"] = status
        else:
            statuses["google_trends"] = "available"
    except Exception as e:
        logger.error(f"Error checking Google Trends agent: {str(e)}")
        statuses["google_trends"] = "error"
    
    # Check RSS agent
    try:
        if hasattr(rss_monitor_agent.root_agent, "get_status"):
            status = await rss_monitor_agent.root_agent.get_status()
            statuses["rss_monitor"] = status
        else:
            statuses["rss_monitor"] = "available"
    except Exception as e:
        logger.error(f"Error checking RSS agent: {str(e)}")
        statuses["rss_monitor"] = "error"
    
    return statuses

async def format_result(result_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format the result from the agent in a standard structure
    
    Args:
        result_data: Raw result data from the agent
        
    Returns:
        Formatted result
    """
    # Create a standard result format
    formatted_result = {
        "success": True,
        "summary": result_data.get("summary", ""),
        "data": result_data.get("data", {}),
        "execution_details": {
            "timestamp": datetime.now().isoformat(),
            "agents_used": result_data.get("agents_used", [])
        }
    }
    
    return formatted_result