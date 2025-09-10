#!/bin/bash

# UltraRAG MCP Servers Launcher for Docker
set -e

# Detect if running in Docker or locally
if [[ -d "/ultrarag" ]]; then
    SCRIPT_DIR="/ultrarag"
    SERVERS_DIR="$SCRIPT_DIR/servers"
else
    SCRIPT_DIR="$(pwd)"
    SERVERS_DIR="$SCRIPT_DIR/servers"
fi

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
# For testing, only enable retriever server
declare -A SERVERS=(
    ["retriever"]="8002"
    # ["sayhello"]="8001"
    # ["generation"]="8003"
    # ["corpus"]="8004"
    # ["reranker"]="8005"
    # ["evaluation"]="8006"
    # ["benchmark"]="8007"
    # ["custom"]="8008"
    # ["prompt"]="8009"
    # ["router"]="8010"
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
    
    # Create log file for this server
    local log_file="/tmp/ultrarag_${server_name}_$(date +%s).log"
    
    # Start server with error logging
    python "$server_path" --transport http --port $port > "$log_file" 2>&1 &
    local pid=$!
    
    # Store PID, port, and log file for cleanup and health checks
    echo "$pid:$port:$server_name:$log_file" >> /tmp/ultrarag_mcp_pids
    
    # Wait a moment and check if the process is still running
    sleep 2
    if kill -0 "$pid" 2>/dev/null; then
        print_status $GREEN "✅ Server $server_name started with PID $pid on port $port"
        print_status $BLUE "📝 Logs available at: $log_file"
    else
        print_status $RED "❌ Server $server_name failed to start (PID $pid)"
        print_status $YELLOW "📋 Last few lines of log:"
        tail -10 "$log_file" 2>/dev/null || print_status $RED "❌ Could not read log file"
        return 1
    fi
    
    # Add sleep after each server to prevent container from exiting too quickly
    print_status $BLUE "⏳ Waiting 5 seconds after starting $server_name..."
    sleep 5
    
    return 0
}

start_all_servers() {
    print_status $YELLOW "🎯 UltraRAG MCP Servers Launcher (Docker) - RETRIEVER ONLY"
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

# Add immediate sleep to prevent container from exiting too quickly
print_status $BLUE "⏳ Waiting 30 seconds to ensure servers are stable..."
sleep 30

# Check if servers are still running after initial sleep
print_status $BLUE "🔍 Checking server status after initial sleep..."
if [[ -f /tmp/health_server_pid ]]; then
    HEALTH_PID=$(cat /tmp/health_server_pid)
    if kill -0 "$HEALTH_PID" 2>/dev/null; then
        print_status $GREEN "✅ Health server still running (PID $HEALTH_PID)"
    else
        print_status $RED "❌ Health server died! Restarting..."
        # Kill any process using port 8000 before restarting
        if lsof -ti:8000 >/dev/null 2>&1; then
            print_status $YELLOW "🔄 Killing processes using port 8000..."
            lsof -ti:8000 | xargs kill -9 2>/dev/null || true
            sleep 2
        fi
        start_health_server
    fi
else
    print_status $RED "❌ Health server PID file not found!"
fi

if [[ -f /tmp/ultrarag_mcp_pids ]]; then
    while IFS=: read -r pid port name; do
        if kill -0 "$pid" 2>/dev/null; then
            print_status $GREEN "✅ Server $name still running (PID $pid)"
        else
            print_status $RED "❌ Server $name died! Restarting..."
            start_server "$name"
        fi
    done < /tmp/ultrarag_mcp_pids
else
    print_status $RED "❌ MCP servers PID file not found!"
fi

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

# Enhanced monitoring loop with crash detection and logging
print_status $YELLOW "🔄 Starting enhanced monitoring loop with crash detection..."
print_status $BLUE "📝 Monitoring MCP servers every 10 seconds for crashes..."

iteration=0
while true; do
    iteration=$((iteration + 1))
    print_status $BLUE "🔄 Monitoring iteration #$iteration - $(date)"
    
    # Check if health server is still running
    if [[ -f /tmp/health_server_pid ]]; then
        HEALTH_PID=$(cat /tmp/health_server_pid)
        if ! kill -0 "$HEALTH_PID" 2>/dev/null; then
            print_status $RED "💥 Health server crashed! (PID $HEALTH_PID)"
            print_status $YELLOW "📋 Checking system logs for crash details..."
            
            # Try to get crash logs
            if command -v dmesg >/dev/null 2>&1; then
                print_status $BLUE "📄 Recent kernel messages:"
                dmesg | tail -10 2>/dev/null || true
            fi
            
            print_status $BLUE "🔄 Restarting health server..."
            # Kill any process using port 8000 before restarting
            if lsof -ti:8000 >/dev/null 2>&1; then
                print_status $YELLOW "🔄 Killing processes using port 8000..."
                lsof -ti:8000 | xargs kill -9 2>/dev/null || true
                sleep 2
            fi
            start_health_server
        else
            # Test health endpoint
            if ! curl -s -f "http://localhost:8000/health" >/dev/null 2>&1; then
                print_status $YELLOW "⚠️  Health server not responding on endpoint (PID $HEALTH_PID)"
            fi
        fi
    else
        print_status $RED "❌ Health server PID file not found! Restarting..."
        start_health_server
    fi
    
    # Check MCP servers with enhanced crash detection
    if [[ -f /tmp/ultrarag_mcp_pids ]]; then
        while IFS=: read -r pid port name log_file; do
            if ! kill -0 "$pid" 2>/dev/null; then
                print_status $RED "💥 MCP Server $name crashed! (PID $pid, Port $port)"
                print_status $YELLOW "📋 Crash analysis for $name:"
                
                # Show crash logs if available
                if [[ -f "$log_file" ]]; then
                    print_status $BLUE "📄 Last 20 lines of $name log:"
                    tail -20 "$log_file" 2>/dev/null || true
                fi
                
                # Check if it's a Python process crash
                if command -v ps >/dev/null 2>&1; then
                    print_status $BLUE "📄 Recent Python processes:"
                    ps aux | grep python | grep -v grep | tail -5 || true
                fi
                
                # Check system resources
                print_status $BLUE "📊 System resources:"
                if command -v free >/dev/null 2>&1; then
                    free -h || true
                fi
                if command -v df >/dev/null 2>&1; then
                    df -h /tmp /ultrarag 2>/dev/null || true
                fi
                
                print_status $BLUE "🔄 Restarting $name..."
                start_server "$name"
            else
                # Server is running, test if it's responding
                if [[ "$name" == "retriever" ]]; then
                    if ! curl -s -f "http://localhost:$port/mcp" >/dev/null 2>&1; then
                        print_status $YELLOW "⚠️  Server $name not responding on MCP endpoint (PID $pid, Port $port)"
                        # Show recent logs for debugging
                        if [[ -f "$log_file" ]]; then
                            print_status $BLUE "📄 Recent $name logs:"
                            tail -10 "$log_file" 2>/dev/null || true
                        fi
                    fi
                fi
            fi
        done < /tmp/ultrarag_mcp_pids
    else
        print_status $RED "❌ MCP servers PID file not found! Restarting all servers..."
        start_all_servers
    fi
    
    # Show status every 60 seconds
    if (( iteration % 6 == 0 )); then
        print_status $GREEN "🟢 UltraRAG MCP Servers Status - Iteration #$iteration"
        print_status $BLUE "📊 Active processes:"
        ps aux | grep -E "(python|ultrarag)" | grep -v grep || true
    fi
    
    sleep 10  # Check every 10 seconds
done