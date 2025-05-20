#!/usr/bin/env python3
"""
Marketplace Analytics Visualization Tools
Enhanced with matplotlib and data science capabilities
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import io
import base64
import json
from typing import Dict, List, Any, Optional

# Set up matplotlib for better visualization
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

async def create_marketplace_visualization(
    data_type: str,
    chart_type: str = "bar",
    parameters: str = "{}"
):
    """Create visualizations for marketplace data.
    
    Args:
        data_type: Type of data to visualize (trending, valuable, demand_price, etc.)
        chart_type: Type of chart (bar, scatter, line, pie, heatmap)
        parameters: JSON string with additional parameters
        
    Returns:
        Dictionary with visualization data and base64 encoded image
    """
    try:
        # Parse parameters
        params = json.loads(parameters) if parameters else {}
        limit = params.get('limit', 20)
        
        # Get database instance
        from .tools import get_db_instance
        db = get_db_instance()
        
        if db is None:
            return {"error": "Database not available"}
        
        # Get data based on type
        if data_type == "trending":
            result = db.query_marketplace_data("trending_items")
            df = pd.DataFrame(result.get('data', []))
            title = "Trending Items Analysis"
            
        elif data_type == "valuable":
            result = db.query_marketplace_data("top_by_value")
            df = pd.DataFrame(result.get('data', []))
            title = "Most Valuable Items"
            
        elif data_type == "demand_price":
            # Get data for demand vs price analysis
            sql_query = """
            SELECT name, price, demand, rolimons_value, rarity_score
            FROM marketplace_items 
            WHERE demand IS NOT NULL AND price > 0 AND rolimons_value > 0
            ORDER BY demand DESC
            LIMIT ?
            """
            result = db.execute_sql_query(sql_query.replace('?', str(limit)))
            df = pd.DataFrame(result.get('data', []))
            title = "Demand vs Price Analysis"
            
        elif data_type == "market_segments":
            # Get category distribution
            sql_query = """
            SELECT category, COUNT(*) as item_count, AVG(price) as avg_price
            FROM marketplace_items 
            WHERE category IS NOT NULL
            GROUP BY category
            ORDER BY item_count DESC
            LIMIT 10
            """
            result = db.execute_sql_query(sql_query)
            df = pd.DataFrame(result.get('data', []))
            title = "Market Segments Distribution"
            
        else:
            return {"error": f"Unknown data type: {data_type}"}
        
        if df.empty:
            return {"error": "No data available for visualization"}
        
        # Create visualization based on chart type
        fig, ax = plt.subplots(figsize=(12, 8))
        
        if chart_type == "bar":
            if data_type == "trending" or data_type == "valuable":
                # Top items bar chart
                top_items = df.head(limit)
                y_values = top_items['rolimons_value'].fillna(top_items['price'])
                
                bars = ax.barh(range(len(top_items)), y_values, color='skyblue', alpha=0.8)
                ax.set_yticks(range(len(top_items)))
                ax.set_yticklabels(top_items['name'], fontsize=10)
                ax.set_xlabel('Value (Robux)', fontsize=12)
                ax.set_title(f'{title} - Top {len(top_items)} Items', fontsize=14, fontweight='bold')
                
                # Add value labels on bars
                for i, (idx, bar) in enumerate(zip(top_items.index, bars)):
                    width = bar.get_width()
                    ax.text(width + max(y_values) * 0.01, bar.get_y() + bar.get_height()/2, 
                           f'{int(width):,}', ha='left', va='center', fontsize=9)
                           
            elif data_type == "market_segments":
                # Category bar chart
                bars = ax.bar(df['category'], df['item_count'], color='lightgreen', alpha=0.8)
                ax.set_ylabel('Number of Items')
                ax.set_xlabel('Category')
                ax.set_title('Items by Category', fontsize=14, fontweight='bold')
                plt.xticks(rotation=45, ha='right')
                
                # Add count labels on bars
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                           f'{int(height)}', ha='center', va='bottom')
        
        elif chart_type == "scatter":
            if data_type == "demand_price":
                # Demand vs Price scatter plot
                scatter = ax.scatter(df['demand'], df['rolimons_value'], 
                                   s=df['rarity_score']*20, alpha=0.6, 
                                   c=df['price'], cmap='viridis')
                ax.set_xlabel('Demand Score')
                ax.set_ylabel('Rolimons Value (Robux)')
                ax.set_title('Demand vs Value Analysis\n(Size = Rarity, Color = Current Price)', 
                           fontsize=14, fontweight='bold')
                
                # Add colorbar
                cbar = plt.colorbar(scatter)
                cbar.set_label('Current Price (Robux)')
                
                # Add trend line
                from scipy import stats
                if len(df) > 2:
                    slope, intercept, r_value, p_value, std_err = stats.linregress(df['demand'], df['rolimons_value'])
                    line = slope * df['demand'] + intercept
                    ax.plot(df['demand'], line, 'r', alpha=0.8, linestyle='--', 
                           label=f'Trend (R²={r_value**2:.3f})')
                    ax.legend()
        
        elif chart_type == "pie":
            if data_type == "market_segments":
                # Category pie chart
                colors = plt.cm.Set3(np.linspace(0, 1, len(df)))
                wedges, texts, autotexts = ax.pie(df['item_count'], labels=df['category'], 
                                                 autopct='%1.1f%%', colors=colors, startangle=90)
                ax.set_title('Market Share by Category', fontsize=14, fontweight='bold')
                
                # Enhance text readability
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')
        
        elif chart_type == "heatmap":
            if data_type == "demand_price":
                # Create correlation heatmap
                numeric_cols = ['price', 'demand', 'rolimons_value', 'rarity_score']
                correlation_matrix = df[numeric_cols].corr()
                
                sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0,
                           square=True, linewidths=0.5, ax=ax)
                ax.set_title('Market Metrics Correlation', fontsize=14, fontweight='bold')
        
        # Improve layout
        plt.tight_layout()
        
        # Save to base64 string
        buffer = io.BytesIO()
        plt.savefig(buffer, format='PNG', dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        # Prepare return data
        return {
            "success": True,
            "image_base64": image_base64,
            "data_summary": {
                "total_items": len(df),
                "chart_type": chart_type,
                "data_type": data_type,
                "parameters": params
            },
            "insights": generate_chart_insights(df, data_type, chart_type)
        }
        
    except Exception as e:
        plt.close()  # Clean up in case of error
        return {
            "success": False,
            "error": str(e),
            "data_type": data_type,
            "chart_type": chart_type
        }

async def generate_trend_report_with_charts(time_period: str = "week"):
    """Generate a comprehensive trend report with multiple visualizations.
    
    Args:
        time_period: Time period for analysis (week, month, quarter)
        
    Returns:
        Dictionary with multiple charts and comprehensive analysis
    """
    try:
        from .tools import get_db_instance
        db = get_db_instance()
        
        if db is None:
            return {"error": "Database not available"}
        
        # Get comprehensive market data
        report_data = {}
        
        # 1. Market Overview
        market_summary = db.query_marketplace_data("market_summary")
        report_data['market_summary'] = market_summary
        
        # 2. Generate multiple visualizations
        visualizations = []
        
        # Trending items chart
        trending_chart = await create_marketplace_visualization("trending", "bar", '{"limit": 15}')
        if trending_chart.get("success"):
            visualizations.append({
                "title": "Top Trending Items",
                "image": trending_chart["image_base64"],
                "insights": trending_chart["insights"]
            })
        
        # Valuable items chart
        valuable_chart = await create_marketplace_visualization("valuable", "bar", '{"limit": 15}')
        if valuable_chart.get("success"):
            visualizations.append({
                "title": "Most Valuable Items",
                "image": valuable_chart["image_base64"],
                "insights": valuable_chart["insights"]
            })
        
        # Demand vs Price analysis
        demand_chart = await create_marketplace_visualization("demand_price", "scatter", '{"limit": 100}')
        if demand_chart.get("success"):
            visualizations.append({
                "title": "Demand vs Value Analysis",
                "image": demand_chart["image_base64"],
                "insights": demand_chart["insights"]
            })
        
        # Market segments
        segments_chart = await create_marketplace_visualization("market_segments", "pie")
        if segments_chart.get("success"):
            visualizations.append({
                "title": "Market Segments",
                "image": segments_chart["image_base64"],
                "insights": segments_chart["insights"]
            })
        
        # Generate executive summary
        executive_summary = generate_executive_summary(market_summary, visualizations)
        
        return {
            "success": True,
            "time_period": time_period,
            "generated_at": datetime.now().isoformat(),
            "executive_summary": executive_summary,
            "market_summary": market_summary,
            "visualizations": visualizations,
            "total_charts": len(visualizations)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "time_period": time_period
        }

def generate_chart_insights(df: pd.DataFrame, data_type: str, chart_type: str) -> List[str]:
    """Generate insights from chart data."""
    insights = []
    
    try:
        if data_type == "trending":
            if not df.empty:
                avg_trend = df['trend'].mean() if 'trend' in df.columns else 0
                insights.append(f"Average trend strength: {avg_trend:.2f}")
                
                if 'demand' in df.columns:
                    high_demand_items = len(df[df['demand'] > 3])
                    insights.append(f"{high_demand_items} trending items have high demand (>3)")
        
        elif data_type == "valuable":
            if not df.empty and 'rolimons_value' in df.columns:
                total_value = df['rolimons_value'].sum()
                avg_value = df['rolimons_value'].mean()
                insights.append(f"Total value of top items: {total_value:,.0f} Robux")
                insights.append(f"Average value: {avg_value:,.0f} Robux")
        
        elif data_type == "demand_price" and chart_type == "scatter":
            if len(df) > 1:
                correlation = df['demand'].corr(df['rolimons_value'])
                insights.append(f"Demand-Value correlation: {correlation:.3f}")
                
                if correlation > 0.3:
                    insights.append("Positive correlation: Higher demand generally means higher value")
                elif correlation < -0.3:
                    insights.append("Negative correlation: Interesting market dynamics detected")
                else:
                    insights.append("Weak correlation: Demand and value are largely independent")
        
        elif data_type == "market_segments":
            if not df.empty:
                top_category = df.iloc[0]['category']
                top_count = df.iloc[0]['item_count']
                insights.append(f"Largest category: {top_category} ({top_count} items)")
                
                if 'avg_price' in df.columns:
                    highest_avg_price_cat = df.loc[df['avg_price'].idxmax(), 'category']
                    highest_avg_price = df['avg_price'].max()
                    insights.append(f"Highest average price category: {highest_avg_price_cat} ({highest_avg_price:,.0f} Robux)")
    
    except Exception as e:
        insights.append(f"Error generating insights: {str(e)}")
    
    return insights

def generate_executive_summary(market_summary: Dict, visualizations: List[Dict]) -> str:
    """Generate an executive summary from market data and visualizations."""
    try:
        summary_parts = []
        
        # Market overview
        if market_summary and 'total_items' in market_summary:
            total_items = market_summary['total_items']
            avg_value = market_summary.get('average_value', 0)
            total_market_value = market_summary.get('total_market_value', 0)
            
            summary_parts.append(
                f"**Market Overview**: {total_items:,} items tracked with total market value of "
                f"{total_market_value:,.0f} Robux (average: {avg_value:,.0f} Robux per item)."
            )
        
        # Key insights from visualizations
        for viz in visualizations:
            if viz.get('insights'):
                title = viz['title']
                key_insight = viz['insights'][0] if viz['insights'] else "No specific insights"
                summary_parts.append(f"**{title}**: {key_insight}")
        
        return " ".join(summary_parts)
        
    except Exception as e:
        return f"Error generating summary: {str(e)}"

# Add these to the tools list in tools.py
tools_to_add = [
    create_marketplace_visualization,
    generate_trend_report_with_charts
]
