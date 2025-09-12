"""
Configuration for MCP authentication
Environment variables and default settings
"""

import os
from typing import Optional
from dataclasses import dataclass

@dataclass
class AuthConfig:
    """Authentication configuration"""
    
    # Database configuration (matching Strapi)
    database_host: str = os.getenv('DATABASE_HOST', 'localhost')
    database_port: int = int(os.getenv('DATABASE_PORT', '5432'))
    database_name: str = os.getenv('DATABASE_NAME', 'strapi')
    database_username: str = os.getenv('DATABASE_USERNAME', 'strapi')
    database_password: str = os.getenv('DATABASE_PASSWORD', 'strapi')
    database_ssl: bool = os.getenv('DATABASE_SSL', 'false').lower() == 'true'
    database_schema: str = os.getenv('DATABASE_SCHEMA', 'public')
    
    # JWT configuration
    jwt_secret: str = os.getenv('JWT_SECRET', 'dev-secret-change-me')
    
    # Strapi configuration
    strapi_base_url: str = os.getenv('STRAPI_BASE_URL', 'http://localhost:1337')
    internal_token: str = os.getenv('INTERNAL_TOKEN', 'change-me-internal')
    
    # API Key configuration
    api_key_header_name: str = os.getenv('API_KEY_HEADER_NAME', 'X-API-Key')
    
    # Development credentials
    dev_api_key: str = os.getenv('DEV_API_KEY', 'dev-api-key-12345')
    dev_user_id: str = os.getenv('DEV_USER_ID', 'dev-user')
    dev_role: str = os.getenv('DEV_ROLE', 'super_admin')
    dev_org_id: str = os.getenv('DEV_ORG_ID', 'dev-org')
    dev_scopes: str = os.getenv('DEV_SCOPES', 'read,write,admin')
    
    # Security settings
    require_https: bool = os.getenv('REQUIRE_HTTPS', 'false').lower() == 'true'
    token_expiry_hours: int = int(os.getenv('TOKEN_EXPIRY_HOURS', '24'))
    
    # Logging
    log_level: str = os.getenv('LOG_LEVEL', 'INFO')
    log_auth_attempts: bool = os.getenv('LOG_AUTH_ATTEMPTS', 'true').lower() == 'true'

# Global configuration instance
config = AuthConfig()

def get_database_config():
    """Get database configuration for DatabaseClient"""
    from database_client import DatabaseConfig
    
    return DatabaseConfig(
        host=config.database_host,
        port=config.database_port,
        database=config.database_name,
        username=config.database_username,
        password=config.database_password,
        ssl=config.database_ssl,
        schema=config.database_schema
    )
