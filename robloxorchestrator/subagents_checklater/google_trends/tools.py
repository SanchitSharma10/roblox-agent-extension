#!/usr/bin/env python3
"""
Google Trends Analysis Tools
Comprehensive Google Trends analysis for Roblox economy intelligence
"""

from pytrends.request import TrendReq
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
import time
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import json

class GoogleTrendsAnalyzer:
    def __init__(self):
        """Initialize Google Trends analyzer"""
        self.pytrends = TrendReq(hl='en-US', tz=360)
        
        # Define comprehensive keyword categories
        self.economy_keywords = {
            "general": [
                "roblox", "robux", "roblox trading", "roblox marketplace",
                "roblox economy", "roblox limiteds", "roblox investing"
            ],
            "items": [
                "dominus empyreus", "dominus frigidus", "dominus astra",
                "shaggy super saiyan", "workclock shades", "fedora roblox",
                "roblox rare items", "roblox expensive items"
            ],
            "games": [
                "adopt me roblox", "tower of hell", "brookhaven roblox",
                "arsenal roblox", "murder mystery 2", "piggy roblox"
            ],
            "tools": [
                "rolimons", "roblox trade calculator", "roblox value list",
                "rbx trade", "roblox trading discord"
            ]
        }
        
        # Regional codes for analysis
        self.regions = {
            "US": "United States",
            "GB": "United Kingdom", 
            "CA": "Canada",
            "AU": "Australia",
            "BR": "Brazil",
            "KR": "South Korea",
            "JP": "Japan",
            "DE": "Germany",
            "FR": "France",
            "NL": "Netherlands"
        }

    def get_trends_data(self, keywords: List[str], timeframe: str = "today 3-m", 
                       geo: str = "US", category: int = 0) -> pd.DataFrame:
        """Get trends data for specified keywords"""
        try:
            # Ensure proper timeframe format
            if timeframe and not timeframe.startswith("today ") and not "-" in timeframe:
                if timeframe == "1d":
                    timeframe = "now 1-d"
                elif timeframe == "7d":
                    timeframe = "now 7-d"
                elif timeframe == "30d":
                    timeframe = "today 1-m"
                elif timeframe == "3m":
                    timeframe = "today 3-m"
                elif timeframe == "12m":
                    timeframe = "today 12-m"
                elif timeframe == "5y":
                    timeframe = "today 5-y"
            
            print(f"Building pytrends payload for keywords: {keywords}, timeframe: {timeframe}, geo: {geo}")
            
            # Add a short delay before API call to avoid rate limiting
            time.sleep(1)
            
            # Build payload
            self.pytrends.build_payload(
                keywords, 
                cat=category, 
                timeframe=timeframe, 
                geo=geo, 
                gprop=''
            )
            
            print("Successfully built payload, getting interest over time...")
            
            # Add another short delay
            time.sleep(1)
            
            # Get interest over time
            interest_over_time = self.pytrends.interest_over_time()
            
            print(f"Got interest over time result with shape: {interest_over_time.shape if not interest_over_time.empty else 'empty'}")
            
            # Remove 'isPartial' column if it exists
            if not interest_over_time.empty and 'isPartial' in interest_over_time.columns:
                interest_over_time = interest_over_time.drop('isPartial', axis=1)
                print(f"Removed isPartial column, remaining columns: {interest_over_time.columns.tolist()}")
            
            return interest_over_time
            
        except Exception as e:
            import traceback
            print(f"Error fetching trends data: {e}")
            print(traceback.format_exc())
            return pd.DataFrame()

    def get_related_queries(self, keyword: str, timeframe: str = "3m", 
                          geo: str = "US") -> Dict:
        """Get related queries for a keyword"""
        try:
            self.pytrends.build_payload([keyword], timeframe=timeframe, geo=geo)
            related_queries_raw = self.pytrends.related_queries()
            
            # Process the data to convert numpy types to Python types
            result = {}
            if keyword in related_queries_raw:
                raw_data = related_queries_raw[keyword]
                
                if 'top' in raw_data and raw_data['top'] is not None and not raw_data['top'].empty:
                    # Convert the DataFrame to a list of dicts
                    top_list = []
                    for _, row in raw_data['top'].iterrows():
                        top_list.append({
                            'query': row.get('query', ''),
                            'value': int(row.get('value', 0))  # Convert numpy int to Python int
                        })
                    result['top'] = top_list
                else:
                    result['top'] = []
                
                if 'rising' in raw_data and raw_data['rising'] is not None and not raw_data['rising'].empty:
                    # Convert the DataFrame to a list of dicts
                    rising_list = []
                    for _, row in raw_data['rising'].iterrows():
                        rising_list.append({
                            'query': row.get('query', ''),
                            'value': int(row.get('value', 0))  # Convert numpy int to Python int
                        })
                    result['rising'] = rising_list
                else:
                    result['rising'] = []
                
                return result
            else:
                return {}
                
        except Exception as e:
            print(f"Error fetching related queries: {e}")
            return {}

    def get_regional_interest(self, keyword: str, timeframe: str = "3m") -> pd.DataFrame:
        """Get regional interest for a keyword"""
        try:
            self.pytrends.build_payload([keyword], timeframe=timeframe)
            regional_interest = self.pytrends.interest_by_region()
            return regional_interest.sort_values(keyword, ascending=False)
        except Exception as e:
            print(f"Error fetching regional interest: {e}")
            return pd.DataFrame()

    def analyze_trend_correlation(self, df1: pd.DataFrame, df2: pd.DataFrame, 
                                 col1: str, col2: str) -> Dict:
        """Analyze correlation between two trend datasets"""
        try:
            # Align the datasets by date
            merged = pd.merge(df1, df2, left_index=True, right_index=True, how='inner')
            
            if col1 in merged.columns and col2 in merged.columns:
                correlation = merged[col1].corr(merged[col2])
                
                # Perform regression analysis
                slope, intercept, r_value, p_value, std_err = stats.linregress(
                    merged[col1].dropna(), merged[col2].dropna()
                )
                
                return {
                    "correlation": correlation,
                    "r_squared": r_value ** 2,
                    "slope": slope,
                    "intercept": intercept,
                    "p_value": p_value,
                    "significance": "high" if p_value < 0.01 else "medium" if p_value < 0.05 else "low"
                }
            else:
                return {"error": f"Columns not found: {col1}, {col2}"}
                
        except Exception as e:
            return {"error": str(e)}

    def detect_trend_anomalies(self, data: pd.Series, threshold: float = 2.0) -> List[Dict]:
        """Detect anomalies in trend data using statistical methods"""
        try:
            # Calculate z-scores
            z_scores = np.abs(stats.zscore(data.dropna()))
            
            # Find anomalies
            anomalies = []
            for idx, z_score in enumerate(z_scores):
                if z_score > threshold:
                    date = data.index[idx]
                    value = data.iloc[idx]
                    anomalies.append({
                        "date": date.strftime("%Y-%m-%d"),
                        "value": int(value),  # Convert numpy.int32/64 to Python int
                        "z_score": float(z_score),  # Convert numpy.float32/64 to Python float
                        "type": "spike" if value > data.mean() else "drop"
                    })
            
            return sorted(anomalies, key=lambda x: x["z_score"], reverse=True)
            
        except Exception as e:
            print(f"Error detecting anomalies: {e}")
            return []

# Global trends analyzer instance
_trends_analyzer = None

def get_trends_analyzer():
    """Get or create trends analyzer instance"""
    global _trends_analyzer
    if _trends_analyzer is None:
        _trends_analyzer = GoogleTrendsAnalyzer()
    return _trends_analyzer

# Tool Functions
async def get_roblox_search_trends(keywords: Optional[List[str]] = None, timeframe: str = "3m", 
                                  region: str = "US") -> Dict[str, Any]:
    """Get search trends for Roblox-related keywords.
    
    Args:
        keywords: List of keywords to analyze
        timeframe: Time period for analysis (1d, 7d, 30d, 3m, 12m, 5y)
        region: Region for analysis (US, GB, CA, etc.)
        
    Returns:
        Dictionary with trend analysis data
    """
    try:
        analyzer = get_trends_analyzer()
        
        # Default keywords if none provided
        if keywords is None or len(keywords) == 0:
            keywords = ["roblox gaming", "roblox games", "robux", "roblox limited", "roblox marketplace"]
        
        # Ensure proper timeframe format for pytrends
        if timeframe and not timeframe.startswith("today ") and not "-" in timeframe:
            if timeframe == "1d":
                timeframe = "now 1-d"
            elif timeframe == "7d":
                timeframe = "now 7-d"
            elif timeframe == "30d":
                timeframe = "today 1-m"
            elif timeframe == "3m":
                timeframe = "today 3-m"
            elif timeframe == "12m":
                timeframe = "today 12-m"
            elif timeframe == "5y":
                timeframe = "today 5-y"
        
        print(f"Getting trends data for keywords: {keywords}, timeframe: {timeframe}, region: {region}")
        
        # Limit keywords to 5 for Google Trends API
        keywords = keywords[:5]
        
        # Get trends data
        trends_data = analyzer.get_trends_data(keywords, timeframe, region)
        
        if trends_data.empty:
            print(f"ERROR: Empty trends data returned for {keywords}")
            return {
                "success": False,
                "error": "No trends data retrieved",
                "keywords": keywords,
                "timeframe": timeframe,
                "region": region
            }
        
        print(f"Successfully retrieved trends data with columns: {trends_data.columns.tolist()}")
        
        # Calculate basic statistics
        trend_stats = {}
        for keyword in keywords:
            if keyword in trends_data.columns:
                series = trends_data[keyword]
                trend_stats[keyword] = {
                    "average": float(round(series.mean(), 2)),
                    "max": int(series.max()),
                    "min": int(series.min()),
                    "std_dev": float(round(series.std(), 2)),
                    "current_value": int(series.iloc[-1]) if len(series) > 0 else 0,
                    "trend_direction": "up" if series.iloc[-1] > series.mean() else "down",
                    "volatility": "high" if series.std() > series.mean() else "medium" if series.std() > series.mean() * 0.5 else "low"
                }
            else:
                print(f"WARNING: Keyword {keyword} not found in trends data")
        
        if not trend_stats:
            print(f"ERROR: No valid keywords found in trends data columns: {trends_data.columns.tolist()}")
            return {
                "success": False,
                "error": "No valid keywords found in trends data",
                "keywords": keywords,
                "available_columns": trends_data.columns.tolist()
            }
        
        # Detect anomalies for the most popular keyword
        main_keyword = max(trend_stats.keys(), key=lambda k: trend_stats[k]["average"])
        anomalies = analyzer.detect_trend_anomalies(trends_data[main_keyword])
        
        # Convert numpy types to Python native types in anomalies
        for anomaly in anomalies:
            anomaly["value"] = int(anomaly["value"])
            anomaly["z_score"] = float(anomaly["z_score"])
        
        # Calculate period-over-period changes
        period_changes = {}
        for keyword in keywords:
            if keyword in trends_data.columns:
                series = trends_data[keyword]
                if len(series) > 1:
                    recent_avg = series.tail(7).mean() if len(series) >= 7 else series.tail().mean()
                    older_avg = series.head(7).mean() if len(series) >= 14 else series.head().mean()
                    change_pct = ((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0
                    period_changes[keyword] = float(round(change_pct, 2))
        
        # Get related queries for main keyword
        related_queries = analyzer.get_related_queries(main_keyword, timeframe, region)
        
        # Convert any numpy types in related_queries
        if isinstance(related_queries, dict):
            # Process top queries
            if 'top' in related_queries and related_queries['top'] is not None:
                for item in related_queries['top']:
                    if 'value' in item:
                        item['value'] = int(item['value'])
            
            # Process rising queries
            if 'rising' in related_queries and related_queries['rising'] is not None:
                for item in related_queries['rising']:
                    if 'value' in item:
                        item['value'] = int(item['value'])
        
        print(f"Analysis complete for {len(trend_stats)} keywords")
        
        return {
            "success": True,
            "keywords": keywords,
            "timeframe": timeframe,
            "region": region,
            "trend_statistics": trend_stats,
            "period_over_period_changes": period_changes,
            "anomalies": anomalies[:5],  # Top 5 anomalies
            "related_queries": related_queries,
            "data_points": int(len(trends_data)),
            "analysis_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        import traceback
        print(f"ERROR in get_roblox_search_trends: {e}")
        print(traceback.format_exc())
        return {
            "success": False,
            "error": str(e),
            "keywords": keywords or [],
            "timeframe": timeframe,
            "region": region
        }

async def analyze_item_search_patterns(item_names: Optional[List[str]] = None, timeframe: str = "3m") -> Dict[str, Any]:
    """Analyze search patterns for specific Roblox items.
    
    Args:
        item_names: List of item names to analyze
        timeframe: Time period for analysis
        
    Returns:
        Dictionary with item search pattern analysis
    """
    try:
        analyzer = get_trends_analyzer()
        
        # Default items if none provided
        if item_names is None:
            item_names = [
                "dominus empyreus", "dominus frigidus",
                "shaggy super saiyan", "workclock shades"
            ]
        
        # Limit to 5 items for API constraints
        item_names = item_names[:5]
        
        # Get trends data for items
        trends_data = analyzer.get_trends_data(item_names, timeframe)
        
        if trends_data.empty:
            return {
                "success": False,
                "error": "No trends data for items",
                "items": item_names
            }
        
        # Analyze each item's search pattern
        item_analysis = {}
        
        for item in item_names:
            if item in trends_data.columns:
                series = trends_data[item]
                
                # Find search peaks
                peaks = []
                for i in range(1, len(series) - 1):
                    if series.iloc[i] > series.iloc[i-1] and series.iloc[i] > series.iloc[i+1]:
                        if series.iloc[i] > series.mean() + series.std():
                            peaks.append({
                                "date": series.index[i].strftime("%Y-%m-%d"),
                                "value": series.iloc[i],
                                "significance": "high" if series.iloc[i] > series.mean() + 2*series.std() else "medium"
                            })
                
                # Calculate search momentum
                recent_trend = series.tail(7).mean() - series.head(7).mean() if len(series) >= 14 else 0
                momentum = "increasing" if recent_trend > 5 else "decreasing" if recent_trend < -5 else "stable"
                
                # Seasonal analysis
                if len(series) >= 30:
                    # Simple seasonality check (weekly pattern)
                    weekly_avg = series.groupby(series.index.dayofweek).mean()
                    seasonality_strength = weekly_avg.std() / weekly_avg.mean() if weekly_avg.mean() > 0 else 0
                    has_seasonality = seasonality_strength > 0.3
                else:
                    has_seasonality = False
                    seasonality_strength = 0
                
                item_analysis[item] = {
                    "average_search_volume": round(series.mean(), 2),
                    "peak_search_value": series.max(),
                    "search_momentum": momentum,
                    "recent_trend_value": recent_trend,
                    "search_peaks": peaks[:3],  # Top 3 peaks
                    "volatility": round(series.std() / series.mean() if series.mean() > 0 else 0, 3),
                    "has_seasonality": has_seasonality,
                    "seasonality_strength": round(seasonality_strength, 3),
                    "search_consistency": "high" if series.min() > series.mean() * 0.5 else "low"
                }
        
        # Compare items
        top_searched = sorted(item_analysis.items(), 
                            key=lambda x: x[1]["average_search_volume"], 
                            reverse=True)
        
        most_volatile = sorted(item_analysis.items(),
                             key=lambda x: x[1]["volatility"],
                             reverse=True)
        
        return {
            "success": True,
            "items_analyzed": item_names,
            "timeframe": timeframe,
            "item_analysis": item_analysis,
            "rankings": {
                "top_searched": [(item, data["average_search_volume"]) for item, data in top_searched],
                "most_volatile": [(item, data["volatility"]) for item, data in most_volatile]
            },
            "insights": generate_item_insights(item_analysis),
            "analysis_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "items": item_names or [],
            "timeframe": timeframe
        }

async def track_seasonal_trends(keywords: Optional[List[str]] = None, years_back: int = 2) -> Dict[str, Any]:
    """Track seasonal patterns in Roblox search trends.
    
    Args:
        keywords: Keywords to analyze for seasonality
        years_back: Number of years to look back
        
    Returns:
        Dictionary with seasonal trend analysis
    """
    try:
        analyzer = get_trends_analyzer()
        
        # Default keywords if none provided
        if keywords is None:
            keywords = ["roblox", "robux", "roblox trading"]
        
        # Limit to 3 keywords for seasonal analysis
        keywords = keywords[:3]
        
        # Get extended timeframe for seasonal analysis
        timeframe = f"{years_back*12}m"  # Convert years to months
        
        # Get trends data
        trends_data = analyzer.get_trends_data(keywords, timeframe)
        
        if trends_data.empty:
            return {
                "success": False,
                "error": "No historical data available",
                "keywords": keywords
            }
        
        seasonal_analysis = {}
        
        for keyword in keywords:
            if keyword in trends_data.columns:
                series = trends_data[keyword]
                
                # Add time-based features
                series_with_time = pd.DataFrame({
                    'value': series,
                    'month': series.index.month,
                    'quarter': series.index.quarter,
                    'day_of_week': series.index.dayofweek,
                    'week_of_year': series.index.isocalendar().week
                })
                
                # Monthly seasonality
                monthly_avg = series_with_time.groupby('month')['value'].mean()
                strongest_month = monthly_avg.idxmax()
                weakest_month = monthly_avg.idxmin()
                seasonal_variation = (monthly_avg.max() - monthly_avg.min()) / monthly_avg.mean()
                
                # Quarterly patterns
                quarterly_avg = series_with_time.groupby('quarter')['value'].mean()
                
                # Weekly patterns
                weekly_avg = series_with_time.groupby('day_of_week')['value'].mean()
                
                # Holiday effect analysis (December spike analysis)
                december_data = series_with_time[series_with_time['month'] == 12]['value']
                december_boost = december_data.mean() / monthly_avg.mean() if len(december_data) > 0 else 1
                
                seasonal_analysis[keyword] = {
                    "seasonal_strength": round(seasonal_variation, 3),
                    "has_strong_seasonality": seasonal_variation > 0.5,
                    "strongest_month": strongest_month,
                    "weakest_month": weakest_month,
                    "monthly_pattern": monthly_avg.to_dict(),
                    "quarterly_pattern": quarterly_avg.to_dict(),
                    "weekly_pattern": weekly_avg.to_dict(),
                    "holiday_boost": round(december_boost, 2),
                    "seasonal_insights": generate_seasonal_insights(monthly_avg, quarterly_avg)
                }
        
        # Cross-keyword seasonal correlation
        correlations = {}
        if len(keywords) > 1:
            for i, kw1 in enumerate(keywords):
                for kw2 in keywords[i+1:]:
                    if kw1 in trends_data.columns and kw2 in trends_data.columns:
                        corr = trends_data[kw1].corr(trends_data[kw2])
                        # Handle NaN values for JSON serialization
                        if pd.isna(corr):
                            correlations[f"{kw1}_vs_{kw2}"] = None
                        else:
                            correlations[f"{kw1}_vs_{kw2}"] = round(corr, 3)
        
        return {
            "success": True,
            "keywords": keywords,
            "years_analyzed": years_back,
            "seasonal_analysis": seasonal_analysis,
            "cross_keyword_correlations": correlations,
            "overall_insights": generate_overall_seasonal_insights(seasonal_analysis),
            "analysis_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "keywords": keywords or [],
            "years_back": years_back
        }

async def compare_game_trends(game_names: Optional[List[str]] = None, 
                              timeframe: str = "3m") -> Dict[str, Any]:
    """Compare search trends between Roblox games to identify patterns and correlations.
    
    Args:
        game_names: List of Roblox game names to compare
        timeframe: Time period for analysis (1d, 7d, 30d, 3m, 12m, 5y)
        
    Returns:
        Dictionary with comparative game trend analysis
    """
    try:
        analyzer = get_trends_analyzer()
        
        # Default games if none provided
        if game_names is None or len(game_names) == 0:
            game_names = ["adopt me roblox", "blox fruits", "murder mystery 2", "brookhaven rp", "tower of hell"]
        
        # Ensure we add "roblox" to game names if not present (for better search results)
        formatted_game_names = []
        for game in game_names:
            if "roblox" not in game.lower():
                formatted_game_names.append(f"{game} roblox")
            else:
                formatted_game_names.append(game)
        
        # Limit to 5 games for API constraints
        formatted_game_names = formatted_game_names[:5]
        
        print(f"Comparing trends for games: {formatted_game_names}, timeframe: {timeframe}")
        
        # Get trends data
        trends_data = analyzer.get_trends_data(formatted_game_names, timeframe)
        
        if trends_data.empty:
            print(f"ERROR: Empty trends data returned for {formatted_game_names}")
            return {
                "success": False,
                "error": "No trends data retrieved for specified games",
                "games": formatted_game_names,
                "timeframe": timeframe
            }
        
        print(f"Successfully retrieved game trends data with columns: {trends_data.columns.tolist()}")
        
        # Calculate basic statistics for each game
        game_stats = {}
        for game in formatted_game_names:
            if game in trends_data.columns:
                series = trends_data[game]
                game_stats[game] = {
                    "average_interest": float(round(series.mean(), 2)),
                    "peak_interest": int(series.max()),
                    "lowest_interest": int(series.min()),
                    "std_dev": float(round(series.std(), 2)),
                    "current_interest": int(series.iloc[-1]) if len(series) > 0 else 0,
                    "trend": "up" if series.iloc[-1] > series.mean() else "down",
                    "volatility": float(round(series.std() / series.mean() if series.mean() > 0 else 0, 3))
                }
        
        if not game_stats:
            print(f"ERROR: No valid games found in trends data columns: {trends_data.columns.tolist()}")
            return {
                "success": False,
                "error": "No valid games found in trends data",
                "games": formatted_game_names
            }
        
        # Find games with similar trends (correlations)
        correlations = {}
        if len(game_stats) > 1:
            for i, game1 in enumerate(formatted_game_names):
                if game1 not in trends_data.columns:
                    continue
                    
                for game2 in formatted_game_names[i+1:]:
                    if game2 not in trends_data.columns:
                        continue
                        
                    # Calculate correlation
                    correlation = trends_data[game1].corr(trends_data[game2])
                    # Handle NaN values which cause JSON serialization errors
                    if pd.isna(correlation):
                        correlations[f"{game1}_vs_{game2}"] = None  # Use None which becomes null in JSON
                    else:
                        correlations[f"{game1}_vs_{game2}"] = float(round(correlation, 3))
        
        # Find games with competitive relationship (inverse correlation)
        competitive_pairs = []
        for pair, corr in correlations.items():
            if corr < -0.3:  # Negative correlation suggests competition
                game1, game2 = pair.split("_vs_")
                competitive_pairs.append({
                    "games": [game1, game2],
                    "correlation": corr,
                    "relationship": "competitive"
                })
        
        # Find games with complementary relationship (positive correlation)
        complementary_pairs = []
        for pair, corr in correlations.items():
            if corr > 0.7:  # Strong positive correlation suggests complementary interest
                game1, game2 = pair.split("_vs_")
                complementary_pairs.append({
                    "games": [game1, game2],
                    "correlation": corr,
                    "relationship": "complementary"
                })
        
        # Game rankings by average interest
        game_rankings = sorted(game_stats.items(), key=lambda x: x[1]["average_interest"], reverse=True)
        
        # Detect anomalies and spikes for each game
        anomalies = {}
        for game, stats in game_stats.items():
            if game in trends_data.columns:
                series = trends_data[game]
                game_anomalies = analyzer.detect_trend_anomalies(series)
                if game_anomalies:
                    anomalies[game] = game_anomalies[:3]  # Top 3 anomalies
        
        # Generate insights
        insights = []
        
        # Top game insight
        if game_rankings:
            top_game = game_rankings[0]
            insights.append(f"'{top_game[0]}' has the highest average search interest at {top_game[1]['average_interest']}")
        
        # Correlation insights
        if complementary_pairs:
            top_complementary = complementary_pairs[0]
            insights.append(f"'{top_complementary['games'][0]}' and '{top_complementary['games'][1]}' show strong correlation ({top_complementary['correlation']}), suggesting shared player interest")
        
        if competitive_pairs:
            top_competitive = competitive_pairs[0]
            insights.append(f"'{top_competitive['games'][0]}' and '{top_competitive['games'][1]}' show inverse correlation ({top_competitive['correlation']}), suggesting they may compete for player attention")
        
        # Volatility insight
        most_volatile = max(game_stats.items(), key=lambda x: x[1]["volatility"])
        insights.append(f"'{most_volatile[0]}' shows the highest search volatility, suggesting player interest fluctuates frequently")
        
        # Create summary for correlation matrix (for visualization)
        correlation_matrix = {}
        for game1 in formatted_game_names:
            if game1 not in trends_data.columns:
                continue
                
            correlation_matrix[game1] = {}
            for game2 in formatted_game_names:
                if game2 not in trends_data.columns:
                    continue
                    
                if game1 == game2:
                    correlation_matrix[game1][game2] = 1.0
                else:
                    key = f"{game1}_vs_{game2}" if f"{game1}_vs_{game2}" in correlations else f"{game2}_vs_{game1}"
                    correlation_matrix[game1][game2] = correlations.get(key, 0.0)
        
        # Generate recommendations
        recommendations = []
        
        # For high-correlation pairs
        for pair in complementary_pairs:
            recommendations.append(f"Consider co-marketing '{pair['games'][0]}' and '{pair['games'][1]}' due to strong audience overlap")
        
        # For games with recent uptrends
        for game, stats in game_stats.items():
            if stats["trend"] == "up" and stats["average_interest"] > 20:
                recommendations.append(f"Capitalize on growing interest in '{game}'")
        
        return {
            "success": True,
            "games_analyzed": formatted_game_names,
            "timeframe": timeframe,
            "game_statistics": game_stats,
            "correlations": correlations,
            "competitive_relationships": competitive_pairs,
            "complementary_relationships": complementary_pairs,
            "rankings": [{"game": game, "average_interest": stats["average_interest"]} for game, stats in game_rankings],
            "anomalies": anomalies,
            "insights": insights,
            "recommendations": recommendations,
            "correlation_matrix": correlation_matrix,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        import traceback
        print(f"ERROR in compare_game_trends: {e}")
        print(traceback.format_exc())
        return {
            "success": False,
            "error": str(e),
            "games": game_names or [],
            "timeframe": timeframe
        }

async def detect_viral_events(keywords: Optional[List[str]] = None, 
                              timeframe: str = "3m",
                              threshold: float = 3.0) -> Dict[str, Any]:
    """Detect viral events and spikes in Roblox-related search trends.
    
    Args:
        keywords: List of keywords to analyze for viral events
        timeframe: Time period for analysis (1d, 7d, 30d, 3m, 12m, 5y)
        threshold: Z-score threshold for viral event detection (higher = more selective)
        
    Returns:
        Dictionary with viral event analysis
    """
    try:
        analyzer = get_trends_analyzer()
        
        # Default keywords if none provided
        if keywords is None or len(keywords) == 0:
            keywords = ["roblox", "robux", "roblox update", "adopt me roblox", "blox fruits"]
        
        # Limit keywords to 5 for API constraints
        keywords = keywords[:5]
        
        print(f"Detecting viral events for: {keywords}, timeframe: {timeframe}, threshold: {threshold}")
        
        # Get trends data
        trends_data = analyzer.get_trends_data(keywords, timeframe)
        
        if trends_data.empty:
            print(f"ERROR: Empty trends data returned for {keywords}")
            return {
                "success": False,
                "error": "No trends data retrieved",
                "keywords": keywords,
                "timeframe": timeframe
            }
        
        # Detect viral events for each keyword
        viral_events = {}
        all_events = []
        
        for keyword in keywords:
            if keyword in trends_data.columns:
                series = trends_data[keyword]
                
                # Detect anomalies with the given threshold
                anomalies = analyzer.detect_trend_anomalies(series, threshold=threshold)
                
                if anomalies:
                    # Add more context to each anomaly
                    for anomaly in anomalies:
                        # Convert the date string to datetime for easier manipulation
                        event_date = datetime.strptime(anomaly["date"], "%Y-%m-%d")
                        
                        # Calculate days since event
                        days_since = (datetime.now() - event_date).days
                        
                        # Check if this is a sustained spike (lasted more than 1 day)
                        # We need to find if there are adjacent high values
                        anomaly_date_index = series.index.get_loc(event_date)
                        
                        # Check the next day if possible
                        sustained = False
                        if anomaly_date_index < len(series) - 1:
                            next_day_value = series.iloc[anomaly_date_index + 1]
                            sustained = next_day_value > series.mean() + series.std()
                        
                        # Add enhanced information
                        anomaly["keyword"] = keyword
                        anomaly["days_since"] = days_since
                        anomaly["sustained_spike"] = sustained
                        anomaly["significance"] = "high" if anomaly["z_score"] > threshold * 1.5 else "medium"
                        
                        # Add to the all events list
                        all_events.append(anomaly)
                    
                    viral_events[keyword] = anomalies
        
        if not viral_events:
            print(f"No viral events detected for the given threshold ({threshold})")
            return {
                "success": True,
                "keywords": keywords,
                "timeframe": timeframe,
                "threshold": threshold,
                "message": "No viral events detected for the given threshold",
                "analysis_timestamp": datetime.now().isoformat()
            }
        
        # Sort all events by date (most recent first)
        all_events_sorted = sorted(all_events, key=lambda x: x["date"], reverse=True)
        
        # Identify major viral periods
        major_viral_periods = []
        
        # Group events by date to find days with multiple keywords spiking
        events_by_date = {}
        for event in all_events:
            if event["date"] not in events_by_date:
                events_by_date[event["date"]] = []
            events_by_date[event["date"]].append(event)
        
        # Find dates with multiple keyword spikes
        for date, events in events_by_date.items():
            if len(events) > 1:
                major_viral_periods.append({
                    "date": date,
                    "keywords": [e["keyword"] for e in events],
                    "average_z_score": float(sum(e["z_score"] for e in events) / len(events)),
                    "potential_cause": "Multiple keyword spike suggests platform-wide event"
                })
        
        # Generate insights about the viral events
        insights = []
        
        # Most recent viral event
        if all_events_sorted:
            most_recent = all_events_sorted[0]
            insights.append(f"Most recent viral event: {most_recent['keyword']} on {most_recent['date']} (z-score: {most_recent['z_score']:.2f})")
        
        # Keyword with most viral events
        keyword_event_counts = {k: len(v) for k, v in viral_events.items()}
        if keyword_event_counts:
            most_viral_keyword = max(keyword_event_counts.items(), key=lambda x: x[1])
            insights.append(f"'{most_viral_keyword[0]}' has the most viral events ({most_viral_keyword[1]}) in the timeframe")
        
        # Major platform-wide events
        if major_viral_periods:
            insights.append(f"Detected {len(major_viral_periods)} platform-wide viral events where multiple keywords spiked simultaneously")
        
        # Generate possible causes for viral events
        event_correlations = []
        
        # For each major viral event, try to correlate with potential causes
        for event in all_events_sorted[:5]:  # Focus on top 5 events
            # Get related queries for the keyword around that time
            # For now, we'll use a placeholder method since we can't directly query Google Trends for a specific date
            event_date = datetime.strptime(event["date"], "%Y-%m-%d")
            
            # Create a potential cause based on the keyword and pattern
            if "update" in event["keyword"].lower():
                potential_cause = "Likely a major game update or platform update"
            elif "adopt me" in event["keyword"].lower():
                potential_cause = "Possible Adopt Me game event or pet release"
            elif "robux" in event["keyword"].lower():
                potential_cause = "Possible Robux promotion or platform economy change"
            else:
                potential_cause = "Unknown - would need external news sources to verify"
            
            event_correlations.append({
                "event_date": event["date"],
                "keyword": event["keyword"],
                "z_score": float(event["z_score"]),
                "potential_cause": potential_cause,
                "confidence": "medium"  # This would ideally be based on additional data sources
            })
        
        return {
            "success": True,
            "keywords": keywords,
            "timeframe": timeframe,
            "threshold": threshold,
            "viral_events_by_keyword": viral_events,
            "all_viral_events": all_events_sorted,
            "major_viral_periods": major_viral_periods,
            "event_correlations": event_correlations,
            "insights": insights,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        import traceback
        print(f"ERROR in detect_viral_events: {e}")
        print(traceback.format_exc())
        return {
            "success": False,
            "error": str(e),
            "keywords": keywords or [],
            "timeframe": timeframe,
            "threshold": threshold
        }

async def get_regional_trend_analysis(keywords: Optional[List[str]] = None, 
                                    regions: Optional[List[str]] = None,
                                    timeframe: str = "3m") -> Dict[str, Any]:
    """Analyze regional differences in Roblox search trends.
    
    Args:
        keywords: Keywords to analyze across regions
        regions: List of region codes (US, GB, CA, etc.)
        timeframe: Time period for analysis
        
    Returns:
        Dictionary with regional trend analysis
    """
    try:
        analyzer = get_trends_analyzer()
        
        # Default parameters
        if keywords is None:
            keywords = ["roblox", "robux"]
        if regions is None:
            regions = ["US", "GB", "CA", "AU", "BR"]
        
        # Limit inputs for API constraints
        keywords = keywords[:2]  # Max 2 keywords for regional analysis
        regions = regions[:5]    # Max 5 regions
        
        regional_data = {}
        
        # Get trends for each region
        for region in regions:
            region_trends = analyzer.get_trends_data(keywords, timeframe, region)
            
            if not region_trends.empty:
                regional_data[region] = {}
                
                for keyword in keywords:
                    if keyword in region_trends.columns:
                        series = region_trends[keyword]
                        regional_data[region][keyword] = {
                            "average": round(series.mean(), 2),
                            "peak": series.max(),
                            "recent_trend": "up" if series.tail(7).mean() > series.head(7).mean() else "down",
                            "volatility": round(series.std(), 2),
                            "current_value": series.iloc[-1] if len(series) > 0 else 0
                        }
        
        # Regional interest analysis for main keyword
        main_keyword = keywords[0]
        regional_interest = analyzer.get_regional_interest(main_keyword, timeframe)
        
        # Convert regional interest data to ensure JSON serialization
        regional_interest_dict = {}
        if not regional_interest.empty:
            # Handle potential NaN values in the data
            for region, value in regional_interest[main_keyword].items():
                if pd.isna(value):
                    regional_interest_dict[region] = None
                else:
                    regional_interest_dict[region] = float(value)
        
        # Find top regions for each keyword
        regional_rankings = {}
        for keyword in keywords:
            rankings = []
            for region in regions:
                if region in regional_data and keyword in regional_data[region]:
                    rankings.append((
                        region,
                        regional_data[region][keyword]["average"],
                        regional_data[region][keyword]["recent_trend"]
                    ))
            
            rankings.sort(key=lambda x: x[1], reverse=True)
            regional_rankings[keyword] = rankings
        
        # Calculate regional correlations
        regional_correlations = {}
        if len(regions) > 1 and keywords[0] in regional_data.get(regions[0], {}):
            # This would compare trends between regions
            # Implementation would depend on having aligned time series data
            pass
        
        # Generate regional insights
        insights = []
        
        # Find regions with highest growth
        for keyword in keywords:
            if keyword in regional_rankings:
                top_region = regional_rankings[keyword][0]
                insights.append(f"{top_region[0]} shows highest search volume for '{keyword}' with average {top_region[1]}")
        
        # Identify emerging markets
        emerging_markets = []
        for region in regions:
            if region in regional_data:
                for keyword in keywords:
                    if keyword in regional_data[region]:
                        if regional_data[region][keyword]["recent_trend"] == "up":
                            emerging_markets.append(f"{region} showing growth in '{keyword}' searches")
        
        return {
            "success": True,
            "keywords": keywords,
            "regions": regions,
            "timeframe": timeframe,
            "regional_data": regional_data,
            "regional_rankings": regional_rankings,
            "regional_interest": regional_interest_dict,
            "insights": insights,
            "emerging_markets": emerging_markets,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "keywords": keywords or [],
            "regions": regions or [],
            "timeframe": timeframe
        }

async def analyze_regional_growth_markets(keywords: Optional[List[str]] = None, 
                                     timeframe: str = "12m") -> Dict[str, Any]:
    """Identify emerging and growth markets for Roblox based on regional search trends.
    
    Args:
        keywords: List of keywords to analyze across regions
        timeframe: Time period for analysis (must be at least 3m for meaningful growth analysis)
        
    Returns:
        Dictionary with emerging markets analysis
    """
    try:
        analyzer = get_trends_analyzer()
        
        # Default keywords if none provided
        if keywords is None or len(keywords) == 0:
            keywords = ["roblox", "robux"]
        
        # Limit to 2 keywords for API constraints
        keywords = keywords[:2]
        
        print(f"Analyzing regional growth markets for: {keywords}, timeframe: {timeframe}")
        
        # We need a longer timeframe for growth analysis
        if timeframe == "1d" or timeframe == "7d":
            timeframe = "3m"
            print(f"Timeframe too short for growth analysis, using {timeframe} instead")
        
        # Get global interest by region
        main_keyword = keywords[0]
        global_interest = analyzer.get_regional_interest(main_keyword, timeframe)
        
        if global_interest.empty:
            print(f"ERROR: Failed to get global interest data for {main_keyword}")
            return {
                "success": False,
                "error": f"No global interest data available for {main_keyword}",
                "keywords": keywords,
                "timeframe": timeframe
            }
            
        # Handle potential NaN values to ensure JSON serialization
        global_interest_clean = global_interest.copy()
        global_interest_clean = global_interest_clean.fillna(0)  # Replace NaN with 0 for ranking purposes
        
        # Top 20 regions by search volume
        top_regions = global_interest_clean.head(20).index.tolist()
        
        # Define additional regions of interest (emerging markets)
        emerging_regions = ["IN", "PH", "VN", "TH", "ID", "SA", "AE", "NG", "ZA", "CL", "PE", "CO"]
        
        # Combine top regions and emerging markets, removing duplicates
        regions_to_analyze = list(set(top_regions + emerging_regions))
        
        # Limit to reasonable number to avoid API throttling
        regions_to_analyze = regions_to_analyze[:15]
        
        regional_data = {}
        growth_data = {}
        
        # Get detailed trends for each region
        for region in regions_to_analyze:
            print(f"Analyzing region: {region}")
            
            # Add a delay to avoid API throttling
            time.sleep(2)
            
            region_trends = analyzer.get_trends_data(keywords, timeframe, region)
            
            if not region_trends.empty:
                regional_data[region] = {}
                
                for keyword in keywords:
                    if keyword in region_trends.columns:
                        series = region_trends[keyword]
                        
                        # Split the time series into two halves to measure growth
                        half_point = len(series) // 2
                        first_half = series[:half_point]
                        second_half = series[half_point:]
                        
                        # Calculate average values for each half
                        first_half_avg = first_half.mean()
                        second_half_avg = second_half.mean()
                        
                        # Calculate growth rate
                        growth_rate = ((second_half_avg - first_half_avg) / first_half_avg * 100) if first_half_avg > 0 else 0
                        
                        # Calculate recent growth (last quarter vs previous quarter)
                        quarter_point = len(series) // 4
                        recent_period = series[-quarter_point:]
                        previous_period = series[-quarter_point*2:-quarter_point]
                        
                        recent_growth = ((recent_period.mean() - previous_period.mean()) / previous_period.mean() * 100) if previous_period.mean() > 0 else 0
                        
                        # Add to regional data
                        regional_data[region][keyword] = {
                            "average_interest": float(round(series.mean(), 2)),
                            "current_interest": int(series.iloc[-1]) if len(series) > 0 else 0,
                            "peak_interest": int(series.max()),
                            "growth_rate": float(round(growth_rate, 2)),
                            "recent_growth": float(round(recent_growth, 2)),
                            "volatility": float(round(series.std() / series.mean() if series.mean() > 0 else 0, 3))
                        }
                        
                        # Add to growth data
                        if keyword not in growth_data:
                            growth_data[keyword] = {}
                        
                        growth_data[keyword][region] = {
                            "growth_rate": float(round(growth_rate, 2)),
                            "recent_growth": float(round(recent_growth, 2)),
                            "average_interest": float(round(series.mean(), 2))
                        }
        
        # Identify emerging markets (high growth, lower average interest)
        emerging_markets = []
        
        for keyword in growth_data:
            # Sort regions by growth rate
            sorted_regions = sorted(
                growth_data[keyword].items(),
                key=lambda x: x[1]["growth_rate"],
                reverse=True
            )
            
            # Top growth regions
            for region, data in sorted_regions[:5]:
                if data["growth_rate"] > 20:  # 20% growth is significant
                    emerging_markets.append({
                        "region": region,
                        "keyword": keyword,
                        "growth_rate": data["growth_rate"],
                        "average_interest": data["average_interest"],
                        "recent_growth": data["recent_growth"],
                        "growth_score": data["growth_rate"] * (1 + data["recent_growth"]/100)  # Weight recent growth
                    })
        
        # Sort emerging markets by growth score
        emerging_markets.sort(key=lambda x: x["growth_score"], reverse=True)
        
        # Identify stable mature markets (high interest, stable or positive growth)
        mature_markets = []
        
        for keyword in growth_data:
            # Sort regions by average interest
            sorted_regions = sorted(
                growth_data[keyword].items(),
                key=lambda x: x[1]["average_interest"],
                reverse=True
            )
            
            # Top interest regions
            for region, data in sorted_regions[:5]:
                if data["average_interest"] > 40 and data["growth_rate"] >= -10:  # High interest, not declining too fast
                    mature_markets.append({
                        "region": region,
                        "keyword": keyword,
                        "growth_rate": data["growth_rate"],
                        "average_interest": data["average_interest"],
                        "market_score": data["average_interest"] * (1 + data["growth_rate"]/100)  # Weight by growth
                    })
        
        # Sort mature markets by market score
        mature_markets.sort(key=lambda x: x["market_score"], reverse=True)
        
        # Identify declining markets (negative growth, historically significant interest)
        declining_markets = []
        
        for keyword in growth_data:
            # Sort regions by negative growth
            declining_regions = [
                (region, data) for region, data in growth_data[keyword].items()
                if data["growth_rate"] < -15 and data["average_interest"] > 30
            ]
            
            declining_regions.sort(key=lambda x: x[1]["growth_rate"])
            
            # Add top declining regions
            for region, data in declining_regions[:3]:
                declining_markets.append({
                    "region": region,
                    "keyword": keyword,
                    "growth_rate": data["growth_rate"],
                    "average_interest": data["average_interest"],
                    "recent_growth": data["recent_growth"]
                })
        
        # Generate insights
        insights = []
        
        # Top emerging market insight
        if emerging_markets:
            top_emerging = emerging_markets[0]
            insights.append(f"{top_emerging['region']} is the fastest growing market with {top_emerging['growth_rate']}% growth for '{top_emerging['keyword']}'")
        
        # Top mature market insight
        if mature_markets:
            top_mature = mature_markets[0]
            insights.append(f"{top_mature['region']} is the most stable large market with {top_mature['average_interest']} average interest for '{top_mature['keyword']}'")
        
        # Declining market insight
        if declining_markets:
            top_declining = declining_markets[0]
            insights.append(f"{top_declining['region']} shows concerning decline of {top_declining['growth_rate']}% for '{top_declining['keyword']}' despite historical significance")
        
        # Generate recommendations
        recommendations = []
        
        # Recommendations for emerging markets
        if emerging_markets:
            emerging_regions_str = ", ".join([m["region"] for m in emerging_markets[:3]])
            recommendations.append(f"Focus expansion efforts on emerging markets: {emerging_regions_str}")
            
            # Specific emerging market recommendations
            for market in emerging_markets[:2]:
                recommendations.append(f"Develop localized content for {market['region']} to capitalize on {market['growth_rate']}% growth")
        
        # Recommendations for declining markets
        if declining_markets:
            declining_regions_str = ", ".join([m["region"] for m in declining_markets[:3]])
            recommendations.append(f"Investigate causes of decline in: {declining_regions_str}")
            
            # Specific declining market recommendations
            for market in declining_markets[:2]:
                recommendations.append(f"Create region-specific engagement campaigns for {market['region']} to reverse {market['growth_rate']}% decline")
        
        return {
            "success": True,
            "keywords": keywords,
            "timeframe": timeframe,
            "regions_analyzed": regions_to_analyze,
            "regional_data": regional_data,
            "emerging_markets": emerging_markets,
            "mature_markets": mature_markets,
            "declining_markets": declining_markets,
            "insights": insights,
            "recommendations": recommendations,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        import traceback
        print(f"ERROR in analyze_regional_growth_markets: {e}")
        print(traceback.format_exc())
        return {
            "success": False,
            "error": str(e),
            "keywords": keywords or [],
            "timeframe": timeframe
        }

async def create_trends_report(timeframe: str = "3m", report_type: str = "comprehensive") -> Dict[str, Any]:
    """Generate comprehensive Google Trends report for Roblox economy.
    
    Args:
        timeframe: Time period for the report
        report_type: Type of report (comprehensive, seasonal, regional, items)
        
    Returns:
        Dictionary with comprehensive trends analysis
    """
    try:
        # Gather different types of trend analyses
        report_sections = {}
        
        # 1. Overall Roblox trends
        overall_trends = await get_roblox_search_trends(
            keywords=["roblox", "robux", "roblox trading"],
            timeframe=timeframe
        )
        report_sections["overall_trends"] = overall_trends
        
        # 2. Item search patterns
        item_patterns = await analyze_item_search_patterns(
            item_names=["dominus empyreus", "dominus frigidus", "roblox limiteds"],
            timeframe=timeframe
        )
        report_sections["item_patterns"] = item_patterns
        
        # 3. Seasonal analysis (if timeframe allows)
        if timeframe in ["12m", "5y"] or report_type == "seasonal":
            seasonal = await track_seasonal_trends(
                keywords=["roblox", "robux"],
                years_back=2 if timeframe == "5y" else 1
            )
            report_sections["seasonal_analysis"] = seasonal
        
        # 4. Regional analysis
        if report_type in ["comprehensive", "regional"]:
            regional = await get_regional_trend_analysis(
                keywords=["roblox", "robux"],
                timeframe=timeframe
            )
            report_sections["regional_analysis"] = regional
        
        # Generate executive summary
        executive_summary = generate_trends_executive_summary(report_sections)
        
        # Extract key insights
        key_insights = extract_key_trends_insights(report_sections)
        
        return {
            "success": True,
            "report_type": report_type,
            "timeframe": timeframe,
            "generated_at": datetime.now().isoformat(),
            "executive_summary": executive_summary,
            "key_insights": key_insights,
            "sections": report_sections,
            "data_sources": ["Google Trends"],
            "recommendations": generate_trends_recommendations(report_sections)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "report_type": report_type,
            "timeframe": timeframe
        }

# Helper functions
def generate_item_insights(item_analysis: Dict) -> List[str]:
    """Generate insights from item search analysis"""
    insights = []
    
    if not item_analysis:
        return ["No item data available for analysis"]
    
    # Find most searched item
    top_item = max(item_analysis.items(), key=lambda x: x[1]["average_search_volume"])
    insights.append(f"'{top_item[0]}' has the highest search volume with average {top_item[1]['average_search_volume']}")
    
    # Find most volatile item
    most_volatile = max(item_analysis.items(), key=lambda x: x[1]["volatility"])
    insights.append(f"'{most_volatile[0]}' shows highest search volatility ({most_volatile[1]['volatility']})")
    
    # Items with strong seasonality
    seasonal_items = [item for item, data in item_analysis.items() if data["has_seasonality"]]
    if seasonal_items:
        insights.append(f"Items with seasonal patterns: {', '.join(seasonal_items)}")
    
    return insights

def generate_seasonal_insights(monthly_avg: pd.Series, quarterly_avg: pd.Series) -> List[str]:
    """Generate insights from seasonal analysis"""
    insights = []
    
    # Peak season
    peak_month = monthly_avg.idxmax()
    month_names = {1: "January", 2: "February", 3: "March", 4: "April", 
                  5: "May", 6: "June", 7: "July", 8: "August",
                  9: "September", 10: "October", 11: "November", 12: "December"}
    
    insights.append(f"Peak search month: {month_names.get(peak_month, peak_month)}")
    
    # Seasonal variation
    variation = (monthly_avg.max() - monthly_avg.min()) / monthly_avg.mean()
    if variation > 0.5:
        insights.append("Strong seasonal variation detected")
    
    # Holiday patterns
    if monthly_avg.get(12, 0) > monthly_avg.mean() * 1.2:
        insights.append("December holiday boost observed")
    
    return insights

def generate_overall_seasonal_insights(seasonal_analysis: Dict) -> List[str]:
    """Generate overall insights from seasonal analysis"""
    insights = []
    
    # Count seasonal keywords
    seasonal_keywords = [kw for kw, data in seasonal_analysis.items() if data["has_strong_seasonality"]]
    
    if seasonal_keywords:
        insights.append(f"{len(seasonal_keywords)} keywords show strong seasonality")
        insights.append(f"Seasonal keywords: {', '.join(seasonal_keywords)}")
    
    # Common peak months
    peak_months = [data["strongest_month"] for data in seasonal_analysis.values()]
    if peak_months:
        most_common_peak = max(set(peak_months), key=peak_months.count)
        insights.append(f"Most common peak month: {most_common_peak}")
    
    return insights

def generate_trends_executive_summary(report_sections: Dict) -> str:
    """Generate executive summary from trends report"""
    summary_parts = []
    
    # Overall trends summary
    if "overall_trends" in report_sections and report_sections["overall_trends"].get("success"):
        overall = report_sections["overall_trends"]
        main_metric = list(overall["trend_statistics"].keys())[0] if overall["trend_statistics"] else "roblox"
        trend_direction = overall["trend_statistics"][main_metric]["trend_direction"] if main_metric in overall["trend_statistics"] else "stable"
        summary_parts.append(f"**Overall Search Trends**: Main keyword '{main_metric}' trending {trend_direction}. ")
    
    # Item analysis summary
    if "item_patterns" in report_sections and report_sections["item_patterns"].get("success"):
        items = report_sections["item_patterns"]
        top_item = items["rankings"]["top_searched"][0] if items["rankings"]["top_searched"] else None
        if top_item:
            summary_parts.append(f"**Item Analysis**: '{top_item[0]}' leads item searches with {top_item[1]} average volume. ")
    
    # Regional summary
    if "regional_analysis" in report_sections and report_sections["regional_analysis"].get("success"):
        regional = report_sections["regional_analysis"]
        top_region = regional["regional_rankings"]["roblox"][0] if "roblox" in regional["regional_rankings"] else None
        if top_region:
            summary_parts.append(f"**Regional Analysis**: {top_region[0]} shows highest search activity. ")
    
    return "".join(summary_parts) if summary_parts else "Unable to generate summary due to data collection issues."

def extract_key_trends_insights(report_sections: Dict) -> List[str]:
    """Extract key insights from all report sections"""
    insights = []
    
    # From overall trends
    if "overall_trends" in report_sections and report_sections["overall_trends"].get("success"):
        overall = report_sections["overall_trends"]
        if overall.get("anomalies"):
            insights.append(f"Detected {len(overall['anomalies'])} search anomalies in recent period")
    
    # From item patterns
    if "item_patterns" in report_sections and report_sections["item_patterns"].get("success"):
        items = report_sections["item_patterns"]
        insights.extend(items.get("insights", []))
    
    # From seasonal analysis
    if "seasonal_analysis" in report_sections and report_sections["seasonal_analysis"].get("success"):
        seasonal = report_sections["seasonal_analysis"]
        insights.extend(seasonal.get("overall_insights", []))
    
    # From regional analysis
    if "regional_analysis" in report_sections and report_sections["regional_analysis"].get("success"):
        regional = report_sections["regional_analysis"]
        insights.extend(regional.get("insights", []))
    
    return insights[:10]  # Limit to top 10 insights

def generate_trends_recommendations(report_sections: Dict) -> List[str]:
    """Generate actionable recommendations from trends analysis"""
    recommendations = []
    
    # Based on overall trends
    if "overall_trends" in report_sections and report_sections["overall_trends"].get("success"):
        overall = report_sections["overall_trends"]
        if overall.get("period_over_period_changes"):
            for keyword, change in overall["period_over_period_changes"].items():
                if change > 20:
                    recommendations.append(f"Capitalize on rising search interest in '{keyword}' (+{change}%)")
                elif change < -20:
                    recommendations.append(f"Investigate declining search interest in '{keyword}' ({change}%)")
    
    # Based on items analysis
    if "item_patterns" in report_sections and report_sections["item_patterns"].get("success"):
        items = report_sections["item_patterns"]
        for item, data in items["item_analysis"].items():
            if data["search_momentum"] == "increasing":
                recommendations.append(f"Monitor marketplace for '{item}' - showing increasing search interest")
    
    # Based on regional analysis
    if "regional_analysis" in report_sections and report_sections["regional_analysis"].get("success"):
        regional = report_sections["regional_analysis"]
        if regional.get("emerging_markets"):
            recommendations.append("Focus on emerging markets: " + ", ".join(regional["emerging_markets"][:3]))
    
    # General recommendations
    recommendations.extend([
        "Use search trend peaks to predict marketplace activity",
        "Monitor regional differences for targeted marketing opportunities",
        "Track seasonal patterns for inventory planning"
    ])
    
    return recommendations[:10]  # Limit to top 10 recommendations

# Export tools
tools = [
    get_roblox_search_trends,
    analyze_item_search_patterns,
    track_seasonal_trends,
    compare_game_trends,
    detect_viral_events,
    get_regional_trend_analysis,
    analyze_regional_growth_markets,
    create_trends_report
]
