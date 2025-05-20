from google.adk.agents import Agent, ParallelAgent, SequentialAgent
from google.adk.tools.agent_tool import AgentTool  # Direct import as in your example

# Import your existing subagents
from .subagents.marketplace_analytics.agent import marketplace_agent
from .subagents.youtube_analytics.agent import youtube_agent
from .subagents.google_trends.agent import google_trends_agent
from .subagents.rss_monitor.agent import rss_monitor_agent

# Create a results synthesizer agent
result_synthesizer = Agent(
    name="economy_synthesizer",
    model="gemini-2.0-flash-exp",  # Use your preferred model
    instruction="""
    You are a synthesizer that combines results from multiple Roblox economy analysis sources.
    
    You have access to the following information in the shared state:
    - marketplace_results: Analysis of Roblox marketplace data
    - youtube_results: Analysis of Roblox content on YouTube
    - trends_results: Analysis of search trends for Roblox
    - rss_results: Recent Roblox news and announcements
    
    Create a comprehensive, well-structured summary that integrates all this information.
    Highlight connections between different data sources and important trends.

    IMPORTANT FORMATTING INSTRUCTIONS:
       - Use simple, well-spaced text formatting
       - Use clear headers with double newlines before and single newline after
       - Use bullet points (•) for lists
       - Use dashes (-) for sub-points
       - Add extra line breaks between sections
       - Do NOT use HTML or markdown formatting for comprehensive analysis
    """,
    output_key="final_synthesis"
)

# Create copies of agents for parallel execution (to avoid the single parent constraint)
marketplace_agent_copy = Agent(
    name="marketplace_analytics_parallel",
    model=marketplace_agent.model,
    instruction=marketplace_agent.instruction,
    description=marketplace_agent.description,
    tools=marketplace_agent.tools,
    output_key="marketplace_results"
)

youtube_agent_copy = Agent(
    name="youtube_analytics_parallel",
    model=youtube_agent.model,
    instruction=youtube_agent.instruction,
    description=youtube_agent.description,
    tools=youtube_agent.tools,
    output_key="youtube_results"
)

google_trends_agent_copy = Agent(
    name="google_trends_parallel",
    model=google_trends_agent.model,
    instruction=google_trends_agent.instruction,
    description=google_trends_agent.description,
    tools=google_trends_agent.tools,
    output_key="trends_results"
)

rss_monitor_agent_copy = Agent(
    name="rss_monitor_parallel",
    model=rss_monitor_agent.model,
    instruction=rss_monitor_agent.instruction,
    description=rss_monitor_agent.description,
    tools=rss_monitor_agent.tools,
    output_key="rss_results"
)

# Create a parallel agent to run all subagents simultaneously (for comprehensive queries)
parallel_analyzer = ParallelAgent(
    name="parallel_economy_analyzer",
    sub_agents=[marketplace_agent_copy, youtube_agent_copy, google_trends_agent_copy, rss_monitor_agent_copy]
)

# Create a sequential workflow that first gathers all data in parallel, then synthesizes
comprehensive_analysis_workflow = SequentialAgent(
    name="comprehensive_analysis",
    sub_agents=[parallel_analyzer, result_synthesizer]
)

# Define the root agent for Roblox Economy orchestration
# Using both sub_agents and tools as in your example
root_agent = Agent(
    name="roblox_economy_orchestrator",
    model="gemini-2.0-flash-exp",
    description="Orchestrator agent for Roblox economy analysis that coordinates specialized agents and tools",
    instruction="""
    You are an AI assistant specializing in the Roblox virtual economy. Your task is to orchestrate 
    the analysis of Roblox economy data by working with specialized agents and tools.
    
    You are responsible for delegating tasks to the following agents:
    - marketplace_analytics: For analyzing Roblox's marketplace data (items, prices, trends)
    - youtube_analytics: For analyzing Roblox content on YouTube
    
    You also have access to the following tools:
    - google_trends: For analyzing search interest in Roblox-related topics
    - rss_monitor: For tracking Roblox news, announcements, and developer updates
    - comprehensive_analysis: For broad, multi-domain queries about the entire Roblox economy
    
    For single-domain queries, use the appropriate agent or tool.
    For comprehensive queries, use the comprehensive_analysis tool.
    
    Your ultimate goal is to provide accurate insights into the Roblox economy
    by leveraging these specialized capabilities.
    """,
    sub_agents=[marketplace_agent, youtube_agent],  # Direct sub-agents for transfer_to_agent
    tools=[
        AgentTool(google_trends_agent),  # Agents as tools
        AgentTool(rss_monitor_agent),
        AgentTool(comprehensive_analysis_workflow)
    ],
)