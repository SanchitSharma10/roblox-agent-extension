# RSS Monitor Connector

This subagent provides RSS feed monitoring capabilities for the Roblox Virtual Economy Chrome Extension. It tracks news, updates, and economic changes related to Roblox from various sources.

## Setup and Installation

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Make sure the Google ADK is properly installed and configured

## Features

The RSS Monitor provides the following capabilities:

- **Monitor Roblox Feeds**: Track updates from official Roblox sources and gaming news sites
- **Analyze Economy News**: Filter and analyze news specifically related to Roblox's economy
- **Track Update Announcements**: Monitor official Roblox announcements for economy-related changes
- **Detect Policy Changes**: Identify policy updates that might affect the Roblox economy
- **Monitor Competitor News**: Track news about Roblox competitors
- **Create Summary Reports**: Generate comprehensive reports combining all monitored sources

## Usage

You can use the RSS Monitor in two ways:

### 1. Via the ADK Agent

The ADK Agent provides a conversational interface to the RSS Monitor. You can ask questions like:

- "Show me the latest Roblox updates"
- "Analyze Roblox economy news from the past week"
- "Are there any policy changes affecting developers?"
- "Generate a news summary for the past month"

### 2. Direct API Usage

You can also call the RSS Monitor functions directly from your code:

```python
from subagents.rss_monitor.tools import (
    monitor_roblox_feeds,
    analyze_economy_news,
    track_update_announcements,
    detect_policy_changes,
    get_competitor_news,
    create_news_summary_report
)

# Example: Monitor Roblox feeds for the past week
async def example():
    result = await monitor_roblox_feeds(time_period="week", category="all")
    print(f"Found {result['total_entries']} relevant entries")
```

## Testing

Run the test script to verify the RSS Monitor is working correctly:

```bash
python test_rss_connector.py
```

This will test the basic functionality and save the results to JSON files for inspection.

## Troubleshooting

If you encounter issues:

1. Check the log files (`rss_monitor.log` and `rss_agent.log`)
2. Verify your internet connection (the RSS Monitor needs to fetch external feeds)
3. Make sure all dependencies are installed correctly
4. Verify the ADK is properly configured

## Common Issues

- **Empty Results**: Some feeds may have changed their URL or format. Check the logs for errors.
- **Performance Issues**: The RSS Monitor makes multiple HTTP requests. Consider increasing timeout values if needed.
- **RSS Format Changes**: If a news site changes its RSS format, you may need to update the parsing logic.
