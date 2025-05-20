FROM python:3.9

WORKDIR /app

# Install system dependencies 
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY improved_app.py .
COPY roblox-economy.js ./static/roblox-economy.js
COPY robloxorchestrator/ ./robloxorchestrator/

# Create directory for static files
RUN mkdir -p /app/static

# Create supervisord configuration
RUN mkdir -p /var/log/supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose port for web application
EXPOSE 8000

# Set environment variables
ENV ADK_API_URL="http://localhost:3000"
ENV APP_NAME="robloxorchestrator"
ENV PORT=8000

# Use supervisord to manage both processes
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
