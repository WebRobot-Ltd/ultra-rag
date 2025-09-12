"""
API Key validation for MCP servers
Replicates Jersey ApiKeyAuthFilter logic
"""

import os
import hashlib
from typing import Optional, Dict, Any, Set
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class APIKeyValidator:
    """API Key validator matching Jersey implementation"""
    
    def __init__(self, strapi_base_url: Optional[str] = None, internal_token: Optional[str] = None):
        self.strapi_base_url = strapi_base_url or os.getenv('STRAPI_BASE_URL', 'http://localhost:1337')
        self.internal_token = internal_token or os.getenv('INTERNAL_TOKEN', 'change-me-internal')
        
        # Dev credentials (matching Jersey dev fallback)
        self.dev_api_key = os.getenv('DEV_API_KEY', 'dev-api-key-12345')
        self.dev_user_id = os.getenv('DEV_USER_ID', 'dev-user')
        self.dev_role = os.getenv('DEV_ROLE', 'super_admin')
        self.dev_org_id = os.getenv('DEV_ORG_ID', 'dev-org')
        
        # Parse dev scopes
        dev_scopes_str = os.getenv('DEV_SCOPES', 'read,write,admin')
        self.dev_scopes = {scope.strip() for scope in dev_scopes_str.split(',') if scope.strip()}
    
    async def validate_api_key(self, api_key: str, db_client) -> Optional[Dict[str, Any]]:
        """
        Validate API key and return user info
        Returns user info dict or None if invalid
        """
        if not api_key or not api_key.strip():
            return None
        
        api_key = api_key.strip()
        
        # Check dev API key first (matching Jersey dev fallback)
        if api_key == self.dev_api_key:
            logger.info("Using dev API key")
            return {
                'user_id': self.dev_user_id,
                'role': self.dev_role,
                'scopes': self.dev_scopes,
                'organization_id': self.dev_org_id,
                'is_dev': True
            }
        
        # Validate against database
        return await self._validate_database_api_key(api_key, db_client)
    
    async def _validate_database_api_key(self, api_key: str, db_client) -> Optional[Dict[str, Any]]:
        """Validate API key against database (Strapi structure)"""
        try:
            # Extract key_id from API key (assuming format: key_id:secret)
            if ':' not in api_key:
                logger.warning("Invalid API key format")
                return None
            
            key_id, secret = api_key.split(':', 1)
            
            # Get API key from database
            api_key_data = await db_client.get_api_key_by_key_id(key_id)
            if not api_key_data:
                logger.warning(f"API key not found: {key_id}")
                return None
            
            # Check if expired
            if api_key_data.get('expires_at'):
                expires_at = api_key_data['expires_at']
                if isinstance(expires_at, str):
                    expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                # Ensure both dates are timezone-aware
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                if expires_at < now:
                    logger.warning(f"API key expired: {key_id}")
                    return None
            
            # Validate secret hash
            if not self._verify_secret_hash(secret, api_key_data['secret_hash']):
                logger.warning(f"Invalid API key secret: {key_id}")
                return None
            
            # Update last used timestamp
            await db_client.update_api_key_last_used(key_id)
            
            # Get user info
            user_data = await db_client.get_user_by_id(api_key_data['owner_id'])
            if not user_data:
                logger.warning(f"User not found for API key: {key_id}")
                return None
            
            # Get scopes (from API key or user role)
            scopes = self._get_scopes_from_api_key(api_key_data, user_data)
            
            return {
                'user_id': str(user_data['id']),
                'role': api_key_data.get('role') or user_data.get('role_name', 'authenticated'),
                'scopes': scopes,
                'organization_id': api_key_data.get('organization_id') or user_data.get('organization_id'),
                'email': user_data.get('email'),
                'username': user_data.get('username'),
                'api_key_id': key_id,
                'is_dev': False
            }
            
        except Exception as e:
            logger.error(f"API key validation error: {e}")
            return None
    
    def _verify_secret_hash(self, secret: str, stored_hash: str) -> bool:
        """
        Verify API key secret against stored hash
        Matches Jersey SHA256 hashing logic
        """
        try:
            # Hash the provided secret
            secret_hash = hashlib.sha256(secret.encode('utf-8')).hexdigest()
            return secret_hash == stored_hash
        except Exception as e:
            logger.error(f"Secret hash verification error: {e}")
            return False
    
    def _get_scopes_from_api_key(self, api_key_data: Dict[str, Any], user_data: Dict[str, Any]) -> Set[str]:
        """Get scopes from API key or fallback to role defaults"""
        # First try API key scopes
        api_scopes = api_key_data.get('scopes')
        if api_scopes:
            if isinstance(api_scopes, list):
                return {str(scope).strip() for scope in api_scopes if scope}
            elif isinstance(api_scopes, str):
                try:
                    # Try to parse as JSON first
                    import json
                    parsed_scopes = json.loads(api_scopes)
                    if isinstance(parsed_scopes, list):
                        return {str(scope).strip() for scope in parsed_scopes if scope}
                except (json.JSONDecodeError, TypeError):
                    # Fallback to comma-separated string
                    return {scope.strip() for scope in api_scopes.split(',') if scope.strip()}
        
        # Fallback to role-based scopes
        role_name = api_key_data.get('role') or user_data.get('role_name', 'viewer')
        return self._get_default_scopes_for_role(role_name)
    
    def _get_default_scopes_for_role(self, role_name: str) -> Set[str]:
        """Get default scopes for role (Strapi structure)"""
        role_scopes = {
            'super_admin': {'read', 'write', 'admin', 'delete'},
            'admin': {'read', 'write', 'admin'},
            'developer': {'read', 'write'},
            'viewer': {'read'},
            'authenticated': {'read'}
        }
        return role_scopes.get(role_name, {'read'})
    
    def is_dev_key(self, api_key: str) -> bool:
        """Check if API key is dev key"""
        return api_key == self.dev_api_key
