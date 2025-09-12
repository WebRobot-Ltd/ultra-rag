#!/usr/bin/env python3
"""
Test script to verify real API key authentication
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
from config import get_database_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_real_api_key():
    """Test authentication with real API key from database"""
    print("🔍 Testing Real API Key Authentication\n")
    
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
        
        # Test with real API key from database
        real_api_key = "JaFUZh9s:85oGQH1XQBE3b6qkCzt2Y__VMN786nMM"
        
        print(f"\n🔑 Testing with real API key: {real_api_key[:20]}...")
        
        headers = {
            "X-API-Key": real_api_key
        }
        
        result = await auth_middleware.validate_request(headers, required_scopes={"read"})
        
        if result['valid']:
            user_data = result['user_data']
            print(f"✅ Authentication successful!")
            print(f"   Username: {user_data.get('username', 'N/A')}")
            print(f"   Email: {user_data.get('email', 'N/A')}")
            print(f"   Role: {user_data.get('role', 'N/A')}")
            print(f"   Scopes: {user_data.get('scopes', [])}")
            print(f"   Auth method: {user_data.get('auth_method', 'unknown')}")
            print(f"   User ID: {user_data.get('user_id', 'N/A')}")
            print(f"   Organization ID: {user_data.get('organization_id', 'N/A')}")
            print(f"   Is Dev: {user_data.get('is_dev', False)}")
        else:
            print(f"❌ Authentication failed: {result['error']}")
        
        return result['valid']
        
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return False
    finally:
        await auth_middleware.close()

async def test_dev_api_key():
    """Test authentication with dev API key for comparison"""
    print("\n🔍 Testing Dev API Key Authentication\n")
    
    config = get_database_config()
    auth_middleware = AuthMiddleware(config)
    
    try:
        await auth_middleware.initialize()
        
        # Test with dev API key
        dev_api_key = "dev-api-key-12345"
        
        print(f"🔑 Testing with dev API key: {dev_api_key}")
        
        headers = {
            "X-API-Key": dev_api_key
        }
        
        result = await auth_middleware.validate_request(headers, required_scopes={"read"})
        
        if result['valid']:
            user_data = result['user_data']
            print(f"✅ Dev authentication successful!")
            print(f"   Username: {user_data.get('username', 'N/A')}")
            print(f"   Role: {user_data.get('role', 'N/A')}")
            print(f"   Scopes: {user_data.get('scopes', [])}")
            print(f"   Auth method: {user_data.get('auth_method', 'unknown')}")
            print(f"   Is Dev: {user_data.get('is_dev', False)}")
        else:
            print(f"❌ Dev authentication failed: {result['error']}")
        
        return result['valid']
        
    except Exception as e:
        print(f"❌ Dev authentication test failed: {e}")
        return False
    finally:
        await auth_middleware.close()

async def main():
    """Run all tests"""
    print("🚀 Starting Real API Key Authentication Tests\n")
    
    # Test real API key
    real_success = await test_real_api_key()
    
    # Test dev API key
    dev_success = await test_dev_api_key()
    
    print("\n" + "="*50)
    print("📊 Test Results Summary:")
    print(f"   Real API Key: {'✅ PASS' if real_success else '❌ FAIL'}")
    print(f"   Dev API Key:  {'✅ PASS' if dev_success else '❌ FAIL'}")
    print("="*50)
    
    if real_success and dev_success:
        print("\n🎉 All authentication tests passed!")
    else:
        print("\n⚠️ Some authentication tests failed.")

if __name__ == "__main__":
    asyncio.run(main())
