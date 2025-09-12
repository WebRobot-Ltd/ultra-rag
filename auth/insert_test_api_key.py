#!/usr/bin/env python3
"""
Script to insert a test API key into the Strapi database
This creates a real API key for testing authentication
"""

import asyncio
import os
import sys
import hashlib
import secrets
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add auth module to path
auth_path = Path(__file__).parent
sys.path.insert(0, str(auth_path))

from database_client import DatabaseClient, DatabaseConfig
from config import get_database_config

async def generate_api_key():
    """Generate a new API key pair (key_id:secret)"""
    # Generate key_id (8 characters)
    key_id = secrets.token_urlsafe(6)
    
    # Generate secret (32 characters)
    secret = secrets.token_urlsafe(24)
    
    # Create full API key
    api_key = f"{key_id}:{secret}"
    
    # Hash the secret for storage
    secret_hash = hashlib.sha256(secret.encode()).hexdigest()
    
    return key_id, secret, api_key, secret_hash

async def create_test_user(db_client):
    """Create a test user if it doesn't exist"""
    print("🔍 Checking for test user...")
    
    # Check if test user exists
    test_user_query = """
        SELECT id, username, email FROM up_users 
        WHERE username = 'test-user' OR email = 'test@webrobot.eu'
        LIMIT 1
    """
    
    try:
        async with db_client.pool.acquire() as conn:
            existing_user = await conn.fetchrow(test_user_query)
            
            if existing_user:
                print(f"✅ Test user already exists: {existing_user['username']} (ID: {existing_user['id']})")
                return existing_user['id']
            
            # Create test user
            print("📝 Creating test user...")
            insert_user_query = """
                INSERT INTO up_users (username, email, password, confirmed, blocked, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
            """
            
            now = datetime.utcnow()
            user_id = await conn.fetchval(
                insert_user_query,
                'test-user',
                'test@webrobot.eu',
                'hashed-password-placeholder',  # In real scenario, this would be properly hashed
                True,  # confirmed
                False,  # not blocked
                now,
                now
            )
            
            print(f"✅ Test user created with ID: {user_id}")
            return user_id
            
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        return None

async def create_test_role(db_client):
    """Create a test role if it doesn't exist"""
    print("🔍 Checking for test role...")
    
    role_query = """
        SELECT id, name FROM up_roles 
        WHERE name = 'test_role'
        LIMIT 1
    """
    
    try:
        async with db_client.pool.acquire() as conn:
            existing_role = await conn.fetchrow(role_query)
            
            if existing_role:
                print(f"✅ Test role already exists: {existing_role['name']} (ID: {existing_role['id']})")
                return existing_role['id']
            
            # Create test role
            print("📝 Creating test role...")
            insert_role_query = """
                INSERT INTO up_roles (name, description, type, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """
            
            now = datetime.utcnow()
            role_id = await conn.fetchval(
                insert_role_query,
                'test_role',
                'Test role for API key authentication',
                'custom',
                now,
                now
            )
            
            print(f"✅ Test role created with ID: {role_id}")
            return role_id
            
    except Exception as e:
        print(f"❌ Error creating test role: {e}")
        return None

async def assign_role_to_user(db_client, user_id, role_id):
    """Assign role to user"""
    print("🔗 Assigning role to user...")
    
    # Check if role is already assigned
    check_query = """
        SELECT user_id FROM up_users_role_links 
        WHERE user_id = $1 AND role_id = $2
    """
    
    try:
        async with db_client.pool.acquire() as conn:
            existing = await conn.fetchrow(check_query, user_id, role_id)
            
            if existing:
                print("✅ Role already assigned to user")
                return True
            
            # Assign role
            assign_query = """
                INSERT INTO up_users_role_links (user_id, role_id, user_order)
                VALUES ($1, $2, $3)
            """
            
            await conn.execute(assign_query, user_id, role_id, 0)
            print("✅ Role assigned to user")
            return True
            
    except Exception as e:
        print(f"❌ Error assigning role: {e}")
        return False

async def insert_api_key(db_client, user_id, key_id, secret_hash):
    """Insert API key into database"""
    print("🔑 Inserting API key...")
    
    # Check if API key already exists
    check_query = """
        SELECT id FROM api_keys WHERE key_id = $1
    """
    
    try:
        async with db_client.pool.acquire() as conn:
            existing = await conn.fetchrow(check_query, key_id)
            
            if existing:
                print(f"⚠️ API key with key_id '{key_id}' already exists")
                return False
            
            # Insert API key
            insert_query = """
                INSERT INTO api_keys (
                    label, key_id, secret_hash, scopes, status, 
                    organization_id, expires_at, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id
            """
            
            now = datetime.utcnow()
            expires_at = now + timedelta(days=365)  # Expires in 1 year
            
            api_key_id = await conn.fetchval(
                insert_query,
                'Test API Key for UltraRAG MCP',
                key_id,
                secret_hash,
                json.dumps(['read', 'write', 'admin']),  # Scopes as JSON
                'active',
                'test-org-123',  # Organization ID
                expires_at,
                now,
                now
            )
            
            print(f"✅ API key inserted with ID: {api_key_id}")
            return api_key_id
            
    except Exception as e:
        print(f"❌ Error inserting API key: {e}")
        return False

async def link_api_key_to_user(db_client, api_key_id, user_id):
    """Link API key to user"""
    print("🔗 Linking API key to user...")
    
    try:
        async with db_client.pool.acquire() as conn:
            # Check if link already exists
            check_query = """
                SELECT api_key_id FROM api_keys_owner_links 
                WHERE api_key_id = $1 AND user_id = $2
            """
            
            existing = await conn.fetchrow(check_query, api_key_id, user_id)
            
            if existing:
                print("✅ API key already linked to user")
                return True
            
            # Create link
            link_query = """
                INSERT INTO api_keys_owner_links (api_key_id, user_id)
                VALUES ($1, $2)
            """
            
            await conn.execute(link_query, api_key_id, user_id)
            print("✅ API key linked to user")
            return True
            
    except Exception as e:
        print(f"❌ Error linking API key to user: {e}")
        return False

async def main():
    """Main function to create test API key"""
    print("🚀 Creating Test API Key for UltraRAG MCP Authentication\n")
    
    # Load database configuration
    config = get_database_config()
    print(f"Database: {config.host}:{config.port}/{config.database}")
    
    # Initialize database client
    db_client = DatabaseClient(config)
    
    try:
        await db_client.initialize()
        print("✅ Database connection established\n")
        
        # Generate API key
        print("🔑 Generating API key...")
        key_id, secret, api_key, secret_hash = await generate_api_key()
        print(f"Key ID: {key_id}")
        print(f"Secret: {secret}")
        print(f"Full API Key: {api_key}")
        print(f"Secret Hash: {secret_hash[:16]}...\n")
        
        # Create test user
        user_id = await create_test_user(db_client)
        if not user_id:
            print("❌ Failed to create test user")
            return
        
        # Create test role
        role_id = await create_test_role(db_client)
        if not role_id:
            print("❌ Failed to create test role")
            return
        
        # Assign role to user
        if not await assign_role_to_user(db_client, user_id, role_id):
            print("❌ Failed to assign role to user")
            return
        
        # Insert API key
        api_key_id = await insert_api_key(db_client, user_id, key_id, secret_hash)
        if not api_key_id:
            print("❌ Failed to insert API key")
            return
        
        # Link API key to user
        if not await link_api_key_to_user(db_client, api_key_id, user_id):
            print("❌ Failed to link API key to user")
            return
        
        print("\n🎉 Test API Key created successfully!")
        print("=" * 50)
        print(f"API Key: {api_key}")
        print(f"User ID: {user_id}")
        print(f"Role ID: {role_id}")
        print(f"API Key ID: {api_key_id}")
        print("=" * 50)
        print("\n📝 You can now test authentication with this API key:")
        print(f"curl -H 'X-API-Key: {api_key}' http://your-mcp-server/endpoint")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await db_client.close()

if __name__ == "__main__":
    asyncio.run(main())
