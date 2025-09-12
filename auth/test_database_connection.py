#!/usr/bin/env python3
"""
Test script to verify database connection and authentication module
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add auth module to path
auth_path = Path(__file__).parent
sys.path.insert(0, str(auth_path))

from auth_middleware import AuthMiddleware
from database_client import DatabaseConfig
from config import get_database_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_database_connection():
    """Test database connection with actual credentials"""
    print("🔍 Testing database connection...")
    
    # Load configuration from environment
    config = get_database_config()
    
    print(f"Database Host: {config.host}")
    print(f"Database Port: {config.port}")
    print(f"Database Name: {config.database}")
    print(f"Database Username: {config.username}")
    print(f"Database SSL: {config.ssl}")
    
    auth_middleware = AuthMiddleware(config)
    
    try:
        await auth_middleware.initialize()
        # Test basic database connectivity
        try:
            # Try to get a simple query result using the database client
            result = await auth_middleware.auth_manager.db_client.pool.fetchval("SELECT 1")
            health = result == 1
        except Exception as e:
            print(f"Health check failed: {e}")
            health = False
        
        if health:
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database health check failed")
            return False
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    finally:
        await auth_middleware.close()

async def test_strapi_tables():
    """Test if Strapi tables exist"""
    print("\n🔍 Testing Strapi tables...")
    
    config = get_database_config()
    auth_middleware = AuthMiddleware(config)
    
    try:
        await auth_middleware.initialize()
        
        # Test up_users table
        try:
            user_data = await auth_middleware.auth_manager.db_client.get_user_by_id("1")
            if user_data:
                print("✅ up_users table accessible")
                print(f"   Sample user: {user_data.get('username', 'N/A')}")
            else:
                print("ℹ️ up_users table accessible (no users found)")
        except Exception as e:
            print(f"❌ up_users table error: {e}")
        
        # Test api_keys table
        try:
            api_key_data = await auth_middleware.auth_manager.db_client.get_api_key_by_key_id("test-key")
            if api_key_data:
                print("✅ api_keys table accessible")
                print(f"   Sample API key: {api_key_data.get('key_id', 'N/A')}")
            else:
                print("ℹ️ api_keys table accessible (no API keys found)")
        except Exception as e:
            print(f"❌ api_keys table error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Table test failed: {e}")
        return False
    finally:
        await auth_middleware.close()

async def test_authentication_flow():
    """Test complete authentication flow"""
    print("\n🔍 Testing authentication flow...")
    
    config = get_database_config()
    auth_middleware = AuthMiddleware(config)
    
    try:
        await auth_middleware.initialize()
        
        # Test with dev API key
        headers = {
            "X-API-Key": os.getenv('DEV_API_KEY', 'dev-api-key-12345')
        }
        
        result = await auth_middleware.validate_request(headers, required_scopes={"read"})
        
        if result['valid']:
            user_data = result['user_data']
            print(f"✅ Authentication successful: {user_data['username']} ({user_data['role']})")
            print(f"   Scopes: {user_data.get('scopes', [])}")
            print(f"   Auth method: {user_data.get('auth_method', 'unknown')}")
        else:
            print(f"❌ Authentication failed: {result['error']}")
        
        return result['valid']
        
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return False
    finally:
        await auth_middleware.close()

async def main():
    """Run all tests"""
    print("🚀 Starting UltraRAG MCP Authentication Database Tests\n")
    
    # Test database connection
    db_ok = await test_database_connection()
    
    if not db_ok:
        print("\n❌ Database connection failed. Please check your configuration.")
        return
    
    # Test Strapi tables
    tables_ok = await test_strapi_tables()
    
    if not tables_ok:
        print("\n❌ Strapi tables test failed.")
        return
    
    # Test authentication flow
    auth_ok = await test_authentication_flow()
    
    if auth_ok:
        print("\n🎉 All tests passed! Authentication module is ready.")
    else:
        print("\n⚠️ Authentication test failed, but database connection works.")

if __name__ == "__main__":
    asyncio.run(main())
