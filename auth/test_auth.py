#!/usr/bin/env python3
"""
Test script for UltraRAG MCP Authentication
Tests JWT and API Key authentication
"""

import asyncio
import os
import sys
from pathlib import Path

# Add auth module to path
auth_path = Path(__file__).parent
sys.path.insert(0, str(auth_path))

from auth_middleware import AuthMiddleware
from database_client import DatabaseConfig
from jwt_validator import JWTValidator
from api_key_validator import APIKeyValidator
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_database_connection():
    """Test database connection"""
    print("🔍 Testing database connection...")
    
    config = DatabaseConfig(
        host=os.getenv('DATABASE_HOST', 'localhost'),
        port=int(os.getenv('DATABASE_PORT', '5432')),
        database=os.getenv('DATABASE_NAME', 'strapi'),
        username=os.getenv('DATABASE_USERNAME', 'strapi'),
        password=os.getenv('DATABASE_PASSWORD', 'strapi'),
        ssl=os.getenv('DATABASE_SSL', 'false').lower() == 'true'
    )
    
    auth_middleware = AuthMiddleware(config)
    
    try:
        await auth_middleware.initialize()
        health = await auth_middleware.health_check()
        
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

async def test_jwt_validation():
    """Test JWT validation"""
    print("\n🔍 Testing JWT validation...")
    
    jwt_validator = JWTValidator()
    
    # Test with invalid token
    invalid_token = "invalid.jwt.token"
    result = jwt_validator.validate_token(invalid_token)
    if result is None:
        print("✅ Invalid JWT correctly rejected")
    else:
        print("❌ Invalid JWT should have been rejected")
    
    # Test with expired token
    expired_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6MSwiZXhwIjoxNjAwMDAwMDAwfQ.invalid"
    result = jwt_validator.validate_token(expired_token)
    if result is None:
        print("✅ Expired JWT correctly rejected")
    else:
        print("❌ Expired JWT should have been rejected")
    
    print("✅ JWT validation tests completed")

async def test_api_key_validation():
    """Test API Key validation"""
    print("\n🔍 Testing API Key validation...")
    
    api_key_validator = APIKeyValidator()
    
    # Test dev API key
    dev_key = os.getenv('DEV_API_KEY', 'dev-api-key-12345')
    result = api_key_validator.validate_api_key(dev_key, None)
    
    if result and result.get('is_dev'):
        print("✅ Dev API key validation successful")
    else:
        print("❌ Dev API key validation failed")
    
    # Test invalid API key
    invalid_key = "invalid:key"
    result = api_key_validator.validate_api_key(invalid_key, None)
    
    if result is None:
        print("✅ Invalid API key correctly rejected")
    else:
        print("❌ Invalid API key should have been rejected")
    
    print("✅ API Key validation tests completed")

async def test_authentication_flow():
    """Test complete authentication flow"""
    print("\n🔍 Testing complete authentication flow...")
    
    config = DatabaseConfig(
        host=os.getenv('DATABASE_HOST', 'localhost'),
        port=int(os.getenv('DATABASE_PORT', '5432')),
        database=os.getenv('DATABASE_NAME', 'strapi'),
        username=os.getenv('DATABASE_USERNAME', 'strapi'),
        password=os.getenv('DATABASE_PASSWORD', 'strapi'),
        ssl=os.getenv('DATABASE_SSL', 'false').lower() == 'true'
    )
    
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
        
        # Test with invalid headers
        invalid_headers = {
            "X-API-Key": "invalid:key"
        }
        
        result = await auth_middleware.validate_request(invalid_headers, required_scopes={"read"})
        
        if not result['valid']:
            print("✅ Invalid authentication correctly rejected")
        else:
            print("❌ Invalid authentication should have been rejected")
        
    except Exception as e:
        print(f"❌ Authentication flow test failed: {e}")
    finally:
        await auth_middleware.close()

async def test_permissions():
    """Test permission checking"""
    print("\n🔍 Testing permission checking...")
    
    config = DatabaseConfig(
        host=os.getenv('DATABASE_HOST', 'localhost'),
        port=int(os.getenv('DATABASE_PORT', '5432')),
        database=os.getenv('DATABASE_NAME', 'strapi'),
        username=os.getenv('DATABASE_USERNAME', 'strapi'),
        password=os.getenv('DATABASE_PASSWORD', 'strapi'),
        ssl=os.getenv('DATABASE_SSL', 'false').lower() == 'true'
    )
    
    auth_middleware = AuthMiddleware(config)
    
    try:
        await auth_middleware.initialize()
        
        # Test with dev API key (should have admin scopes)
        headers = {
            "X-API-Key": os.getenv('DEV_API_KEY', 'dev-api-key-12345')
        }
        
        result = await auth_middleware.validate_request(headers)
        
        if result['valid']:
            user_data = result['user_data']
            
            # Test scope checking
            has_read = auth_middleware.check_permissions(user_data, {"read"})
            has_write = auth_middleware.check_permissions(user_data, {"write"})
            has_admin = auth_middleware.check_permissions(user_data, {"admin"})
            
            print(f"✅ Scope checking:")
            print(f"   Has read: {has_read}")
            print(f"   Has write: {has_write}")
            print(f"   Has admin: {has_admin}")
            
            # Test role checking
            is_admin = auth_middleware.check_role(user_data, {"admin", "super_admin"})
            is_developer = auth_middleware.check_role(user_data, {"developer"})
            
            print(f"✅ Role checking:")
            print(f"   Is admin: {is_admin}")
            print(f"   Is developer: {is_developer}")
            
        else:
            print(f"❌ Permission test failed: {result['error']}")
        
    except Exception as e:
        print(f"❌ Permission test failed: {e}")
    finally:
        await auth_middleware.close()

async def main():
    """Run all tests"""
    print("🚀 Starting UltraRAG MCP Authentication Tests\n")
    
    # Test database connection
    db_ok = await test_database_connection()
    
    if not db_ok:
        print("\n❌ Database connection failed. Please check your configuration.")
        print("   Make sure PostgreSQL is running and accessible.")
        print("   Check your DATABASE_* environment variables.")
        return
    
    # Test JWT validation
    await test_jwt_validation()
    
    # Test API Key validation
    await test_api_key_validation()
    
    # Test complete authentication flow
    await test_authentication_flow()
    
    # Test permissions
    await test_permissions()
    
    print("\n🎉 All tests completed!")
    print("\n📝 Next steps:")
    print("   1. Configure your .env file with actual database credentials")
    print("   2. Test with real JWT tokens from Strapi")
    print("   3. Test with real API keys from your database")
    print("   4. Integrate with your MCP servers")

if __name__ == "__main__":
    asyncio.run(main())
