"""
YouTube Query Handler - Wrapper for YouTube tools to handle generic queries
"""

import logging
from typing import Dict, Any, List, Optional
from .tools import (
    get_trending_roblox_content,
    track_roblox_creators,
    analyze_economy_videos,
    detect_viral_roblox_content
)

# Use the existing logger
logger = logging.getLogger("youtube_analytics")

async def process_youtube_query(query: str) -> Dict[str, Any]:
    """Process a general YouTube query by routing it to the appropriate tool.
    
    Args:
        query: The user's query about YouTube content
        
    Returns:
        Results from the appropriate YouTube analysis function
    """
    try:
        logger.info(f"Processing YouTube query: {query}")
        query_lower = query.lower()
        
        # Route to the appropriate function based on query content
        if any(word in query_lower for word in ["trend", "popular", "viral"]) and "adopt me" in query_lower:
            # Get trending content with focus on Adopt Me
            result = await get_trending_roblox_content(days=30, max_results=20)
            
            # Filter results to focus on Adopt Me if needed
            if result.get("success") and result.get("trending_videos"):
                # Filter videos related to Adopt Me
                adopt_me_videos = [
                    video for video in result.get("trending_videos", [])
                    if "adopt me" in video.get("title", "").lower() or 
                       "adopt me" in video.get("description", "").lower()
                ]
                
                # Update the result with filtered videos
                if adopt_me_videos:
                    result["adopt_me_videos"] = adopt_me_videos
                    result["filtered_for"] = "Adopt Me"
                    result["filtered_video_count"] = len(adopt_me_videos)
            
            return result
            
        elif any(word in query_lower for word in ["creator", "youtuber", "channel"]):
            # Creator-focused query
            return await track_roblox_creators()
            
        elif any(word in query_lower for word in ["economy", "trading", "robux", "limited"]):
            # Economy-focused query
            return await analyze_economy_videos()
            
        elif any(word in query_lower for word in ["viral", "popular"]):
            # Viral content query
            return await detect_viral_roblox_content(hours=48)
            
        else:
            # Default to trending content
            return await get_trending_roblox_content()
            
    except Exception as e:
        logger.error(f"Error processing YouTube query: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to process YouTube query: {str(e)}",
            "query": query
        }
