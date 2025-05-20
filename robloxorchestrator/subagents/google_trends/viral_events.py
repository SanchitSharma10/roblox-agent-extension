from typing import Dict, List, Any, Optional
from datetime import datetime
import sys

# Import the get_trends_analyzer function
from .tools import get_trends_analyzer

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
