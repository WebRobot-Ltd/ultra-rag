# UltraRAG MCP Authentication - Development Guide

## 🚀 Quick Start

### 1. Setup Database Tunnel

```bash
# Start persistent database tunnel
./persistent-db-tunnel.sh start

# Check tunnel status
./persistent-db-tunnel.sh status

# Stop tunnel
./persistent-db-tunnel.sh stop
```

### 2. Configure Environment

```bash
# Copy example configuration
cp dev.env.example dev.env

# Edit with your values
nano dev.env
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Test Authentication

```bash
# Test with development API key
python test_real_api_key.py

# Test database connection
python test_database_connection.py
```

## 🔑 Development API Keys

### Default Development Key
- **Key**: `dev-api-key-12345`
- **Role**: `super_admin`
- **Scopes**: `read`, `write`, `admin`
- **Usage**: Automatically used when no real API key is found

### Create Real API Key

```bash
# Insert a test API key into database
python insert_test_api_key.py
```

This will create:
- Test user in `up_users` table
- Test role in `up_roles` table
- API key in `api_keys` table
- Proper relationships between them

## 🗄️ Database Schema

The module works with Strapi database schema:

- `up_users` - User accounts
- `up_roles` - User roles
- `up_users_role_links` - User-role relationships
- `api_keys` - API key storage
- `api_keys_owner_links` - API key-user relationships

## 🧪 Testing

### Test Scripts

1. **`test_database_connection.py`** - Test database connectivity
2. **`test_real_api_key.py`** - Test with real and dev API keys
3. **`insert_test_api_key.py`** - Create test API keys

### Test Commands

```bash
# Full test suite
export $(cat dev.env | xargs) && python test_real_api_key.py

# Database only
export $(cat dev.env | xargs) && python test_database_connection.py

# Create test data
export $(cat dev.env | xargs) && python insert_test_api_key.py
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_HOST` | PostgreSQL host | `localhost` |
| `DATABASE_PORT` | PostgreSQL port | `5432` |
| `DATABASE_NAME` | Database name | `strapi` |
| `DATABASE_USERNAME` | Database user | `strapi` |
| `DATABASE_PASSWORD` | Database password | `strapi` |
| `JWT_SECRET` | JWT signing secret | `change-me` |
| `DEV_API_KEY` | Development API key | `dev-api-key-12345` |
| `DEV_ROLE` | Development role | `super_admin` |

### Database Connection

The module supports both local and remote database connections:

- **Local**: Direct connection to PostgreSQL
- **Remote**: Via SSH tunnel (recommended for development)

## 🚨 Security Notes

### Development Mode
- Development API keys are automatically accepted
- No real database validation required
- Useful for local testing

### Production Mode
- All API keys must exist in database
- JWT tokens must be valid
- Proper role and scope validation

## 📝 Integration Examples

### Flask Integration

```python
from auth_middleware import AuthMiddleware
from config import get_database_config

# Initialize auth
config = get_database_config()
auth = AuthMiddleware(config)
await auth.initialize()

# Protect endpoint
@auth.require_auth(required_scopes={'read'})
async def protected_endpoint():
    user = auth.get_current_user()
    return {"message": f"Hello {user['username']}"}
```

### MCP Server Integration

```python
# In your MCP server
from auth_middleware import AuthMiddleware

# Add to your server initialization
auth_middleware = AuthMiddleware()
await auth_middleware.initialize()

# Use in request handlers
async def handle_request(request):
    headers = extract_headers(request)
    result = await auth_middleware.validate_request(headers)
    
    if not result['valid']:
        return {"error": result['error']}
    
    # Process authenticated request
    user_data = result['user_data']
    # ... your logic here
```

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check tunnel status: `./persistent-db-tunnel.sh status`
   - Verify credentials in `dev.env`
   - Test connection: `python test_database_connection.py`

2. **API Key Not Found**
   - Check if key exists: `python insert_test_api_key.py`
   - Verify key format: `key_id:secret`
   - Check database logs

3. **Permission Denied**
   - Verify user has required scopes
   - Check role assignments
   - Review API key permissions

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export LOG_AUTH_ATTEMPTS=true

# Run tests with debug info
python test_real_api_key.py
```

## 📚 Next Steps

1. **Integrate with MCP servers** - Add auth middleware to your servers
2. **Configure production** - Set up real API keys and JWT secrets
3. **Deploy to Kubernetes** - Use provided K8s configurations
4. **Monitor authentication** - Add logging and metrics

## 🤝 Contributing

When adding new features:

1. Update tests in `test_*.py`
2. Add documentation to `README.md`
3. Update `DEVELOPMENT.md` if needed
4. Test with both dev and real API keys
