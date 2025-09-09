#!/bin/bash

# UltraRAG MCP Servers Docker Launcher
# Builds and runs all MCP servers in Docker containers

set -e

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

# Function to build the Docker image
build_image() {
    print_status $BLUE "🔨 Building UltraRAG MCP Servers Docker image..."
    docker build -f Dockerfile.mcp-servers -t ultrarag-mcp-servers:latest .
    print_status $GREEN "✅ Docker image built successfully"
}

# Function to start MCP servers
start_servers() {
    print_status $BLUE "🚀 Starting UltraRAG MCP Servers..."
    
    # Create necessary directories
    mkdir -p data logs
    
    # Start with docker-compose
    docker-compose -f docker-compose.mcp-servers.yml up -d
    
    print_status $GREEN "✅ MCP Servers started successfully"
    print_status $YELLOW "📊 Use 'docker-compose -f docker-compose.mcp-servers.yml logs -f' to view logs"
    print_status $YELLOW "🛑 Use 'docker-compose -f docker-compose.mcp-servers.yml down' to stop"
}

# Function to stop MCP servers
stop_servers() {
    print_status $YELLOW "🛑 Stopping UltraRAG MCP Servers..."
    docker-compose -f docker-compose.mcp-servers.yml down
    print_status $GREEN "✅ MCP Servers stopped"
}

# Function to show server status
show_status() {
    print_status $BLUE "📊 MCP Server Status:"
    echo "====================="
    docker-compose -f docker-compose.mcp-servers.yml ps
}

# Function to show logs
show_logs() {
    print_status $BLUE "📋 MCP Server Logs:"
    echo "==================="
    docker-compose -f docker-compose.mcp-servers.yml logs -f
}

# Function to restart servers
restart_servers() {
    print_status $YELLOW "🔄 Restarting MCP Servers..."
    stop_servers
    sleep 2
    start_servers
}

# Function to clean up
cleanup() {
    print_status $YELLOW "🧹 Cleaning up MCP Servers..."
    docker-compose -f docker-compose.mcp-servers.yml down -v
    docker rmi ultrarag-mcp-servers:latest 2>/dev/null || true
    print_status $GREEN "✅ Cleanup completed"
}

# Main script logic
case "${1:-start}" in
    "build")
        build_image
        ;;
    "start")
        if ! docker images | grep -q ultrarag-mcp-servers; then
            print_status $YELLOW "⚠️  Image not found, building first..."
            build_image
        fi
        start_servers
        ;;
    "stop")
        stop_servers
        ;;
    "restart")
        restart_servers
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs
        ;;
    "cleanup")
        cleanup
        ;;
    "rebuild")
        cleanup
        build_image
        start_servers
        ;;
    *)
        echo "UltraRAG MCP Servers Docker Launcher"
        echo "===================================="
        echo ""
        echo "Usage: $0 {build|start|stop|restart|status|logs|cleanup|rebuild}"
        echo ""
        echo "Commands:"
        echo "  build    - Build Docker image"
        echo "  start    - Start MCP servers (default)"
        echo "  stop     - Stop MCP servers"
        echo "  restart  - Restart MCP servers"
        echo "  status   - Show server status"
        echo "  logs     - Show server logs"
        echo "  cleanup  - Stop and remove containers/images"
        echo "  rebuild  - Clean, build, and start"
        echo ""
        echo "Examples:"
        echo "  $0 start     # Start servers"
        echo "  $0 logs      # View logs"
        echo "  $0 status    # Check status"
        echo "  $0 stop      # Stop servers"
        exit 1
        ;;
esac

