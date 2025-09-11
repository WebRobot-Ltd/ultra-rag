# UltraRAG MCP Servers - Endpoints Guide

## Overview
All UltraRAG MCP servers are now accessible via dedicated HTTPS subdomains on `metaglobe.finance`. Each server has its own subdomain and responds to JSON-RPC requests on the `/mcp` endpoint.

## Available MCP Servers

### 1. Retriever MCP Server
- **URL (Dev)**: `https://retriever-mcp-dev.metaglobe.finance/mcp` (No Auth)
- **URL (Prod)**: `https://retriever-mcp.metaglobe.finance/mcp` (Basic Auth Required)
- **Port**: 8002
- **Purpose**: Document retrieval and search using Milvus vector database
- **Key Features**: 
  - Semantic search
  - Document indexing
  - Vector similarity search
  - Milvus integration (primary database)

### 2. Generation MCP Server
- **URL (Dev)**: `https://generation-mcp-dev.metaglobe.finance/mcp` (No Auth)
- **URL (Prod)**: `https://generation-mcp.metaglobe.finance/mcp` (Basic Auth Required)
- **Port**: 8003
- **Purpose**: Text generation and content creation

### 3. Corpus MCP Server
- **URL (Dev)**: `https://corpus-mcp-dev.metaglobe.finance/mcp` (No Auth)
- **URL (Prod)**: `https://corpus-mcp.metaglobe.finance/mcp` (Basic Auth Required)
- **Port**: 8004
- **Purpose**: Corpus management and document processing

### 4. Reranker MCP Server
- **URL (Dev)**: `https://reranker-mcp-dev.metaglobe.finance/mcp` (No Auth)
- **URL (Prod)**: `https://reranker-mcp.metaglobe.finance/mcp` (Basic Auth Required)
- **Port**: 8005
- **Purpose**: Result reranking and relevance scoring

### 5. Evaluation MCP Server
- **URL (Dev)**: `https://evaluation-mcp-dev.metaglobe.finance/mcp` (No Auth)
- **URL (Prod)**: `https://evaluation-mcp.metaglobe.finance/mcp` (Basic Auth Required)
- **Port**: 8006
- **Purpose**: Performance evaluation and metrics

### 6. Benchmark MCP Server
- **URL (Dev)**: `https://benchmark-mcp-dev.metaglobe.finance/mcp` (No Auth)
- **URL (Prod)**: `https://benchmark-mcp.metaglobe.finance/mcp` (Basic Auth Required)
- **Port**: 8007
- **Purpose**: Benchmarking and performance testing

### 7. Custom MCP Server
- **URL (Dev)**: `https://custom-mcp-dev.metaglobe.finance/mcp` (No Auth)
- **URL (Prod)**: `https://custom-mcp.metaglobe.finance/mcp` (Basic Auth Required)
- **Port**: 8008
- **Purpose**: Custom operations and extensions

### 8. Prompt MCP Server
- **URL (Dev)**: `https://prompt-mcp-dev.metaglobe.finance/mcp` (No Auth)
- **URL (Prod)**: `https://prompt-mcp.metaglobe.finance/mcp` (Basic Auth Required)
- **Port**: 8009
- **Purpose**: Prompt management and optimization

### 9. Router MCP Server
- **URL (Dev)**: `https://router-mcp-dev.metaglobe.finance/mcp` (No Auth)
- **URL (Prod)**: `https://router-mcp.metaglobe.finance/mcp` (Basic Auth Required)
- **Port**: 8010
- **Purpose**: Request routing and load balancing

## Usage Examples

### Initialize Connection (Development - No Auth)
```bash
curl -X POST https://retriever-mcp-dev.metaglobe.finance/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "method": "initialize",
    "id": 1,
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {
        "name": "my-client",
        "version": "1.0.0"
      }
    }
  }'
```

### Initialize Connection (Production - With Auth)
```bash
curl -X POST https://retriever-mcp.metaglobe.finance/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -u admin:WebRobot2025Secure \
  -d '{
    "jsonrpc": "2.0",
    "method": "initialize",
    "id": 1,
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {
        "name": "my-client",
        "version": "1.0.0"
      }
    }
  }'
```

### List Available Tools (Production)
```bash
curl -X POST https://retriever-mcp.metaglobe.finance/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -u admin:WebRobot2025Secure \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": 1
  }'
```

## Architecture

```
Client HTTPS → Caddy (65.109.165.204:443) → Traefik LoadBalancer (porta 80) → MCP Pod (porta specifica)
```

- **Caddy**: Handles TLS termination and HTTPS redirects
- **Traefik**: Routes requests to appropriate MCP servers based on subdomain
- **Kubernetes**: Manages MCP server pods and services
- **Supervisor**: Manages multiple MCP server processes within each pod

## Security

- All endpoints use HTTPS with valid TLS certificates
- CORS is enabled for cross-origin requests
- **Development endpoints** (`-dev` subdomains): No authentication required
- **Production endpoints** (without `-dev`): Basic Auth required (admin:WebRobot2025Secure)
- All production endpoints are protected and require credentials

## Monitoring

- All MCP servers are managed by Supervisor
- Logs are available via `kubectl logs`
- Health checks available on each server
- Kubernetes provides automatic restart and failover

## Development vs Production

- **Development**: All endpoints use `-dev` suffix (e.g., `retriever-mcp-dev.metaglobe.finance`)
- **Production**: Can be configured with production subdomains (e.g., `retriever-mcp.metaglobe.finance`)
- **Authentication**: Development endpoints are open, production can require Basic Auth

## Integration

These MCP servers can be integrated with any application that supports the Model Context Protocol (MCP), including:
- Claude Desktop
- Custom AI applications
- RAG systems
- Document processing pipelines
