# AOTrust notary MCP server (stdio) — Glama / local container build.
FROM python:3.12-slim

WORKDIR /app
COPY mcp_server.py /app/mcp_server.py
RUN pip install --no-cache-dir "mcp>=1.2"

# stdio transport: the client speaks JSON-RPC on stdin/stdout
ENTRYPOINT ["python", "/app/mcp_server.py"]
