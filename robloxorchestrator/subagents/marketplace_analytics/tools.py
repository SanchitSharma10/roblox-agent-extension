#!/usr/bin/env python3
"""
Marketplace Analytics Subagent - Tools (Fixed for ADK Compatibility)
Database query functions for marketplace_items table with ADK-compatible signatures
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Union
from supabase import create_client, Client
from dotenv import load_dotenv, find_dotenv
from datetime import datetime, timedelta

# Set up logging
logger = logging.getLogger(__name__)

# Try to load environment variables from multiple possible locations
env_loaded = False

# First try the local .env file
if os.path.exists('.env'):
    load_dotenv('.env')
    env_loaded = True

# Then try the parent directory .env file  
if not env_loaded:
    parent_env = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
    if os.path.exists(parent_env):
        load_dotenv(parent_env)
        env_loaded = True

# Try to find any .env file in the project
if not env_loaded:
    env_file = find_dotenv()
    if env_file:
        load_dotenv(env_file)

class MarketplaceDB:
    def __init__(self):
        """Initialize Supabase connection for marketplace data"""
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            # Try alternative environment variable names
            supabase_url = supabase_url or os.getenv('SUPABASE_PROJECT_URL')
            supabase_key = supabase_key or os.getenv('SUPABASE_ANON_KEY')
            
        if not supabase_url or not supabase_key:
            raise ValueError(f"Missing Supabase credentials. URL: {bool(supabase_url)}, Key: {bool(supabase_key)}")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)

    def execute_sql_query(self, sql_query: str, parameters_json: str = "{}"):
        """Execute raw SQL query on Supabase - SECURITY RESTRICTED"""
        
        # SECURITY: Only allow pre-approved safe queries
        SAFE_QUERIES = {
            'top_by_value': """
                SELECT name, price, rap, rolimons_value, demand, rarity_score, creator_name
                FROM marketplace_items 
                WHERE rolimons_value IS NOT NULL AND rolimons_value > 0
                ORDER BY rolimons_value DESC 
                LIMIT 20
            """,
            'trending_analysis': """
                SELECT name, price, trend, trend_direction, demand
                FROM marketplace_items 
                WHERE trend IS NOT NULL
                ORDER BY trend DESC 
                LIMIT 15
            """
        }
        
        # Security check: only allow whitelisted queries
        sql_normalized = ' '.join(sql_query.split())  # Normalize whitespace
        is_safe = any(sql_normalized.strip() == ' '.join(safe_sql.split()) 
                     for safe_sql in SAFE_QUERIES.values())
        
        if not is_safe:
            logger.warning(f"SECURITY: Blocked unsafe SQL query: {sql_query[:100]}...")
            return {
                'success': False,
                'error': 'SQL query not in whitelist - security restriction',
                'timestamp': datetime.now().isoformat()
            }
        
        try:
            # Parse parameters from JSON string
            parameters = json.loads(parameters_json) if parameters_json else {}
            
            # Use Supabase's RPC to call our SQL function
            result = self.supabase.rpc('execute_sql', {
                'sql_query': sql_query,
                'parameters': parameters
            }).execute()
            
            return {
                'success': True,
                'data': result.data,
                'count': len(result.data) if result.data else 0,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"SQL execution error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def query_marketplace_data(self, query_type: str, params: dict = None):
        """Query marketplace_items table based on type"""
        
        try:
            if query_type == "trending_items":
                # Get items trending up with high trend scores
                result = self.supabase.table('marketplace_items').select(
                    'name, price, rap, trend, trend_direction, demand, rarity_score, creator_name, rolimons_value'
                ).eq('trend_direction', 1).order('trend', desc=True).limit(20).execute()
                
            elif query_type == "top_by_value":
                # FIXED: Get highest value items - filter out nulls and order properly
                # Try multiple sorting strategies to get truly high-value items
                
                # Strategy 1: Sort by rolimons_value (excluding nulls and zeros)
                result = self.supabase.table('marketplace_items').select(
                    'name, price, rap, rolimons_value, demand, rarity_score, creator_name'
                ).not_.is_('rolimons_value', None).gt('rolimons_value', 0).order('rolimons_value', desc=True).limit(20).execute()
                
                # If that doesn't work well, try Strategy 2: Sort by RAP
                if not result.data or len(result.data) < 10:
                    result = self.supabase.table('marketplace_items').select(
                        'name, price, rap, rolimons_value, demand, rarity_score, creator_name'
                    ).not_.is_('rap', None).gt('rap', 0).order('rap', desc=True).limit(20).execute()
                
                # Strategy 3: Sort by price as fallback
                if not result.data or len(result.data) < 10:
                    result = self.supabase.table('marketplace_items').select(
                        'name, price, rap, rolimons_value, demand, rarity_score, creator_name'
                    ).gt('price', 0).order('price', desc=True).limit(20).execute()
                
            elif query_type == "top_by_value_sql":
                # Direct SQL approach for most valuable items
                sql_query = """
                SELECT name, price, rap, rolimons_value, demand, rarity_score, creator_name
                FROM marketplace_items 
                WHERE rolimons_value IS NOT NULL AND rolimons_value > 0
                ORDER BY rolimons_value DESC 
                LIMIT 20
                """
                return self.execute_sql_query(sql_query)
                
            elif query_type == "high_demand_low_price":
                # Find undervalued items (high demand, relatively low price)
                result = self.supabase.table('marketplace_items').select(
                    'name, price, rap, demand, rarity_score, trend_direction, creator_name, rolimons_value'
                ).gte('demand', 3).lt('price', 1000).order('demand', desc=True).limit(15).execute()
                
            elif query_type == "recent_price_changes":
                # Items with significant trend changes (since we don't have price_change_percent)
                result = self.supabase.table('marketplace_items').select(
                    'name, price, rap, trend, trend_direction, creator_name, rolimons_value'
                ).not_.is_('trend', None).order('trend', desc=True).limit(20).execute()
                
            elif query_type == "rarity_analysis":
                # Rarest items analysis
                result = self.supabase.table('marketplace_items').select(
                    'name, rarity_score, demand, price, rap, trend_direction, creator_name, rolimons_value'
                ).gte('rarity_score', 3).order('rarity_score', desc=True).limit(15).execute()
                
            elif query_type == "market_summary":
                # Overall market statistics
                total_result = self.supabase.table('marketplace_items').select('item_id', count='exact').execute()
                
                # Get items with non-null prices for average calculation
                price_result = self.supabase.table('marketplace_items').select('price, rap, rolimons_value').not_.is_('price', None).execute()
                
                # Calculate basic stats
                total_items = total_result.count if total_result.count else 0
                
                if price_result.data:
                    prices = [item['price'] for item in price_result.data if item['price'] and item['price'] > 0]
                    raps = [item['rap'] for item in price_result.data if item['rap'] and item['rap'] > 0]
                    values = [item['rolimons_value'] for item in price_result.data if item['rolimons_value'] and item['rolimons_value'] > 0]
                    
                    avg_price = sum(prices) / len(prices) if prices else 0
                    avg_rap = sum(raps) / len(raps) if raps else 0
                    avg_value = sum(values) / len(values) if values else 0
                    total_value = sum(values) if values else 0
                else:
                    avg_price = 0
                    avg_rap = 0
                    avg_value = 0
                    total_value = 0
                
                return {
                    'total_items': total_items,
                    'average_price': round(avg_price, 2),
                    'average_rap': round(avg_rap, 2),
                    'average_value': round(avg_value, 2),
                    'total_market_value': total_value,
                    'query_timestamp': datetime.now().isoformat()
                }
            
            elif query_type == "custom_sql":
                # SECURITY FIX: REMOVED DANGEROUS SQL EXECUTION
                # This was a critical SQL injection vulnerability!
                return {
                    'success': False,
                    'error': 'Custom SQL queries disabled for security',
                    'message': 'Use predefined query types instead',
                    'available_types': ['trending_items', 'top_by_value', 'high_demand_low_price'],
                    'timestamp': datetime.now().isoformat()
                }
            
            else:
                # Default: return recent items
                result = self.supabase.table('marketplace_items').select(
                    'name, price, rap, trend, demand, rarity_score, rolimons_value'
                ).order('last_checked_timestamp', desc=True).limit(10).execute()
            
            return {
                'data': result.data,
                'count': len(result.data) if result.data else 0,
                'query_type': query_type,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'query_type': query_type,
                'timestamp': datetime.now().isoformat()
            }

# Global instance (will be initialized when needed)
_marketplace_db = None
_db_error = None

def get_db_instance():
    """Get or create MarketplaceDB instance"""
    global _marketplace_db, _db_error
    if _marketplace_db is None and _db_error is None:
        try:
            _marketplace_db = MarketplaceDB()
        except Exception as e:
            _db_error = str(e)
            print(f"Warning: Could not initialize MarketplaceDB: {e}")
    return _marketplace_db

# ADK Tool Functions (Fixed for ADK compatibility - simplified signatures)
async def execute_custom_sql(sql_query: str, parameters_json: str = "{}"):
    """Execute a custom SQL query on the marketplace database.
    
    Args:
        sql_query: The SQL query to execute
        parameters_json: Optional JSON string of parameters for the query
        
    Returns:
        Dictionary with query results
    """
    db = get_db_instance()
    if db is None:
        return {"error": _db_error or "Database not available"}
    
    return db.execute_sql_query(sql_query, parameters_json)

async def get_market_summary():
    """Get overall marketplace summary statistics.
    
    Returns:
        Dictionary with market summary data including total items, average prices, and total market value
    """
    db = get_db_instance()
    if db is None:
        return {"error": _db_error or "Database not available"}
    return db.query_marketplace_data("market_summary")

async def get_trending_items():
    """Get currently trending marketplace items.
    
    Returns:
        List of trending items with trend data
    """
    db = get_db_instance()
    if db is None:
        return []
    result = db.query_marketplace_data("trending_items")
    return result.get('data', [])

async def get_high_value_items():
    """Get highest value marketplace items (fixed with better sorting).
    
    Returns:
        List of items with highest rolimons values, RAP, or prices
    """
    db = get_db_instance()
    if db is None:
        return []
    result = db.query_marketplace_data("top_by_value")
    return result.get('data', [])

async def get_high_value_items_sql():
    """Get highest value items using direct SQL query.
    
    Returns:
        List of highest value items using optimized SQL
    """
    db = get_db_instance()
    if db is None:
        return []
    
    # Use direct SQL for more control
    sql_query = """
    SELECT name, price, rap, rolimons_value, demand, rarity_score, creator_name,
           COALESCE(rolimons_value, rap, price, 0) as max_value
    FROM marketplace_items 
    WHERE COALESCE(rolimons_value, rap, price) > 0
    ORDER BY max_value DESC 
    LIMIT 20
    """
    
    result = db.execute_sql_query(sql_query)
    return result.get('data', []) if result.get('success') else []

async def find_investment_opportunities():
    """Find undervalued items with high demand.
    
    Returns:
        List of items that have high demand but relatively low prices
    """
    db = get_db_instance()
    if db is None:
        return []
    result = db.query_marketplace_data("high_demand_low_price")
    return result.get('data', [])

async def analyze_rare_items():
    """Get analysis of rare marketplace items.
    
    Returns:
        List of items with high rarity scores
    """
    db = get_db_instance()
    if db is None:
        return []
    result = db.query_marketplace_data("rarity_analysis")
    return result.get('data', [])

async def search_marketplace_items(query: str):
    """Search marketplace items based on query.
    
    Args:
        query: Search query for marketplace items
        
    Returns:
        List of marketplace items matching the query context
    """
    # Simple keyword matching to determine query type
    query_lower = query.lower()
    
    if "trending" in query_lower or "trend" in query_lower:
        query_type = "trending_items"
    elif "valuable" in query_lower or "expensive" in query_lower or "value" in query_lower:
        query_type = "top_by_value"
    elif "undervalued" in query_lower or ("demand" in query_lower and ("price" in query_lower or "low" in query_lower)):
        query_type = "high_demand_low_price"
    elif "price change" in query_lower or "changed" in query_lower:
        query_type = "recent_price_changes"
    elif "rare" in query_lower or "rarity" in query_lower:
        query_type = "rarity_analysis"
    elif "summary" in query_lower or "overview" in query_lower or "market" in query_lower:
        query_type = "market_summary"
    else:
        query_type = "default"
    
    db = get_db_instance()
    if db is None:
        return []
    result = db.query_marketplace_data(query_type)
    return result.get('data', []) if query_type != "market_summary" else [result]

async def advanced_marketplace_query(query_description: str):
    """Execute advanced marketplace queries using SQL.
    
    Args:
        query_description: Description of what data to retrieve
        
    Returns:
        Dictionary with query results based on the description
    """
    db = get_db_instance()
    if db is None:
        return {"error": _db_error or "Database not available"}
    
    # Map common descriptions to SQL queries
    query_lower = query_description.lower()
    
    if "most expensive" in query_lower or "highest price" in query_lower:
        sql = """
        SELECT name, price, rap, rolimons_value, creator_name
        FROM marketplace_items 
        WHERE price > 0
        ORDER BY price DESC 
        LIMIT 20
        """
        result = db.execute_sql_query(sql)
        return result
    
    elif "highest rap" in query_lower:
        sql = """
        SELECT name, price, rap, rolimons_value, demand, creator_name
        FROM marketplace_items 
        WHERE rap IS NOT NULL AND rap > 0
        ORDER BY rap DESC 
        LIMIT 20
        """
        result = db.execute_sql_query(sql)
        return result
    
    elif "limited" in query_lower and "valuable" in query_lower:
        sql = """
        SELECT name, price, rap, rolimons_value, demand, creator_name
        FROM marketplace_items 
        WHERE is_limited = true 
        AND rolimons_value > 1000
        ORDER BY rolimons_value DESC 
        LIMIT 15
        """
        result = db.execute_sql_query(sql)
        return result
    
    else:
        return {"error": f"Could not interpret query: {query_description}"}

# Main agent function for ADK
async def call_marketplace_agent(request: str):
    """Main marketplace analytics agent function.
    
    Args:
        request: Natural language request about marketplace data
        
    Returns:
        Dictionary containing marketplace analysis results
    """
    db = get_db_instance()
    if db is None:
        return {"error": _db_error or "Database not available", "request": request}
    
    # Determine what type of analysis is needed
    request_lower = request.lower()
    
    if "summary" in request_lower or "overview" in request_lower:
        return await get_market_summary()
    elif "trending" in request_lower:
        data = await get_trending_items()
        return {"type": "trending_items", "data": data, "count": len(data)}
    elif "valuable" in request_lower or "value" in request_lower:
        # Try the enhanced SQL-based query first
        data = await get_high_value_items_sql()
        if not data:
            data = await get_high_value_items()
        return {"type": "high_value_items", "data": data, "count": len(data)}
    elif "investment" in request_lower or "undervalued" in request_lower:
        data = await find_investment_opportunities()
        return {"type": "investment_opportunities", "data": data, "count": len(data)}
    elif "rare" in request_lower or "rarity" in request_lower:
        data = await analyze_rare_items()
        return {"type": "rare_items", "data": data, "count": len(data)}
    elif "sql" in request_lower or "query" in request_lower:
        # Handle direct SQL requests
        return await advanced_marketplace_query(request)
    else:
        # General search
        data = await search_marketplace_items(request)
        return {"type": "search_results", "data": data, "count": len(data)}

# Import visualization tools
from .visualization_tools import (
    create_marketplace_visualization,
    generate_trend_report_with_charts
)

# Export the tools for ADK (simplified for compatibility)
tools = [
    call_marketplace_agent,
    get_market_summary,
    get_trending_items,
    get_high_value_items,
    get_high_value_items_sql,
    find_investment_opportunities,
    analyze_rare_items,
    search_marketplace_items,
    execute_custom_sql,
    advanced_marketplace_query,
    create_marketplace_visualization,
    generate_trend_report_with_charts,
]
