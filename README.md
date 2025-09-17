# Roblox Economy Google ADK Agent

An Agentic application that provides insights into the Roblox virtual economy through AI-powered analysis. 
While it is a WIP, you can access the link here: https://roblox-agent-extension.fly.dev/
- The chat may not work right away and give an error. It just means the server was asleep. Try it again in a few minutes and it should be working!

  Built with Google ADK—following best practices from ADK Documentation (https://google.github.io/adk-docs/) and MCP Tool Integration Guide(https://google.github.io/adk-docs/tools/mcp-tools/).

## Features

- Updated analysis of Roblox marketplace data (credit: Rolimons)
- YouTube trends for Roblox games
- Google search trends analysis
- RSS feeds monitoring for Roblox news and updates

## Media
Example of analyzing a specific game via youtube metrics:
<img width="1031" height="460" alt="image" src="https://github.com/user-attachments/assets/b58acc4f-b2f4-4260-aa66-fd7fc16a4441" />
<img width="1032" height="453" alt="image" src="https://github.com/user-attachments/assets/fd31a9b2-91a1-4955-9844-4e01c1825a28" />


## Deployment

This application is designed to be deployed on Fly.io. See the Dockerfile and fly.toml for configuration details.

To run locally:

1. Install dependencies: `pip install -r requirements.txt`
2. Start the ADK API server: `adk api_server --port 3000`
3. Run the web app: `python improved_app.py`

## License

MIT
EOF
