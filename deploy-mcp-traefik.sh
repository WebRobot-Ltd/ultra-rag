#!/bin/bash

# UltraRAG MCP Servers - Traefik Deployment Script
# This script deploys the MCP servers with Traefik Ingress

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

# Function to check if kubectl is available
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    print_status "kubectl is available"
}

# Function to check if cluster is accessible
check_cluster() {
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    print_status "Kubernetes cluster is accessible"
}

# Function to deploy MCP services
deploy_mcp_services() {
    print_header "Deploying MCP Services"
    
    print_status "Applying MCP service configuration..."
    kubectl apply -f k8s-mcp-traefik-complete.yaml
    
    print_status "Waiting for services to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/ultrarag -n default || true
    
    print_status "MCP services deployed successfully!"
}

# Function to verify deployment
verify_deployment() {
    print_header "Verifying Deployment"
    
    print_status "Checking pods..."
    kubectl get pods -l app=ultrarag -n default
    
    print_status "Checking services..."
    kubectl get svc ultrarag-mcp-service -n default
    
    print_status "Checking ingress..."
    kubectl get ingress -n default | grep ultrarag-mcp
    
    print_status "Checking middlewares..."
    kubectl get middleware -n default | grep ultrarag-mcp
    
    print_status "Deployment verification completed!"
}

# Function to test endpoints
test_endpoints() {
    print_header "Testing Endpoints"
    
    # Wait a bit for ingress to be ready
    sleep 10
    
    print_status "Testing health endpoint (dev)..."
    if curl -s https://ultrarag-mcp-dev.webrobot.local/health >/dev/null; then
        print_status "✅ Dev health endpoint is accessible"
    else
        print_warning "❌ Dev health endpoint is not accessible (this might be expected if DNS is not configured)"
    fi
    
    print_status "Testing health endpoint (prod)..."
    if curl -s -u admin:UltraRAG2025Secure https://ultrarag-mcp.webrobot.local/health >/dev/null; then
        print_status "✅ Prod health endpoint is accessible"
    else
        print_warning "❌ Prod health endpoint is not accessible (this might be expected if DNS is not configured)"
    fi
}

# Function to show access information
show_access_info() {
    print_header "Access Information"
    
    echo "🌐 Production URLs (with authentication):"
    echo "   Health: https://ultrarag-mcp.webrobot.local/health"
    echo "   Retriever: https://ultrarag-mcp.webrobot.local/retriever/mcp"
    echo "   Corpus: https://ultrarag-mcp.webrobot.local/corpus/mcp"
    echo "   Generation: https://ultrarag-mcp.webrobot.local/generation/mcp"
    echo ""
    echo "🔧 Development URLs (no authentication):"
    echo "   Health: https://ultrarag-mcp-dev.webrobot.local/health"
    echo "   Retriever: https://ultrarag-mcp-dev.webrobot.local/retriever/mcp"
    echo "   Corpus: https://ultrarag-mcp-dev.webrobot.local/corpus/mcp"
    echo "   Generation: https://ultrarag-mcp-dev.webrobot.local/generation/mcp"
    echo ""
    echo "🔐 Authentication (production only):"
    echo "   Username: admin"
    echo "   Password: UltraRAG2025Secure"
    echo ""
    echo "📋 Configuration file: ultrarag-mcp-config.json"
    echo "📖 Documentation: MCP_ACCESS_GUIDE.md"
}

# Function to show help
show_help() {
    echo "UltraRAG MCP Servers - Traefik Deployment Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  deploy     Deploy MCP services with Traefik Ingress"
    echo "  verify     Verify deployment status"
    echo "  test       Test endpoints accessibility"
    echo "  info       Show access information"
    echo "  help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 deploy                    # Deploy everything"
    echo "  $0 verify                    # Verify deployment"
    echo "  $0 test                      # Test endpoints"
    echo "  $0 info                      # Show access info"
}

# Main script logic
case "${1:-deploy}" in
    "deploy")
        check_kubectl
        check_cluster
        deploy_mcp_services
        verify_deployment
        test_endpoints
        show_access_info
        ;;
    "verify")
        check_kubectl
        check_cluster
        verify_deployment
        ;;
    "test")
        check_kubectl
        check_cluster
        test_endpoints
        ;;
    "info")
        show_access_info
        ;;
    "help"|*)
        show_help
        ;;
esac
