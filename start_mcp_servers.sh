#!/bin/bash

# UltraRAG MCP Servers Launcher for Docker
set -e

SCRIPT_DIR="/app"
SERVERS_DIR="$SCRIPT_DIR/servers"

# List of available MCP servers
SERVERS=(
    "sayhello"
    "corpus"
    "custom" 
    "evaluation"
    "generation"
    "prompt"
    "reranker"
    "retriever"
    "benchmark"
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
    local server_index=$2
    local server_path="$SERVERS_DIR/$server_name/src/${server_name}.py"
    
    if [[ ! -f "$server_path" ]]; then
        print_status $RED "❌ Server $server_name not found at $server_path"
        return 1
    fi
    
    print_status $BLUE "🚀 Starting MCP server: $server_name"
    
    # Start server in background with proper Python path and HTTP transport
    cd "$SCRIPT_DIR"
    local port=$((8000 + server_index))
    python "$server_path" transport=http port=$port &
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
    local index=0
    for server in "${SERVERS[@]}"; do
        if start_server "$server" "$index"; then
            ((started++))
        fi
        ((index++))
        sleep 2  # Delay between starts
    done
    
    print_status $GREEN "🎉 Started $started MCP servers"
    echo ""
    print_status $BLUE "Available servers:"
    for server in "${SERVERS[@]}"; do
        echo "  - $server"
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

# Start all servers
start_all_servers

# Keep container running and monitor servers
print_status $YELLOW "👀 Servers running... (Press Ctrl+C to stop)"
while true; do
    sleep 30
    # Check if any servers died and restart them
    if [[ -f /tmp/ultrarag_mcp_pids ]]; then
        local index=0
        while IFS=: read -r pid port name; do
            if ! kill -0 "$pid" 2>/dev/null; then
                print_status $YELLOW "⚠️  Server $name on port $port (PID $pid) stopped unexpectedly"
                print_status $BLUE "🔄 Restarting $name..."
                start_server "$name" "$index"
            fi
            ((index++))
        done < /tmp/ultrarag_mcp_pids
    fi
done