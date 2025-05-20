# Marketplace Analytics ADK Agent

## Overview
This subagent provides analytics and insights for Roblox marketplace data using the ADK framework. It follows the same pattern as the data science multi-agent system shown in your example.

## Structure
```
subagents/marketplace_analytics/
├── __init__.py           # Package initialization
├── agent.py             # Main agent definition and setup
├── instructions.py      # Agent instructions and prompts  
├── tools.py            # Database query tools and functions
```

## Features

### Available Queries
- **Trending Analysis**: Items currently trending up/down
- **Value Analysis**: Most valuable items in the marketplace
- **Demand Insights**: High demand items with reasonable prices
- **Price Movements**: Recent price changes and volatility
- **Rarity Analysis**: Rarest items and their market performance
- **Market Summary**: Overall marketplace statistics

### Database Integration
- Connects to Supabase marketplace_items table
- Queries Rolimons data including prices, trends, demand, rarity
- Supports complex filtering and analysis

## Usage

### 1. Test the Agent
```bash
python test_marketplace_agent.py
```

### 2. Run Interactive Session
```bash
python run_marketplace_agent.py
```

### 3. Run Example Queries
```bash
python run_marketplace_agent.py examples
```

### 4. Integrate with Main Agent System
```python
from subagents.marketplace_analytics.agent import marketplace_agent

# Use in your main ADK agent system
main_agent = Agent(
    sub_agents=[marketplace_agent],
    tools=[call_marketplace_agent],
    # ... other config
)
```

## Example Queries

- "What items are trending up?"
- "Show me the most valuable items"
- "Find undervalued items with high demand"
- "What are the recent price changes?"
- "Analyze the rarest items in the market"
- "Give me a market summary"

## Database Schema

The agent works with the marketplace_items table containing:
- `name`: Item name
- `price`: Current price in Robux
- `recent_average_price`: RAP from Rolimons
- `trend`: Trend strength (0-4)
- `trend_direction`: 1=up, -1=down, 0=stable
- `demand`: Demand score (0-5)
- `rarity_score`: Rarity rating (1-5)
- `price_change_percent`: Recent price change
- `creator_name`: Item creator

## Integration Notes

This follows the exact same pattern as your data science agent:
- Tools handle database queries
- Agent orchestrates analysis
- Instructions guide behavior
- Setup function configures database connection

Ready to extend with additional analytics capabilities!
