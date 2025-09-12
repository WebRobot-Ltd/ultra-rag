#!/bin/bash

# Persistent PostgreSQL Database Tunnel Script
# Establishes and maintains a stable SSH tunnel to PostgreSQL database

set -e

# Configuration
BASTION_HOST="root@metaglobe.finance"
LOCAL_PORT="5433"
REMOTE_PORT="5432"
NAMESPACE="nuvolaris"
SERVICE_NAME="nuvolaris-postgres"
LOG_FILE="/tmp/postgres-tunnel.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

# Function to check if port is already in use
check_port() {
    if lsof -Pi :$LOCAL_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        warning "Port $LOCAL_PORT is already in use"
        return 1
    fi
    return 0
}

# Function to kill existing processes
cleanup() {
    log "Cleaning up existing processes..."
    
    # Kill existing kubectl port-forward processes
    pkill -f "kubectl port-forward.*$SERVICE_NAME" || true
    
    # Kill existing SSH tunnel processes
    pkill -f "ssh.*$LOCAL_PORT.*$REMOTE_PORT" || true
    
    # Wait a moment for processes to terminate
    sleep 2
}

# Function to establish SSH tunnel
establish_tunnel() {
    log "Establishing SSH tunnel to $BASTION_HOST..."
    
    # First, establish SSH tunnel
    ssh -f -N -L $LOCAL_PORT:localhost:$REMOTE_PORT $BASTION_HOST &
    SSH_PID=$!
    
    # Wait for SSH tunnel to establish
    sleep 3
    
    # Check if SSH tunnel is working
    if ! kill -0 $SSH_PID 2>/dev/null; then
        error "SSH tunnel failed to establish"
        return 1
    fi
    
    success "SSH tunnel established (PID: $SSH_PID)"
    
    # Now establish kubectl port-forward on the bastion host
    log "Establishing kubectl port-forward on bastion host..."
    
    ssh $BASTION_HOST "kubectl port-forward -n $NAMESPACE svc/$SERVICE_NAME $REMOTE_PORT:$REMOTE_PORT" &
    KUBECTL_PID=$!
    
    # Wait for kubectl port-forward to establish
    sleep 5
    
    # Check if kubectl port-forward is working
    if ! ssh $BASTION_HOST "pgrep -f 'kubectl port-forward.*$SERVICE_NAME'" >/dev/null 2>&1; then
        error "kubectl port-forward failed to establish"
        kill $SSH_PID 2>/dev/null || true
        return 1
    fi
    
    success "kubectl port-forward established (PID: $KUBECTL_PID)"
    
    # Test the connection
    log "Testing database connection..."
    if timeout 10 bash -c "echo > /dev/tcp/localhost/$LOCAL_PORT" 2>/dev/null; then
        success "Database connection test successful!"
        success "PostgreSQL is now accessible at localhost:$LOCAL_PORT"
        return 0
    else
        error "Database connection test failed"
        kill $SSH_PID 2>/dev/null || true
        return 1
    fi
}

# Function to monitor and maintain tunnel
monitor_tunnel() {
    log "Starting tunnel monitoring..."
    
    while true; do
        # Check if SSH tunnel is still alive
        if ! lsof -Pi :$LOCAL_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
            error "SSH tunnel lost, reconnecting..."
            cleanup
            if ! establish_tunnel; then
                error "Failed to reestablish tunnel, retrying in 30 seconds..."
                sleep 30
                continue
            fi
        fi
        
        # Check if kubectl port-forward is still running on bastion
        if ! ssh $BASTION_HOST "pgrep -f 'kubectl port-forward.*$SERVICE_NAME'" >/dev/null 2>&1; then
            warning "kubectl port-forward lost on bastion host, reconnecting..."
            ssh $BASTION_HOST "kubectl port-forward -n $NAMESPACE svc/$SERVICE_NAME $REMOTE_PORT:$REMOTE_PORT" &
            sleep 5
        fi
        
        # Sleep before next check
        sleep 10
    done
}

# Function to show status
show_status() {
    log "Checking tunnel status..."
    
    if lsof -Pi :$LOCAL_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        success "SSH tunnel is active on port $LOCAL_PORT"
        
        if ssh $BASTION_HOST "pgrep -f 'kubectl port-forward.*$SERVICE_NAME'" >/dev/null 2>&1; then
            success "kubectl port-forward is active on bastion host"
            success "Database should be accessible at localhost:$LOCAL_PORT"
        else
            warning "kubectl port-forward is not active on bastion host"
        fi
    else
        error "SSH tunnel is not active"
    fi
}

# Function to stop tunnel
stop_tunnel() {
    log "Stopping tunnel..."
    cleanup
    success "Tunnel stopped"
}

# Main function
main() {
    case "${1:-start}" in
        "start")
            log "Starting persistent PostgreSQL tunnel..."
            
            if ! check_port; then
                error "Port $LOCAL_PORT is already in use. Use 'stop' first or choose a different port."
                exit 1
            fi
            
            cleanup
            
            if establish_tunnel; then
                success "Tunnel established successfully!"
                log "Tunnel will be monitored and maintained automatically"
                log "Use 'status' to check tunnel status"
                log "Use 'stop' to stop the tunnel"
                log "Logs are written to: $LOG_FILE"
                
                # Start monitoring in background
                monitor_tunnel &
                MONITOR_PID=$!
                echo $MONITOR_PID > /tmp/postgres-tunnel-monitor.pid
                
                # Wait for user interrupt
                trap 'stop_tunnel; kill $MONITOR_PID 2>/dev/null; exit 0' INT TERM
                wait
            else
                error "Failed to establish tunnel"
                exit 1
            fi
            ;;
        "stop")
            stop_tunnel
            if [ -f /tmp/postgres-tunnel-monitor.pid ]; then
                kill $(cat /tmp/postgres-tunnel-monitor.pid) 2>/dev/null || true
                rm -f /tmp/postgres-tunnel-monitor.pid
            fi
            ;;
        "status")
            show_status
            ;;
        "restart")
            stop_tunnel
            sleep 2
            main start
            ;;
        *)
            echo "Usage: $0 {start|stop|status|restart}"
            echo ""
            echo "Commands:"
            echo "  start   - Start the persistent tunnel (default)"
            echo "  stop    - Stop the tunnel"
            echo "  status  - Show tunnel status"
            echo "  restart - Restart the tunnel"
            echo ""
            echo "Configuration:"
            echo "  Bastion Host: $BASTION_HOST"
            echo "  Local Port: $LOCAL_PORT"
            echo "  Remote Port: $REMOTE_PORT"
            echo "  Namespace: $NAMESPACE"
            echo "  Service: $SERVICE_NAME"
            echo "  Log File: $LOG_FILE"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
