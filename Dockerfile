FROM python:3.13-slim

LABEL maintainer="GeekJohn <mordang7>"
LABEL description="ContextKeep - Infinite Long-Term Memory for AI Agents"
LABEL version="1.3.0"

WORKDIR /app

# Install dependencies
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY core/ ./core/
COPY static/ ./static/
COPY templates/ ./templates/
COPY server.py webui.py install.py store_mem_cli.py ./
COPY mcp_config.example.json ./

# Persistent memory storage
VOLUME ["/app/data"]

# Expose MCP SSE (5100) and WebUI (5000) ports
EXPOSE 5100 5000

# Default: run MCP server in SSE mode
CMD ["python", "server.py", "--transport", "sse"]
