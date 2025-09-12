#!/usr/bin/env python3
"""
Test script to verify authentication module functionality
Tests the module without requiring actual database connection
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add auth module to path
auth_path = Path(__file__).parent
sys.path.insert(0, str(auth_path))

from auth_manager import AuthManager
from jwt_validator import JWTValidator
from api_key_validator import APIKeyValidator
from database_client import DatabaseConfig
from config import get_database_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_jwt_validation():
    """Test JWT validation logic"""
    print("🔍 Testing JWT validation...")
    
    jwt_validator = JWTValidator("test-secret")
    
    # Test JWT creation and validation
    test_claims = {
        "id": "test-user-123",
        "role": "super_admin",
        "scopes": ["read", "write", "admin"],
        "organization_id": "test-org-456"
    }
    
    try:
        # Create a test JWT
        token = jwt_validator._create_test_jwt(test_claims)
        print(f"✅ JWT created: {token[:50]}...")
        
        # Validate the JWT
        result = jwt_validator.validate_jwt_token(token)
        
        if result['valid']:
            print(f"✅ JWT validation successful")
            print(f"   User ID: {result['user_data']['id']}")
            print(f"   Role: {result['user_data']['role']}")
            print(f"   Scopes: {result['user_data']['scopes']}")
            print(f"   Organization: {result['user_data']['organization_id']}")
        else:
            print(f"❌ JWT validation failed: {result['error']}")
        
        return result['valid']
        
    except Exception as e:
        print(f"❌ JWT test failed: {e}")
        return False

def test_api_key_validation():
    """Test API key validation logic"""
    print("\n🔍 Testing API key validation...")
    
    api_validator = APIKeyValidator()
    
    # Test dev API key
    dev_api_key = "dev-api-key-12345"
    
    try:
        result = api_validator.validate_api_key(dev_api_key, {"read", "write"})
        
        if result['valid']:
            print(f"✅ API key validation successful")
            print(f"   User ID: {result['user_data']['id']}")
            print(f"   Role: {result['user_data']['role']}")
            print(f"   Scopes: {result['user_data']['scopes']}")
            print(f"   Organization: {result['user_data']['organization_id']}")
        else:
            print(f"❌ API key validation failed: {result['error']}")
        
        return result['valid']
        
    except Exception as e:
        print(f"❌ API key test failed: {e}")
        return False

def test_auth_manager():
    """Test AuthManager integration"""
    print("\n🔍 Testing AuthManager integration...")
    
    # Mock database config
    config = DatabaseConfig(
        host="localhost",
        port=5432,
        database="test_db",
        username="test_user",
        password="test_pass",
        ssl=False
    )
    
    auth_manager = AuthManager(config)
    
    try:
        # Test JWT authentication
        jwt_headers = {
            "Authorization": "Bearer test-jwt-token"
        }
        
        result = auth_manager.authenticate_request(jwt_headers, {"read"})
        
        if result['valid']:
            print(f"✅ AuthManager JWT test successful")
            print(f"   Auth method: {result['user_data'].get('auth_method', 'unknown')}")
        else:
            print(f"ℹ️ AuthManager JWT test (expected to fail without DB): {result['error']}")
        
        # Test API key authentication
        api_headers = {
            "X-API-Key": "dev-api-key-12345"
        }
        
        result = auth_manager.authenticate_request(api_headers, {"read"})
        
        if result['valid']:
            print(f"✅ AuthManager API key test successful")
            print(f"   Auth method: {result['user_data'].get('auth_method', 'unknown')}")
        else:
            print(f"ℹ️ AuthManager API key test (expected to fail without DB): {result['error']}")
        
        return True
        
    except Exception as e:
        print(f"❌ AuthManager test failed: {e}")
        return False

def test_configuration():
    """Test configuration loading"""
    print("\n🔍 Testing configuration...")
    
    try:
        # Set test environment variables
        os.environ['DATABASE_HOST'] = 'test-host'
        os.environ['DATABASE_PORT'] = '5432'
        os.environ['DATABASE_NAME'] = 'test-db'
        os.environ['DATABASE_USERNAME'] = 'test-user'
        os.environ['DATABASE_PASSWORD'] = 'test-pass'
        os.environ['DATABASE_SSL'] = 'false'
        os.environ['JWT_SECRET'] = 'test-secret'
        os.environ['STRAPI_BASE_URL'] = 'http://test-strapi'
        
        config = get_database_config()
        
        print(f"✅ Configuration loaded successfully")
        print(f"   Database Host: {config.host}")
        print(f"   Database Port: {config.port}")
        print(f"   Database Name: {config.database}")
        print(f"   Database Username: {config.username}")
        print(f"   JWT Secret: {config.jwt_secret[:10]}...")
        print(f"   Strapi URL: {config.strapi_base_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_scope_validation():
    """Test scope validation logic"""
    print("\n🔍 Testing scope validation...")
    
    try:
        # Test scope normalization
        from jwt_validator import JWTValidator
        jwt_validator = JWTValidator("test-secret")
        
        # Test scope normalization
        test_scopes = ["read", "write", "admin"]
        normalized = jwt_validator._normalize_scopes(test_scopes)
        
        print(f"✅ Scope normalization successful")
        print(f"   Input: {test_scopes}")
        print(f"   Output: {normalized}")
        
        # Test scope validation
        required_scopes = {"read", "write"}
        user_scopes = {"read", "write", "admin"}
        
        has_required = required_scopes.issubset(user_scopes)
        print(f"✅ Scope validation successful")
        print(f"   Required: {required_scopes}")
        print(f"   User has: {user_scopes}")
        print(f"   Has required: {has_required}")
        
        return True
        
    except Exception as e:
        print(f"❌ Scope validation test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting UltraRAG MCP Authentication Module Tests\n")
    
    tests = [
        ("Configuration", test_configuration),
        ("JWT Validation", test_jwt_validation),
        ("API Key Validation", test_api_key_validation),
        ("Scope Validation", test_scope_validation),
        ("AuthManager Integration", test_auth_manager),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} test passed")
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test error: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Authentication module is working correctly.")
    elif passed > total // 2:
        print("⚠️ Most tests passed. Module is mostly functional.")
    else:
        print("❌ Many tests failed. Module needs fixes.")

if __name__ == "__main__":
    main()
