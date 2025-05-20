#!/usr/bin/env python3
"""
Enhanced Marketplace Analytics Agent with Vertex AI Code Executor Visualization Support
"""

import os
from google.adk.code_executors import VertexAiCodeExecutor
from google.adk.agents import Agent
from .tools import (
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
    # Keep existing visualization tools as fallback
    create_marketplace_visualization,
    generate_trend_report_with_charts
)
from .instructions import return_instructions_marketplace


def setup_before_agent_call(callback_context):
    """Setup the marketplace analytics agent with Code Executor visualization capabilities."""
    
    # Setting up database settings in session state
    if "all_db_settings" not in callback_context.state:
        db_settings = {
            "use_database": "Supabase",
            "connection_established": True,
            "visualization_enabled": True,
            "code_executor_enabled": True
        }
        callback_context.state["all_db_settings"] = db_settings
    
    # Setting up schema information
    if callback_context.state["all_db_settings"]["use_database"] == "Supabase":
        callback_context.state["database_settings"] = {
            "primary_table": "marketplace_items",
            "schema": """
            marketplace_items table columns:
            - name: Item name
            - price: Current price in Robux
            - rap: Recent Average Price from trading data
            - trend: Trend strength (higher = more trending)
            - trend_direction: Trend direction (1=up, -1=down, 0=stable)
            - demand: Demand score (higher = more demand)
            - rarity_score: Rarity rating (higher = more rare)
            - creator_name: Item creator
            - rolimons_value: Rolimons valuation in Robux
            - is_limited: Whether item is limited edition
            - category: Item category (Accessories, etc.)
            
            Visualization Capabilities (via Code Interpreter):
            - Dynamic price distribution charts
            - Custom trend analysis graphs
            - Multi-dimensional scatter plots (demand vs price vs rarity)
            - Interactive market segment visualizations
            - Time series analysis with forecasting
            - Correlation heatmaps
            - 3D visualizations for complex relationships
            
            Code Interpreter Usage Examples:
            - "Create a correlation heatmap between price, demand, and rarity"
            - "Generate a 3D scatter plot showing price, demand, and trend relationships"
            - "Build an interactive chart comparing limited vs non-limited items"
            - "Visualize price distribution by category with box plots"
            
            SQL Functions Available:
            - get_highest_value_items(limit): Get items with highest value
            - get_items_by_price_range(min, max, sort_by, direction, limit): Filter by price
            - get_trending_analysis(limit): Advanced trending analysis
            - execute_sql(query): Execute custom SQL queries
            """
        }
    
    # Set up Code Interpreter context for marketplace data
    callback_context.state["code_interpreter_context"] = {
        "data_source": "marketplace_items table",
        "available_libraries": [
            "pandas", "numpy", "matplotlib", "seaborn", 
            "plotly", "scipy", "sklearn", "datetime"
        ],
        "visualization_types": [
            "bar charts", "line plots", "scatter plots", "heatmaps",
            "box plots", "violin plots", "3D plots", "correlation matrices",
            "distribution plots", "time series", "regression plots"
        ],
        "data_processing": [
            "filtering", "grouping", "aggregation", "correlation analysis",
            "statistical analysis", "outlier detection", "clustering"
        ]
    }

# Enhanced instructions for Code Executor integration
enhanced_instructions = return_instructions_marketplace() + """

## Code Interpreter Integration

You now have access to the Code Interpreter capabilities through Vertex AI Code Executor. Use this for:

### When to Use Code Interpreter:
1. **Complex Visualizations**: Multi-dimensional plots, custom charts, interactive visualizations
2. **Statistical Analysis**: Correlation analysis, regression, clustering
3. **Data Exploration**: Advanced filtering, custom aggregations, outlier detection
4. **Custom Charts**: User-specific visualization requests that go beyond standard charts

### How to Use Code in Your Response:
1. First, get the data using marketplace analytics tools (get_trending_items, execute_custom_sql, etc.)
2. Then, write Python code blocks in your response using standard markdown:

```python
# Import necessary libraries
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Example code using marketplace data
# This is a placeholder - replace with actual data from marketplace functions
data = {
    'name': ['Item1', 'Item2', 'Item3'],
    'price': [1000, 500, 2000],
    'demand': [4, 3, 5],
    'rarity': [3, 2, 4]
}
df = pd.DataFrame(data)

# Create visualization
plt.figure(figsize=(10, 6))
sns.heatmap(df[['price', 'demand', 'rarity']].corr(), annot=True, cmap='coolwarm')
plt.title('Correlation Heatmap')
plt.show()
```

### Code Interpreter Best Practices:
- Always provide clear, specific code with imports and comments
- Include sample data or how to fetch the data in your code
- Specify chart types, colors, and styling preferences
- Generate both static and exportable visualizations when needed

### Fallback Strategy:
- Use built-in visualization tools for simple charts (bar, line, pie)
- Use code blocks for advanced, custom, or multi-dimensional visualizations
- Always verify the code makes sense with the data
"""

# Main agent instance with Code Executor integration
try:
    # Get Vertex AI extension ID from environment variable or use a default
    code_interpreter_extension = os.getenv("CODE_INTERPRETER_EXTENSION_NAME", None)
    
    # Create agent with code executor if extension is available
    if code_interpreter_extension:
        marketplace_agent = Agent(
            name="marketplace_analytics_with_code_interpreter",
            model="gemini-2.0-flash-exp",
            description="Advanced Roblox marketplace analytics with Code Interpreter for dynamic visualizations, SQL queries, and comprehensive market intelligence",
            instruction=enhanced_instructions,
            tools=[
                # Core marketplace tools
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
                # Visualization tools (fallback)
                create_marketplace_visualization,
                generate_trend_report_with_charts
            ],
            code_executor=VertexAiCodeExecutor(
                optimize_data_file=True,
                stateful=True,
                extension_name=code_interpreter_extension
            )
        )
    else:
        # Fallback to agent without code executor if extension not configured
        marketplace_agent = Agent(
            name="marketplace_analytics_system_enhanced",
            model="gemini-2.0-flash-exp",
            description="Advanced Roblox marketplace analytics with visualization, SQL queries, and comprehensive market intelligence",
            instruction=return_instructions_marketplace(),
            tools=[
                # Core marketplace tools
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
                # Visualization tools (fallback)
                create_marketplace_visualization,
                generate_trend_report_with_charts
            ]
        )
        
except ImportError:
    # Fallback if VertexAiCodeExecutor is not available
    marketplace_agent = Agent(
        name="marketplace_analytics_system_enhanced",
        model="gemini-2.0-flash-exp",
        description="Advanced Roblox marketplace analytics with visualization, SQL queries, and comprehensive market intelligence",
        instruction=return_instructions_marketplace(),
        tools=[
            # Core marketplace tools
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
            # Visualization tools (fallback)
            create_marketplace_visualization,
            generate_trend_report_with_charts
        ],
        output_key="marketplace_results"
    )
