#!/usr/bin/env python3
"""
YouTube Analytics Tools
Provides comprehensive YouTube data analysis for Roblox economy intelligence
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
from googleapiclient.discovery import build
from dotenv import load_dotenv
import asyncio
import re

# Load environment variables
load_dotenv()

class YouTubeAnalytics:
    def __init__(self):
        """Initialize YouTube API connection"""
        self.api_key = os.getenv('YOUTUBE_API_KEY')
        
        if not self.api_key:
            raise ValueError("YouTube API key not found in environment variables")
        
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)
        
        # Roblox-related keywords and channels
        self.roblox_keywords = [
            "roblox economy", "roblox trading", "limited items", "robux", 
            "dominus", "roblox marketplace", "roblox items", "rolimons",
            "roblox investing", "roblox rich", "roblox limiteds"
        ]
        
        # Known Roblox YouTubers (you can expand this list)
        self.roblox_creators = {
            "KreekCraft": "UCFkp5t8mQTBfq3yE6yKgkHg",
            "Flamingo": "UCYNmmnN75YD6fqIUYGUF8ZIg", 
            "RussoPlays": "UC4tgEZ5kGnEhGjwN0Yqg0nw",
            "Poke": "UC_jQE8JEpRxY0xR_D2qB-xQ",
            "TanqR": "UC6RYRHAKEoVc5CwJlNp-TPQ"
        }

    def search_videos(self, query: str, max_results: int = 50, 
                     published_after: datetime = None) -> List[Dict]:
        """Search for videos with specific query"""
        try:
            # Set default time range to last 7 days if not specified
            if published_after is None:
                published_after = datetime.now() - timedelta(days=7)
            
            request = self.youtube.search().list(
                part="snippet",
                q=query,
                type="video",
                order="relevance",
                maxResults=max_results,
                publishedAfter=published_after.isoformat() + 'Z'
            )
            
            response = request.execute()
            return response.get('items', [])
            
        except Exception as e:
            print(f"Error searching videos: {e}")
            return []

    def get_video_statistics(self, video_ids: List[str]) -> Dict:
        """Get detailed statistics for videos"""
        try:
            request = self.youtube.videos().list(
                part="statistics,snippet",
                id=','.join(video_ids[:50])  # API limit
            )
            
            response = request.execute()
            return response.get('items', [])
            
        except Exception as e:
            print(f"Error getting video statistics: {e}")
            return []

    def get_channel_videos(self, channel_id: str, max_results: int = 20) -> List[Dict]:
        """Get recent videos from a specific channel"""
        try:
            request = self.youtube.search().list(
                part="snippet",
                channelId=channel_id,
                type="video",
                order="date",
                maxResults=max_results
            )
            
            response = request.execute()
            return response.get('items', [])
            
        except Exception as e:
            print(f"Error getting channel videos: {e}")
            return []

# Global instance
_youtube_analytics = None

def get_youtube_instance():
    """Get or create YouTube analytics instance"""
    global _youtube_analytics
    if _youtube_analytics is None:
        try:
            _youtube_analytics = YouTubeAnalytics()
        except Exception as e:
            print(f"Warning: Could not initialize YouTube Analytics: {e}")
    return _youtube_analytics

# Tool Functions
async def get_roblox_content_trends(time_period: str = "week", max_videos: int = 100):
    """Analyze trending Roblox content on YouTube.
    
    Args:
        time_period: Time period for analysis (day, week, month)
        max_videos: Maximum number of videos to analyze
        
    Returns:
        Dictionary with trending content analysis
    """
    yt = get_youtube_instance()
    if yt is None:
        return {"error": "YouTube Analytics not available"}
    
    try:
        # Map time period to days
        time_map = {"day": 1, "week": 7, "month": 30}
        days = time_map.get(time_period, 7)
        published_after = datetime.now() - timedelta(days=days)
        
        trends_data = {}
        
        # Search for each keyword
        for keyword in yt.roblox_keywords:
            videos = yt.search_videos(keyword, max_results=max_videos//len(yt.roblox_keywords), 
                                    published_after=published_after)
            trends_data[keyword] = len(videos)
        
        # Get most popular videos for general analysis
        popular_videos = yt.search_videos("roblox", max_results=20, published_after=published_after)
        
        # Get video IDs for statistics
        video_ids = [video['id']['videoId'] for video in popular_videos if 'videoId' in video['id']]
        video_stats = yt.get_video_statistics(video_ids)
        
        # Analyze trends
        trending_topics = []
        total_views = 0
        
        for video in video_stats:
            if 'statistics' in video:
                views = int(video['statistics'].get('viewCount', 0))
                total_views += views
                
                # Extract trending topics from titles
                title = video['snippet']['title'].lower()
                for keyword in yt.roblox_keywords:
                    if keyword.lower() in title:
                        trending_topics.append({
                            "keyword": keyword,
                            "title": video['snippet']['title'],
                            "views": views,
                            "published": video['snippet']['publishedAt']
                        })
        
        return {
            "success": True,
            "time_period": time_period,
            "keyword_trends": trends_data,
            "total_videos_analyzed": len(popular_videos),
            "total_views": total_views,
            "trending_topics": trending_topics[:10],  # Top 10
            "analysis_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "time_period": time_period
        }

async def analyze_creator_mentions(item_names: List[str] = [], creator_filter: str = "all"):
    """Analyze which Roblox creators are mentioning specific items.
    
    Args:
        item_names: List of item names to track (optional)
        creator_filter: Filter by creator (all, top_creators, specific_channel)
        
    Returns:
        Dictionary with creator mention analysis
    """
    yt = get_youtube_instance()
    if yt is None:
        return {"error": "YouTube Analytics not available"}
    
    try:
        creator_mentions = {}
        
        # If no items specified, use popular item keywords
        if not item_names:
            item_names = ["dominus", "limiteds", "expensive roblox items", "rare items"]
        
        # Analyze mentions by creator
        for creator_name, channel_id in yt.roblox_creators.items():
            creator_mentions[creator_name] = {
                "channel_id": channel_id,
                "item_mentions": {},
                "total_videos": 0,
                "total_views": 0
            }
            
            # Get recent videos from creator
            videos = yt.get_channel_videos(channel_id, max_results=20)
            creator_mentions[creator_name]["total_videos"] = len(videos)
            
            # Check for item mentions in titles and descriptions
            for item in item_names:
                mentions = []
                for video in videos:
                    title = video['snippet']['title'].lower()
                    description = video['snippet']['description'].lower()
                    
                    if item.lower() in title or item.lower() in description:
                        mentions.append({
                            "video_id": video['id']['videoId'],
                            "title": video['snippet']['title'],
                            "published": video['snippet']['publishedAt'],
                            "mentioned_in": "title" if item.lower() in title else "description"
                        })
                
                creator_mentions[creator_name]["item_mentions"][item] = mentions
        
        return {
            "success": True,
            "creator_analysis": creator_mentions,
            "items_tracked": item_names,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "items_tracked": item_names or []
        }

async def get_viral_roblox_videos(min_views: int = 100000, time_period: str = "week"):
    """Find viral Roblox videos that might indicate market trends.
    
    Args:
        min_views: Minimum view count to consider viral
        time_period: Time period to analyze (day, week, month)
        
    Returns:
        Dictionary with viral video analysis
    """
    yt = get_youtube_instance()
    if yt is None:
        return {"error": "YouTube Analytics not available"}
    
    try:
        # Map time period to days
        time_map = {"day": 1, "week": 7, "month": 30}
        days = time_map.get(time_period, 7)
        published_after = datetime.now() - timedelta(days=days)
        
        # Search for popular Roblox videos
        videos = yt.search_videos("roblox", max_results=50, published_after=published_after)
        
        # Get video IDs for statistics
        video_ids = [video['id']['videoId'] for video in videos if 'videoId' in video['id']]
        video_stats = yt.get_video_statistics(video_ids)
        
        # Filter viral videos
        viral_videos = []
        for video in video_stats:
            if 'statistics' in video:
                views = int(video['statistics'].get('viewCount', 0))
                if views >= min_views:
                    viral_videos.append({
                        "title": video['snippet']['title'],
                        "channel": video['snippet']['channelTitle'],
                        "views": views,
                        "likes": int(video['statistics'].get('likeCount', 0)),
                        "published": video['snippet']['publishedAt'],
                        "video_id": video['id'],
                        "thumbnail": video['snippet']['thumbnails']['high']['url']
                    })
        
        # Sort by views
        viral_videos.sort(key=lambda x: x['views'], reverse=True)
        
        # Analyze trends from viral content
        trend_keywords = {}
        for video in viral_videos:
            title = video['title'].lower()
            for keyword in yt.roblox_keywords:
                if keyword.lower() in title:
                    trend_keywords[keyword] = trend_keywords.get(keyword, 0) + 1
        
        return {
            "success": True,
            "viral_videos": viral_videos[:20],  # Top 20
            "total_viral_videos": len(viral_videos),
            "trend_keywords": trend_keywords,
            "min_views_threshold": min_views,
            "time_period": time_period,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "min_views_threshold": min_views,
            "time_period": time_period
        }

async def track_game_popularity(game_names: List[str] = [], time_period: str = "week"):
    """Track popularity of specific Roblox games on YouTube.
    
    Args:
        game_names: List of game names to track
        time_period: Time period for analysis
        
    Returns:
        Dictionary with game popularity analysis
    """
    yt = get_youtube_instance()
    if yt is None:
        return {"error": "YouTube Analytics not available"}
    
    try:
        # Default games to track if none specified
        if not game_names:
            game_names = [
                "Adopt Me", "Brookhaven", "Tower of Hell", "Arsenal", 
                "Piggy", "Murder Mystery 2", "Royale High", "Bloxburg"
            ]
        
        # Map time period to days
        time_map = {"day": 1, "week": 7, "month": 30}
        days = time_map.get(time_period, 7)
        published_after = datetime.now() - timedelta(days=days)
        
        game_popularity = {}
        
        for game in game_names:
            # Search for game-specific content
            query = f"roblox {game}"
            videos = yt.search_videos(query, max_results=30, published_after=published_after)
            
            # Get video statistics
            video_ids = [video['id']['videoId'] for video in videos if 'videoId' in video['id']]
            video_stats = yt.get_video_statistics(video_ids)
            
            # Calculate metrics
            total_views = 0
            total_videos = len(video_stats)
            avg_views = 0
            top_video = None
            max_views = 0
            
            for video in video_stats:
                if 'statistics' in video:
                    views = int(video['statistics'].get('viewCount', 0))
                    total_views += views
                    
                    if views > max_views:
                        max_views = views
                        top_video = {
                            "title": video['snippet']['title'],
                            "channel": video['snippet']['channelTitle'],
                            "views": views,
                            "published": video['snippet']['publishedAt']
                        }
            
            avg_views = total_views / total_videos if total_videos > 0 else 0
            
            game_popularity[game] = {
                "total_videos": total_videos,
                "total_views": total_views,
                "average_views": round(avg_views),
                "top_video": top_video,
                "popularity_score": round(total_views / 1000)  # Simplified score
            }
        
        # Rank games by popularity
        ranked_games = sorted(game_popularity.items(), 
                            key=lambda x: x[1]['total_views'], reverse=True)
        
        return {
            "success": True,
            "game_popularity": game_popularity,
            "ranked_games": ranked_games,
            "time_period": time_period,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "games_tracked": game_names or [],
            "time_period": time_period
        }

async def get_youtube_market_sentiment(keywords: List[str] = []):
    """Analyze sentiment around Roblox economy topics on YouTube.
    
    Args:
        keywords: Specific keywords to analyze sentiment for
        
    Returns:
        Dictionary with sentiment analysis
    """
    yt = get_youtube_instance()
    if yt is None:
        return {"error": "YouTube Analytics not available"}
    
    try:
        # Default keywords if none provided
        if not keywords:
            keywords = ["roblox economy", "roblox trading", "roblox limiteds", "robux prices"]
        
        sentiment_data = {}
        
        for keyword in keywords:
            videos = yt.search_videos(keyword, max_results=20)
            
            # Analyze titles for sentiment indicators
            positive_indicators = ["profit", "win", "success", "best", "amazing", "rich"]
            negative_indicators = ["crash", "lose", "scam", "worst", "dead", "broken"]
            
            sentiment_scores = {
                "positive": 0,
                "negative": 0,
                "neutral": 0,
                "total": len(videos)
            }
            
            sentiment_examples = {
                "positive": [],
                "negative": [],
                "neutral": []
            }
            
            for video in videos:
                title = video['snippet']['title'].lower()
                description = video['snippet']['description'].lower()
                
                positive_count = sum(1 for word in positive_indicators if word in title or word in description)
                negative_count = sum(1 for word in negative_indicators if word in title or word in description)
                
                if positive_count > negative_count:
                    sentiment_scores["positive"] += 1
                    sentiment_examples["positive"].append(video['snippet']['title'][:80])
                elif negative_count > positive_count:
                    sentiment_scores["negative"] += 1
                    sentiment_examples["negative"].append(video['snippet']['title'][:80])
                else:
                    sentiment_scores["neutral"] += 1
                    sentiment_examples["neutral"].append(video['snippet']['title'][:80])
            
            # Calculate percentages
            total = sentiment_scores["total"]
            sentiment_percentages = {
                "positive": round((sentiment_scores["positive"] / total) * 100, 1) if total > 0 else 0,
                "negative": round((sentiment_scores["negative"] / total) * 100, 1) if total > 0 else 0,
                "neutral": round((sentiment_scores["neutral"] / total) * 100, 1) if total > 0 else 0
            }
            
            sentiment_data[keyword] = {
                "scores": sentiment_scores,
                "percentages": sentiment_percentages,
                "examples": sentiment_examples,
                "overall_sentiment": "positive" if sentiment_percentages["positive"] > 50 else 
                                  "negative" if sentiment_percentages["negative"] > 40 else "neutral"
            }
        
        return {
            "success": True,
            "sentiment_analysis": sentiment_data,
            "keywords_analyzed": keywords,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "keywords_analyzed": keywords or []
        }

async def create_youtube_analytics_report(time_period: str = "week"):
    """Generate comprehensive YouTube analytics report.
    
    Args:
        time_period: Time period for the report
        
    Returns:
        Dictionary with comprehensive YouTube analytics
    """
    try:
        # Gather all analytics
        report_sections = {}
        
        # 1. Content trends
        trends = await get_roblox_content_trends(time_period)
        report_sections["content_trends"] = trends
        
        # 2. Creator analysis
        creator_analysis = await analyze_creator_mentions()
        report_sections["creator_analysis"] = creator_analysis
        
        # 3. Viral videos
        viral_videos = await get_viral_roblox_videos(time_period=time_period)
        report_sections["viral_content"] = viral_videos
        
        # 4. Game popularity
        game_popularity = await track_game_popularity(time_period=time_period)
        report_sections["game_popularity"] = game_popularity
        
        # 5. Market sentiment
        sentiment = await get_youtube_market_sentiment()
        report_sections["market_sentiment"] = sentiment
        
        # Generate executive summary
        executive_summary = generate_youtube_executive_summary(report_sections)
        
        return {
            "success": True,
            "report_type": "youtube_analytics",
            "time_period": time_period,
            "generated_at": datetime.now().isoformat(),
            "executive_summary": executive_summary,
            "sections": report_sections,
            "data_sources": ["YouTube API v3"],
            "total_videos_analyzed": sum([
                section.get("total_videos_analyzed", 0) 
                for section in report_sections.values() 
                if isinstance(section, dict)
            ])
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "report_type": "youtube_analytics",
            "time_period": time_period
        }

def generate_youtube_executive_summary(report_sections: Dict) -> str:
    """Generate executive summary from YouTube analytics report."""
    try:
        summary_parts = []
        
        # Content trends summary
        if "content_trends" in report_sections and report_sections["content_trends"].get("success"):
            trends = report_sections["content_trends"]
            total_videos = trends.get("total_videos_analyzed", 0)
            total_views = trends.get("total_views", 0)
            summary_parts.append(
                f"**Content Analysis**: Analyzed {total_videos} videos with {total_views:,} total views. "
            )
        
        # Viral content summary
        if "viral_content" in report_sections and report_sections["viral_content"].get("success"):
            viral = report_sections["viral_content"]
            viral_count = viral.get("total_viral_videos", 0)
            summary_parts.append(f"**Viral Content**: {viral_count} videos exceeded viral threshold. ")
        
        # Sentiment summary
        if "market_sentiment" in report_sections and report_sections["market_sentiment"].get("success"):
            sentiment_data = report_sections["market_sentiment"]["sentiment_analysis"]
            # Get overall sentiment across all keywords
            positive_avg = sum([s["percentages"]["positive"] for s in sentiment_data.values()]) / len(sentiment_data)
            summary_parts.append(f"**Market Sentiment**: {positive_avg:.1f}% positive sentiment across economy-related content. ")
        
        return "".join(summary_parts) if summary_parts else "Unable to generate summary due to data collection issues."
        
    except Exception as e:
        return f"Error generating summary: {str(e)}"

# Export tools
tools = [
    get_roblox_content_trends,
    analyze_creator_mentions,
    get_viral_roblox_videos,
    track_game_popularity,
    get_youtube_market_sentiment,
    create_youtube_analytics_report
]
