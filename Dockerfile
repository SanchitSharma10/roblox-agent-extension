FROM python:3.9-slim

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

ENV PORT=8080  # Change from 8000 to 8080

# Expose the port
EXPOSE 8080  # Change from 8000 to 8080

# Run the application
CMD ["uvicorn", "improved_app:app", "--host", "0.0.0.0", "--port", "8080"]
