"""
Main authentication manager for MCP servers
Orchestrates JWT and API Key validation
"""

import os
from typing import Optional, Dict, Any, Set
import logging

from jwt_validator import JWTValidator
from api_key_validator import APIKeyValidator
from database_client import DatabaseClient, DatabaseConfig

logger = logging.getLogger(__name__)

class AuthManager:
    """
    Main authentication manager
    Replicates Jersey authentication flow with priority: JWT > API Key
    """
    
    def __init__(self, db_config: Optional[DatabaseConfig] = None):
        self.jwt_validator = JWTValidator()
        self.api_key_validator = APIKeyValidator()
        self.db_client = DatabaseClient(db_config)
        self._initialized = False
    
    async def initialize(self):
        """Initialize database connection"""
        if not self._initialized:
            await self.db_client.initialize()
            self._initialized = True
            logger.info("AuthManager initialized")
    
    async def close(self):
        """Close database connection"""
        if self._initialized:
            await self.db_client.close()
            self._initialized = False
            logger.info("AuthManager closed")
    
    async def authenticate_request(self, headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Authenticate request using Jersey-style priority:
        1. JWT Bearer token
        2. API Key (X-API-Key or Authorization: ApiKey)
        3. None (unauthenticated)
        """
        if not self._initialized:
            await self.initialize()
        
        # Try JWT authentication first
        jwt_result = await self._try_jwt_auth(headers)
        if jwt_result:
            return jwt_result
        
        # Try API Key authentication
        api_key_result = await self._try_api_key_auth(headers)
        if api_key_result:
            return api_key_result
        
        # No authentication found
        return None
    
    async def _try_jwt_auth(self, headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Try JWT authentication"""
        auth_header = headers.get('authorization') or headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header[7:].strip()
        if not token:
            return None
        
        # Validate JWT token
        jwt_data = self.jwt_validator.validate_token(token)
        if not jwt_data:
            return None
        
        # Get additional user info from database
        user_data = await self.db_client.get_user_by_id(jwt_data['user_id'])
        if not user_data:
            logger.warning(f"JWT user not found in database: {jwt_data['user_id']}")
            return None
        
        # Merge JWT claims with database user data
        return {
            **jwt_data,
            'email': user_data.get('email') or jwt_data.get('email'),
            'username': user_data.get('username') or jwt_data.get('username'),
            'confirmed': user_data.get('confirmed', True),
            'blocked': user_data.get('blocked', False),
            'auth_method': 'jwt'
        }
    
    async def _try_api_key_auth(self, headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Try API Key authentication"""
        # Check X-API-Key header
        api_key = headers.get('X-API-Key')
        
        # Check Authorization: ApiKey header
        if not api_key:
            auth_header = headers.get('authorization') or headers.get('Authorization')
            if auth_header and auth_header.startswith('ApiKey '):
                api_key = auth_header[7:].strip()
        
        if not api_key:
            return None
        
        # Validate API key
        api_key_data = await self.api_key_validator.validate_api_key(api_key, self.db_client)
        if not api_key_data:
            return None
        
        # Get user data if we have owner_id
        user_data = None
        if api_key_data.get('owner_id'):
            user_data = await self.db_client.get_user_by_id(str(api_key_data['owner_id']))
        
        return {
            **api_key_data,
            'username': user_data.get('username', 'unknown') if user_data else 'unknown',
            'email': user_data.get('email', '') if user_data else '',
            'auth_method': 'api_key'
        }
    
    def check_permissions(self, user_data: Dict[str, Any], required_scopes: Set[str]) -> bool:
        """
        Check if user has required scopes
        Returns True if user has all required scopes
        """
        if not user_data:
            return False
        
        user_scopes = user_data.get('scopes', set())
        if not isinstance(user_scopes, set):
            user_scopes = set(user_scopes) if user_scopes else set()
        
        # Check if user has all required scopes
        return required_scopes.issubset(user_scopes)
    
    def check_role(self, user_data: Dict[str, Any], required_roles: Set[str]) -> bool:
        """
        Check if user has required role
        Returns True if user role is in required roles
        """
        if not user_data:
            return False
        
        user_role = user_data.get('role', '')
        return user_role in required_roles
    
    def check_organization(self, user_data: Dict[str, Any], required_org_id: str) -> bool:
        """
        Check if user belongs to required organization
        Returns True if user org matches or user is super_admin
        """
        if not user_data:
            return False
        
        # Super admin can access any organization
        if user_data.get('role') == 'super_admin':
            return True
        
        user_org_id = user_data.get('organization_id')
        return user_org_id == required_org_id
    
    def is_authenticated(self, user_data: Dict[str, Any]) -> bool:
        """Check if user is properly authenticated"""
        if not user_data:
            return False
        
        # Check if user is blocked
        if user_data.get('blocked', False):
            return False
        
        # Check if user is confirmed (for JWT auth)
        if user_data.get('auth_method') == 'jwt' and not user_data.get('confirmed', True):
            return False
        
        return True
    
    async def health_check(self) -> bool:
        """Check authentication system health"""
        try:
            return await self.db_client.health_check()
        except Exception as e:
            logger.error(f"Auth health check failed: {e}")
            return False
