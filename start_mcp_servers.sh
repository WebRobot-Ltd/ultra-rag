#!/bin/bash

# UltraRAG MCP Servers Launcher for Docker
set -e

SCRIPT_DIR="/ultrarag"
SERVERS_DIR="$SCRIPT_DIR/servers"

# Start simple health check server
start_health_server() {
    python3 -c "
import http.server
import socketserver
import json
from urllib.parse import urlparse

class HealthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {'status': 'healthy', 'service': 'ultrarag-mcp'}
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

with socketserver.TCPServer(('', 8000), HealthHandler) as httpd:
    httpd.serve_forever()
" &
    
    HEALTH_PID=$!
    echo "$HEALTH_PID" > /tmp/health_server_pid
    print_status $GREEN "✅ Health check server started on port 8000 (PID $HEALTH_PID)"
}

# List of available MCP servers with their default ports
# Port 8000 is reserved for health check server
declare -A SERVERS=(
    ["sayhello"]="8001"
    ["retriever"]="8002"
    ["generation"]="8003"
    ["corpus"]="8004"
    ["reranker"]="8005"
    ["evaluation"]="8006"
    ["benchmark"]="8007"
    ["custom"]="8008"
    ["prompt"]="8009"
    ["router"]="8010"
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

start_server() {
    local server_name=$1
    local server_path="$SERVERS_DIR/$server_name/src/${server_name}.py"
    
    if [[ ! -f "$server_path" ]]; then
        print_status $RED "❌ Server $server_name not found at $server_path"
        return 1
    fi
    
    # Get port from SERVERS array
    local port=${SERVERS[$server_name]}
    if [[ -z "$port" ]]; then
        print_status $RED "❌ No port configured for server $server_name"
        return 1
    fi
    
    print_status $BLUE "🚀 Starting MCP server: $server_name on port $port"
    
    # Start server in background with proper Python path and HTTP transport
    cd "$SCRIPT_DIR"
    python "$server_path" --transport http --port $port &
    local pid=$!
    
    # Store PID and port for cleanup and health checks
    echo "$pid:$port:$server_name" >> /tmp/ultrarag_mcp_pids
    
    print_status $GREEN "✅ Server $server_name started with PID $pid on port $port"
    return 0
}

start_all_servers() {
    print_status $YELLOW "🎯 UltraRAG MCP Servers Launcher (Docker)"
    echo "=================================================="
    
    # Clear PID file
    > /tmp/ultrarag_mcp_pids
    
    local started=0
    for server_name in "${!SERVERS[@]}"; do
        if start_server "$server_name"; then
            ((started++))
        fi
        sleep 2  # Delay between starts
    done
    
    print_status $GREEN "🎉 Started $started MCP servers"
    echo ""
    print_status $BLUE "Available servers:"
    for server_name in "${!SERVERS[@]}"; do
        local port=${SERVERS[$server_name]}
        echo "  - $server_name (port $port)"
    done
}

stop_all_servers() {
    print_status $YELLOW "🛑 Stopping all MCP servers..."
    
    if [[ -f /tmp/ultrarag_mcp_pids ]]; then
        while IFS=: read -r pid port name; do
            if kill -0 "$pid" 2>/dev/null; then
                print_status $BLUE "Stopping $name on port $port (PID $pid)"
                kill "$pid"
            fi
        done < /tmp/ultrarag_mcp_pids
        rm -f /tmp/ultrarag_mcp_pids
    fi
    
    print_status $GREEN "✅ All servers stopped"
}

cleanup() {
    print_status $YELLOW "🛑 Shutdown requested"
    stop_all_servers
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start health check server first
start_health_server

# Start all servers
start_all_servers

# Keep container running and monitor servers
print_status $YELLOW "👀 Servers running... (Press Ctrl+C to stop)"

# Test health check after longer delay
print_status $BLUE "🔍 Waiting 30 seconds before testing health check endpoint..."
sleep 30
print_status $BLUE "🔍 Testing health check endpoint..."
curl -f http://localhost:8000/health && print_status $GREEN "✅ Health check OK" || print_status $RED "❌ Health check failed"

# Check if servers are still running
print_status $BLUE "🔍 Checking if servers are still running..."
if [[ -f /tmp/health_server_pid ]]; then
    HEALTH_PID=$(cat /tmp/health_server_pid)
    if kill -0 "$HEALTH_PID" 2>/dev/null; then
        print_status $GREEN "✅ Health server still running (PID $HEALTH_PID)"
    else
        print_status $RED "❌ Health server died!"
    fi
fi

if [[ -f /tmp/ultrarag_mcp_pids ]]; then
    while IFS=: read -r pid port name; do
        if kill -0 "$pid" 2>/dev/null; then
            print_status $GREEN "✅ Server $name still running (PID $pid)"
        else
            print_status $RED "❌ Server $name died!"
        fi
    done < /tmp/ultrarag_mcp_pids
fi

while true; do
    print_status $BLUE "🔄 Monitoring loop iteration $(date)"
    sleep 30
    
    # Check if health server is still running
    if [[ -f /tmp/health_server_pid ]]; then
        HEALTH_PID=$(cat /tmp/health_server_pid)
        if ! kill -0 "$HEALTH_PID" 2>/dev/null; then
            print_status $RED "❌ Health server died! Restarting..."
            start_health_server
        else
            print_status $GREEN "✅ Health server still running (PID $HEALTH_PID)"
        fi
    fi
    
    # Check if any servers died and restart them
    if [[ -f /tmp/ultrarag_mcp_pids ]]; then
        while IFS=: read -r pid port name; do
            if ! kill -0 "$pid" 2>/dev/null; then
                print_status $YELLOW "⚠️  Server $name on port $port (PID $pid) stopped unexpectedly"
                print_status $BLUE "🔄 Restarting $name..."
                start_server "$name"
            else
                print_status $GREEN "✅ Server $name still running (PID $pid)"
            fi
        done < /tmp/ultrarag_mcp_pids
    fi
done