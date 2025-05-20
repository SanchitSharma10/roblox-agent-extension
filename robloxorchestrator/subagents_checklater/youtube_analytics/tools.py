#!/usr/bin/env python3
"""
YouTube Analytics Tools
Comprehensive YouTube monitoring for Roblox economy intelligence
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import isodate
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("youtube_analytics.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("youtube_analytics")

class YouTubeAnalyzer:
    def __init__(self):
        """Initialize YouTube analyzer with API key"""
        api_key = os.environ.get("YOUTUBE_API_KEY")
        if not api_key:
            logger.warning("YOUTUBE_API_KEY not found in environment variables")
            self.youtube = None
        else:
            self.youtube = build("youtube", "v3", developerKey=api_key)
        
        logger.info("YouTube Analyzer initialized")
        
        # Define Roblox creators to monitor
        self.top_creators = [
            "Roblox", "KreekCraft", "Denis", "Flamingo", "InquisitorMaster",
            "PrestonPlayz", "LankyBox", "ThinknoodleOfficial", "Leah Ashe", 
            "iamSanna", "DanTDM", "ThinkNoodles", "Sketch", "Poke"
        ]
        
        # Roblox-related keywords
        self.roblox_keywords = [
            "roblox", "robux", "bloxburg", "adopt me", "brookhaven",
            "royale high", "blox fruits", "piggy", "pet simulator", "jailbreak"
        ]
        
        # Economy-related keywords
        self.economy_keywords = [
            "robux", "trading", "limiteds", "economy", "developer exchange",
            "devex", "ugc", "marketplace", "premium", "monetization"
        ]

    def search_videos(self, query: str, max_results: int = 10, published_after: Optional[str] = None):
        """Search for videos with the given query"""
        try:
            if not self.youtube:
                return {"error": "YouTube API key not configured", "success": False}
            
            # Prepare published after parameter if provided
            if published_after:
                published_after_param = published_after
            else:
                # Default to 7 days ago
                week_ago = (datetime.now() - timedelta(days=7)).isoformat() + "Z"
                published_after_param = week_ago
            
            logger.info(f"Searching for videos with query: {query}, published after: {published_after_param}")
            
            search_response = self.youtube.search().list(
                q=query,
                part="id,snippet",
                maxResults=max_results,
                type="video",
                publishedAfter=published_after_param,
                relevanceLanguage="en",
                safeSearch="moderate"
            ).execute()
            
            videos = []
            for item in search_response.get("items", []):
                video_id = item["id"]["videoId"]
                videos.append({
                    "id": video_id,
                    "title": item["snippet"]["title"],
                    "channel_title": item["snippet"]["channelTitle"],
                    "channel_id": item["snippet"]["channelId"],
                    "published_at": item["snippet"]["publishedAt"],
                    "thumbnail": item["snippet"]["thumbnails"]["high"]["url"],
                    "url": f"https://www.youtube.com/watch?v={video_id}"
                })
            
            logger.info(f"Found {len(videos)} videos for query: {query}")
            
            return {
                "success": True,
                "query": query,
                "videos": videos,
                "total_results": len(videos)
            }
            
        except HttpError as e:
            logger.error(f"Error searching videos: {str(e)}")
            return {"error": str(e), "success": False}
        except Exception as e:
            logger.error(f"Unexpected error searching videos: {str(e)}")
            return {"error": str(e), "success": False}

    def get_video_details(self, video_ids: List[str]):
        """Get detailed information for specific videos"""
        try:
            if not self.youtube:
                return {"error": "YouTube API key not configured", "success": False}
            
            logger.info(f"Getting details for {len(video_ids)} videos")
            
            # Split video IDs into chunks of 50 (API limit)
            video_chunks = [video_ids[i:i+50] for i in range(0, len(video_ids), 50)]
            
            all_videos = []
            for chunk in video_chunks:
                video_response = self.youtube.videos().list(
                    id=",".join(chunk),
                    part="snippet,contentDetails,statistics"
                ).execute()
                
                for item in video_response.get("items", []):
                    video_data = {
                        "id": item["id"],
                        "title": item["snippet"]["title"],
                        "channel_title": item["snippet"]["channelTitle"],
                        "channel_id": item["snippet"]["channelId"],
                        "published_at": item["snippet"]["publishedAt"],
                        "description": item["snippet"]["description"],
                        "thumbnails": item["snippet"]["thumbnails"],
                        "tags": item["snippet"].get("tags", []),
                        "duration": isodate.parse_duration(item["contentDetails"]["duration"]).total_seconds(),
                        "view_count": int(item["statistics"].get("viewCount", 0)),
                        "like_count": int(item["statistics"].get("likeCount", 0)),
                        "comment_count": int(item["statistics"].get("commentCount", 0)),
                        "url": f"https://www.youtube.com/watch?v={item['id']}"
                    }
                    all_videos.append(video_data)
            
            return {
                "success": True,
                "videos": all_videos,
                "total_videos": len(all_videos)
            }
            
        except HttpError as e:
            logger.error(f"Error getting video details: {str(e)}")
            return {"error": str(e), "success": False}
        except Exception as e:
            logger.error(f"Unexpected error getting video details: {str(e)}")
            return {"error": str(e), "success": False}

    def get_channel_videos(self, channel_id: str, max_results: int = 10):
        """Get recent videos from a specific channel"""
        try:
            if not self.youtube:
                return {"error": "YouTube API key not configured", "success": False}
            
            logger.info(f"Getting videos for channel: {channel_id}")
            
            # First get uploads playlist ID for the channel
            channel_response = self.youtube.channels().list(
                id=channel_id,
                part="contentDetails"
            ).execute()
            
            if not channel_response.get("items"):
                return {"error": "Channel not found", "success": False}
            
            uploads_playlist_id = channel_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
            
            # Get videos from the uploads playlist
            playlist_response = self.youtube.playlistItems().list(
                playlistId=uploads_playlist_id,
                part="snippet",
                maxResults=max_results
            ).execute()
            
            video_ids = [item["snippet"]["resourceId"]["videoId"] for item in playlist_response.get("items", [])]
            
            # Get detailed info for these videos
            if video_ids:
                return self.get_video_details(video_ids)
            else:
                return {
                    "success": True,
                    "videos": [],
                    "total_videos": 0
                }
            
        except HttpError as e:
            logger.error(f"Error getting channel videos: {str(e)}")
            return {"error": str(e), "success": False}
        except Exception as e:
            logger.error(f"Unexpected error getting channel videos: {str(e)}")
            return {"error": str(e), "success": False}

    def analyze_video_engagement(self, videos: List[Dict[str, Any]]):
        """Analyze engagement metrics for a list of videos"""
        try:
            logger.info(f"Analyzing engagement for {len(videos)} videos")
            
            for video in videos:
                # Calculate engagement ratio (likes + comments per view)
                if video.get("view_count", 0) > 0:
                    video["engagement_ratio"] = (video.get("like_count", 0) + video.get("comment_count", 0)) / video["view_count"]
                else:
                    video["engagement_ratio"] = 0
                
                # Calculate virality score (views per hour since published)
                published_time = datetime.fromisoformat(video["published_at"].replace("Z", "+00:00"))
                hours_since_published = max(1, (datetime.now().astimezone() - published_time).total_seconds() / 3600)
                video["virality_score"] = video.get("view_count", 0) / hours_since_published
                
                # Determine engagement level
                if video["engagement_ratio"] >= 0.1:
                    video["engagement_level"] = "high"
                elif video["engagement_ratio"] >= 0.05:
                    video["engagement_level"] = "medium"
                else:
                    video["engagement_level"] = "low"
                
                # Determine virality level
                if video["virality_score"] >= 10000:
                    video["virality_level"] = "viral"
                elif video["virality_score"] >= 1000:
                    video["virality_level"] = "trending"
                else:
                    video["virality_level"] = "normal"
            
            return {
                "success": True,
                "videos_analyzed": len(videos),
                "analyzed_videos": videos,
                "high_engagement_videos": [v for v in videos if v.get("engagement_level") == "high"],
                "viral_videos": [v for v in videos if v.get("virality_level") == "viral"],
                "trending_videos": [v for v in videos if v.get("virality_level") == "trending"]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing video engagement: {str(e)}")
            return {"error": str(e), "success": False}

# Global YouTube analyzer instance
_youtube_analyzer = None

def get_youtube_analyzer():
    """Get or create YouTube analyzer instance"""
    global _youtube_analyzer
    if _youtube_analyzer is None:
        _youtube_analyzer = YouTubeAnalyzer()
    return _youtube_analyzer

# Tool Functions
async def get_trending_roblox_content(days: int = 7, max_results: int = 10) -> Dict[str, Any]:
    """Get trending Roblox-related content from YouTube.
    
    Args:
        days: Number of days to look back
        max_results: Maximum number of results to return
        
    Returns:
        Dictionary with trending videos data
    """
    try:
        logger.info(f"Getting trending Roblox content for past {days} days, max_results={max_results}")
        analyzer = get_youtube_analyzer()
        
        if not analyzer.youtube:
            return {
                "success": False,
                "error": "YouTube API key not configured. Please set the YOUTUBE_API_KEY environment variable.",
                "cache_notice": "This is a required step for YouTube data access."
            }
        
        # Calculate published_after date
        published_after = (datetime.now() - timedelta(days=days)).isoformat() + "Z"
        
        # Search for trending Roblox content
        search_results = analyzer.search_videos(
            query="roblox",
            max_results=max_results,
            published_after=published_after
        )
        
        if not search_results["success"]:
            return search_results
        
        # Get detailed info and analyze engagement
        if search_results["videos"]:
            video_ids = [video["id"] for video in search_results["videos"]]
            video_details = analyzer.get_video_details(video_ids)
            
            if not video_details["success"]:
                return video_details
            
            # Analyze engagement
            engagement_analysis = analyzer.analyze_video_engagement(video_details["videos"])
            
            if not engagement_analysis["success"]:
                return engagement_analysis
            
            # Sort by virality score
            trending_videos = sorted(
                engagement_analysis["analyzed_videos"],
                key=lambda x: x.get("virality_score", 0),
                reverse=True
            )
            
            # Group by channel
            videos_by_channel = {}
            for video in trending_videos:
                channel = video["channel_title"]
                if channel not in videos_by_channel:
                    videos_by_channel[channel] = []
                videos_by_channel[channel].append(video)
            
            # Find viral topics (from video titles and tags)
            keywords = {}
            for video in trending_videos:
                title_words = video["title"].lower().split()
                for word in title_words:
                    if len(word) > 4 and word not in ["roblox", "video", "minecraft"]:
                        keywords[word] = keywords.get(word, 0) + 1
                
                for tag in video.get("tags", []):
                    if len(tag) > 4 and tag.lower() not in ["roblox", "video", "minecraft"]:
                        keywords[tag.lower()] = keywords.get(tag.lower(), 0) + 1
            
            trending_topics = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                "success": True,
                "days_analyzed": days,
                "trending_videos": trending_videos[:max_results],
                "videos_by_channel": videos_by_channel,
                "viral_videos": engagement_analysis["viral_videos"],
                "trending_topics": trending_topics,
                "analysis_timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": True,
                "days_analyzed": days,
                "trending_videos": [],
                "message": "No videos found for the given criteria"
            }
        
    except Exception as e:
        logger.error(f"Error in get_trending_roblox_content: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "days": days,
            "max_results": max_results
        }

async def track_roblox_creators(creators: Optional[List[str]] = None, max_videos_per_creator: int = 5) -> Dict[str, Any]:
    """Track recent videos from popular Roblox creators.
    
    Args:
        creators: List of creator channels to track (defaults to top creators)
        max_videos_per_creator: Maximum videos to fetch per creator
        
    Returns:
        Dictionary with creator videos and analysis
    """
    try:
        logger.info(f"Tracking Roblox creators: {creators if creators else 'using default list'}")
        analyzer = get_youtube_analyzer()
        
        if not analyzer.youtube:
            return {
                "success": False,
                "error": "YouTube API key not configured. Please set the YOUTUBE_API_KEY environment variable."
            }
        
        # Use default creators if none provided
        if not creators:
            creators = analyzer.top_creators
        
        # Get channel IDs for creators
        all_creator_videos = []
        creator_data = {}
        
        for creator_name in creators[:10]:  # Limit to 10 creators to avoid exceeding quota
            # Search for the channel
            channel_search = analyzer.search_videos(
                query=f"channel:{creator_name}",
                max_results=1
            )
            
            if not channel_search["success"] or not channel_search["videos"]:
                continue
            
            channel_id = channel_search["videos"][0]["channel_id"]
            
            # Get videos for this channel
            channel_videos = analyzer.get_channel_videos(
                channel_id=channel_id,
                max_results=max_videos_per_creator
            )
            
            if channel_videos["success"] and channel_videos["videos"]:
                # Analyze engagement for these videos
                engagement_analysis = analyzer.analyze_video_engagement(channel_videos["videos"])
                
                if engagement_analysis["success"]:
                    creator_data[creator_name] = {
                        "channel_id": channel_id,
                        "recent_videos": engagement_analysis["analyzed_videos"],
                        "high_engagement_videos": engagement_analysis["high_engagement_videos"],
                        "viral_videos": engagement_analysis["viral_videos"],
                        "trending_videos": engagement_analysis["trending_videos"]
                    }
                    
                    all_creator_videos.extend(engagement_analysis["analyzed_videos"])
        
        # Find emerging trends across all creator videos
        keywords = {}
        for video in all_creator_videos:
            # Look for words in titles
            title_words = video["title"].lower().split()
            for word in title_words:
                if len(word) > 4 and word not in ["roblox", "video", "minecraft"]:
                    keywords[word] = keywords.get(word, 0) + 1
            
            # Look for words in tags
            for tag in video.get("tags", []):
                if len(tag) > 4 and tag.lower() not in ["roblox", "video", "minecraft"]:
                    keywords[tag.lower()] = keywords.get(tag.lower(), 0) + 1
        
        trending_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Calculate overall engagement metrics
        total_views = sum(video.get("view_count", 0) for video in all_creator_videos)
        total_likes = sum(video.get("like_count", 0) for video in all_creator_videos)
        total_comments = sum(video.get("comment_count", 0) for video in all_creator_videos)
        
        return {
            "success": True,
            "creators_tracked": list(creator_data.keys()),
            "creator_data": creator_data,
            "trending_keywords": trending_keywords,
            "overall_metrics": {
                "total_videos": len(all_creator_videos),
                "total_views": total_views,
                "total_likes": total_likes,
                "total_comments": total_comments,
                "average_views_per_video": total_views / len(all_creator_videos) if all_creator_videos else 0
            },
            "high_impact_creators": sorted(
                creator_data.keys(),
                key=lambda c: sum(v.get("view_count", 0) for v in creator_data[c]["recent_videos"]),
                reverse=True
            )[:3],
            "analysis_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in track_roblox_creators: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "creators": creators
        }

async def analyze_economy_videos(days: int = 30, max_results: int = 20) -> Dict[str, Any]:
    """Analyze videos specifically related to Roblox economy, trading, or monetization.
    
    Args:
        days: Number of days to look back
        max_results: Maximum number of results to return
        
    Returns:
        Dictionary with economy-related video analysis
    """
    try:
        logger.info(f"Analyzing Roblox economy videos for past {days} days")
        analyzer = get_youtube_analyzer()
        
        if not analyzer.youtube:
            return {
                "success": False,
                "error": "YouTube API key not configured. Please set the YOUTUBE_API_KEY environment variable."
            }
        
        # Calculate published_after date
        published_after = (datetime.now() - timedelta(days=days)).isoformat() + "Z"
        
        # Search for economy-related content
        all_economy_videos = []
        
        # Try different economy-related search terms
        for query in analyzer.economy_keywords[:5]:  # Limit to top 5 keywords to avoid quota issues
            search_query = f"roblox {query}"
            search_results = analyzer.search_videos(
                query=search_query,
                max_results=max_results // 5,  # Distribute results across keywords
                published_after=published_after
            )
            
            if search_results["success"] and search_results["videos"]:
                all_economy_videos.extend(search_results["videos"])
        
        # If we got videos, get detailed info and analyze
        if all_economy_videos:
            # Remove duplicates
            unique_video_ids = {}
            unique_videos = []
            for video in all_economy_videos:
                if video["id"] not in unique_video_ids:
                    unique_video_ids[video["id"]] = True
                    unique_videos.append(video)
            
            video_ids = list(unique_video_ids.keys())
            video_details = analyzer.get_video_details(video_ids[:50])  # Limit to 50 videos
            
            if not video_details["success"]:
                return video_details
            
            # Analyze engagement
            engagement_analysis = analyzer.analyze_video_engagement(video_details["videos"])
            
            if not engagement_analysis["success"]:
                return engagement_analysis
            
            # Categorize by specific topics
            video_categories = {
                "trading": [],
                "robux": [],
                "limited_items": [],
                "creator_earnings": [],
                "game_monetization": [],
                "other": []
            }
            
            for video in engagement_analysis["analyzed_videos"]:
                title = video["title"].lower()
                description = video["description"].lower()
                content = f"{title} {description}"
                
                if any(word in content for word in ["trading", "trade", "limiteds"]):
                    video_categories["trading"].append(video)
                elif any(word in content for word in ["robux", "currency"]):
                    video_categories["robux"].append(video)
                elif any(word in content for word in ["limited", "limiteds", "rare items"]):
                    video_categories["limited_items"].append(video)
                elif any(word in content for word in ["developer", "dev", "earning", "creator", "devex"]):
                    video_categories["creator_earnings"].append(video)
                elif any(word in content for word in ["monetization", "monetize", "gamepass", "vip", "premium"]):
                    video_categories["game_monetization"].append(video)
                else:
                    video_categories["other"].append(video)
            
            # Sort videos by engagement
            for category in video_categories:
                video_categories[category] = sorted(
                    video_categories[category],
                    key=lambda x: x.get("engagement_ratio", 0),
                    reverse=True
                )
            
            # Analyze sentiment (basic keyword approach)
            positive_words = ["profit", "growth", "success", "opportunity", "increase", "easy"]
            negative_words = ["scam", "loss", "waste", "problem", "issue", "risky", "ban"]
            
            sentiment_scores = {}
            for category, videos in video_categories.items():
                if not videos:
                    continue
                
                category_sentiment = 0
                for video in videos:
                    content = f"{video['title']} {video['description']}".lower()
                    positive_count = sum(1 for word in positive_words if word in content)
                    negative_count = sum(1 for word in negative_words if word in content)
                    
                    video_sentiment = positive_count - negative_count
                    category_sentiment += video_sentiment
                
                avg_sentiment = category_sentiment / len(videos)
                sentiment_scores[category] = {
                    "score": avg_sentiment,
                    "sentiment": "positive" if avg_sentiment > 0 else "negative" if avg_sentiment < 0 else "neutral"
                }
            
            return {
                "success": True,
                "days_analyzed": days,
                "unique_videos": len(unique_videos),
                "analyzed_videos": engagement_analysis["analyzed_videos"],
                "categories": video_categories,
                "top_videos": sorted(
                    engagement_analysis["analyzed_videos"],
                    key=lambda x: x.get("view_count", 0),
                    reverse=True
                )[:5],
                "sentiment_analysis": sentiment_scores,
                "analysis_timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": True,
                "days_analyzed": days,
                "unique_videos": 0,
                "message": "No economy-related videos found for the given criteria"
            }
        
    except Exception as e:
        logger.error(f"Error in analyze_economy_videos: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "days": days,
            "max_results": max_results
        }

async def detect_viral_roblox_content(hours: int = 24, threshold: int = 100000) -> Dict[str, Any]:
    """Detect viral Roblox content over a recent time period.
    
    Args:
        hours: Number of hours to look back for recent viral content
        threshold: View count threshold to consider content viral
        
    Returns:
        Dictionary with viral content analysis
    """
    try:
        logger.info(f"Detecting viral Roblox content in past {hours} hours with threshold {threshold} views")
        analyzer = get_youtube_analyzer()
        
        if not analyzer.youtube:
            return {
                "success": False,
                "error": "YouTube API key not configured. Please set the YOUTUBE_API_KEY environment variable."
            }
        
        # Calculate published_after date
        published_after = (datetime.now() - timedelta(hours=hours)).isoformat() + "Z"
        
        # Search for recent Roblox content
        search_results = analyzer.search_videos(
            query="roblox",
            max_results=50,  # Get more videos to filter down
            published_after=published_after
        )
        
        if not search_results["success"] or not search_results["videos"]:
            return {
                "success": search_results["success"],
                "error": search_results.get("error", "No videos found"),
                "videos": []
            }
        
        # Get detailed info for analysis
        video_ids = [video["id"] for video in search_results["videos"]]
        video_details = analyzer.get_video_details(video_ids)
        
        if not video_details["success"] or not video_details["videos"]:
            return {
                "success": video_details["success"],
                "error": video_details.get("error", "Failed to get video details"),
                "videos": []
            }
        
        # Filter for viral videos that meet the threshold
        viral_videos = [
            video for video in video_details["videos"]
            if video.get("view_count", 0) >= threshold
        ]
        
        # Further analyze viral videos
        if viral_videos:
            # Calculate virality metrics
            for video in viral_videos:
                published_time = datetime.fromisoformat(video["published_at"].replace("Z", "+00:00"))
                hours_since_published = max(1, (datetime.now().astimezone() - published_time).total_seconds() / 3600)
                
                video["hours_since_published"] = hours_since_published
                video["views_per_hour"] = video.get("view_count", 0) / hours_since_published
                video["engagement_ratio"] = (video.get("like_count", 0) + video.get("comment_count", 0)) / max(1, video.get("view_count", 0))
                
                # Classify virality level
                if video["views_per_hour"] >= 50000:
                    video["virality_level"] = "extreme"
                elif video["views_per_hour"] >= 20000:
                    video["virality_level"] = "very high"
                elif video["views_per_hour"] >= 10000:
                    video["virality_level"] = "high"
                else:
                    video["virality_level"] = "moderate"
            
            # Sort by virality
            viral_videos.sort(key=lambda x: x.get("views_per_hour", 0), reverse=True)
            
            # Group by virality level
            virality_groups = {
                "extreme": [],
                "very high": [],
                "high": [],
                "moderate": []
            }
            
            for video in viral_videos:
                level = video.get("virality_level", "moderate")
                virality_groups[level].append(video)
            
            # Extract topics from viral videos
            topics = {}
            for video in viral_videos:
                title_words = video["title"].lower().split()
                for word in title_words:
                    if len(word) > 4 and word not in ["roblox", "video", "this", "that", "what", "when"]:
                        topics[word] = topics.get(word, 0) + 1
            
            trending_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Detect virality patterns (e.g., specific creators, game updates)
            viral_creators = {}
            for video in viral_videos:
                creator = video["channel_title"]
                viral_creators[creator] = viral_creators.get(creator, 0) + 1
            
            top_viral_creators = sorted(viral_creators.items(), key=lambda x: x[1], reverse=True)
            
            return {
                "success": True,
                "hours_analyzed": hours,
                "view_threshold": threshold,
                "total_viral_videos": len(viral_videos),
                "viral_videos": viral_videos,
                "virality_groups": virality_groups,
                "trending_topics": trending_topics,
                "top_viral_creators": top_viral_creators[:5],
                "most_viral_video": viral_videos[0] if viral_videos else None,
                "analysis_timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": True,
                "hours_analyzed": hours,
                "view_threshold": threshold,
                "total_viral_videos": 0,
                "viral_videos": [],
                "message": f"No viral videos found that meet the {threshold} view threshold in the past {hours} hours"
            }
        
    except Exception as e:
        logger.error(f"Error in detect_viral_roblox_content: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "hours": hours,
            "threshold": threshold
        }

async def create_content_summary_report(days: int = 7) -> Dict[str, Any]:
    """Generate a comprehensive YouTube content summary report for Roblox economy.
    
    Args:
        days: Number of days to include in the report
        
    Returns:
        Dictionary with comprehensive content analysis
    """
    try:
        logger.info(f"Creating content summary report for past {days} days")
        
        # Gather all content analyses
        report_sections = {}
        
        # 1. Trending Roblox content
        trending_content = await get_trending_roblox_content(days=days, max_results=10)
        report_sections["trending_content"] = trending_content
        
        # 2. Top creator tracking
        creator_tracking = await track_roblox_creators(max_videos_per_creator=3)
        report_sections["creator_tracking"] = creator_tracking
        
        # 3. Economy videos analysis
        economy_analysis = await analyze_economy_videos(days=days, max_results=10)
        report_sections["economy_analysis"] = economy_analysis
        
        # 4. Viral content detection (last 48 hours)
        viral_content = await detect_viral_roblox_content(hours=48, threshold=50000)
        report_sections["viral_content"] = viral_content
        
        # Generate executive summary
        executive_summary = generate_content_executive_summary(report_sections)
        
        # Extract key insights
        key_insights = extract_key_content_insights(report_sections)
        
        # Identify market signals
        market_signals = identify_market_signals(report_sections)
        
        logger.info("Content summary report generation complete")
        
        return {
            "success": True,
            "report_type": "youtube_content_summary",
            "days_analyzed": days,
            "generated_at": datetime.now().isoformat(),
            "executive_summary": executive_summary,
            "key_insights": key_insights,
            "market_signals": market_signals,
            "sections": report_sections,
            "data_source": "YouTube",
            "recommendations": generate_content_recommendations(report_sections)
        }
        
    except Exception as e:
        logger.error(f"Error in create_content_summary_report: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "days": days
        }

# Helper functions
def generate_content_executive_summary(report_sections: Dict[str, Any]) -> str:
    """Generate executive summary from content report sections"""
    try:
        summary_parts = []
        
        # Trending content summary
        if "trending_content" in report_sections and report_sections["trending_content"].get("success"):
            trending = report_sections["trending_content"]
            viral_count = len(trending.get("viral_videos", []))
            trending_topics = trending.get("trending_topics", [])
            
            topic_text = ""
            if trending_topics:
                top_topics = [topic[0] for topic in trending_topics[:3]]
                topic_text = f" Key topics: {', '.join(top_topics)}."
                
            summary_parts.append(f"**Trending Content**: {viral_count} viral videos identified.{topic_text} ")
        
        # Creator tracking summary
        if "creator_tracking" in report_sections and report_sections["creator_tracking"].get("success"):
            creators = report_sections["creator_tracking"]
            tracked_count = len(creators.get("creators_tracked", []))
            top_creators = creators.get("high_impact_creators", [])
            
            creator_text = ""
            if top_creators:
                creator_text = f" Top creators: {', '.join(top_creators[:2])}."
                
            summary_parts.append(f"**Creator Activity**: Tracked {tracked_count} creators.{creator_text} ")
        
        # Economy analysis summary
        if "economy_analysis" in report_sections and report_sections["economy_analysis"].get("success"):
            economy = report_sections["economy_analysis"]
            video_count = economy.get("unique_videos", 0)
            
            # Get top category
            top_category = None
            max_count = 0
            for category, videos in economy.get("categories", {}).items():
                if len(videos) > max_count:
                    max_count = len(videos)
                    top_category = category
            
            category_text = f" Top content area: {top_category.replace('_', ' ')}." if top_category else ""
            
            summary_parts.append(f"**Economy Content**: {video_count} economy-related videos analyzed.{category_text} ")
        
        # Viral content summary
        if "viral_content" in report_sections and report_sections["viral_content"].get("success"):
            viral = report_sections["viral_content"]
            viral_count = viral.get("total_viral_videos", 0)
            most_viral = viral.get("most_viral_video", {})
            
            viral_text = ""
            if most_viral:
                viral_text = f" Most viral: \"{most_viral.get('title', '')}\" ({most_viral.get('views_per_hour', 0):.0f} views/hour)."
                
            summary_parts.append(f"**Viral Content**: {viral_count} viral videos in last 48 hours.{viral_text} ")
        
        return "".join(summary_parts) if summary_parts else "Unable to generate summary due to data collection issues."
        
    except Exception as e:
        logger.error(f"Error generating content summary: {str(e)}")
        return f"Error generating summary: {str(e)}"

def extract_key_content_insights(report_sections: Dict[str, Any]) -> List[str]:
    """Extract key insights from content report sections"""
    insights = []
    
    # Insights from trending content
    if "trending_content" in report_sections and report_sections["trending_content"].get("success"):
        trending = report_sections["trending_content"]
        trending_topics = trending.get("trending_topics", [])
        
        if trending_topics:
            insights.append(f"Top trending topics: {', '.join([t[0] for t in trending_topics[:3]])}")
        
        viral_videos = trending.get("viral_videos", [])
        if viral_videos:
            insights.append(f"Highest engagement video: \"{viral_videos[0].get('title', '')}\" with {viral_videos[0].get('engagement_ratio', 0):.2f} engagement ratio")
    
    # Insights from creator tracking
    if "creator_tracking" in report_sections and report_sections["creator_tracking"].get("success"):
        creators = report_sections["creator_tracking"]
        
        high_impact = creators.get("high_impact_creators", [])
        if high_impact:
            insights.append(f"Most influential creators: {', '.join(high_impact[:3])}")
        
        trending_keywords = creators.get("trending_keywords", [])
        if trending_keywords:
            insights.append(f"Creator content focus: {', '.join([k[0] for k in trending_keywords[:3]])}")
    
    # Insights from economy analysis
    if "economy_analysis" in report_sections and report_sections["economy_analysis"].get("success"):
        economy = report_sections["economy_analysis"]
        
        sentiment = economy.get("sentiment_analysis", {})
        positive_categories = [cat for cat, data in sentiment.items() if data.get("sentiment") == "positive"]
        negative_categories = [cat for cat, data in sentiment.items() if data.get("sentiment") == "negative"]
        
        if positive_categories:
            insights.append(f"Positive sentiment around: {', '.join([c.replace('_', ' ') for c in positive_categories])}")
        
        if negative_categories:
            insights.append(f"Negative sentiment around: {', '.join([c.replace('_', ' ') for c in negative_categories])}")
    
    return insights

def identify_market_signals(report_sections: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Identify market signals from content analysis"""
    signals = []
    
    # Signals from trending content
    if "trending_content" in report_sections and report_sections["trending_content"].get("success"):
        trending = report_sections["trending_content"]
        
        trending_topics = trending.get("trending_topics", [])
        if trending_topics:
            for topic, count in trending_topics[:5]:
                if topic in ["limiteds", "trading", "robux", "sale", "update", "event"]:
                    signals.append({
                        "type": "trending_topic",
                        "topic": topic,
                        "strength": "high" if count > 5 else "medium",
                        "description": f"High interest in {topic} detected across multiple videos"
                    })
    
    # Signals from economy analysis
    if "economy_analysis" in report_sections and report_sections["economy_analysis"].get("success"):
        economy = report_sections["economy_analysis"]
        
        categories = economy.get("categories", {})
        for category, videos in categories.items():
            if len(videos) > 3:  # If category has significant content
                sentiment = economy.get("sentiment_analysis", {}).get(category, {}).get("sentiment")
                
                if category == "trading" and len(videos) > 5:
                    signals.append({
                        "type": "market_activity",
                        "topic": "trading_volume",
                        "strength": "high",
                        "sentiment": sentiment,
                        "description": "High volume of trading-related content suggests increased market activity"
                    })
                
                if category == "limited_items" and len(videos) > 3:
                    signals.append({
                        "type": "market_activity",
                        "topic": "limited_items",
                        "strength": "medium",
                        "sentiment": sentiment,
                        "description": "Increased interest in limited items may indicate collector activity"
                    })
    
    # Signals from viral content
    if "viral_content" in report_sections and report_sections["viral_content"].get("success"):
        viral = report_sections["viral_content"]
        
        viral_videos = viral.get("viral_videos", [])
        for video in viral_videos:
            title = video.get("title", "").lower()
            
            if any(word in title for word in ["update", "new", "event"]):
                signals.append({
                    "type": "platform_update",
                    "topic": "game_update",
                    "strength": "high" if video.get("views_per_hour", 0) > 20000 else "medium",
                    "description": f"Viral video about update: \"{video.get('title')}\""
                })
            
            if any(word in title for word in ["economy", "robux", "trading", "limiteds", "ugc"]):
                signals.append({
                    "type": "economy_activity",
                    "topic": "economy_change",
                    "strength": "high" if video.get("views_per_hour", 0) > 20000 else "medium",
                    "description": f"Viral video about economy: \"{video.get('title')}\""
                })
    
    return signals

def generate_content_recommendations(report_sections: Dict[str, Any]) -> List[str]:
    """Generate actionable recommendations from content analysis"""
    recommendations = []
    
    # Based on trending content
    if "trending_content" in report_sections and report_sections["trending_content"].get("success"):
        trending = report_sections["trending_content"]
        trending_topics = trending.get("trending_topics", [])
        
        if trending_topics:
            top_topic = trending_topics[0][0]
            recommendations.append(f"Monitor {top_topic}-related marketplace activity for potential shifts in demand")
    
    # Based on creator tracking
    if "creator_tracking" in report_sections and report_sections["creator_tracking"].get("success"):
        creators = report_sections["creator_tracking"]
        high_impact = creators.get("high_impact_creators", [])
        
        if high_impact:
            recommendations.append(f"Track new uploads from {high_impact[0]} for potential market-moving announcements")
    
    # Based on economy analysis
    if "economy_analysis" in report_sections and report_sections["economy_analysis"].get("success"):
        economy = report_sections["economy_analysis"]
        sentiment = economy.get("sentiment_analysis", {})
        
        negative_categories = [cat for cat, data in sentiment.items() if data.get("sentiment") == "negative"]
        if negative_categories:
            cat = negative_categories[0].replace("_", " ")
            recommendations.append(f"Investigate creator concerns around {cat} highlighted in YouTube content")
    
    # General recommendations
    recommendations.extend([
        "Use trending topics as inputs for market forecasting models",
        "Monitor viral content for early indicators of market direction"
    ])
    
    return recommendations[:5]  # Limit to top 5 recommendations

async def analyze_video_comments(video_id: str, max_comments: int = 100) -> Dict[str, Any]:
    """Analyze comments on a specific YouTube video to extract insights.
    
    Args:
        video_id: The YouTube video ID to analyze
        max_comments: Maximum number of comments to analyze
        
    Returns:
        Dictionary with comment analysis and economic insights
    """
    try:
        logger.info(f"Analyzing comments for video {video_id}, max_comments={max_comments}")
        analyzer = get_youtube_analyzer()
        
        if not analyzer.youtube:
            return {
                "success": False,
                "error": "YouTube API key not configured. Please set the YOUTUBE_API_KEY environment variable.",
                "video_id": video_id
            }
        
        # First get video details
        video_details = await analyzer.get_video_details([video_id])
        
        if not video_details["success"] or not video_details["videos"]:
            return {
                "success": False,
                "error": "Failed to get video details",
                "video_id": video_id
            }
        
        video_info = video_details["videos"][0]
        
        # Fetch comments for the video
        try:
            comments_response = analyzer.youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=max_comments,
                order="relevance"
            ).execute()
            
            comments = []
            
            # Process comments
            for item in comments_response.get("items", []):
                comment = item["snippet"]["topLevelComment"]["snippet"]
                comments.append({
                    "id": item["id"],
                    "text": comment["textDisplay"],
                    "author": comment["authorDisplayName"],
                    "like_count": comment["likeCount"],
                    "published_at": comment["publishedAt"]
                })
            
            logger.info(f"Retrieved {len(comments)} comments for video {video_id}")
            
            # Analyze comments for economic mentions and sentiment
            economy_mentions = analyze_comments_for_economy(comments)
            
            # Analyze overall sentiment
            sentiment = analyze_comment_sentiment(comments)
            
            # Extract popular items mentioned
            mentioned_items = extract_mentioned_items(comments)
            
            # Get user engagement signals
            engagement_signals = analyze_user_engagement(comments)
            
            return {
                "success": True,
                "video_id": video_id,
                "video_title": video_info["title"],
                "channel_title": video_info["channel_title"],
                "total_comments": len(comments),
                "comments": comments[:10],  # Return only the top 10 comments for brevity
                "economy_mentions": economy_mentions,
                "sentiment": sentiment,
                "mentioned_items": mentioned_items,
                "engagement_signals": engagement_signals,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error fetching comments for video {video_id}: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to fetch comments: {str(e)}",
                "video_id": video_id
            }
            
    except Exception as e:
        logger.error(f"Error in analyze_video_comments: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "video_id": video_id
        }

async def discover_top_creators(query: str = "roblox", max_results: int = 10) -> Dict[str, Any]:
    """Dynamically discover top content creators for a specific query.
    
    Args:
        query: The search query to find creators (default: "roblox")
        max_results: Maximum number of creators to return
        
    Returns:
        Dictionary with discovered creators and their metrics
    """
    try:
        logger.info(f"Discovering top creators for query '{query}', max_results={max_results}")
        analyzer = get_youtube_analyzer()
        
        if not analyzer.youtube:
            return {
                "success": False,
                "error": "YouTube API key not configured. Please set the YOUTUBE_API_KEY environment variable.",
                "query": query
            }
        
        # Search for top channels related to the query
        try:
            search_response = analyzer.youtube.search().list(
                q=query,
                part="snippet",
                maxResults=max_results * 2,  # Get more to filter
                type="channel",
                order="relevance"
            ).execute()
            
            channels = []
            channel_ids = []
            
            # Extract channel information
            for item in search_response.get("items", []):
                channel_id = item["snippet"]["channelId"]
                if channel_id not in channel_ids:  # Avoid duplicates
                    channels.append({
                        "id": channel_id,
                        "title": item["snippet"]["channelTitle"],
                        "description": item["snippet"]["description"],
                        "thumbnail": item["snippet"]["thumbnails"]["high"]["url"] if "high" in item["snippet"]["thumbnails"] else item["snippet"]["thumbnails"]["default"]["url"]
                    })
                    channel_ids.append(channel_id)
            
            # Get detailed channel statistics
            if channel_ids:
                channels_response = analyzer.youtube.channels().list(
                    part="statistics,contentDetails",
                    id=",".join(channel_ids[:50])  # API limit
                ).execute()
                
                # Add statistics to channel data
                for channel_item in channels_response.get("items", []):
                    channel_id = channel_item["id"]
                    for channel in channels:
                        if channel["id"] == channel_id:
                            stats = channel_item["statistics"]
                            channel["subscriber_count"] = int(stats.get("subscriberCount", 0))
                            channel["video_count"] = int(stats.get("videoCount", 0))
                            channel["view_count"] = int(stats.get("viewCount", 0))
                            channel["uploads_playlist"] = channel_item["contentDetails"]["relatedPlaylists"]["uploads"]
                            break
            
            # Sort by subscriber count
            channels = sorted(
                [c for c in channels if "subscriber_count" in c],
                key=lambda x: x["subscriber_count"],
                reverse=True
            )
            
            # Get recent videos for each channel
            for channel in channels[:max_results]:
                try:
                    # Get uploads playlist
                    playlist_items = analyzer.youtube.playlistItems().list(
                        part="snippet",
                        playlistId=channel["uploads_playlist"],
                        maxResults=5
                    ).execute()
                    
                    recent_videos = []
                    for item in playlist_items.get("items", []):
                        video_id = item["snippet"]["resourceId"]["videoId"]
                        recent_videos.append({
                            "id": video_id,
                            "title": item["snippet"]["title"],
                            "published_at": item["snippet"]["publishedAt"],
                            "thumbnail": item["snippet"]["thumbnails"]["high"]["url"] if "high" in item["snippet"]["thumbnails"] else item["snippet"]["thumbnails"]["default"]["url"],
                            "url": f"https://www.youtube.com/watch?v={video_id}"
                        })
                    
                    channel["recent_videos"] = recent_videos
                    
                except Exception as e:
                    logger.error(f"Error getting recent videos for channel {channel['id']}: {str(e)}")
                    channel["recent_videos"] = []
            
            return {
                "success": True,
                "query": query,
                "creators": channels[:max_results],
                "total_creators": len(channels[:max_results]),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error searching for channels: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to search for channels: {str(e)}",
                "query": query
            }
            
    except Exception as e:
        logger.error(f"Error in discover_top_creators: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "query": query
        }

# Helper functions for comment analysis
def analyze_comments_for_economy(comments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze comments for economy-related mentions"""
    economy_keywords = {
        "robux": 0,
        "trading": 0,
        "limiteds": 0,
        "purchase": 0,
        "expensive": 0,
        "cheap": 0,
        "price": 0,
        "cost": 0,
        "worth": 0,
        "gamepass": 0,
        "developer": 0,
        "premium": 0,
        "ugc": 0,
        "marketplace": 0
    }
    
    economy_comments = []
    
    for comment in comments:
        text = comment["text"].lower()
        matched_keywords = []
        
        for keyword in economy_keywords:
            if keyword in text:
                economy_keywords[keyword] += 1
                matched_keywords.append(keyword)
        
        if matched_keywords:
            economy_comments.append({
                "text": comment["text"],
                "keywords": matched_keywords,
                "author": comment["author"],
                "likes": comment["like_count"]
            })
    
    # Sort keywords by frequency
    sorted_keywords = sorted(
        economy_keywords.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    return {
        "economy_comments": economy_comments,
        "keyword_frequency": sorted_keywords,
        "total_economy_mentions": len(economy_comments),
        "percentage_of_comments": (len(economy_comments) / len(comments) * 100) if comments else 0
    }

def analyze_comment_sentiment(comments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze sentiment in comments using keyword-based approach"""
    positive_words = ["good", "great", "amazing", "awesome", "love", "best", "cool", "worth", "recommend"]
    negative_words = ["bad", "terrible", "awful", "worst", "hate", "sucks", "boring", "expensive", "waste"]
    
    positive_count = 0
    negative_count = 0
    neutral_count = 0
    
    sentiment_comments = {
        "positive": [],
        "negative": [],
        "neutral": []
    }
    
    for comment in comments:
        text = comment["text"].lower()
        positive_matches = sum(1 for word in positive_words if word in text)
        negative_matches = sum(1 for word in negative_words if word in text)
        
        if positive_matches > negative_matches:
            positive_count += 1
            sentiment_comments["positive"].append({
                "text": comment["text"],
                "author": comment["author"],
                "likes": comment["like_count"]
            })
        elif negative_matches > positive_matches:
            negative_count += 1
            sentiment_comments["negative"].append({
                "text": comment["text"],
                "author": comment["author"],
                "likes": comment["like_count"]
            })
        else:
            neutral_count += 1
            sentiment_comments["neutral"].append({
                "text": comment["text"],
                "author": comment["author"],
                "likes": comment["like_count"]
            })
    
    total = len(comments)
    
    return {
        "positive_count": positive_count,
        "negative_count": negative_count,
        "neutral_count": neutral_count,
        "positive_percentage": (positive_count / total * 100) if total > 0 else 0,
        "negative_percentage": (negative_count / total * 100) if total > 0 else 0,
        "neutral_percentage": (neutral_count / total * 100) if total > 0 else 0,
        "overall_sentiment": "positive" if positive_count > negative_count else "negative" if negative_count > positive_count else "neutral",
        "sentiment_examples": {
            "positive": sentiment_comments["positive"][:3],
            "negative": sentiment_comments["negative"][:3]
        }
    }

def extract_mentioned_items(comments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract Roblox items, games, and features mentioned in comments"""
    roblox_games = [
        "adopt me", "brookhaven", "royale high", "blox fruits", 
        "pet simulator", "murder mystery", "jailbreak", "arsenal",
        "tower of hell", "bee swarm simulator", "islands", "build a boat",
        "meep city", "piggy", "shindo life", "anime fighting simulator"
    ]
    
    roblox_items = [
        "limited", "ugc", "robux", "avatar", "pet", "weapon", "accessory",
        "hair", "face", "shirt", "pants", "hat", "back", "waist", "gamepass"
    ]
    
    game_mentions = {}
    item_mentions = {}
    
    for comment in comments:
        text = comment["text"].lower()
        
        # Check for game mentions
        for game in roblox_games:
            if game in text:
                game_mentions[game] = game_mentions.get(game, 0) + 1
        
        # Check for item mentions
        for item in roblox_items:
            if item in text:
                item_mentions[item] = item_mentions.get(item, 0) + 1
    
    # Sort by frequency
    sorted_games = sorted(game_mentions.items(), key=lambda x: x[1], reverse=True)
    sorted_items = sorted(item_mentions.items(), key=lambda x: x[1], reverse=True)
    
    # Extract comments about most mentioned games and items
    top_comments = []
    if sorted_games:
        top_game = sorted_games[0][0]
        game_comments = [c for c in comments if top_game in c["text"].lower()]
        if game_comments:
            top_comments.append({
                "topic": top_game,
                "comment": game_comments[0]["text"],
                "likes": game_comments[0]["like_count"]
            })
    
    if sorted_items:
        top_item = sorted_items[0][0]
        item_comments = [c for c in comments if top_item in c["text"].lower()]
        if item_comments:
            top_comments.append({
                "topic": top_item,
                "comment": item_comments[0]["text"],
                "likes": item_comments[0]["like_count"]
            })
    
    return {
        "game_mentions": sorted_games[:5],
        "item_mentions": sorted_items[:5],
        "top_comments": top_comments,
        "total_mentions": sum(count for _, count in sorted_games + sorted_items)
    }

def analyze_user_engagement(comments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze user engagement patterns from comments"""
    engagement_categories = {
        "feature_requests": ["should add", "would be cool if", "can you add", "need to add", "feature request"],
        "questions": ["how do you", "how to", "where is", "can anyone", "does anyone", "is there a way"],
        "issues": ["bug", "glitch", "broken", "not working", "issue", "problem", "fix this"],
        "appreciation": ["thank you", "thanks for", "love this", "amazing video", "great content"],
        "criticism": ["dislike", "don't like", "hate this", "bad video", "waste of time"]
    }
    
    category_counts = {category: 0 for category in engagement_categories}
    category_examples = {category: [] for category in engagement_categories}
    
    for comment in comments:
        text = comment["text"].lower()
        
        for category, phrases in engagement_categories.items():
            if any(phrase in text for phrase in phrases):
                category_counts[category] += 1
                category_examples[category].append({
                    "text": comment["text"],
                    "author": comment["author"],
                    "likes": comment["like_count"]
                })
    
    # Sort examples by likes for each category
    for category in category_examples:
        category_examples[category] = sorted(
            category_examples[category],
            key=lambda x: x["likes"],
            reverse=True
        )[:2]  # Keep top 2 examples
    
    return {
        "category_counts": category_counts,
        "examples": category_examples,
        "primary_engagement": max(category_counts.items(), key=lambda x: x[1])[0] if any(category_counts.values()) else None,
        "engagement_ratio": sum(category_counts.values()) / len(comments) if comments else 0
    }

async def analyze_top_video_comments(query: str = "roblox", max_videos: int = 5, max_comments_per_video: int = 20) -> Dict[str, Any]:
    """Analyze comments across multiple top videos for a given query.
    
    Args:
        query: Search query for videos (default: "roblox")
        max_videos: Maximum number of videos to analyze
        max_comments_per_video: Maximum comments to fetch per video
        
    Returns:
        Dictionary with aggregated comment analysis across multiple videos
    """
    try:
        logger.info(f"Analyzing comments for top {max_videos} videos matching '{query}'")
        analyzer = get_youtube_analyzer()
        
        if not analyzer.youtube:
            return {
                "success": False,
                "error": "YouTube API key not configured. Please set the YOUTUBE_API_KEY environment variable.",
                "query": query
            }
        
        # Step 1: Find top videos using search
        search_results = analyzer.search_videos(
            query=query,
            max_results=max_videos
        )
        
        if not search_results["success"] or not search_results["videos"]:
            return {
                "success": False,
                "error": "Failed to find videos for the query",
                "query": query
            }
        
        # Step 2: Analyze comments for each video
        video_analyses = []
        aggregated_economy_mentions = {}
        all_economy_comments = []
        all_mentioned_items = {
            "game_mentions": {},
            "item_mentions": {}
        }
        sentiment_counts = {
            "positive": 0,
            "negative": 0,
            "neutral": 0
        }
        total_comments_analyzed = 0
        
        logger.info(f"Found {len(search_results['videos'])} videos, analyzing comments...")
        
        for video in search_results["videos"]:
            video_id = video["id"]
            
            # Analyze comments for this video
            comment_analysis = await analyze_video_comments(
                video_id=video_id,
                max_comments=max_comments_per_video
            )
            
            if comment_analysis["success"]:
                video_analyses.append({
                    "video_id": video_id,
                    "video_title": video["title"],
                    "channel": video["channel_title"],
                    "total_comments": comment_analysis.get("total_comments", 0),
                    "economy_mentions": comment_analysis.get("economy_mentions", {}).get("total_economy_mentions", 0),
                    "sentiment": comment_analysis.get("sentiment", {}).get("overall_sentiment", "neutral")
                })
                
                total_comments_analyzed += comment_analysis.get("total_comments", 0)
                
                # Aggregate economy mentions
                for keyword, count in comment_analysis.get("economy_mentions", {}).get("keyword_frequency", []):
                    aggregated_economy_mentions[keyword] = aggregated_economy_mentions.get(keyword, 0) + count
                
                # Collect economy comments
                all_economy_comments.extend(comment_analysis.get("economy_mentions", {}).get("economy_comments", []))
                
                # Aggregate mentioned items
                for game, count in comment_analysis.get("mentioned_items", {}).get("game_mentions", []):
                    all_mentioned_items["game_mentions"][game] = all_mentioned_items["game_mentions"].get(game, 0) + count
                
                for item, count in comment_analysis.get("mentioned_items", {}).get("item_mentions", []):
                    all_mentioned_items["item_mentions"][item] = all_mentioned_items["item_mentions"].get(item, 0) + count
                
                # Aggregate sentiment counts
                sentiment = comment_analysis.get("sentiment", {})
                sentiment_counts["positive"] += sentiment.get("positive_count", 0)
                sentiment_counts["negative"] += sentiment.get("negative_count", 0)
                sentiment_counts["neutral"] += sentiment.get("neutral_count", 0)
                
                logger.info(f"Analyzed {comment_analysis.get('total_comments', 0)} comments for video '{video['title']}'")
            else:
                logger.warning(f"Failed to analyze comments for video {video_id}: {comment_analysis.get('error', 'Unknown error')}")
        
        # Sort aggregated mentions
        sorted_economy_mentions = sorted(
            aggregated_economy_mentions.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        sorted_game_mentions = sorted(
            all_mentioned_items["game_mentions"].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        sorted_item_mentions = sorted(
            all_mentioned_items["item_mentions"].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Calculate overall sentiment
        overall_sentiment = "neutral"
        if sentiment_counts["positive"] > sentiment_counts["negative"]:
            overall_sentiment = "positive"
        elif sentiment_counts["negative"] > sentiment_counts["positive"]:
            overall_sentiment = "negative"
        
        # Calculate sentiment percentages
        total_sentiment = sum(sentiment_counts.values())
        sentiment_percentages = {
            "positive": (sentiment_counts["positive"] / total_sentiment * 100) if total_sentiment > 0 else 0,
            "negative": (sentiment_counts["negative"] / total_sentiment * 100) if total_sentiment > 0 else 0,
            "neutral": (sentiment_counts["neutral"] / total_sentiment * 100) if total_sentiment > 0 else 0
        }
        
        # Extract key insights
        key_insights = []
        
        # Add economy keyword insight
        if sorted_economy_mentions:
            top_keywords = [f"{keyword} ({count})" for keyword, count in sorted_economy_mentions[:3]]
            key_insights.append(f"Top economy terms in comments: {', '.join(top_keywords)}")
        
        # Add game mention insight
        if sorted_game_mentions:
            top_games = [f"{game} ({count})" for game, count in sorted_game_mentions[:3]]
            key_insights.append(f"Most discussed games: {', '.join(top_games)}")
        
        # Add item mention insight
        if sorted_item_mentions:
            top_items = [f"{item} ({count})" for item, count in sorted_item_mentions[:3]]
            key_insights.append(f"Most mentioned items: {', '.join(top_items)}")
        
        # Add sentiment insight
        key_insights.append(f"Overall comment sentiment is {overall_sentiment.upper()} " +
                           f"({sentiment_percentages['positive']:.1f}% positive, " +
                           f"{sentiment_percentages['negative']:.1f}% negative)")
        
        logger.info(f"Completed analysis of {len(video_analyses)} videos with {total_comments_analyzed} total comments")
        
        return {
            "success": True,
            "query": query,
            "videos_analyzed": len(video_analyses),
            "video_summaries": video_analyses,
            "total_comments_analyzed": total_comments_analyzed,
            "aggregated_insights": {
                "economy_keywords": sorted_economy_mentions[:10],
                "game_mentions": sorted_game_mentions[:10],
                "item_mentions": sorted_item_mentions[:10],
                "top_economy_comments": sorted(all_economy_comments, key=lambda x: x.get("likes", 0), reverse=True)[:5],
                "overall_sentiment": overall_sentiment,
                "sentiment_distribution": sentiment_percentages
            },
            "key_insights": key_insights,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in analyze_top_video_comments: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "query": query,
            "videos_attempted": max_videos
        }    

# Export tools
tools = [
    get_trending_roblox_content,
    track_roblox_creators,
    analyze_economy_videos,
    detect_viral_roblox_content,
    create_content_summary_report,
    analyze_video_comments,
    discover_top_creators,
    analyze_top_video_comments  # Add the new function here
]