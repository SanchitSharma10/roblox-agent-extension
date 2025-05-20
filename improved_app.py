import os
import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import json
import logging
from datetime import datetime
import uuid
import asyncio
from typing import Dict, List, Optional
import traceback
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("robloxorchestrator")

# Import orchestrator (update path as needed)
import httpx
import asyncio

# Configuration for ADK API server
ADK_API_URL = "http://localhost:3000"  # Base URL for the ADK API server
APP_NAME = "robloxorchestrator"
ORCHESTRATOR_AVAILABLE = True  # Assume available by default

# Add global session state
SESSION_STATE = {
    "user_id": f"user-{uuid.uuid4()}",
    "session_id": f"session-{int(time.time())}",
    "session_created": False
}

# Function to check if ADK API server is running
async def check_adk_server():
    """Check if the ADK API server is running by making a simple request."""
    global ORCHESTRATOR_AVAILABLE
    
    try:
        # Attempt to connect to the ADK API server
        async with httpx.AsyncClient() as client:
            # Make a simple request to check if the server is responsive
            # We just check if the server responds to any request
            response = await client.get(
                f"{ADK_API_URL}",
                timeout=2.0
            )
            
            # If we get any response, the server is up
            logger.info(f"ADK API server is available (Status: {response.status_code})")
            ORCHESTRATOR_AVAILABLE = True
            return True
    
    except Exception as e:
        logger.warning(f"ADK API server not available: {e}")
        ORCHESTRATOR_AVAILABLE = False
        return False

async def process_user_query(query):
    """Process a query by sending it to the ADK API server."""
    global SESSION_STATE
    
    if not ORCHESTRATOR_AVAILABLE:
        raise Exception("ADK API Server is not available")
        
    logger.info(f"Sending query to ADK API server: {query}")
    
    try:
        # Create the session if it doesn't exist yet
        if not SESSION_STATE["session_created"]:
            create_session_url = f"{ADK_API_URL}/apps/{APP_NAME}/users/{SESSION_STATE['user_id']}/sessions/{SESSION_STATE['session_id']}"
            
            logger.info(f"Creating new session at: {create_session_url}")
            
            async with httpx.AsyncClient() as client:
                session_response = await client.post(
                    create_session_url,
                    headers={"Content-Type": "application/json"},
                    json={},
                    timeout=30.0
                )
                
                logger.info(f"Session creation response: {session_response.status_code}")
                
                if session_response.status_code == 200:
                    SESSION_STATE["session_created"] = True
                    logger.info(f"Session created successfully: {SESSION_STATE['session_id']}")
                else:
                    logger.error(f"Failed to create session: {session_response.text}")
                    raise Exception(f"Failed to create session: {session_response.text}")
        
        # Send the message to the existing session
        run_url = f"{ADK_API_URL}/run"
        
        # Simplified payload that just contains the query text
        payload = {
            "app_name": APP_NAME,
            "user_id": SESSION_STATE["user_id"],
            "session_id": SESSION_STATE["session_id"],
            "new_message": {
                "role": "user",
                "parts": [{"text": query}]
            }
        }
        
        logger.info(f"Sending message to: {run_url}")
        logger.info(f"With payload: {payload}")
        
        async with httpx.AsyncClient() as client:
            message_response = await client.post(
                run_url,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=60.0
            )
            
            logger.info(f"Message response: {message_response.status_code}")
            
            if message_response.status_code == 200:
                try:
                    events = message_response.json()
                    logger.info(f"Received response with {len(events)} events")
                    
                    # Extract assistant's message from the events
                    assistant_message = "No response from assistant"
                    agent_data = {}
                    for event in events:
                        # Get the most recent model text response
                        if event.get("content", {}).get("role") == "model" and "text" in event.get("content", {}).get("parts", [{}])[0]:
                            assistant_message = event["content"]["parts"][0]["text"]
                        
                        # Look for any structured data in the response (optional)
                        if "actions" in event and "state_delta" in event["actions"]:
                            state = event["actions"]["state_delta"]
                            # Extract any relevant state data
                            if "marketplace_results" in state:
                                agent_data["marketplace"] = state["marketplace_results"]
                            if "youtube_results" in state:
                                agent_data["youtube"] = state["youtube_results"]
                            if "trends_results" in state:
                                agent_data["trends"] = state["trends_results"]
                    
                    # Return a simplified response structure
                    return {
                        "success": True,
                        "query": query,
                        "summary": assistant_message,
                        "data": agent_data,
                        "execution_details": {
                            "tasks_executed": 1,
                            "successful_tasks": 1,
                            "execution_time": 0.0
                        }
                    }
                except Exception as e:
                    logger.error(f"Error parsing response: {e}")
                    logger.error(f"Raw response: {message_response.text}")
                    raise Exception(f"Failed to parse response: {str(e)}")
            else:
                error_msg = f"Message sending failed: {message_response.status_code}"
                try:
                    error_content = message_response.text
                    logger.error(f"Error content: {error_content}")
                    error_msg += f" - {error_content}"
                except:
                    pass
                raise Exception(error_msg)
    except Exception as e:
        logger.error(f"Error in process_user_query: {e}")
        raise Exception(f"Failed to communicate with the ADK API server: {str(e)}")
    

async def get_system_status():
    # Check if ADK server is available
    global ORCHESTRATOR_AVAILABLE
    is_available = await check_adk_server()
    
    if is_available:
        # Server is reachable
        return {
            "agents": {
                "marketplace_analytics": "available",
                "youtube_analytics": "available",
                "google_trends": "available",
                "rss_monitor": "available"
            },
            "adk_api_status": "available",
            "active_plans": 0
        }
    else:
        # The server is not available
        return {
            "agents": {
                "marketplace_analytics": "unknown",
                "youtube_analytics": "unknown",
                "google_trends": "unknown",
                "rss_monitor": "unknown"
            },
            "adk_api_status": "unavailable",
            "active_plans": 0
        }

# Create FastAPI app
app = FastAPI(title="Roblox Economy Analysis")

# Add CORS to allow local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active WebSocket connections
active_connections: List[WebSocket] = []

# Periodic health check task
health_check_task: Optional[asyncio.Task] = None

@app.on_event("startup")
async def startup_event():
    """Check if ADK API server is available on startup and start periodic health checks."""
    global health_check_task, SESSION_STATE
    
    logger.info("===== Starting Roblox Economy Analysis Web App =====")
    logger.info(f"ADK API URL configured as: {ADK_API_URL}")
    logger.info("Checking if ADK API server is available...")
    
    is_available = await check_adk_server()
    
    if is_available:
        logger.info("✅ ADK API Server is available at startup")
        logger.info("The application will use the ADK API server for AI processing")
        
        # Initialize a session
        create_session_url = f"{ADK_API_URL}/apps/{APP_NAME}/users/{SESSION_STATE['user_id']}/sessions/{SESSION_STATE['session_id']}"
        
        logger.info(f"Creating initial session at: {create_session_url}")
        
        try:
            async with httpx.AsyncClient() as client:
                session_response = await client.post(
                    create_session_url,
                    headers={"Content-Type": "application/json"},
                    json={},
                    timeout=30.0
                )
                
                logger.info(f"Session creation response: {session_response.status_code}")
                
                if session_response.status_code == 200:
                    SESSION_STATE["session_created"] = True
                    logger.info(f"Initial session created successfully: {SESSION_STATE['session_id']}")
                else:
                    logger.error(f"Failed to create initial session: {session_response.text}")
        except Exception as e:
            logger.error(f"Error creating initial session: {e}")
    else:
        logger.warning("⚠️ ADK API Server not available at startup")
        logger.warning("Make sure the ADK API server is running with:")
        logger.warning("   adk api_server --port 3000")
        logger.warning("Requests to the API will fail until the server is available")
    
    # Start periodic health checks
    logger.info("Starting periodic health checks for ADK API server")
    health_check_task = asyncio.create_task(periodic_health_check())
    
    logger.info("===== Web App Started =====")
    logger.info(f"Access the web interface at: http://localhost:8000")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    global health_check_task
    
    if health_check_task:
        health_check_task.cancel()
        try:
            await health_check_task
        except asyncio.CancelledError:
            pass
    
    logger.info("Application shutting down")

async def periodic_health_check():
    """Periodically check if ADK API server is available and notify clients of status changes."""
    global ORCHESTRATOR_AVAILABLE
    previous_status = ORCHESTRATOR_AVAILABLE
    
    while True:
        try:
            current_status = await check_adk_server()
            
            # Notify clients if status changed
            if current_status != previous_status:
                logger.info(f"ADK API Server status changed: {previous_status} -> {current_status}")
                
                # Broadcast status change to all connected clients
                if active_connections:
                    status_message = {
                        "type": "status_change",
                        "status": "connected" if current_status else "disconnected",
                        "orchestrator_available": current_status
                    }
                    
                    for connection in active_connections:
                        try:
                            await connection.send_json(status_message)
                        except Exception as e:
                            logger.error(f"Error sending status update to client: {e}")
                
                previous_status = current_status
            
            # Check every 30 seconds
            await asyncio.sleep(30)
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            await asyncio.sleep(60)  # Wait longer if there was an error

# Script directory
script_dir = os.path.dirname(os.path.realpath(__file__))
static_dir = os.path.join(script_dir, 'static')
os.makedirs(static_dir, exist_ok=True)

# Instead of trying to copy the file, let's just directly serve it
@app.get("/static/roblox-economy.js")
async def get_js_file():
    js_file = os.path.join(script_dir, 'roblox-economy.js')
    if os.path.exists(js_file):
        return FileResponse(js_file, media_type="application/javascript")
    else:
        logger.error(f"JS file not found: {js_file}")
        return {"error": "File not found"}

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, background_tasks: BackgroundTasks):
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Check if ADK server is running
        adk_server_available = await check_adk_server()
        
        logger.info(f"New WebSocket connection accepted, session_id: {session_id}")
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "session_id": session_id,
            "orchestrator_available": adk_server_available
        })
        
        while True:
            # Wait for messages
            try:
                # Use a timeout to prevent hanging connections
                data = await asyncio.wait_for(websocket.receive_json(), timeout=60)
                logger.info(f"Received WebSocket message: {data}")
                
                if data.get("type") == "query":
                    query = data.get("query", "")
                    query_id = data.get("query_id", str(uuid.uuid4()))
                    
                    logger.info(f"Processing query request: '{query}' with ID: {query_id}")
                    
                    # Send acknowledgment
                    await websocket.send_json({
                        "type": "processing",
                        "query_id": query_id,
                        "message": "Processing your query..."
                    })
                    
                    # Process query directly (no background tasks)
                    try:
                        logger.info(f"Starting to process query: {query}")
                        result = await process_user_query(query)
                        logger.info(f"Query processed successfully: {query_id}")
                        
                        # Send the result
                        await websocket.send_json({
                            "type": "result",
                            "query_id": query_id,
                            "result": result
                        })
                        logger.info(f"Result sent for query: {query_id}")
                    except Exception as e:
                        logger.error(f"Error processing query: {str(e)}")
                        logger.error(traceback.format_exc())
                        await websocket.send_json({
                            "type": "error",
                            "query_id": query_id,
                            "error": str(e)
                        })
                
                elif data.get("type") == "get_status":
                    # Get system status
                    try:
                        status = await get_system_status()
                        await websocket.send_json({
                            "type": "status",
                            "status": status
                        })
                    except Exception as e:
                        logger.error(f"Error getting status: {str(e)}")
                        await websocket.send_json({
                            "type": "error",
                            "error": f"Failed to get system status: {str(e)}"
                        })
                
                elif data.get("type") == "toggle_theme":
                    # Just acknowledge theme toggle (handled client-side)
                    await websocket.send_json({
                        "type": "theme_toggled",
                        "theme": data.get("theme", "dark")
                    })
                else:
                    logger.warning(f"Unknown message type: {data.get('type')}")
            except asyncio.TimeoutError:
                # This is normal, just continue the loop
                continue
            except Exception as e:
                logger.error(f"Error receiving WebSocket message: {str(e)}")
                logger.error(traceback.format_exc())
                break
    
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        logger.error(traceback.format_exc())
        # Try to send error message to client
        try:
            await websocket.send_json({
                "type": "connection_error",
                "error": f"WebSocket error: {str(e)}"
            })
        except:
            pass
    finally:
        # Remove connection when done
        if websocket in active_connections:
            active_connections.remove(websocket)
        logger.info(f"WebSocket connection closed, session_id: {session_id}")

# Function to process query in background
async def process_query_and_send_result(websocket: WebSocket, query: str, query_id: str):
    """Process a query and send the result back to the client."""
    try:
        # Process the query through ADK API Server
        result = await process_user_query(query)
        
        # Check if client is still connected
        if websocket in active_connections:
            # Send the result
            await websocket.send_json({
                "type": "result",
                "query_id": query_id,
                "result": result
            })
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        # Try to send error message if client is still connected
        if websocket in active_connections:
            try:
                await websocket.send_json({
                    "type": "error",
                    "query_id": query_id,
                    "error": str(e)
                })
            except Exception as send_error:
                logger.error(f"Error sending error message: {str(send_error)}")

# HTTP endpoint for queries (alternative to WebSocket)
@app.post("/api/query")
async def query_endpoint(request: Request):
    data = await request.json()
    if "query" not in data:
        return {"success": False, "error": "Query parameter is required"}
    
    query = data["query"]
    
    try:
        # Process the query using the same function as the WebSocket
        result = await process_user_query(query)
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error processing query via HTTP: {str(e)}")
        return {"success": False, "error": str(e)}

# Get system status
@app.get("/api/status")
async def get_status_endpoint():
    try:
        return await get_system_status()
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return {"error": str(e)}

# HTML for the single-file app with dark indigo theme
@app.get("/", response_class=HTMLResponse)
async def get_index():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Roblox Economy AI Analysis</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
        <script src="/static/roblox-economy.js"></script>
        <style>
            :root {
                /* Branding colors */
                --roblox-red: #00A2FF; /* Changed from #FF4500 to blue */
                --roblox-red-hover: #0081CC; /* Changed from #E63E00 to blue hover */
                --roblox-blue: #00A2FF;
                --roblox-blue-hover: #0081CC;
                --robux-gold: #FFBC00;
                
                /* Light theme */
                --light-bg: #F2F2F2;
                --light-panel: #FFFFFF;
                --light-text: #1E293B;
                --light-text-muted: #64748B;
                --light-border: #E2E8F0;
                
                /* Dark theme - indigo/blue focused */
                --dark-bg: #1E293B;
                --dark-panel: #283548;
                --dark-text: #E2E8F0;
                --dark-text-muted: #94A3B8;
                --dark-border: #374151;
                
                /* Functional colors */
                --success-color: #10B981;
                --error-color: #EF4444;
                --warning-color: #F59E0B;
                
                /* Active theme colors - default to dark */
                --bg-color: var(--dark-bg);
                --panel-color: var(--dark-panel);
                --text-color: var(--dark-text);
                --text-muted: var(--dark-text-muted);
                --border-color: var(--dark-border);
                
                /* Shadows */
                --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.1);
                --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
                --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
            }
            
            .light-theme {
                --bg-color: var(--light-bg);
                --panel-color: var(--light-panel);
                --text-color: var(--light-text);
                --text-muted: var(--light-text-muted);
                --border-color: var(--light-border);
            }
            
            * {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }
            
            body {
                font-family: 'Gotham SSm', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background-color: var(--bg-color);
                color: var(--text-color);
                transition: background-color 0.3s, color 0.3s;
            }
            
            .app-container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }
            
            header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
            }
            
            .logo {
                display: flex;
                align-items: center;
                gap: 12px;
            }
            
            .logo-icon {
                color: var(--roblox-red);
                font-size: 30px;
                font-weight: bold;
            }
            
            header h1 {
                color: var(--text-color);
                font-weight: 700;
                font-size: 24px;
            }
            
            .header-controls {
                display: flex;
                align-items: center;
                gap: 12px;
            }
            
            .commands-btn {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 8px 14px;
                background-color: var(--panel-color);
                color: var(--text-color);
                border: 1px solid var(--border-color);
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s;
            }
            
            .commands-btn:hover {
                background-color: rgba(0, 162, 255, 0.1);
            }
            
            .commands-btn i {
                color: var(--roblox-red);
            }
            
            .system-status {
                padding: 6px 12px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                display: flex;
                align-items: center;
                gap: 6px;
            }
            
            .system-status.connected {
                background-color: rgba(16, 185, 129, 0.1);
                color: var(--success-color);
            }
            
            .system-status.disconnected {
                background-color: rgba(239, 68, 68, 0.1);
                color: var(--error-color);
            }
            
            .content-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
            }
            
            @media (max-width: 768px) {
                .content-grid {
                    grid-template-columns: 1fr;
                }
            }
            
            .panel {
                background-color: var(--panel-color);
                border-radius: 12px;
                box-shadow: var(--shadow-md);
                overflow: hidden;
                transition: background-color 0.3s;
            }
            
            .panel-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 16px 20px;
                border-bottom: 1px solid var(--border-color);
            }
            
            .panel-header h2 {
                color: var(--text-color);
                font-size: 18px;
                font-weight: 600;
                margin: 0;
            }
            
            .panel-actions {
                display: flex;
                gap: 8px;
            }
            
            .action-btn {
                width: 32px;
                height: 32px;
                display: flex;
                align-items: center;
                justify-content: center;
                border: none;
                background: transparent;
                color: var(--text-muted);
                border-radius: 4px;
                cursor: pointer;
                transition: all 0.2s;
            }
            
            .action-btn:hover {
                background-color: rgba(0, 162, 255, 0.1);
                color: var(--roblox-red);
            }
            
            .chat-panel {
                display: flex;
                flex-direction: column;
                height: 600px;
            }
            
            .chat-container {
                flex: 1;
                overflow-y: auto;
                padding: 20px;
            }
            
            .welcome-message {
                background-color: rgba(0, 162, 255, 0.05);
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
                border: 1px solid rgba(0, 162, 255, 0.1);
            }
            
            .welcome-message h2 {
                color: var(--roblox-red);
                font-size: 18px;
                margin-bottom: 12px;
            }
            
            .welcome-message p {
                margin-bottom: 8px;
            }
            
            .welcome-message ul {
                margin-left: 20px;
                margin-top: 10px;
            }
            
            .welcome-message li {
                margin-bottom: 6px;
            }
            
            .message {
                margin-bottom: 16px;
                max-width: 80%;
                animation: fadeIn 0.3s ease;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .user-message {
                background-color: var(--roblox-red);
                color: white;
                padding: 12px 16px;
                border-radius: 12px 12px 0 12px;
                margin-left: auto;
            }
            
            .system-message {
                background-color: rgba(255, 255, 255, 0.05);
                padding: 12px 16px;
                border-radius: 12px 12px 12px 0;
                border: 1px solid var(--border-color);
            }
            
            /* YouTube Analysis Styles for AI response */
            .youtube-analysis {
                background-color: rgba(0, 162, 255, 0.05);
                border-radius: 8px;
                padding: 15px;
                margin-top: 10px;
                margin-bottom: 15px;
                border: 1px solid rgba(0, 162, 255, 0.1);
            }
            
            .youtube-analysis h2 {
                color: var(--roblox-red);
                font-size: 18px;
                margin-bottom: 15px;
                border-bottom: 1px solid var(--border-color);
                padding-bottom: 8px;
            }
            
            .game-cards {
                display: flex;
                flex-direction: column;
                gap: 10px;
            }
            
            .game-card {
                display: flex;
                background-color: var(--panel-color);
                padding: 12px;
                border-radius: 8px;
                box-shadow: var(--shadow-sm);
            }
            
            .rank {
                display: flex;
                align-items: center;
                justify-content: center;
                min-width: 30px;
                height: 30px;
                background-color: var(--roblox-red);
                color: white;
                border-radius: 50%;
                font-weight: bold;
                margin-right: 15px;
            }
            
            .game-info {
                flex-grow: 1;
            }
            
            .game-title {
                font-weight: 600;
                margin-bottom: 4px;
            }
            
            .game-metrics {
                display: flex;
                gap: 10px;
                font-size: 12px;
                color: var(--text-muted);
            }
            
            .popularity {
                background-color: rgba(16, 185, 129, 0.1);
                color: var(--success-color);
                padding: 2px 8px;
                border-radius: 12px;
                font-weight: 500;
            }
            
            .top-video {
                margin-top: 8px;
                font-size: 13px;
            }
            
            .video-title {
                font-weight: 500;
                margin-bottom: 2px;
            }
            
            .video-channel {
                color: var(--text-muted);
                font-size: 12px;
            }
            
            .thinking {
                padding: 8px 16px;
            }
            
            .thinking-indicator {
                display: flex;
                gap: 4px;
                align-items: center;
                justify-content: center;
                height: 24px;
            }
            
            .thinking-indicator .dot {
                width: 8px;
                height: 8px;
                background-color: var(--roblox-red);
                border-radius: 50%;
                animation: pulse 1.5s infinite ease-in-out;
            }
            
            .thinking-indicator .dot:nth-child(2) {
                animation-delay: 0.2s;
            }
            
            .thinking-indicator .dot:nth-child(3) {
                animation-delay: 0.4s;
            }
            
            @keyframes pulse {
                0%, 100% {
                    transform: scale(0.5);
                    opacity: 0.5;
                }
                50% {
                    transform: scale(1);
                    opacity: 1;
                }
            }
            
            .input-container {
                display: flex;
                padding: 16px;
                border-top: 1px solid var(--border-color);
            }
            
            .input-wrapper {
                position: relative;
                flex: 1;
            }
            
            #queryInput {
                width: 100%;
                padding: 12px 42px 12px 16px;
                background-color: var(--bg-color);
                color: var(--text-color);
                border: 1px solid var(--border-color);
                border-radius: 8px;
                font-size: 16px;
                outline: none;
                transition: all 0.3s;
            }
            
            #queryInput:focus {
                border-color: var(--roblox-red);
                box-shadow: 0 0 0 2px rgba(0, 162, 255, 0.1);
            }
            
            #queryInput::placeholder {
                color: var(--text-muted);
            }
            
            .input-actions {
                position: absolute;
                right: 8px;
                top: 50%;
                transform: translateY(-50%);
                display: flex;
                gap: 4px;
            }
            
            .input-action-btn {
                background: transparent;
                border: none;
                width: 28px;
                height: 28px;
                border-radius: 4px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: var(--text-muted);
                cursor: pointer;
                transition: all 0.2s;
            }
            
            .input-action-btn:hover {
                background-color: rgba(0, 162, 255, 0.1);
                color: var(--roblox-red);
            }
            
            #submitBtn {
                background-color: var(--roblox-red);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 20px;
                margin-left: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: background-color 0.2s;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            #submitBtn:hover {
                background-color: var(--roblox-red-hover);
            }
            
            .data-panel {
                min-height: 600px;
                display: flex;
                flex-direction: column;
            }
            
            .marketplace-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 16px 20px;
                border-bottom: 1px solid var(--border-color);
            }
            
            .marketplace-header h2 {
                color: var(--text-color);
                font-size: 18px;
                font-weight: 600;
                margin: 0;
            }
            
            .header-actions {
                display: flex;
                gap: 12px;
                align-items: center;
            }
            
            .date-range {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 6px 12px;
                background-color: var(--bg-color);
                border: 1px solid var(--border-color);
                border-radius: 6px;
                font-size: 14px;
                color: var(--text-color);
                cursor: pointer;
                transition: all 0.2s;
            }
            
            .date-range:hover {
                border-color: var(--roblox-red);
            }
            
            .marketplace-content {
                padding: 20px;
                flex: 1;
                overflow-y: auto;
            }
            
            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 16px;
                margin-bottom: 20px;
            }
            
            .metric-card {
                background-color: rgba(0, 162, 255, 0.05);
                padding: 16px;
                border-radius: 8px;
                text-align: center;
                position: relative;
            }
            
            .metric-title {
                font-size: 14px;
                color: var(--text-muted);
                margin-bottom: 10px;
                font-weight: 500;
            }
            
            .metric-value {
                font-size: 24px;
                font-weight: 700;
                color: var(--roblox-red);
                margin-bottom: 6px;
            }
            
            .metric-trend {
                font-size: 12px;
                display: inline-flex;
                align-items: center;
                gap: 4px;
                padding: 2px 8px;
                border-radius: 12px;
                font-weight: 500;
            }
            
            .metric-trend.positive {
                background-color: rgba(16, 185, 129, 0.1);
                color: var(--success-color);
            }
            
            .metric-trend.negative {
                background-color: rgba(239, 68, 68, 0.1);
                color: var(--error-color);
            }
            
            .metric-trend.neutral {
                background-color: rgba(148, 163, 184, 0.1);
                color: var(--text-muted);
            }
            
            /* Smart Table Integration */
            .items-table {
                background-color: var(--panel-color);
                border-radius: 12px;
                box-shadow: var(--shadow-md);
                overflow: hidden;
                margin-bottom: 20px;
            }
            
            .items-table h3 {
                padding: 15px;
                margin: 0;
                background-color: rgba(0, 162, 255, 0.05);
                border-bottom: 1px solid var(--border-color);
                font-size: 16px;
                color: var(--text-color);
            }
            
            .table-container {
                max-height: 300px;
                overflow-y: auto;
            }
            
            table {
                width: 100%;
                border-collapse: collapse;
            }
            
            th, td {
                padding: 12px 16px;
                text-align: left;
                border-bottom: 1px solid var(--border-color);
            }
            
            th {
                background-color: rgba(0, 162, 255, 0.05);
                font-weight: 600;
                font-size: 12px;
                color: var(--text-muted);
                text-transform: uppercase;
            }
            
            td {
                font-size: 14px;
            }
            
            .price-change {
                padding: 3px 8px;
                border-radius: 15px;
                font-size: 12px;
                font-weight: 500;
            }
            
            .price-change.positive {
                background-color: rgba(16, 185, 129, 0.1);
                color: var(--success-color);
            }
            
            .price-change.negative {
                background-color: rgba(239, 68, 68, 0.1);
                color: var(--error-color);
            }
            
            .price-change.neutral {
                background-color: rgba(255, 255, 255, 0.05);
                color: var(--text-muted);
            }
            
            .loading {
                text-align: center;
                padding: 40px;
                color: var(--text-muted);
            }
            
            .error {
                text-align: center;
                padding: 40px;
                color: var(--error-color);
                background-color: rgba(239, 68, 68, 0.1);
                border-radius: 8px;
            }
            
            /* Trend and Rarity Styles */
            .trend {
                padding: 3px 8px;
                border-radius: 15px;
                font-size: 12px;
                font-weight: 500;
                font-family: monospace;
            }
            
            .trend.positive {
                background-color: rgba(16, 185, 129, 0.1);
                color: var(--success-color);
            }
            
            .trend.negative {
                background-color: rgba(239, 68, 68, 0.1);
                color: var(--error-color);
            }
            
            .trend.neutral {
                background-color: rgba(255, 255, 255, 0.05);
                color: var(--text-muted);
            }
            
            .rarity {
                font-size: 16px;
            }
            
            .rarity.legendary {
                color: #ff6b35;
                text-shadow: 0 0 3px rgba(255, 107, 53, 0.5);
            }
            
            .rarity.epic {
                color: #8e44ad;
                text-shadow: 0 0 3px rgba(142, 68, 173, 0.5);
            }
            
            .rarity.rare {
                color: #00A2FF;
                text-shadow: 0 0 3px rgba(0, 162, 255, 0.5);
            }
            
            .rarity.common {
                color: var(--text-muted);
            }
            
            /* Demand Styling */
            .demand {
                font-size: 14px;
                font-weight: 500;
            }
            
            .demand.high {
                color: var(--success-color);
            }
            
            .demand.medium {
                color: var(--warning-color);
            }
            
            .demand.low {
                color: var(--error-color);
            }
            
            .filter-section {
                background-color: var(--panel-color);
                padding: 15px;
                border-radius: 8px;
                box-shadow: var(--shadow-md);
                margin-bottom: 20px;
            }
            
            .filter-section h3 {
                margin: 0 0 10px 0;
                font-size: 16px;
                color: var(--text-color);
            }
            
            .filter-controls {
                display: flex;
                gap: 10px;
                align-items: center;
            }
            
            .filter-controls select {
                padding: 8px 12px;
                background-color: var(--bg-color);
                color: var(--text-color);
                border: 1px solid var(--border-color);
                border-radius: 6px;
                font-size: 14px;
                outline: none;
            }
            
            .filter-controls select:focus {
                border-color: var(--roblox-red);
            }
            
            .theme-toggle {
                width: 36px;
                height: 36px;
                border-radius: 50%;
                background-color: var(--panel-color);
                color: var(--text-muted);
                border: 1px solid var(--border-color);
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: all 0.2s;
            }
            
            .theme-toggle:hover {
                color: var(--roblox-red);
                border-color: var(--roblox-red);
            }
            
            /* Tabbed interface - alternative to side-by-side layout */
            .tabs-container {
                margin-bottom: 20px;
                display: none; /* Hidden by default, enable in JS to switch to tabbed layout */
            }
            
            .tabs {
                display: flex;
                border-bottom: 1px solid var(--border-color);
                margin-bottom: 20px;
            }
            
            .tab {
                padding: 12px 24px;
                cursor: pointer;
                border-bottom: 2px solid transparent;
                transition: all 0.2s;
                font-weight: 500;
            }
            
            .tab.active {
                border-bottom: 2px solid var(--roblox-red);
                color: var(--roblox-red);
            }
            
            .tab:hover:not(.active) {
                background-color: rgba(0, 162, 255, 0.05);
            }
            
            .tab-content {
                display: none;
            }
            
            .tab-content.active {
                display: block;
            }
            
            /* Layout toggle button */
            .layout-toggle {
                background-color: var(--panel-color);
                color: var(--text-muted);
                border: 1px solid var(--border-color);
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 8px;
                transition: all 0.2s;
            }
            
            .layout-toggle:hover {
                background-color: rgba(0, 162, 255, 0.05);
                color: var(--roblox-red);
            }
        </style>
    </head>
    <body>
        <div class="app-container">
            <header>
                <div class="logo">
                    <div class="logo-icon">R$</div>
                    <h1>Roblox Analytics Dashboard</h1>
                </div>
                <div class="header-controls">
                    <button class="commands-btn">
                        <i class="fas fa-bolt"></i>
                        <span>Commands</span>
                    </button>
                    <button class="layout-toggle" id="layoutToggle">
                        <i class="fas fa-columns"></i>
                        <span>Toggle Layout</span>
                    </button>
                    <button class="theme-toggle" id="themeToggle">
                        <i class="fas fa-sun"></i>
                    </button>
                    <div id="systemStatus" class="system-status disconnected">
                        <i class="fas fa-circle"></i>
                        <span>Disconnected</span>
                    </div>
                </div>
            </header>
            
            <!-- Tabbed interface (initially hidden) -->
            <div class="tabs-container" id="tabsContainer">
                <div class="tabs">
                    <div class="tab active" data-tab="assistant">AI Assistant</div>
                    <div class="tab" data-tab="marketplace">Marketplace Overview</div>
                </div>
            </div>
            
            <!-- Side-by-side layout (default) -->
            <div class="content-grid" id="contentGrid">
                <div class="panel chat-panel" id="assistantPanel">
                    <div class="panel-header">
                        <h2>AI Assistant</h2>
                        <div class="panel-actions">
                            <button class="action-btn" title="Clear chat" id="clearChatBtn">
                                <i class="fas fa-trash-alt"></i>
                            </button>
                            <button class="action-btn" title="Settings">
                                <i class="fas fa-cog"></i>
                            </button>
                        </div>
                    </div>
                    <div class="chat-container" id="chatContainer">
                        <div class="welcome-message">
                            <h2>Welcome to Roblox Analytics</h2>
                            <p>Ask any question about the Roblox economy, marketplace trends, content creators, or game analytics.</p>
                            <p>Examples:</p>
                            <ul>
                                <li>What are the most valuable limited items right now?</li>
                                <li>Which games are trending on YouTube this week?</li>
                                <li>Show me marketplace trends for hats and accessories</li>
                                <li>What's the investment potential of animation packs?</li>
                            </ul>
                        </div>
                    </div>
                    
                    <div class="input-container">
                        <div class="input-wrapper">
                            <input type="text" id="queryInput" placeholder="Ask about the Roblox economy...">
                            <div class="input-actions">
                                <button class="input-action-btn" title="Voice input" id="voiceInputBtn">
                                    <i class="fas fa-microphone"></i>
                                </button>
                                <button class="input-action-btn" title="History" id="historyBtn">
                                    <i class="fas fa-history"></i>
                                </button>
                            </div>
                        </div>
                        <button id="submitBtn">
                            <i class="fas fa-paper-plane"></i>
                            <span>Ask AI</span>
                        </button>
                    </div>
                </div>
                
                <div class="panel data-panel" id="marketplacePanel">
                    <div class="panel-header">
                        <h2>Marketplace Overview</h2>
                        <div class="panel-actions">
                            <div class="date-range">
                                <span>Last 7 Days</span>
                                <i class="fas fa-chevron-down"></i>
                            </div>
                            <button class="action-btn" title="Refresh" id="refreshBtn">
                                <i class="fas fa-sync-alt"></i>
                            </button>
                            <button class="action-btn" title="Download">
                                <i class="fas fa-download"></i>
                            </button>
                        </div>
                    </div>
                    
                    <div class="marketplace-content">
                        <div class="metrics-grid">
                            <div class="metric-card">
                                <div class="metric-title">Total Items</div>
                                <div class="metric-value" id="totalItems">--</div>
                                <div class="metric-trend positive">
                                    <i class="fas fa-arrow-up"></i>
                                    <span>5.2%</span>
                                </div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-title">Total Value (R$)</div>
                                <div class="metric-value" id="totalValue">--</div>
                                <div class="metric-trend positive">
                                    <i class="fas fa-arrow-up"></i>
                                    <span>12.7%</span>
                                </div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-title">Active Categories</div>
                                <div class="metric-value" id="activeCategories">--</div>
                                <div class="metric-trend neutral">
                                    <i class="fas fa-minus"></i>
                                    <span>0%</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="filter-section">
                            <h3>Filter Items</h3>
                            <div class="filter-controls">
                                <select id="categoryFilter">
                                    <option value="">All Categories</option>
                                </select>
                                <select id="sortFilter">
                                    <option value="price">Highest Price</option>
                                    <option value="name">Name (A-Z)</option>
                                    <option value="demand">Highest Demand</option>
                                    <option value="rarity_score">Rarest Items</option>
                                    <option value="trend">Trending</option>
                                </select>
                            </div>
                        </div>
                        
                        <div class="items-table">
                            <h3>Marketplace Items</h3>
                            <div class="table-container">
                                <table>
                                    <thead>
                                        <tr>
                                            <th>Name</th>
                                            <th>Category</th>
                                            <th>Price (R$)</th>
                                            <th>RAP (R$)</th>
                                            <th>Price Change</th>
                                            <th>Trend</th>
                                            <th>Demand</th>
                                            <th>Rarity</th>
                                        </tr>
                                    </thead>
                                    <tbody id="itemsTableBody">
                                        <tr>
                                            <td colspan="8" class="loading">Loading items...</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            // Roblox Economy AI Client - Handles WebSocket communication and UI updates
            class RobloxEconomyAIClient {
                constructor() {
                    this.socket = null;
                    this.isConnected = false;
                    this.messageQueue = [];
                    this.sessionId = null;
                    this.queryCounter = 0;
                    this.isDarkTheme = true; // Default to dark theme
                    this.isGridLayout = true; // Default to grid/side-by-side layout
                    this.reconnectAttempts = 0;
                    this.maxReconnectAttempts = 5;
                    this.reconnectDelay = 3000; // Start with 3 seconds
                    
                    // Initialize the client
                    this.init();
                }
                
                async init() {
                    console.log('🚀 Initializing AI client...');
                    
                    // Set initial theme from localStorage or default
                    this.loadThemePreference();
                    this.loadLayoutPreference();
                    
                    // Connect to WebSocket server
                    this.connectWebSocket();
                    
                    // Set up event listeners
                    this.setupEventListeners();
                }
                
                loadThemePreference() {
                    const savedTheme = localStorage.getItem('theme');
                    this.isDarkTheme = savedTheme !== 'light'; // Default to dark if not set
                    this.applyTheme();
                }
                
                loadLayoutPreference() {
                    const savedLayout = localStorage.getItem('layout');
                    this.isGridLayout = savedLayout !== 'tabs'; // Default to grid if not set
                    this.applyLayout();
                }
                
                toggleTheme() {
                    this.isDarkTheme = !this.isDarkTheme;
                    localStorage.setItem('theme', this.isDarkTheme ? 'dark' : 'light');
                    this.applyTheme();
                    
                    // Notify server of theme change (optional)
                    if (this.isConnected) {
                        this.sendMessage({
                            type: 'toggle_theme',
                            theme: this.isDarkTheme ? 'dark' : 'light'
                        });
                    }
                }
                
                toggleLayout() {
                    this.isGridLayout = !this.isGridLayout;
                    localStorage.setItem('layout', this.isGridLayout ? 'grid' : 'tabs');
                    this.applyLayout();
                }
                
                applyTheme() {
                    const themeToggle = document.getElementById('themeToggle');
                    
                    if (this.isDarkTheme) {
                        document.body.classList.remove('light-theme');
                        if (themeToggle) themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
                    } else {
                        document.body.classList.add('light-theme');
                        if (themeToggle) themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
                    }
                }
                
                applyLayout() {
                    const contentGrid = document.getElementById('contentGrid');
                    const tabsContainer = document.getElementById('tabsContainer');
                    const assistantPanel = document.getElementById('assistantPanel');
                    const marketplacePanel = document.getElementById('marketplacePanel');
                    const layoutToggle = document.getElementById('layoutToggle');
                    
                    if (!contentGrid || !tabsContainer) {
                        console.error('Layout elements not found');
                        return;
                    }
                    
                    if (this.isGridLayout) {
                        // Side-by-side layout
                        contentGrid.style.display = 'grid';
                        tabsContainer.style.display = 'none';
                        
                        // Reset panel displays
                        if (assistantPanel) assistantPanel.style.display = 'flex';
                        if (marketplacePanel) marketplacePanel.style.display = 'flex';
                        
                        if (layoutToggle) {
                            layoutToggle.innerHTML = '<i class="fas fa-columns"></i><span>Side by Side</span>';
                        }
                    } else {
                        // Tabbed layout
                        contentGrid.style.display = 'block';
                        tabsContainer.style.display = 'block';
                        
                        // Set initial tab
                        this.switchTab('assistant');
                        
                        if (layoutToggle) {
                            layoutToggle.innerHTML = '<i class="fas fa-folder"></i><span>Tabs</span>';
                        }
                    }
                    
                    // If window is smaller than 768px, force tabbed layout
                    if (window.innerWidth < 768) {
                        contentGrid.style.display = 'block';
                        tabsContainer.style.display = 'block';
                        this.switchTab('assistant');
                    }
                }
                
                switchTab(tabName) {
                    const tabs = document.querySelectorAll('.tab');
                    const assistantPanel = document.getElementById('assistantPanel');
                    const marketplacePanel = document.getElementById('marketplacePanel');
                    
                    if (!assistantPanel || !marketplacePanel) {
                        console.error('Panel elements not found');
                        return;
                    }
                    
                    // Update tab status
                    tabs.forEach(tab => {
                        if (tab.dataset.tab === tabName) {
                            tab.classList.add('active');
                        } else {
                            tab.classList.remove('active');
                        }
                    });
                    
                    // Show/hide panels
                    if (tabName === 'assistant') {
                        assistantPanel.style.display = 'flex';
                        marketplacePanel.style.display = 'none';
                    } else {
                        assistantPanel.style.display = 'none';
                        marketplacePanel.style.display = 'flex';
                    }
                }
                
                connectWebSocket() {
                    // Determine WebSocket URL
                    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                    const wsUrl = `${protocol}//${window.location.host}/ws`;
                    
                    console.log(`🔌 Connecting to WebSocket at ${wsUrl}`);
                    
                    try {
                        this.socket = new WebSocket(wsUrl);
                        
                        this.socket.onopen = (event) => {
                            console.log('✅ WebSocket connection established');
                            this.isConnected = true;
                            this.reconnectAttempts = 0;
                            this.reconnectDelay = 3000;
                            
                            // Process any queued messages
                            this.processQueue();
                        };
                        
                        this.socket.onmessage = (event) => {
                            console.log('📩 Received message from server');
                            try {
                                const message = JSON.parse(event.data);
                                this.handleMessage(message);
                            } catch (e) {
                                console.error('Error parsing WebSocket message:', e);
                                console.error('Raw message:', event.data);
                            }
                        };
                        
                        this.socket.onclose = (event) => {
                            console.log('🔌 WebSocket connection closed', event.code, event.reason);
                            this.isConnected = false;
                            
                            // Update UI to show disconnected state
                            this.updateConnectionStatus(false);
                            
                            // Attempt to reconnect with backoff
                            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                                this.reconnectAttempts++;
                                const delay = Math.min(30000, this.reconnectDelay * Math.pow(1.5, this.reconnectAttempts - 1));
                                console.log(`⏱️ Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                                
                                setTimeout(() => this.connectWebSocket(), delay);
                            } else {
                                console.error('❌ Max reconnect attempts reached. Please refresh the page.');
                                this.displayError('Connection lost. Please refresh the page to try again.');
                            }
                        };
                        
                        this.socket.onerror = (error) => {
                            console.error('❌ WebSocket error:', error);
                        };
                    } catch (error) {
                        console.error('❌ Error creating WebSocket:', error);
                        this.updateConnectionStatus(false);
                        
                        // Show error in chat
                        this.displayError('Failed to connect to server. Please check your internet connection.');
                    }
                }
                
                setupEventListeners() {
                    // Query submission
                    const submitBtn = document.getElementById('submitBtn');
                    const queryInput = document.getElementById('queryInput');
                    const voiceInputBtn = document.getElementById('voiceInputBtn');
                    const historyBtn = document.getElementById('historyBtn');
                    const refreshBtn = document.getElementById('refreshBtn');
                    const clearChatBtn = document.getElementById('clearChatBtn');
                    const layoutToggle = document.getElementById('layoutToggle');
                    
                    if (submitBtn && queryInput) {
                        submitBtn.addEventListener('click', () => {
                            const query = queryInput.value.trim();
                            if (query) {
                                console.log('🔍 Submitting query:', query);
                                this.submitQuery(query);
                                queryInput.value = '';
                                queryInput.focus();
                            }
                        });
                        
                        queryInput.addEventListener('keypress', (e) => {
                            if (e.key === 'Enter') {
                                const query = queryInput.value.trim();
                                if (query) {
                                    console.log('🔍 Submitting query (Enter key):', query);
                                    this.submitQuery(query);
                                    queryInput.value = '';
                                }
                            }
                        });
                    }
                    
                    // Layout toggle
                    if (layoutToggle) {
                        layoutToggle.addEventListener('click', () => {
                            this.toggleLayout();
                        });
                    }
                    
                    // Tab switching
                    const tabs = document.querySelectorAll('.tab');
                    tabs.forEach(tab => {
                        tab.addEventListener('click', () => {
                            this.switchTab(tab.dataset.tab);
                        });
                    });
                    
                    if (voiceInputBtn) {
                        voiceInputBtn.addEventListener('click', () => {
                            this.startVoiceInput();
                        });
                    }
                    
                    if (historyBtn) {
                        historyBtn.addEventListener('click', () => {
                            this.showQueryHistory();
                        });
                    }
                    
                    if (refreshBtn) {
                        refreshBtn.addEventListener('click', () => {
                            console.log('🔄 Refresh button clicked');
                            if (window.app && typeof window.app.loadData === 'function') {
                                window.app.loadData();
                            }
                        });
                    }
                    
                    if (clearChatBtn) {
                        clearChatBtn.addEventListener('click', () => {
                            this.clearChat();
                        });
                    }
                    
                    // Theme toggle
                    const themeToggle = document.getElementById('themeToggle');
                    if (themeToggle) {
                        themeToggle.addEventListener('click', () => {
                            this.toggleTheme();
                        });
                    }
                    
                    // Window resize handler
                    window.addEventListener('resize', () => {
                        if (window.innerWidth < 768 && this.isGridLayout) {
                            // Force tabbed layout on small screens
                            const contentGrid = document.getElementById('contentGrid');
                            const tabsContainer = document.getElementById('tabsContainer');
                            if (contentGrid && tabsContainer) {
                                contentGrid.style.display = 'block';
                                tabsContainer.style.display = 'block';
                                this.switchTab('assistant');
                            }
                        } else {
                            // Apply current layout preference
                            this.applyLayout();
                        }
                    });
                }
                
                clearChat() {
                    const chatContainer = document.getElementById('chatContainer');
                    if (!chatContainer) return;
                    
                    // Keep welcome message, remove all other messages
                    const welcomeMessage = chatContainer.querySelector('.welcome-message');
                    chatContainer.innerHTML = '';
                    
                    if (welcomeMessage) {
                        chatContainer.appendChild(welcomeMessage);
                    }
                    
                    console.log('🧹 Chat cleared');
                }
                
                startVoiceInput() {
                    if (!('webkitSpeechRecognition' in window)) {
                        alert('Speech recognition is not supported in this browser');
                        return;
                    }
                    
                    const recognition = new webkitSpeechRecognition();
                    recognition.continuous = false;
                    recognition.interimResults = false;
                    
                    const voiceBtn = document.getElementById('voiceInputBtn');
                    if (voiceBtn) {
                        voiceBtn.classList.add('active');
                        voiceBtn.innerHTML = '<i class="fas fa-microphone-slash"></i>';
                    }
                    
                    recognition.onstart = () => {
                        console.log('🎤 Voice recognition started');
                    };
                    
                    recognition.onresult = (event) => {
                        const transcript = event.results[0][0].transcript;
                        console.log('🎤 Transcript:', transcript);
                        const queryInput = document.getElementById('queryInput');
                        if (queryInput) {
                            queryInput.value = transcript;
                        }
                    };
                    
                    recognition.onerror = (event) => {
                        console.error('🎤 Speech recognition error', event.error);
                    };
                    
                    recognition.onend = () => {
                        if (voiceBtn) {
                            voiceBtn.classList.remove('active');
                            voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
                        }
                    };
                    
                    recognition.start();
                }
                
                showQueryHistory() {
                    // Implementation for query history display
                    console.log('📜 Query history button clicked');
                }
                
                submitQuery(query) {
                    this.queryCounter++;
                    const queryId = `q-${Date.now()}-${this.queryCounter}`;
                    
                    // Add user message to chat
                    this.addUserMessage(query);
                    
                    // Send query to server
                    this.sendMessage({
                        type: 'query',
                        query_id: queryId,
                        query: query
                    });
                    
                    // If we're in tabbed layout and not on the assistant tab, switch to it
                    if (!this.isGridLayout) {
                        this.switchTab('assistant');
                    }
                    
                    // Debug message to console
                    console.log(`📤 Query sent: "${query}" with ID: ${queryId}`);
                }
                
                getSystemStatus() {
                    this.sendMessage({
                        type: 'get_status'
                    });
                }
                
                sendMessage(message) {
                    if (this.isConnected && this.socket.readyState === WebSocket.OPEN) {
                        try {
                            const messageString = JSON.stringify(message);
                            this.socket.send(messageString);
                            console.log('📤 Message sent:', message);
                        } catch (error) {
                            console.error('❌ Error sending message:', error);
                            // Queue message if send fails
                            this.messageQueue.push(message);
                        }
                    } else {
                        // Queue message if not connected
                        this.messageQueue.push(message);
                        console.log('📋 Message queued (not connected):', message);
                        
                        // Try to reconnect if socket is closed
                        if (!this.isConnected) {
                            console.log('🔄 Attempting to reconnect...');
                            this.connectWebSocket();
                        }
                    }
                }
                
                processQueue() {
                    // Process any queued messages
                    if (this.messageQueue.length > 0) {
                        console.log(`📋 Processing ${this.messageQueue.length} queued messages`);
                        
                        const messages = [...this.messageQueue];
                        this.messageQueue = [];
                        
                        for (const message of messages) {
                            this.sendMessage(message);
                        }
                    }
                }
                
                handleMessage(message) {
                    console.log('📩 Processing message:', message);
                    
                    if (!message || typeof message !== 'object' || !message.type) {
                        console.error('❌ Invalid message format:', message);
                        return;
                    }
                    
                    switch (message.type) {
                        case 'connection_established':
                            this.sessionId = message.session_id;
                            this.updateConnectionStatus(true, message.orchestrator_available);
                            console.log(`🔗 Connection established with session ID: ${this.sessionId}`);
                            console.log(`🔗 ADK API Server available: ${message.orchestrator_available}`);
                            
                            // Get system status after connection
                            this.getSystemStatus();
                            break;
                            
                        case 'processing':
                            console.log(`⏳ Processing query ID: ${message.query_id}`);
                            this.showThinkingIndicator(message.query_id);
                            break;
                            
                        case 'result':
                            console.log(`✅ Received result for query`);
                            this.hideThinkingIndicator();
                            this.displayResult(message.result);
                            break;
                            
                        case 'error':
                            console.error(`❌ Error:`, message.error);
                            this.hideThinkingIndicator();
                            this.displayError(message.error);
                            break;
                            
                        case 'status':
                            console.log(`ℹ️ System status update:`, message.status);
                            this.updateSystemInfo(message.status);
                            break;
                            
                        case 'theme_toggled':
                            console.log(`🎨 Theme toggled to ${message.theme}`);
                            break;
                            
                        case 'status_change':
                            console.log(`🔄 Status change: ${message.status}`);
                            this.updateConnectionStatus(message.status === 'connected', message.orchestrator_available);
                            break;
                            
                        case 'connection_error':
                            console.error(`🔌 Connection error:`, message.error);
                            this.displayError(`Connection error: ${message.error}`);
                            break;
                            
                        default:
                            console.warn(`⚠️ Unknown message type: ${message.type}`);
                    }
                }
                
                updateConnectionStatus(connected, orchestratorAvailable) {
                    const statusElement = document.getElementById('systemStatus');
                    if (!statusElement) return;
                    
                    if (connected) {
                        if (orchestratorAvailable === false) {
                            statusElement.innerHTML = '<i class="fas fa-circle"></i><span>Demo Mode</span>';
                            statusElement.className = 'system-status connected';
                            statusElement.style.backgroundColor = 'rgba(255, 188, 0, 0.1)';
                            statusElement.style.color = '#FFBC00';
                        } else {
                            statusElement.innerHTML = '<i class="fas fa-circle"></i><span>Connected</span>';
                            statusElement.className = 'system-status connected';
                        }
                    } else {
                        statusElement.innerHTML = '<i class="fas fa-circle"></i><span>Disconnected</span>';
                        statusElement.className = 'system-status disconnected';
                    }
                }
                
                updateSystemInfo(status) {
                    if (!status) return;
                    
                    console.log('ℹ️ System info:', status);
                    
                    // Update UI with system status if needed
                    // For example, you could update icons to show which agents are available
                }
                
                addUserMessage(message) {
                    const chatContainer = document.getElementById('chatContainer');
                    if (!chatContainer) return;
                    
                    const messageElement = document.createElement('div');
                    messageElement.className = 'message user-message';
                    messageElement.innerHTML = `<p>${this.escapeHtml(message)}</p>`;
                    
                    chatContainer.appendChild(messageElement);
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }
                
                showThinkingIndicator(queryId) {
                    const chatContainer = document.getElementById('chatContainer');
                    if (!chatContainer) return;
                    
                    const thinkingElement = document.createElement('div');
                    thinkingElement.className = 'message system-message thinking';
                    thinkingElement.id = `thinking-${queryId}`;
                    thinkingElement.innerHTML = `
                        <div class="thinking-indicator">
                            <span class="dot"></span>
                            <span class="dot"></span>
                            <span class="dot"></span>
                        </div>
                    `;
                    
                    chatContainer.appendChild(thinkingElement);
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }
                
                hideThinkingIndicator() {
                    const thinkingElements = document.querySelectorAll('.thinking');
                    thinkingElements.forEach(element => element.remove());
                }
                
                displayResult(result) {
                    if (!result) return;
                    
                    const chatContainer = document.getElementById('chatContainer');
                    if (!chatContainer) return;
                    
                    const messageElement = document.createElement('div');
                    messageElement.className = 'message system-message';
                    
                    // Create content based on the result
                    let content = '';
                    
                    if (result.summary) {
                        // Check if the summary contains markdown code blocks with HTML
                        if (result.summary.includes('```html')) {
                            // Extract the HTML content from inside the code block
                            let htmlContent = result.summary;
                            htmlContent = htmlContent.replace(/```html\s*/g, '');
                            htmlContent = htmlContent.replace(/```\s*$/g, '');
                            // Add the clean HTML directly to the content
                            content += htmlContent;
                        } else {
                            // Just use the regular text as before
                            content += `<p>${this.escapeHtml(result.summary)}</p>`;
                        }
                    }
                    
                    // Add data sections if available
                    if (result.data) {
                        content += '<div class="result-data">';
                        
                        // Process marketplace data
                        const marketplaceKey = Object.keys(result.data).find(k => k.includes('marketplace'));
                        if (marketplaceKey && result.data[marketplaceKey]?.data) {
                            const items = result.data[marketplaceKey].data;
                            
                            if (items && items.length > 0) {
                                content += `<h3>Marketplace Items</h3>`;
                                content += `<p>Found ${items.length} relevant items</p>`;
                                
                                // Update the app's data with the marketplace items
                                if (window.app && typeof window.app.updateData === 'function') {
                                    window.app.updateData(items);
                                }
                                
                                // If we're in tabbed layout, switch to marketplace tab
                                if (!this.isGridLayout) {
                                    setTimeout(() => {
                                        this.switchTab('marketplace');
                                    }, 2000);
                                }
                            }
                        }
                        
                        content += '</div>';
                    }
                    
                    // Add execution details
                    if (result.execution_details) {
                        content += `
                            <div class="execution-details">
                                <small>Analyzed with ${result.execution_details.tasks_executed} tasks in 
                                ${Math.round(result.execution_details.execution_time * 100) / 100}s</small>
                            </div>
                        `;
                    }
                    
                    messageElement.innerHTML = content;
                    chatContainer.appendChild(messageElement);
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }
                
                displayError(error) {
                    const chatContainer = document.getElementById('chatContainer');
                    if (!chatContainer) return;
                    
                    const messageElement = document.createElement('div');
                    messageElement.className = 'message system-message';
                    messageElement.innerHTML = `
                        <p class="error-message">Sorry, I encountered an error:</p>
                        <p>${this.escapeHtml(error)}</p>
                    `;
                    
                    chatContainer.appendChild(messageElement);
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }
                
                escapeHtml(text) {
                    if (text === null || text === undefined) return '';
                    const div = document.createElement('div');
                    div.textContent = String(text);
                    return div.innerHTML;
                }
            }
                        
            // Initialize the app when DOM is loaded
            document.addEventListener('DOMContentLoaded', () => {
                // First initialize WebSocket client for AI responses
                window.aiClient = new RobloxEconomyAIClient();
                
                // Then initialize the RobloxEconomyApp for the Supabase data
                window.app = new RobloxEconomyApp();
            });
        </script>
    </body>
    </html>
    """

# Start the application
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    # Use reload=True during development, remove for production
    uvicorn.run(app, host="0.0.0.0", port=port)
