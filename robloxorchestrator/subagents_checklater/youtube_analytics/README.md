# YouTube Analytics Agent

This agent analyzes YouTube content trends related to the Roblox economy.

## Features

- Track Roblox economy content trends
- Analyze creator mentions of specific items
- Identify viral videos that might impact the market
- Monitor game popularity through YouTube metrics
- Sentiment analysis of economy-related content

## Setup

1. Ensure you have a YouTube API v3 key
2. Add it to your .env file as `YOUTUBE_API_KEY`
3. Install required dependencies:
   ```bash
   pip install google-api-python-client
   ```

## Usage

The agent can be used standalone or as part of the multi-agent economy intelligence system.

```python
from youtube_analytics.agent import youtube_agent

# Get trending content analysis
trends = await youtube_agent.get_roblox_content_trends(time_period="week")

# Analyze creator mentions
mentions = await youtube_agent.analyze_creator_mentions(["Dominus", "Limiteds"])

# Generate comprehensive report
report = await youtube_agent.create_youtube_analytics_report()
```

## Integration

This agent is designed to work with the marketplace analytics agent to provide comprehensive economy intelligence by correlating YouTube trends with marketplace data.
