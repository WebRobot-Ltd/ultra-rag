# UltraRAG MCP Authentication Integration

## Overview

This document describes the authentication integration implemented for UltraRAG MCP servers. The authentication system supports both API Key and JWT token validation.

## Features

- **API Key Authentication**: Validate requests using API keys stored in the database
- **JWT Token Authentication**: Validate requests using JWT tokens
- **Database Integration**: Connects to Strapi database for user validation
- **Configurable**: Can be enabled/disabled via environment variables
- **Per-Server**: Each MCP server can have authentication enabled independently

## Configuration

### Environment Variables

Set the following environment variables to configure authentication:

```bash
# Enable/disable authentication
ENABLE_AUTH=true

# Database connection
DATABASE_URL=postgresql://user:password@localhost:5432/strapi

# JWT secret for token validation
JWT_SECRET=your-secret-key

# API Key header name (optional)
API_KEY_HEADER=X-API-Key
```

### Configuration File

Copy `auth-config.env` to `.env` and modify the values:

```bash
cp auth-config.env .env
```

## Usage

### Starting Servers with Authentication

```bash
# Enable authentication
export ENABLE_AUTH=true
export DATABASE_URL=postgresql://user:password@localhost:5432/strapi
export JWT_SECRET=your-secret-key

# Start servers
python start_mcp_servers.py
```

### Making Authenticated Requests

#### Using API Key

```bash
curl -H "X-API-Key: your-api-key" \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}' \
     https://retriever-mcp-dev.metaglobe.finance/mcp
```

#### Using JWT Token

```bash
curl -H "Authorization: Bearer your-jwt-token" \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}' \
     https://retriever-mcp-dev.metaglobe.finance/mcp
```

## Server Integration

All MCP servers have been updated to support authentication:

- **retriever**: Search and retrieval operations
- **generation**: Text generation operations
- **corpus**: Document processing
- **benchmark**: Performance testing
- **custom**: Custom operations
- **evaluation**: Model evaluation
- **prompt**: Prompt management
- **reranker**: Result reranking
- **router**: Request routing
- **sayhello**: Health check

## Authentication Flow

1. **Request Received**: Server receives HTTP request
2. **Header Extraction**: Extracts API key or JWT token from headers
3. **Validation**: Validates credentials against database
4. **Authorization**: Grants or denies access based on validation result
5. **Response**: Returns appropriate response or error

## Error Handling

### Unauthorized Access

```json
{
  "error": "Unauthorized",
  "message": "Authentication required. Please provide a valid API key or JWT token."
}
```

### Invalid Credentials

```json
{
  "error": "Forbidden",
  "message": "Invalid API key or JWT token provided."
}
```

## Testing

### Test Authentication Module

```bash
cd auth
python test_auth_module.py
```

### Test with Real API Key

```bash
cd auth
python test_real_api_key.py
```

### Test Database Connection

```bash
cd auth
python test_database_connection.py
```

## Security Considerations

1. **Environment Variables**: Store sensitive configuration in environment variables
2. **JWT Secret**: Use a strong, unique JWT secret in production
3. **Database Security**: Ensure database connection is secure
4. **API Key Management**: Implement proper API key rotation and revocation
5. **Logging**: Monitor authentication attempts and failures

## Troubleshooting

### Common Issues

1. **Authentication Not Working**: Check `ENABLE_AUTH` environment variable
2. **Database Connection Failed**: Verify `DATABASE_URL` configuration
3. **Invalid API Key**: Check API key in database and request headers
4. **JWT Validation Failed**: Verify JWT secret and token format

### Debug Mode

Enable debug logging:

```bash
export AUTH_LOG_LEVEL=DEBUG
```

## Migration from Non-Authenticated

To migrate from non-authenticated to authenticated servers:

1. **Backup Configuration**: Backup existing server configurations
2. **Set Environment Variables**: Configure authentication environment variables
3. **Test Authentication**: Test with a single server first
4. **Deploy Gradually**: Enable authentication for servers one by one
5. **Monitor**: Monitor logs for authentication issues

## Support

For issues or questions regarding authentication integration:

1. Check the logs for error messages
2. Verify environment variable configuration
3. Test database connectivity
4. Review API key and JWT token format
