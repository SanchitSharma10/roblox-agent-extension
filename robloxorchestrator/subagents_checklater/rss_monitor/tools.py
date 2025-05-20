#!/usr/bin/env python3
"""
RSS Feed Monitor Tools
Comprehensive RSS feed monitoring for Roblox economy intelligence
"""

import feedparser
import asyncio
import aiohttp
import re
import json
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib
from typing import Dict, List, Any, Optional

# Set up logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("rss_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("rss_monitor")

class RSSMonitor:
    def __init__(self):
        """Initialize RSS monitor with feed sources"""
        logger.info("Initializing RSS Monitor")
        
        # Define comprehensive feed sources
        self.feed_sources = {
            "official_roblox": [
                {"url": "https://blog.roblox.com/feed/", "name": "Roblox Blog"},
                {"url": "https://devforum.roblox.com/latest.rss", "name": "DevForum"},
            ],
            "gaming_news": [
                {"url": "https://www.gamesindustry.biz/rss", "name": "Games Industry"},
                {"url": "https://venturebeat.com/games/feed/", "name": "VentureBeat Games"},
                {"url": "https://www.gamasutra.com/rss/", "name": "Gamasutra"},
            ],
            "metaverse_economy": [
                {"url": "https://decrypt.co/feed", "name": "Decrypt"},
                {"url": "https://cointelegraph.com/rss", "name": "Cointelegraph"},
            ],
            "tech_news": [
                {"url": "https://techcrunch.com/feed/", "name": "TechCrunch"},
                {"url": "https://www.theverge.com/rss/index.xml", "name": "The Verge"},
            ]
        }
        
        # Keywords for different types of analysis
        self.economy_keywords = [
            "roblox economy", "robux", "virtual currency", "in-game purchases",
            "monetization", "developer exchange", "premium", "limited items"
        ]
        
        self.policy_keywords = [
            "terms of service", "policy update", "moderation", "safety",
            "age rating", "content guidelines", "creator economy"
        ]
        
        self.competition_keywords = [
            "fortnite", "minecraft", "vrchat", "second life", "metaverse",
            "virtual worlds", "gaming platforms"
        ]
        
        logger.info(f"RSS Monitor initialized with {sum(len(sources) for sources in self.feed_sources.values())} feed sources")

    async def fetch_feed(self, feed_url, session):
        """Fetch and parse a single RSS feed"""
        try:
            logger.info(f"Fetching feed: {feed_url}")
            async with session.get(feed_url, timeout=10) as response:
                if response.status == 200:
                    content = await response.text()
                    feed = feedparser.parse(content)
                    
                    result = {
                        "success": True,
                        "url": feed_url,
                        "title": feed.feed.get("title", "Unknown"),
                        "entries": feed.entries[:50],  # Limit to recent 50 entries
                        "last_updated": datetime.now().isoformat()
                    }
                    
                    logger.info(f"Successfully fetched feed: {feed_url} with {len(feed.entries)} entries")
                    return result
                else:
                    logger.warning(f"Failed to fetch feed: {feed_url}, status code: {response.status}")
                    return {
                        "success": False,
                        "url": feed_url,
                        "error": f"HTTP {response.status}"
                    }
        except Exception as e:
            logger.error(f"Error fetching feed {feed_url}: {str(e)}")
            return {
                "success": False,
                "url": feed_url,
                "error": str(e)
            }

    async def fetch_multiple_feeds(self, feed_list):
        """Fetch multiple RSS feeds concurrently"""
        logger.info(f"Fetching {len(feed_list)} feeds concurrently")
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            tasks = [self.fetch_feed(feed["url"], session) for feed in feed_list]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions
            valid_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Exception in fetch_multiple_feeds for {feed_list[i]['url']}: {str(result)}")
                    valid_results.append({
                        "success": False,
                        "url": feed_list[i]["url"],
                        "error": str(result)
                    })
                else:
                    valid_results.append(result)
            
            logger.info(f"Completed fetching {len(feed_list)} feeds, {len([r for r in valid_results if r['success']])} successful")
            return valid_results

    def filter_entries_by_keywords(self, entries, keywords, days_back=7):
        """Filter feed entries by keywords and recency"""
        logger.info(f"Filtering {len(entries) if entries else 0} entries with {len(keywords)} keywords, {days_back} days back")
        filtered_entries = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        for entry in entries:
            # Check publication date
            pub_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                pub_date = datetime(*entry.updated_parsed[:6])
            
            # Skip if too old
            if pub_date and pub_date < cutoff_date:
                continue
            
            # Check for keywords in title and description
            title = entry.get('title', '').lower()
            description = entry.get('description', '').lower()
            summary = entry.get('summary', '').lower()
            
            text_content = f"{title} {description} {summary}"
            
            # Check if any keyword matches
            matching_keywords = []
            for keyword in keywords:
                if keyword.lower() in text_content:
                    matching_keywords.append(keyword)
            
            if matching_keywords:
                filtered_entries.append({
                    "title": entry.get('title'),
                    "link": entry.get('link'),
                    "description": entry.get('description', '')[:500] if hasattr(entry, 'description') else entry.get('summary', '')[:500],
                    "published": entry.get('published', ''),
                    "author": entry.get('author', ''),
                    "matching_keywords": matching_keywords,
                    "relevance_score": len(matching_keywords),
                    "source_url": entry.get('link', ''),
                    "content_hash": hashlib.md5(text_content.encode()).hexdigest()
                })
        
        # Sort by relevance and date
        filtered_entries.sort(key=lambda x: (x['relevance_score'], x['published']), reverse=True)
        logger.info(f"Filtered entries: {len(filtered_entries)} matches found")
        return filtered_entries

# Global RSS monitor instance
_rss_monitor = None

def get_rss_monitor():
    """Get or create RSS monitor instance"""
    global _rss_monitor
    if _rss_monitor is None:
        _rss_monitor = RSSMonitor()
    return _rss_monitor

# Tool Functions
async def monitor_roblox_feeds(time_period: str = "week", category: str = "all") -> Dict[str, Any]:
    """Monitor Roblox-related RSS feeds for recent updates.
    
    Args:
        time_period: Time period to monitor (day, week, month)
        category: Category of feeds to monitor (all, official, gaming_news, metaverse)
        
    Returns:
        Dictionary with monitored feed data
    """
    try:
        logger.info(f"Starting monitor_roblox_feeds: time_period={time_period}, category={category}")
        monitor = get_rss_monitor()
        
        # Map time period to days
        time_map = {"day": 1, "week": 7, "month": 30}
        days_back = time_map.get(time_period, 7)
        
        # Select feed sources based on category
        if category == "all":
            selected_feeds = []
            for feeds in monitor.feed_sources.values():
                selected_feeds.extend(feeds)
        elif category in monitor.feed_sources:
            selected_feeds = monitor.feed_sources[category]
        else:
            selected_feeds = monitor.feed_sources["official_roblox"]
        
        logger.info(f"Selected {len(selected_feeds)} feeds to monitor")
        
        # Fetch feeds
        results = await monitor.fetch_multiple_feeds(selected_feeds)
        
        # Process and filter results
        all_entries = []
        successful_feeds = 0
        high_priority_entries = []
        
        for result in results:
            if result["success"]:
                successful_feeds += 1
                entries = monitor.filter_entries_by_keywords(
                    result["entries"], 
                    monitor.economy_keywords + ["roblox"],
                    days_back
                )
                
                for entry in entries:
                    entry["source_feed"] = result["title"]
                    entry["source_url"] = result["url"]
                    
                    # Check for high-priority entries (based on keywords)
                    high_priority_keywords = ["major update", "breaking", "announcement", 
                                             "policy change", "economy update", "new feature"]
                    
                    content = f"{entry.get('title', '')} {entry.get('description', '')}".lower()
                    if any(keyword in content for keyword in high_priority_keywords):
                        entry["priority"] = "high"
                        high_priority_entries.append(entry)
                    elif entry.get("relevance_score", 0) > 3:  # Multiple keyword matches
                        entry["priority"] = "medium"
                    else:
                        entry["priority"] = "low"
                
                all_entries.extend(entries)
        
        # Remove duplicates based on content hash
        unique_entries = {}
        for entry in all_entries:
            hash_key = entry.get("content_hash", entry.get("link", ""))
            if hash_key not in unique_entries:
                unique_entries[hash_key] = entry
        
        final_entries = list(unique_entries.values())
        final_entries.sort(key=lambda x: (
            {"high": 3, "medium": 2, "low": 1}[x.get("priority", "low")],
            x.get("relevance_score", 0)
        ), reverse=True)
        
        logger.info(f"Feed monitoring complete: {successful_feeds}/{len(selected_feeds)} successful, {len(final_entries)} unique entries, {len(high_priority_entries)} high priority")
        
        # Prepare result
        result = {
            "success": True,
            "time_period": time_period,
            "category": category,
            "feeds_processed": len(selected_feeds),
            "successful_feeds": successful_feeds,
            "total_entries": len(final_entries),
            "entries": final_entries[:50],  # Limit to top 50
            "high_priority_entries": len(high_priority_entries),
            "monitored_at": datetime.now().isoformat()
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in monitor_roblox_feeds: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "time_period": time_period,
            "category": category
        }

async def analyze_economy_news(time_period: str = "week", focus_area: str = "general") -> Dict[str, Any]:
    """Analyze economy-related news from RSS feeds.
    
    Args:
        time_period: Time period for analysis
        focus_area: Specific area to focus on (general, policy, monetization, competition)
        
    Returns:
        Dictionary with economy news analysis
    """
    try:
        logger.info(f"Starting analyze_economy_news: time_period={time_period}, focus_area={focus_area}")
        monitor = get_rss_monitor()
        
        # Select keywords based on focus area
        if focus_area == "policy":
            keywords = monitor.policy_keywords + monitor.economy_keywords
        elif focus_area == "competition":
            keywords = monitor.competition_keywords + monitor.economy_keywords
        elif focus_area == "monetization":
            keywords = ["monetization", "revenue", "robux", "developer exchange", "premium"]
        else:
            keywords = monitor.economy_keywords
        
        logger.info(f"Selected {len(keywords)} keywords for analysis")
        
        # Get feed data
        feed_results = await monitor_roblox_feeds(time_period, "all")
        
        if not feed_results["success"]:
            logger.error(f"Failed to get feed data: {feed_results.get('error', 'Unknown error')}")
            return feed_results
        
        logger.info(f"Received {feed_results['total_entries']} entries for analysis")
        
        # Analyze entries for economic themes
        economic_themes = defaultdict(list)
        sentiment_analysis = {"positive": 0, "negative": 0, "neutral": 0}
        
        # Define sentiment keywords
        positive_words = ["growth", "success", "profit", "increase", "expansion", "opportunity"]
        negative_words = ["decline", "loss", "decrease", "problem", "issue", "controversy"]
        
        for entry in feed_results["entries"]:
            title = entry["title"].lower()
            description = entry["description"].lower()
            content = f"{title} {description}"
            
            # Categorize by theme
            if any(word in content for word in ["policy", "regulation", "terms"]):
                economic_themes["policy_changes"].append(entry)
            elif any(word in content for word in ["robux", "currency", "monetization"]):
                economic_themes["currency_news"].append(entry)
            elif any(word in content for word in ["developer", "creator", "earnings"]):
                economic_themes["creator_economy"].append(entry)
            elif any(word in content for word in ["competition", "rival", "vs"]):
                economic_themes["competition"].append(entry)
            else:
                economic_themes["general_economy"].append(entry)
            
            # Sentiment analysis
            positive_score = sum(1 for word in positive_words if word in content)
            negative_score = sum(1 for word in negative_words if word in content)
            
            if positive_score > negative_score:
                sentiment_analysis["positive"] += 1
            elif negative_score > positive_score:
                sentiment_analysis["negative"] += 1
            else:
                sentiment_analysis["neutral"] += 1
        
        # Calculate sentiment percentages
        total_articles = len(feed_results["entries"])
        sentiment_percentages = {
            "positive": round((sentiment_analysis["positive"] / total_articles) * 100, 1) if total_articles > 0 else 0,
            "negative": round((sentiment_analysis["negative"] / total_articles) * 100, 1) if total_articles > 0 else 0,
            "neutral": round((sentiment_analysis["neutral"] / total_articles) * 100, 1) if total_articles > 0 else 0
        }
        
        logger.info(f"Analysis complete: {total_articles} articles analyzed, themes: {', '.join(economic_themes.keys())}")
        
        # Convert defaultdict to regular dict for JSON serialization
        economic_themes_dict = {k: v for k, v in economic_themes.items()}
        
        return {
            "success": True,
            "time_period": time_period,
            "focus_area": focus_area,
            "total_articles_analyzed": total_articles,
            "economic_themes": economic_themes_dict,
            "sentiment_analysis": sentiment_analysis,
            "sentiment_percentages": sentiment_percentages,
            "overall_sentiment": "positive" if sentiment_percentages["positive"] > 50 else 
                              "negative" if sentiment_percentages["negative"] > 40 else "neutral",
            "analyzed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in analyze_economy_news: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "time_period": time_period,
            "focus_area": focus_area
        }

async def track_update_announcements(time_period: str = "month") -> Dict[str, Any]:
    """Track official Roblox update announcements that might affect the economy.
    
    Args:
        time_period: Time period to track updates
        
    Returns:
        Dictionary with update tracking data
    """
    try:
        logger.info(f"Starting track_update_announcements: time_period={time_period}")
        monitor = get_rss_monitor()
        
        # Focus on official Roblox sources
        official_feeds = monitor.feed_sources["official_roblox"]
        
        # Keywords specific to updates
        update_keywords = [
            "update", "release", "launch", "new feature", "announcement",
            "economy", "monetization", "developer exchange", "premium",
            "creator marketplace", "ugc", "limited items"
        ]
        
        # Fetch official feeds
        results = await monitor.fetch_multiple_feeds(official_feeds)
        
        # Process updates
        time_map = {"week": 7, "month": 30, "quarter": 90}
        days_back = time_map.get(time_period, 30)
        
        updates = []
        for result in results:
            if result["success"]:
                entries = monitor.filter_entries_by_keywords(
                    result["entries"], 
                    update_keywords,
                    days_back
                )
                
                for entry in entries:
                    # Classify update type
                    content = f"{entry['title']} {entry['description']}".lower()
                    
                    update_type = "general"
                    if any(word in content for word in ["economy", "robux", "monetization"]):
                        update_type = "economy"
                    elif any(word in content for word in ["developer", "creator", "ugc"]):
                        update_type = "creator_tools"
                    elif any(word in content for word in ["premium", "membership"]):
                        update_type = "premium_features"
                    elif any(word in content for word in ["safety", "moderation", "policy"]):
                        update_type = "policy"
                    
                    updates.append({
                        "title": entry["title"],
                        "type": update_type,
                        "description": entry["description"],
                        "published": entry["published"],
                        "link": entry["link"],
                        "source": result["title"],
                        "economic_impact": "high" if update_type == "economy" else "medium" if update_type in ["creator_tools", "premium_features"] else "low"
                    })
        
        # Sort by economic impact and date
        updates.sort(key=lambda x: (
            {"high": 3, "medium": 2, "low": 1}[x["economic_impact"]],
            x["published"]
        ), reverse=True)
        
        # Categorize updates
        update_categories = defaultdict(list)
        for update in updates:
            update_categories[update["type"]].append(update)
        
        logger.info(f"Update tracking complete: {len(updates)} updates found")
        
        # Convert defaultdict to regular dict for JSON serialization
        update_categories_dict = {k: v for k, v in update_categories.items()}
        
        return {
            "success": True,
            "time_period": time_period,
            "total_updates": len(updates),
            "updates": updates[:20],  # Top 20 most relevant
            "categories": update_categories_dict,
            "high_impact_updates": [u for u in updates if u["economic_impact"] == "high"],
            "tracked_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in track_update_announcements: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "time_period": time_period
        }

async def detect_policy_changes(time_period: str = "month") -> Dict[str, Any]:
    """Detect policy changes that might affect the Roblox economy.
    
    Args:
        time_period: Time period to scan for policy changes
        
    Returns:
        Dictionary with policy change detection results
    """
    try:
        logger.info(f"Starting detect_policy_changes: time_period={time_period}")
        monitor = get_rss_monitor()
        
        # Policy-specific keywords
        policy_keywords = [
            "terms of service", "tos", "policy", "guidelines", "rules",
            "moderation", "content policy", "age rating", "safety",
            "developer program", "creator guidelines", "monetization policy"
        ]
        
        # Get feed data focusing on policy
        feed_results = await monitor_roblox_feeds(time_period, "official")
        
        if not feed_results["success"]:
            logger.error(f"Failed to get feed data: {feed_results.get('error', 'Unknown error')}")
            return feed_results
        
        logger.info(f"Received {feed_results['total_entries']} entries for policy analysis")
        
        # Filter for policy-related content
        policy_entries = []
        for entry in feed_results["entries"]:
            content = f"{entry['title']} {entry['description']}".lower()
            
            # Check for policy keywords
            policy_matches = [kw for kw in policy_keywords if kw in content]
            
            if policy_matches:
                # Assess economic impact
                economic_impact = "low"
                if any(word in content for word in ["economy", "monetization", "robux", "developer"]):
                    economic_impact = "high"
                elif any(word in content for word in ["creator", "ugc", "premium"]):
                    economic_impact = "medium"
                
                # Determine change type
                change_type = "general"
                if "terms of service" in content or "tos" in content:
                    change_type = "terms_of_service"
                elif "developer" in content or "creator" in content:
                    change_type = "developer_policy"
                elif "moderation" in content or "content" in content:
                    change_type = "content_policy"
                elif "safety" in content or "age" in content:
                    change_type = "safety_policy"
                
                policy_entries.append({
                    "title": entry["title"],
                    "description": entry["description"],
                    "published": entry["published"],
                    "link": entry["link"],
                    "change_type": change_type,
                    "economic_impact": economic_impact,
                    "matching_keywords": policy_matches,
                    "urgency": "high" if economic_impact == "high" else "medium" if economic_impact == "medium" else "low"
                })
        
        # Sort by urgency and economic impact
        policy_entries.sort(key=lambda x: (
            {"high": 3, "medium": 2, "low": 1}[x["urgency"]],
            x["published"]
        ), reverse=True)
        
        # Group by change type
        policy_categories = defaultdict(list)
        for entry in policy_entries:
            policy_categories[entry["change_type"]].append(entry)
        
        logger.info(f"Policy change detection complete: {len(policy_entries)} policy changes found")
        
        # Convert defaultdict to regular dict for JSON serialization
        policy_categories_dict = {k: v for k, v in policy_categories.items()}
        
        # Prepare result
        result = {
            "success": True,
            "time_period": time_period,
            "total_policy_changes": len(policy_entries),
            "policy_changes": policy_entries,
            "categories": policy_categories_dict,
            "high_priority_changes": [p for p in policy_entries if p["urgency"] == "high"],
            "economic_impact_summary": {
                "high": len([p for p in policy_entries if p["economic_impact"] == "high"]),
                "medium": len([p for p in policy_entries if p["economic_impact"] == "medium"]),
                "low": len([p for p in policy_entries if p["economic_impact"] == "low"])
            },
            "detected_at": datetime.now().isoformat()
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in detect_policy_changes: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "time_period": time_period
        }

async def get_competitor_news(time_period: str = "week", competitors: Optional[List[str]] = None) -> Dict[str, Any]:
    """Monitor competitor news that might affect Roblox's market position.
    
    Args:
        time_period: Time period for monitoring
        competitors: List of competitors to track
        
    Returns:
        Dictionary with competitor news analysis
    """
    try:
        logger.info(f"Starting get_competitor_news: time_period={time_period}, competitors={competitors}")
        monitor = get_rss_monitor()
        
        # Default competitors if none specified
        if competitors is None:
            competitors = ["fortnite", "minecraft", "vrchat", "second life", "metaverse platforms"]
        
        # Focus on gaming and tech news feeds
        gaming_feeds = monitor.feed_sources["gaming_news"] + monitor.feed_sources["tech_news"]
        
        # Get feed data
        results = await monitor.fetch_multiple_feeds(gaming_feeds)
        
        # Process competitor mentions
        time_map = {"day": 1, "week": 7, "month": 30}
        days_back = time_map.get(time_period, 7)
        
        competitor_news = defaultdict(list)
        
        for result in results:
            if result["success"]:
                for entry in result["entries"]:
                    # Check publication date
                    pub_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6])
                    
                    if pub_date and pub_date < datetime.now() - timedelta(days=days_back):
                        continue
                    
                    content = f"{entry.get('title', '')} {entry.get('description', '')}".lower()
                    
                    # Check for competitor mentions
                    for competitor in competitors:
                        if competitor.lower() in content:
                            # Analyze impact on Roblox
                            roblox_relevance = "low"
                            if "roblox" in content:
                                roblox_relevance = "direct"
                            elif any(word in content for word in ["virtual economy", "metaverse", "ugc", "creator economy"]):
                                roblox_relevance = "high"
                            elif any(word in content for word in ["gaming platform", "social game", "virtual world"]):
                                roblox_relevance = "medium"
                            
                            competitor_news[competitor].append({
                                "title": entry.get("title"),
                                "description": entry.get("description", "")[:300] if hasattr(entry, 'description') else entry.get("summary", "")[:300],
                                "published": entry.get("published"),
                                "link": entry.get("link"),
                                "source": result["title"],
                                "roblox_relevance": roblox_relevance,
                                "potential_impact": assess_competitor_impact(content)
                            })
        
        # Sort news by relevance to Roblox
        for competitor in competitor_news:
            competitor_news[competitor].sort(
                key=lambda x: {"direct": 4, "high": 3, "medium": 2, "low": 1}[x["roblox_relevance"]],
                reverse=True
            )
        
        logger.info(f"Competitor news analysis complete: {sum(len(news) for news in competitor_news.values())} mentions found")
        
        # Convert defaultdict to regular dict for JSON serialization
        competitor_news_dict = {k: v for k, v in competitor_news.items()}
        
        return {
            "success": True,
            "time_period": time_period,
            "competitors_tracked": competitors,
            "competitor_news": competitor_news_dict,
            "total_mentions": sum(len(news) for news in competitor_news.values()),
            "high_relevance_news": [
                item for news_list in competitor_news.values() 
                for item in news_list 
                if item["roblox_relevance"] in ["direct", "high"]
            ],
            "monitored_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in get_competitor_news: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "time_period": time_period,
            "competitors_tracked": competitors or []
        }

async def create_news_summary_report(time_period: str = "week") -> Dict[str, Any]:
    """Generate comprehensive news summary report from all RSS sources.
    
    Args:
        time_period: Time period for the report
        
    Returns:
        Dictionary with comprehensive news analysis
    """
    try:
        logger.info(f"Starting create_news_summary_report: time_period={time_period}")
        
        # Gather all news analyses
        report_sections = {}
        
        # 1. General Roblox news monitoring
        roblox_news = await monitor_roblox_feeds(time_period, "all")
        report_sections["roblox_news"] = roblox_news
        
        # 2. Economy-specific analysis
        economy_analysis = await analyze_economy_news(time_period, "general")
        report_sections["economy_analysis"] = economy_analysis
        
        # 3. Update tracking
        updates = await track_update_announcements(time_period)
        report_sections["official_updates"] = updates
        
        # 4. Policy changes
        policy_changes = await detect_policy_changes(time_period)
        report_sections["policy_changes"] = policy_changes
        
        # 5. Competitor news
        competitor_news = await get_competitor_news(time_period)
        report_sections["competitor_analysis"] = competitor_news
        
        # Generate executive summary
        executive_summary = generate_news_executive_summary(report_sections)
        
        # Calculate key metrics
        total_articles = sum([
            section.get("total_entries", 0) + section.get("total_articles_analyzed", 0) + 
            section.get("total_updates", 0) + section.get("total_policy_changes", 0) +
            section.get("total_mentions", 0)
            for section in report_sections.values()
            if isinstance(section, dict) and section.get("success")
        ])
        
        logger.info(f"News summary report complete: {total_articles} total articles across all sections")
        
        # Prepare the final report
        report = {
            "success": True,
            "report_type": "news_summary",
            "time_period": time_period,
            "generated_at": datetime.now().isoformat(),
            "executive_summary": executive_summary,
            "sections": report_sections,
            "key_metrics": {
                "total_articles_processed": total_articles,
                "successful_sections": len([s for s in report_sections.values() if s.get("success")]),
                "high_priority_items": len(policy_changes.get("high_priority_changes", [])) + 
                                     len(updates.get("high_impact_updates", [])),
            },
            "data_sources": ["RSS Feeds", "Official Roblox Sources", "Gaming News", "Tech News"]
        }
        
        return report
        
    except Exception as e:
        logger.error(f"Error in create_news_summary_report: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "report_type": "news_summary",
            "time_period": time_period
        }

def assess_competitor_impact(content):
    """Assess potential impact of competitor news on Roblox"""
    high_impact_keywords = ["virtual economy", "creator earnings", "ugc", "metaverse economy"]
    medium_impact_keywords = ["new features", "user growth", "partnerships", "funding"]
    
    if any(keyword in content for keyword in high_impact_keywords):
        return "high"
    elif any(keyword in content for keyword in medium_impact_keywords):
        return "medium"
    else:
        return "low"

def generate_news_executive_summary(report_sections):
    """Generate executive summary from news report sections"""
    try:
        summary_parts = []
        
        # Economy analysis summary
        if "economy_analysis" in report_sections and report_sections["economy_analysis"].get("success"):
            econ = report_sections["economy_analysis"]
            sentiment = econ.get("overall_sentiment", "neutral")
            articles = econ.get("total_articles_analyzed", 0)
            summary_parts.append(f"**Economy News**: {articles} articles analyzed with {sentiment} sentiment overall. ")
        
        # Policy changes summary
        if "policy_changes" in report_sections and report_sections["policy_changes"].get("success"):
            policy = report_sections["policy_changes"]
            high_priority = len(policy.get("high_priority_changes", []))
            total_changes = policy.get("total_policy_changes", 0)
            if total_changes > 0:
                summary_parts.append(f"**Policy Updates**: {total_changes} policy changes detected, {high_priority} high-priority. ")
        
        # Update announcements summary
        if "official_updates" in report_sections and report_sections["official_updates"].get("success"):
            updates = report_sections["official_updates"]
            high_impact = len(updates.get("high_impact_updates", []))
            total_updates = updates.get("total_updates", 0)
            summary_parts.append(f"**Official Updates**: {total_updates} updates tracked, {high_impact} with high economic impact. ")
        
        # Competitor analysis summary
        if "competitor_analysis" in report_sections and report_sections["competitor_analysis"].get("success"):
            comp = report_sections["competitor_analysis"]
            high_relevance = len(comp.get("high_relevance_news", []))
            total_mentions = comp.get("total_mentions", 0)
            summary_parts.append(f"**Competitor News**: {total_mentions} mentions tracked, {high_relevance} highly relevant to Roblox. ")
        
        return "".join(summary_parts) if summary_parts else "Unable to generate summary due to data collection issues."
        
    except Exception as e:
        logger.error(f"Error generating news summary: {str(e)}", exc_info=True)
        return f"Error generating summary: {str(e)}"

# Export tools
tools = [
    monitor_roblox_feeds,
    analyze_economy_news,
    track_update_announcements,
    detect_policy_changes,
    get_competitor_news,
    create_news_summary_report
]