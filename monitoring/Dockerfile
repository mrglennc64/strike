FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy monitoring modules
COPY . .

# Create data directory
RUN mkdir -p /app/data /app/logs

# Run monitoring service
CMD ["python", "-m", "monitoring_service"]
