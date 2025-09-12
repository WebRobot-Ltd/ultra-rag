"""
Database client for authentication queries
Replicates Strapi database access patterns
"""

import os
import asyncio
import asyncpg
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Database configuration matching Strapi setup"""
    host: str
    port: int
    database: str
    username: str
    password: str
    ssl: bool = False
    schema: str = "public"

class DatabaseClient:
    """PostgreSQL client for authentication queries"""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or self._load_from_env()
        self.pool: Optional[asyncpg.Pool] = None
        
    def _load_from_env(self) -> DatabaseConfig:
        """Load database config from environment variables (Strapi style)"""
        return DatabaseConfig(
            host=os.getenv('DATABASE_HOST', 'localhost'),
            port=int(os.getenv('DATABASE_PORT', '5432')),
            database=os.getenv('DATABASE_NAME', 'strapi'),
            username=os.getenv('DATABASE_USERNAME', 'strapi'),
            password=os.getenv('DATABASE_PASSWORD', 'strapi'),
            ssl=os.getenv('DATABASE_SSL', 'false').lower() == 'true',
            schema=os.getenv('DATABASE_SCHEMA', 'public')
        )
    
    async def initialize(self):
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password,
                ssl=self.config.ssl,
                min_size=2,
                max_size=10
            )
            logger.info("Database connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID (Strapi structure)"""
        if not self.pool:
            raise RuntimeError("Database not initialized")
        
        query = """
        SELECT 
            u.id,
            u.username,
            u.email,
            u.password,
            u.provider,
            u.confirmed,
            u.blocked,
            u.created_at,
            u.updated_at
        FROM up_users u
        WHERE u.id = $1
        """
        
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, int(user_id))
                if row:
                    user_data = dict(row)
                    
                    # Get user roles
                    role_query = """
                        SELECT r.name as role_name, r.type as role_type
                        FROM up_users_role_links url
                        JOIN up_roles r ON url.role_id = r.id
                        WHERE url.user_id = $1
                    """
                    roles = await conn.fetch(role_query, int(user_id))
                    user_data['roles'] = [dict(role) for role in roles]
                    
                    # Get organization (if any) - check if table exists first
                    try:
                        org_query = """
                            SELECT o.id as organization_id, o.name as organization_name
                            FROM organizations o
                            WHERE o.owner_id = $1
                            LIMIT 1
                        """
                        org_row = await conn.fetchrow(org_query, int(user_id))
                        if org_row:
                            user_data['organization_id'] = org_row['organization_id']
                            user_data['organization_name'] = org_row['organization_name']
                    except Exception:
                        # Organizations table doesn't exist or user not in any organization
                        pass
                    
                    return user_data
                return None
        except Exception as e:
            logger.error(f"Error fetching user {user_id}: {e}")
            return None
    
    async def get_api_key_by_key_id(self, key_id: str) -> Optional[Dict[str, Any]]:
        """Get API key by key_id with validation (Strapi structure)"""
        if not self.pool:
            raise RuntimeError("Database not initialized")
        
        query = """
        SELECT 
            ak.id,
            ak.label,
            ak.key_id,
            ak.secret_hash,
            ak.scopes,
            ak.status,
            ak.organization_id,
            ak.expires_at,
            ak.last_used_at,
            ak.created_at,
            ak.updated_at
        FROM api_keys ak
        WHERE ak.key_id = $1 AND ak.status = 'active'
        """
        
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, key_id)
                if row:
                    api_key_data = dict(row)
                    
                    # Get owner information
                    owner_query = """
                        SELECT aol.user_id as owner_id
                        FROM api_keys_owner_links aol
                        WHERE aol.api_key_id = $1
                        LIMIT 1
                    """
                    owner_row = await conn.fetchrow(owner_query, api_key_data['id'])
                    if owner_row:
                        api_key_data['owner_id'] = owner_row['owner_id']
                    
                    return api_key_data
                return None
        except Exception as e:
            logger.error(f"Error fetching API key {key_id}: {e}")
            return None
    
    async def update_api_key_last_used(self, key_id: str):
        """Update last_used_at timestamp for API key"""
        if not self.pool:
            return
        
        query = """
        UPDATE api_keys 
        SET last_used_at = NOW() 
        WHERE key_id = $1
        """
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(query, key_id)
        except Exception as e:
            logger.error(f"Error updating API key last_used_at: {e}")
    
    async def get_user_scopes_by_role(self, role_name: str) -> List[str]:
        """Get default scopes for a role (Strapi structure)"""
        if not self.pool:
            return []
        
        # Default scopes based on role (matching Jersey logic)
        role_scopes = {
            'super_admin': ['read', 'write', 'admin', 'delete'],
            'admin': ['read', 'write', 'admin'],
            'developer': ['read', 'write'],
            'viewer': ['read'],
            'authenticated': ['read']
        }
        
        return role_scopes.get(role_name, ['read'])
    
    async def health_check(self) -> bool:
        """Check database connectivity"""
        if not self.pool:
            return False
        
        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
