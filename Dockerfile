FROM python:3.10
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the port
EXPOSE 8080

# Create a startup script
RUN echo '#!/bin/bash\n\
# Start ADK API server in background\n\
adk api_server --port 3000 --host 0.0.0.0 &\n\
# Wait a moment for ADK to start\n\
sleep 5\n\
# Start the web app\n\
python improved_app.py\n\
' > /app/start.sh && chmod +x /app/start.sh

# Run the startup script
CMD ["/app/start.sh"]
