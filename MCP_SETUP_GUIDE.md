# UltraRAG MCP Servers - Setup Guide

## Overview
This guide explains how to set up and deploy the UltraRAG MCP (Model Context Protocol) servers on Kubernetes with proper authentication.

## Files Structure

- `k8s-mcp-auth-secret.yaml` - Basic Auth secret (contains placeholder credentials)
- `k8s-mcp-middleware.yaml` - Traefik middleware for CORS and authentication
- `k8s-mcp-ingress-dev.yaml` - Development ingress (no authentication)
- `k8s-mcp-ingress-prod.yaml` - Production ingress (with authentication)
- `MCP_ENDPOINTS_GUIDE.md` - Complete endpoints documentation

## Security Setup

### 1. Generate Authentication Credentials

Before deploying to production, you must generate secure credentials:

```bash
# Generate password hash for admin user
htpasswd -nbB admin YOUR_SECURE_PASSWORD

# Example output:
# admin:$2y$05$AXuNtguRKG7rgtEztsb//OLOjYvJGI1CY4jvs8BhvVkS3ae1uznV.
```

### 2. Update Secret File

Edit `k8s-mcp-auth-secret.yaml` and replace the placeholder:

```yaml
stringData:
  users: |
    admin:YOUR_GENERATED_HASH_HERE
```

### 3. Deploy Secret

```bash
kubectl apply -f k8s-mcp-auth-secret.yaml
```

## Deployment

### Development Environment
```bash
# Deploy middleware and development ingress (no auth)
kubectl apply -f k8s-mcp-middleware.yaml
kubectl apply -f k8s-mcp-ingress-dev.yaml
```

### Production Environment
```bash
# Deploy middleware, secret, and production ingress (with auth)
kubectl apply -f k8s-mcp-middleware.yaml
kubectl apply -f k8s-mcp-auth-secret.yaml  # After updating credentials
kubectl apply -f k8s-mcp-ingress-prod.yaml
```

## Jenkins Integration

The Jenkins pipeline automatically deploys:
- Middleware (CORS)
- Development ingress (no auth)
- Production ingress (with auth) - only for non-dev builds

**Important**: The auth secret is NOT deployed automatically for security reasons. You must configure it manually before production use.

## Available Endpoints

### Development (No Authentication)
- `https://retriever-mcp-dev.metaglobe.finance/mcp`
- `https://generation-mcp-dev.metaglobe.finance/mcp`
- `https://corpus-mcp-dev.metaglobe.finance/mcp`
- `https://reranker-mcp-dev.metaglobe.finance/mcp`
- `https://evaluation-mcp-dev.metaglobe.finance/mcp`
- `https://benchmark-mcp-dev.metaglobe.finance/mcp`
- `https://custom-mcp-dev.metaglobe.finance/mcp`
- `https://prompt-mcp-dev.metaglobe.finance/mcp`
- `https://router-mcp-dev.metaglobe.finance/mcp`

### Production (Basic Auth Required)
- `https://retriever-mcp.metaglobe.finance/mcp`
- `https://generation-mcp.metaglobe.finance/mcp`
- `https://corpus-mcp.metaglobe.finance/mcp`
- `https://reranker-mcp.metaglobe.finance/mcp`
- `https://evaluation-mcp.metaglobe.finance/mcp`
- `https://benchmark-mcp.metaglobe.finance/mcp`
- `https://custom-mcp.metaglobe.finance/mcp`
- `https://prompt-mcp.metaglobe.finance/mcp`
- `https://router-mcp.metaglobe.finance/mcp`

## Testing

### Test Development Endpoint
```bash
curl -X POST https://retriever-mcp-dev.metaglobe.finance/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"initialize","id":1,"params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test-client","version":"1.0.0"}}}'
```

### Test Production Endpoint
```bash
curl -X POST https://retriever-mcp.metaglobe.finance/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -u admin:YOUR_PASSWORD \
  -d '{"jsonrpc":"2.0","method":"initialize","id":1,"params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test-client","version":"1.0.0"}}}'
```

## Security Notes

- **Never commit real credentials to the repository**
- **Use strong passwords for production**
- **Rotate credentials regularly**
- **Monitor access logs**
- **Use HTTPS only in production**

## Troubleshooting

### 401 Unauthorized
- Check if the auth secret is deployed: `kubectl get secret ultrarag-mcp-basic-auth`
- Verify credentials are correct
- Ensure production ingress is using the auth middleware

### 404 Not Found
- Check if ingress is deployed: `kubectl get ingress | grep mcp`
- Verify DNS resolution
- Check Traefik logs: `kubectl logs -n kube-system deployment/traefik`

### CORS Issues
- Verify CORS middleware is deployed
- Check browser developer tools for CORS errors
- Ensure proper headers are sent
