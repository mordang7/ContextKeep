FROM python:3.10-slim

WORKDIR /app

# Install system dependencies if any are needed
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create data directory for volume mapping
RUN mkdir -p /app/data/memories

# Default command (can be overridden by docker-compose)
CMD ["python", "server.py", "--transport", "sse", "--host", "0.0.0.0", "--port", "5100"]
