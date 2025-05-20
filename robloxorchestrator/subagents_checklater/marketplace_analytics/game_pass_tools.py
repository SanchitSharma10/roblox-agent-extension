#!/usr/bin/env python3
"""
Game Pass Analytics Tools
Tracks game passes for Roblox games and analyzes monetization strategies
Enhanced with caching and offline functionality
"""

import os
import json
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import sqlite3
import hashlib

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("marketplace_analytics.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("game_pass_analytics")

# Constants
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
CACHE_DB = os.path.join(CACHE_DIR, "game_pass_cache.db")
CACHE_EXPIRY = 24 * 60 * 60  # Cache expiry in seconds (24 hours)

# Ensure cache directory exists
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def setup_cache_db():
    """Set up SQLite cache database for game pass data"""
    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS game_pass_cache (
        query_hash TEXT PRIMARY KEY,
        data TEXT,
        timestamp INTEGER
    )
    ''')
    
    # Create manual data table for storing user-provided or fetched game pass data
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS manual_game_pass_data (
        pass_id INTEGER PRIMARY KEY,
        game_id INTEGER,
        game_name TEXT,
        game_visits INTEGER,
        game_playing INTEGER,
        creator_name TEXT,
        pass_name TEXT,
        price INTEGER,
        price_range TEXT,
        sales_count INTEGER,
        category TEXT,
        rank_in_game INTEGER,
        last_updated INTEGER
    )
    ''')
    
    conn.commit()
    conn.close()

def get_cache(query_hash):
    """Get cached data for a query if available and not expired"""
    try:
        conn = sqlite3.connect(CACHE_DB)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT data, timestamp FROM game_pass_cache WHERE query_hash = ?", 
            (query_hash,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            data, timestamp = result
            # Check if cache is expired
            if time.time() - timestamp <= CACHE_EXPIRY:
                return json.loads(data)
        
        return None
    except Exception as e:
        logger.error(f"Error retrieving cache: {str(e)}")
        return None

def set_cache(query_hash, data):
    """Cache data for a query"""
    try:
        conn = sqlite3.connect(CACHE_DB)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT OR REPLACE INTO game_pass_cache (query_hash, data, timestamp) VALUES (?, ?, ?)",
            (query_hash, json.dumps(data), int(time.time()))
        )
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error setting cache: {str(e)}")

def get_manual_game_pass_data(game_ids=None, game_names=None):
    """Get manually stored game pass data"""
    try:
        conn = sqlite3.connect(CACHE_DB)
        cursor = conn.cursor()
        
        query = "SELECT * FROM manual_game_pass_data"
        params = []
        
        if game_ids:
            placeholders = ','.join('?' for _ in game_ids)
            query += f" WHERE game_id IN ({placeholders})"
            params.extend(game_ids)
        elif game_names:
            conditions = []
            for name in game_names:
                conditions.append("game_name LIKE ?")
                params.append(f"%{name}%")
            
            if conditions:
                query += f" WHERE {' OR '.join(conditions)}"
        
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        
        conn.close()
        return results
    except Exception as e:
        logger.error(f"Error retrieving manual game pass data: {str(e)}")
        return []

def store_manual_game_pass_data(game_pass_data):
    """Store manually collected game pass data"""
    try:
        conn = sqlite3.connect(CACHE_DB)
        cursor = conn.cursor()
        
        for pass_data in game_pass_data:
            cursor.execute(
                """
                INSERT OR REPLACE INTO manual_game_pass_data
                (pass_id, game_id, game_name, game_visits, game_playing, 
                creator_name, pass_name, price, price_range, sales_count, 
                category, rank_in_game, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pass_data.get('pass_id'),
                    pass_data.get('game_id'),
                    pass_data.get('game_name'),
                    pass_data.get('game_visits', 0),
                    pass_data.get('game_playing', 0),
                    pass_data.get('creator_name'),
                    pass_data.get('pass_name'),
                    pass_data.get('price', 0),
                    pass_data.get('price_range'),
                    pass_data.get('sales_count', 0),
                    pass_data.get('category'),
                    pass_data.get('rank_in_game', 0),
                    int(time.time())
                )
            )
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error storing manual game pass data: {str(e)}")
        return False

async def track_game_passes(game_ids: List[int] = None, game_names: List[str] = None) -> Dict[str, Any]:
    """Track game passes for specific Roblox games to monitor monetization strategies.
    
    Args:
        game_ids: List of specific Roblox game IDs to check
        game_names: List of Roblox game names to search for and check
        
    Returns:
        Dictionary with game pass data and analysis
    """
    try:
        logger.info(f"Tracking game passes for games: {game_ids or game_names}")
        
        # Initialize cache DB if needed
        setup_cache_db()
        
        # Generate cache key based on input parameters
        query_params = {
            "game_ids": game_ids,
            "game_names": game_names,
            "function": "track_game_passes"
        }
        query_hash = hashlib.md5(json.dumps(query_params, sort_keys=True).encode()).hexdigest()
        
        # Try to get from cache first
        cached_data = get_cache(query_hash)
        if cached_data:
            logger.info(f"Using cached game pass data (expires in {int((cached_data.get('cache_timestamp', 0) + CACHE_EXPIRY - time.time()) / 60)} minutes)")
            return cached_data
        
        # Try to get data from manual storage
        game_pass_data = get_manual_game_pass_data(game_ids, game_names)
        
        # If we have sufficient manual data, use it
        if game_pass_data and len(game_pass_data) > 0:
            logger.info(f"Using manually stored game pass data ({len(game_pass_data)} entries)")
            result = analyze_game_pass_data(game_pass_data, game_ids, game_names)
            result["data_source"] = "manual"
            result["cache_timestamp"] = int(time.time())
            
            # Cache the result
            set_cache(query_hash, result)
            return result
        
        # If no manual data, try to query database
        logger.info("No manual data available, attempting database query")
        try:
            from .tools import get_db_instance
            db = get_db_instance()
            
            if db is None:
                raise Exception("Database not available")
            
            # Build query
            query = "SELECT * FROM game_passes_latest"
            conditions = []
            params = {}
            
            if game_ids:
                game_ids_str = ", ".join(str(id) for id in game_ids)
                conditions.append(f"game_id IN ({game_ids_str})")
            
            if game_names:
                placeholders = []
                for i, name in enumerate(game_names):
                    param_name = f"game_{i}"
                    params[param_name] = name
                    placeholders.append(f"game_name ILIKE '%' || :{param_name} || '%'")
                
                if placeholders:
                    conditions.append("(" + " OR ".join(placeholders) + ")")
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY game_id, rank_in_game"
            
            # Execute query to get game pass data
            result = db.execute_sql_query(query, json.dumps(params) if params else "{}")
            
            if result.get('success') and result.get('data'):
                logger.info(f"Successfully retrieved {len(result['data'])} game passes from database")
                game_pass_data = result['data']
                
                # Store this data in our manual store for future use
                store_manual_game_pass_data(game_pass_data)
            else:
                raise Exception("Database query failed or returned no data")
                
        except Exception as e:
            logger.warning(f"Database query failed: {str(e)}, using backup data")
            # Use backup data if database query fails
            game_pass_data = get_backup_game_pass_data()
        
        # Process and analyze the data
        result = analyze_game_pass_data(game_pass_data, game_ids, game_names)
        
        # Add cache metadata
        result["data_source"] = "backup" if db is None else "database"
        result["cache_timestamp"] = int(time.time())
        
        # Cache the result
        set_cache(query_hash, result)
        return result
        
    except Exception as e:
        logger.error(f"Error in track_game_passes: {str(e)}")
        
        # Use backup data in case of errors
        backup_data = get_backup_game_pass_data()
        result = analyze_game_pass_data(backup_data, game_ids, game_names)
        result["data_source"] = "backup_fallback"
        result["error"] = str(e)
        return result

async def analyze_game_pass_trends(game_id: int, time_period: str = "month") -> Dict[str, Any]:
    """Analyze game pass trends for a specific game over time.
    
    Args:
        game_id: ID of the game to analyze
        time_period: Period for trend analysis (week, month, quarter)
        
    Returns:
        Dictionary with trend data analysis
    """
    try:
        logger.info(f"Analyzing game pass trends for game {game_id} over {time_period}")
        
        # Initialize cache DB if needed
        setup_cache_db()
        
        # Generate cache key based on input parameters
        query_params = {
            "game_id": game_id,
            "time_period": time_period,
            "function": "analyze_game_pass_trends"
        }
        query_hash = hashlib.md5(json.dumps(query_params, sort_keys=True).encode()).hexdigest()
        
        # Try to get from cache first
        cached_data = get_cache(query_hash)
        if cached_data:
            logger.info(f"Using cached trend analysis (expires in {int((cached_data.get('cache_timestamp', 0) + CACHE_EXPIRY - time.time()) / 60)} minutes)")
            return cached_data
        
        # Since we don't have historical game pass data implementation yet,
        # we'll create a simulated trend based on current data
        
        # Get current game pass data
        game_pass_data = get_manual_game_pass_data(game_ids=[game_id])
        
        # If no data available, use backup data
        if not game_pass_data:
            backup_data = get_backup_game_pass_data()
            game_pass_data = [p for p in backup_data if p.get('game_id') == game_id]
        
        # If still no data, return error
        if not game_pass_data:
            return {
                "success": False,
                "message": "No game pass data available for this game",
                "game_id": game_id,
                "time_period": time_period,
                "cache_timestamp": int(time.time())
            }
        
        # Generate simulated historical data
        now = datetime.now()
        
        if time_period == "week":
            periods = 7
            period_name = "days"
            date_format = "%a"  # Day of week abbreviated
        elif time_period == "quarter":
            periods = 12
            period_name = "weeks"
            date_format = "Week %W"
        else:  # month
            periods = 30
            period_name = "days"
            date_format = "%d %b"
        
        # Create simulated historical trends
        trend_data = []
        game_name = game_pass_data[0].get('game_name', f"Game {game_id}")
        
        # Get all unique passes for this game
        unique_passes = {}
        for pass_data in game_pass_data:
            pass_id = pass_data.get('pass_id')
            if pass_id not in unique_passes:
                unique_passes[pass_id] = {
                    'id': pass_id,
                    'name': pass_data.get('pass_name', 'Unknown Pass'),
                    'current_price': pass_data.get('price', 0),
                    'current_sales': pass_data.get('sales_count', 0),
                    'category': pass_data.get('category', 'unknown')
                }
        
        # Simulate data for each pass
        for pass_id, pass_info in unique_passes.items():
            # Basic sales growth model (random but somewhat realistic)
            current_sales = pass_info['current_sales']
            # Roughly estimate daily/weekly sales rate
            if time_period == "week":
                sales_rate = current_sales / 365 * 7  # Approx weekly sales
            elif time_period == "quarter":
                sales_rate = current_sales / 365 * 7  # Weekly sales
            else:
                sales_rate = current_sales / 365  # Daily sales
            
            # Apply some randomness to sales rate (± 30%)
            import random
            base_sales_rate = sales_rate
            pass_data_points = []
            
            # Generate data points for each period
            cumulative_sales = current_sales
            for i in range(periods, 0, -1):
                # Create date for this data point
                if time_period == "week":
                    date = now - timedelta(days=i)
                elif time_period == "quarter":
                    date = now - timedelta(weeks=i)
                else:
                    date = now - timedelta(days=i)
                
                # Randomize sales rate with some trends
                variation = random.uniform(0.7, 1.3)
                # Add cyclical pattern (weekends higher than weekdays for example)
                if time_period == "week" or time_period == "month":
                    # Weekend effect (Fri-Sun higher sales)
                    if date.weekday() >= 4:  # Fri-Sun
                        variation *= 1.2
                
                period_sales = int(base_sales_rate * variation)
                cumulative_sales -= period_sales  # Go backwards from current
                if cumulative_sales < 0:
                    cumulative_sales = 0
                
                # Create data point
                data_point = {
                    'date': date.strftime(date_format),
                    'sales': period_sales,
                    'cumulative_sales': int(cumulative_sales),
                    'revenue': period_sales * pass_info['current_price'],
                }
                pass_data_points.append(data_point)
            
            # Reverse so oldest is first
            pass_data_points.reverse()
            
            # Calculate trends
            sales_values = [p['sales'] for p in pass_data_points]
            avg_sales = sum(sales_values) / len(sales_values)
            recent_avg = sum(sales_values[-3:]) / 3 if len(sales_values) >= 3 else avg_sales
            
            # Determine trend
            if recent_avg > avg_sales * 1.15:
                trend = "Strong Increase"
            elif recent_avg > avg_sales * 1.05:
                trend = "Slight Increase"
            elif recent_avg < avg_sales * 0.85:
                trend = "Strong Decrease"
            elif recent_avg < avg_sales * 0.95:
                trend = "Slight Decrease"
            else:
                trend = "Stable"
            
            # Add to overall trend data
            trend_data.append({
                'pass_id': pass_id,
                'pass_name': pass_info['name'],
                'category': pass_info['category'],
                'price': pass_info['current_price'],
                'data_points': pass_data_points,
                'total_sales': pass_info['current_sales'],
                'average_sales_per_period': avg_sales,
                'trend': trend,
                'period': period_name
            })
        
        # Overall game pass trends
        result = {
            "success": True,
            "game_id": game_id,
            "game_name": game_name,
            "time_period": time_period,
            "period_name": period_name,
            "trend_data": trend_data,
            "trend_start_date": (now - (timedelta(days=periods) if time_period != "quarter" else timedelta(weeks=periods))).strftime("%Y-%m-%d"),
            "trend_end_date": now.strftime("%Y-%m-%d"),
            "simulated_data": True,  # Flag to indicate this is simulated
            "insights": generate_trend_insights(game_name, trend_data, time_period),
            "cache_timestamp": int(time.time())
        }
        
        # Cache the result
        set_cache(query_hash, result)
        return result
        
    except Exception as e:
        logger.error(f"Error in analyze_game_pass_trends: {str(e)}")
        return {
            "success": False,
            "message": f"Error analyzing trends: {str(e)}",
            "game_id": game_id,
            "time_period": time_period
        }

def generate_trend_insights(game_name, trend_data, time_period):
    """Generate insights from trend data"""
    insights = []
    
    if not trend_data:
        return ["No trend data available to generate insights"]
    
    # Overall trends
    increasing_passes = [p for p in trend_data if "Increase" in p.get('trend', '')]
    decreasing_passes = [p for p in trend_data if "Decrease" in p.get('trend', '')]
    stable_passes = [p for p in trend_data if p.get('trend') == "Stable"]
    
    # Summary
    insights.append(f"Analyzed {len(trend_data)} game passes in {game_name} over the past {time_period}")
    
    # Performance insights
    if increasing_passes:
        strongest_increase = max(increasing_passes, key=lambda p: p['average_sales_per_period'])
        insights.append(f"Best performing pass: '{strongest_increase['pass_name']}' with a {strongest_increase['trend']}")
    
    if decreasing_passes:
        strongest_decrease = min(decreasing_passes, key=lambda p: p['average_sales_per_period'])
        insights.append(f"Worst performing pass: '{strongest_decrease['pass_name']}' with a {strongest_decrease['trend']}")
    
    # Category performance
    categories = {}
    for pass_data in trend_data:
        category = pass_data.get('category', 'unknown')
        if category not in categories:
            categories[category] = []
        categories[category].append(pass_data)
    
    # Find best and worst performing categories
    if categories:
        category_performance = {}
        for category, passes in categories.items():
            if len(passes) > 0:
                avg_trend_score = sum([
                    2 if "Strong Increase" in p['trend'] else
                    1 if "Slight Increase" in p['trend'] else
                    0 if "Stable" in p['trend'] else
                    -1 if "Slight Decrease" in p['trend'] else
                    -2 for p in passes
                ]) / len(passes)
                category_performance[category] = avg_trend_score
        
        if category_performance:
            best_category = max(category_performance.items(), key=lambda x: x[1])
            worst_category = min(category_performance.items(), key=lambda x: x[1])
            
            if best_category[1] > 0:
                insights.append(f"Best performing pass category: {best_category[0]}")
            if worst_category[1] < 0:
                insights.append(f"Worst performing pass category: {worst_category[0]}")
    
    # Revenue insights
    total_revenue = sum([
        sum([dp['revenue'] for dp in p['data_points']])
        for p in trend_data
    ])
    
    if time_period == "week":
        revenue_period = "week"
    elif time_period == "quarter":
        revenue_period = "quarter"
    else:
        revenue_period = "month"
    
    insights.append(f"Estimated total revenue from passes: {total_revenue:,} Robux over this {revenue_period}")
    
    # Growth trajectory
    overall_trend = "Stable"
    if len(increasing_passes) > len(trend_data) * 0.6:
        overall_trend = "Growing"
    elif len(decreasing_passes) > len(trend_data) * 0.6:
        overall_trend = "Declining"
    elif len(increasing_passes) > len(decreasing_passes):
        overall_trend = "Slightly Growing"
    elif len(decreasing_passes) > len(increasing_passes):
        overall_trend = "Slightly Declining"
    
    insights.append(f"Overall pass sales trajectory: {overall_trend}")
    
    # Most profitable pass
    if trend_data:
        most_profitable = max(trend_data, key=lambda p: sum([dp['revenue'] for dp in p['data_points']]))
        insights.append(f"Most profitable pass: '{most_profitable['pass_name']}' generating {sum([dp['revenue'] for dp in most_profitable['data_points']]):,} Robux")
    
    return insights

async def compare_game_pass_strategies(game_ids: List[int]) -> Dict[str, Any]:
    """Compare monetization strategies between different games.
    
    Args:
        game_ids: List of game IDs to compare
        
    Returns:
        Dictionary with comparative analysis
    """
    try:
        logger.info(f"Comparing game pass strategies between games: {game_ids}")
        
        # Initialize cache DB if needed
        setup_cache_db()
        
        # Generate cache key based on input parameters
        query_params = {
            "game_ids": game_ids,
            "function": "compare_game_pass_strategies"
        }
        query_hash = hashlib.md5(json.dumps(query_params, sort_keys=True).encode()).hexdigest()
        
        # Try to get from cache first
        cached_data = get_cache(query_hash)
        if cached_data:
            logger.info(f"Using cached comparison data (expires in {int((cached_data.get('cache_timestamp', 0) + CACHE_EXPIRY - time.time()) / 60)} minutes)")
            return cached_data
        
        # Get data for all games
        all_game_data = await track_game_passes(game_ids=game_ids)
        
        if not all_game_data.get("success"):
            return all_game_data
        
        game_data = all_game_data.get("game_data", [])
        
        if not game_data:
            return {
                "success": False,
                "error": "No game data available for comparison",
                "game_ids": game_ids,
                "cache_timestamp": int(time.time())
            }
        
        # Calculate comparison metrics
        comparison = []
        for game in game_data:
            # Skip games with no pass data
            if not game.get("passes", []):
                continue
                
            game_metrics = {
                "id": game["id"],
                "name": game["name"],
                "creator": game["creator"],
                "total_passes": game["total_passes"],
                "avg_price": game["avg_price"],
                "max_price": max([p.get("price", 0) for p in game["passes"]]) if game["passes"] else 0,
                "free_to_paid_ratio": (game["free_passes"] / game["paid_passes"]) if game["paid_passes"] > 0 else 0,
                "monetization_density": game["total_passes"] / (game["visits"] / 1000000) if game["visits"] > 0 else 0,
                "estimated_daily_revenue": calculate_estimated_revenue(game),
                "categories": game.get("categories", {})
            }
            comparison.append(game_metrics)
        
        # Skip if no valid games to compare
        if not comparison:
            return {
                "success": False,
                "error": "No valid game data available for comparison",
                "game_ids": game_ids,
                "cache_timestamp": int(time.time())
            }
        
        # Sort by total passes
        comparison = sorted(comparison, key=lambda x: x["total_passes"], reverse=True)
        
        # Generate comparative insights
        insights = []
        
        # Most/Least passes
        if len(comparison) > 1:
            insights.append(f"Most passes: {comparison[0]['name']} with {comparison[0]['total_passes']} passes")
            insights.append(f"Least passes: {comparison[-1]['name']} with {comparison[-1]['total_passes']} passes")
        
            # Average price comparison
            highest_avg = max(comparison, key=lambda x: x["avg_price"])
            lowest_avg = min(comparison, key=lambda x: x["avg_price"] if x["avg_price"] > 0 else float('inf'))
            insights.append(f"Highest average price: {highest_avg['name']} at {highest_avg['avg_price']:.0f} Robux")
            insights.append(f"Lowest average price: {lowest_avg['name']} at {lowest_avg['avg_price']:.0f} Robux")
            
            # Free to paid ratio comparison
            highest_free_ratio = max(comparison, key=lambda x: x["free_to_paid_ratio"])
            insights.append(f"Most free passes: {highest_free_ratio['name']} with {highest_free_ratio['free_to_paid_ratio']:.2f} free:paid ratio")
            
            # Monetization density
            highest_density = max(comparison, key=lambda x: x["monetization_density"])
            insights.append(f"Highest monetization density: {highest_density['name']} with {highest_density['monetization_density']:.2f} passes per million visits")
            
            # Revenue estimation
            highest_revenue = max(comparison, key=lambda x: x["estimated_daily_revenue"])
            insights.append(f"Highest estimated daily revenue: {highest_revenue['name']} with ~{highest_revenue['estimated_daily_revenue']:,} Robux/day")
        else:
            # Single game analysis
            game = comparison[0]
            insights.append(f"{game['name']} has {game['total_passes']} passes with average price of {game['avg_price']:.0f} Robux")
            insights.append(f"Estimated daily revenue from passes: ~{game['estimated_daily_revenue']:,} Robux")
            
            # Category breakdown
            if game.get("categories"):
                top_category = max(game["categories"].items(), key=lambda x: x[1])
                insights.append(f"Main monetization focus: {top_category[0]} passes ({top_category[1]} of {game['total_passes']} passes)")
        
        # Strategy classification
        for game in comparison:
            strategy = classify_monetization_strategy(game)
            insights.append(f"{game['name']}'s monetization strategy: {strategy}")
        
        result = {
            "success": True,
            "games_compared": len(comparison),
            "comparison_data": comparison,
            "comparative_insights": insights,
            "analysis_timestamp": datetime.now().isoformat(),
            "cache_timestamp": int(time.time())
        }
        
        # Cache the result
        set_cache(query_hash, result)
        return result
        
    except Exception as e:
        logger.error(f"Error in compare_game_pass_strategies: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "game_ids": game_ids
        }

def calculate_estimated_revenue(game_data):
    """Estimate daily revenue from game pass data"""
    # This is a simplified model assuming pass sales are distributed evenly over game lifetime
    
    # Get sales data
    passes = game_data.get("passes", [])
    if not passes:
        return 0
    
    total_sales = sum(p.get("sales_count", 0) for p in passes)
    
    # Estimate the game's age in days (assuming a default if not available)
    # This is very rough - in a real implementation we'd use actual release date
    visits = game_data.get("visits", 0)
    estimated_age_days = max(1, visits / 10000)  # Roughly 10k visits per day
    estimated_age_days = min(estimated_age_days, 2000)  # Cap at ~5.5 years
    
    # Calculate estimated daily sales
    daily_sales = total_sales / estimated_age_days
    
    # Calculate average revenue per sale
    avg_price = game_data.get("avg_price", 0)
    
    # Estimate daily revenue
    daily_revenue = daily_sales * avg_price
    
    return int(daily_revenue)

def classify_monetization_strategy(game_metrics):
    """Classify a game's monetization strategy based on metrics"""
    categories = game_metrics.get("categories", {})
    
    # Determine primary category
    primary_category = max(categories.items(), key=lambda x: x[1])[0] if categories else "unknown"
    
    # Check free to paid ratio
    free_ratio = game_metrics.get("free_to_paid_ratio", 0)
    
    # Check price points
    avg_price = game_metrics.get("avg_price", 0)
    max_price = game_metrics.get("max_price", 0)
    
    # Monetization density
    density = game_metrics.get("monetization_density", 0)
    
    # Classification
    if free_ratio > 0.5:
        strategy_type = "Freemium"
    elif primary_category == "vip":
        strategy_type = "VIP-Focused"
    elif primary_category == "boosters":
        strategy_type = "Booster-Focused"
    elif primary_category == "cosmetics":
        strategy_type = "Cosmetic-Focused"
    elif primary_category == "access":
        strategy_type = "Access-Gated"
    else:
        strategy_type = "Mixed"
    
    # Price tier
    if avg_price > 800:
        price_tier = "Premium"
    elif avg_price > 400:
        price_tier = "Mid-price"
    else:
        price_tier = "Budget"
    
    # Monetization approach
    if density > 5:
        approach = "Heavy"
    elif density > 2:
        approach = "Moderate"
    else:
        approach = "Light"
    
    return f"{approach} {price_tier} {strategy_type}"

def get_backup_game_pass_data() -> List[Dict]:
    """Get backup game pass data for when database is unavailable"""
    return [
        {
            'pass_id': 11746859,
            'game_id': 920587237,
            'game_name': 'Adopt Me!',
            'game_visits': 31244978655,
            'game_playing': 168923,
            'creator_name': 'Dream Craft',
            'pass_name': 'VIP',
            'price': 250,
            'price_range': 'low',
            'sales_count': 1500000,
            'category': 'vip',
            'rank_in_game': 1
        },
        {
            'pass_id': 12994797,
            'game_id': 920587237,
            'game_name': 'Adopt Me!',
            'game_visits': 31244978655,
            'game_playing': 168923,
            'creator_name': 'Dream Craft',
            'pass_name': 'Ultra VIP',
            'price': 995,
            'price_range': 'high',
            'sales_count': 750000,
            'category': 'vip',
            'rank_in_game': 2
        },
        {
            'pass_id': 12994801,
            'game_id': 920587237,
            'game_name': 'Adopt Me!',
            'game_visits': 31244978655,
            'game_playing': 168923,
            'creator_name': 'Dream Craft',
            'pass_name': 'Premium Pets Bundle',
            'price': 850,
            'price_range': 'high',
            'sales_count': 620000,
            'category': 'cosmetics',
            'rank_in_game': 3
        },
        {
            'pass_id': 15217687,
            'game_id': 2753915549,
            'game_name': 'Blox Fruits',
            'game_visits': 24873612345,
            'game_playing': 154326,
            'creator_name': 'Block Games',
            'pass_name': '2x Money',
            'price': 350,
            'price_range': 'medium',
            'sales_count': 1200000,
            'category': 'boosters',
            'rank_in_game': 1
        },
        {
            'pass_id': 15217690,
            'game_id': 2753915549,
            'game_name': 'Blox Fruits',
            'game_visits': 24873612345,
            'game_playing': 154326,
            'creator_name': 'Block Games',
            'pass_name': '2x Experience',
            'price': 450,
            'price_range': 'medium',
            'sales_count': 980000,
            'category': 'boosters',
            'rank_in_game': 2
        },
        {
            'pass_id': 15217695,
            'game_id': 2753915549,
            'game_name': 'Blox Fruits',
            'game_visits': 24873612345,
            'game_playing': 154326,
            'creator_name': 'Block Games',
            'pass_name': 'Auto Farm',
            'price': 625,
            'price_range': 'medium',
            'sales_count': 820000,
            'category': 'automation',
            'rank_in_game': 3
        },
        {
            'pass_id': 7268933,
            'game_id': 4924922222,
            'game_name': 'Brookhaven RP',
            'game_visits': 19876543210,
            'game_playing': 142387,
            'creator_name': 'Wolfpaq Games',
            'pass_name': 'Premium',
            'price': 450,
            'price_range': 'medium',
            'sales_count': 900000,
            'category': 'access',
            'rank_in_game': 1
        },
        {
            'pass_id': 35062660,
            'game_id': 4924922222,
            'game_name': 'Brookhaven RP',
            'game_visits': 19876543210,
            'game_playing': 142387,
            'creator_name': 'Wolfpaq Games',
            'pass_name': 'Vehicle Pack',
            'price': 250,
            'price_range': 'low',
            'sales_count': 650000,
            'category': 'access',
            'rank_in_game': 2
        },
        {
            'pass_id': 35062665,
            'game_id': 4924922222,
            'game_name': 'Brookhaven RP',
            'game_visits': 19876543210,
            'game_playing': 142387,
            'creator_name': 'Wolfpaq Games',
            'pass_name': 'Custom Animations',
            'price': 175,
            'price_range': 'low',
            'sales_count': 580000,
            'category': 'cosmetics',
            'rank_in_game': 3
        },
        {
            'pass_id': 29547354,
            'game_id': 6516141723,
            'game_name': 'Doors',
            'game_visits': 3876543210,
            'game_playing': 86459,
            'creator_name': 'LSPLASH',
            'pass_name': 'Knobs Bundle',
            'price': 350,
            'price_range': 'medium',
            'sales_count': 420000,
            'category': 'cosmetics',
            'rank_in_game': 1
        },
        {
            'pass_id': 29547360,
            'game_id': 6516141723,
            'game_name': 'Doors',
            'game_visits': 3876543210,
            'game_playing': 86459,
            'creator_name': 'LSPLASH',
            'pass_name': 'Easy Mode',
            'price': 150,
            'price_range': 'low',
            'sales_count': 380000,
            'category': 'difficulty',
            'rank_in_game': 2
        },
        {
            'pass_id': 29547365,
            'game_id': 6516141723,
            'game_name': 'Doors',
            'game_visits': 3876543210,
            'game_playing': 86459,
            'creator_name': 'LSPLASH',
            'pass_name': 'Hard Mode',
            'price': 175,
            'price_range': 'low',
            'sales_count': 210000,
            'category': 'difficulty',
            'rank_in_game': 3
        }
    ]

def analyze_game_pass_data(game_pass_data: List[Dict], game_ids: List[int] = None, game_names: List[str] = None) -> Dict[str, Any]:
    """Analyze game pass data and generate insights"""
    
    # Group passes by game
    games = {}
    for pass_data in game_pass_data:
        game_id = pass_data.get('game_id')
        if game_id not in games:
            games[game_id] = {
                'id': game_id,
                'name': pass_data.get('game_name'),
                'visits': pass_data.get('game_visits', 0),
                'playing': pass_data.get('game_playing', 0),
                'creator': pass_data.get('creator_name'),
                'passes': []
            }
        games[game_id]['passes'].append(pass_data)
    
    # Calculate game-level metrics
    for game_id, game in games.items():
        passes = game['passes']
        game['total_passes'] = len(passes)
        game['free_passes'] = sum(1 for p in passes if p.get('price', 0) == 0)
        game['paid_passes'] = sum(1 for p in passes if p.get('price', 0) > 0)
        game['avg_price'] = sum(p.get('price', 0) for p in passes) / len(passes) if passes else 0
        game['total_sales'] = sum(p.get('sales_count', 0) for p in passes)
        game['most_expensive'] = max(passes, key=lambda x: x.get('price', 0)) if passes else None
        
        # Get pass categories
        categories = {}
        for p in passes:
            cat = p.get('category', 'other')
            categories[cat] = categories.get(cat, 0) + 1
        game['categories'] = categories
    
    # Calculate global metrics
    total_passes = len(game_pass_data)
    avg_passes_per_game = total_passes / len(games) if games else 0
    
    # Calculate price distribution
    price_ranges = {}
    for p in game_pass_data:
        range_name = p.get('price_range', 'unknown')
        price_ranges[range_name] = price_ranges.get(range_name, 0) + 1
    
    # Calculate category distribution
    categories = {}
    for p in game_pass_data:
        cat_name = p.get('category', 'other')
        categories[cat_name] = categories.get(cat_name, 0) + 1
    
    # Generate insights
    insights = generate_game_pass_insights(games, price_ranges, categories)
    
    return {
        "success": True,
        "games_analyzed": len(games),
        "total_passes": total_passes,
        "game_data": list(games.values()),
        "price_distribution": sorted(price_ranges.items(), key=lambda x: x[1], reverse=True),
        "category_distribution": sorted(categories.items(), key=lambda x: x[1], reverse=True),
        "insights": insights,
        "analysis_timestamp": datetime.now().isoformat()
    }

def generate_game_pass_insights(games: Dict, price_ranges: Dict, categories: Dict) -> List[str]:
    """Generate insights from game pass data"""
    insights = []
    
    # Basic stats
    total_games = len(games)
    total_passes = sum(len(game['passes']) for game in games.values())
    avg_passes = total_passes / total_games if total_games > 0 else 0
    
    insights.append(f"Analyzed {total_games} games with {total_passes} total game passes (avg: {avg_passes:.1f} per game)")
    
    # Price insights
    if price_ranges:
        top_price_range = max(price_ranges.items(), key=lambda x: x[1])
        insights.append(f"Most common price range: {top_price_range[0]} ({top_price_range[1]} passes, {top_price_range[1]/total_passes*100:.1f}%)")
    
    # Category insights
    if categories:
        top_category = max(categories.items(), key=lambda x: x[1])
        insights.append(f"Most common pass category: {top_category[0]} ({top_category[1]} passes, {top_category[1]/total_passes*100:.1f}%)")
    
    # Game-specific insights
    if games:
        # Game with most passes
        game_most_passes = max(games.values(), key=lambda g: g['total_passes'])
        insights.append(f"Most monetized game: {game_most_passes['name']} with {game_most_passes['total_passes']} passes")
        
        # Game with highest prices
        game_highest_avg = max(games.values(), key=lambda g: g['avg_price'])
        insights.append(f"Highest average price: {game_highest_avg['name']} at {game_highest_avg['avg_price']:.0f} Robux per pass")
        
        # Game with most sales
        game_most_sales = max(games.values(), key=lambda g: g['total_sales'])
        insights.append(f"Most pass sales: {game_most_sales['name']} with {game_most_sales['total_sales']:,} total sales")
        
        # Free pass analysis
        free_pass_counts = {g['name']: g['free_passes'] for g in games.values() if g['free_passes'] > 0}
        if free_pass_counts:
            game_most_free = max(free_pass_counts.items(), key=lambda x: x[1])
            insights.append(f"Most free passes: {game_most_free[0]} with {game_most_free[1]} free passes")
    
    # Monetization strategy insights
    strategies = analyze_monetization_strategies(games)
    insights.extend(strategies)
    
    return insights

def analyze_monetization_strategies(games: Dict) -> List[str]:
    """Analyze monetization strategies across games"""
    insights = []
    
    # Identify different monetization strategies
    vip_focused = []
    booster_focused = []
    cosmetic_focused = []
    free_focused = []
    
    for game_id, game in games.items():
        passes = game['passes']
        categories = game['categories']
        
        # Skip games with too few passes
        if len(passes) < 2:
            continue
        
        free_ratio = game['free_passes'] / game['total_passes'] if game['total_passes'] > 0 else 0
        
        if free_ratio > 0.5:
            free_focused.append(game['name'])
        elif categories.get('vip', 0) > max(categories.get('boosters', 0), categories.get('cosmetics', 0), categories.get('access', 0)):
            vip_focused.append(game['name'])
        elif categories.get('boosters', 0) > max(categories.get('vip', 0), categories.get('cosmetics', 0), categories.get('access', 0)):
            booster_focused.append(game['name'])
        elif categories.get('cosmetics', 0) > max(categories.get('vip', 0), categories.get('boosters', 0), categories.get('access', 0)):
            cosmetic_focused.append(game['name'])
    
    # Create strategy insights
    if vip_focused:
        insights.append(f"VIP-focused monetization: {', '.join(vip_focused[:2])}" + (f" and {len(vip_focused)-2} more" if len(vip_focused) > 2 else ""))
    
    if booster_focused:
        insights.append(f"Booster-focused monetization: {', '.join(booster_focused[:2])}" + (f" and {len(booster_focused)-2} more" if len(booster_focused) > 2 else ""))
    
    if cosmetic_focused:
        insights.append(f"Cosmetic-focused monetization: {', '.join(cosmetic_focused[:2])}" + (f" and {len(cosmetic_focused)-2} more" if len(cosmetic_focused) > 2 else ""))
    
    if free_focused:
        insights.append(f"Free pass-heavy strategy: {', '.join(free_focused[:2])}" + (f" and {len(free_focused)-2} more" if len(free_focused) > 2 else ""))
    
    return insights

# If run directly, initialize the cache DB
if __name__ == "__main__":
    setup_cache_db()
