"""
ADK Configuration for Marketplace Analytics Agent
"""

import os
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv())

# ADK Configuration
class Config:
    MODEL = os.getenv('ADK_MODEL', 'gemini-2.0-flash-exp')
    
    # Supabase credentials
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
    
    # API keys
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    
    # Validate required settings
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Missing required Supabase configuration")
    
    if not GEMINI_API_KEY and not GOOGLE_API_KEY:
        raise ValueError("Missing required API key configuration")

# Export config for use in agent
config = Config()
