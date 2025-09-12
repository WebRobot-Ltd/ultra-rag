"""
Authentication middleware for MCP servers
Provides easy integration with existing MCP server code
"""

import json
from typing import Optional, Dict, Any, Set, Callable
from functools import wraps
import logging

from auth_manager import AuthManager
from database_client import DatabaseConfig

logger = logging.getLogger(__name__)

class AuthMiddleware:
    """
    Middleware for adding authentication to MCP servers
    Provides decorators and request validation
    """
    
    def __init__(self, db_config: Optional[DatabaseConfig] = None):
        self.auth_manager = AuthManager(db_config)
        self._initialized = False
    
    async def initialize(self):
        """Initialize authentication system"""
        if not self._initialized:
            await self.auth_manager.initialize()
            self._initialized = True
            logger.info("AuthMiddleware initialized")
    
    async def close(self):
        """Close authentication system"""
        if self._initialized:
            await self.auth_manager.close()
            self._initialized = False
            logger.info("AuthMiddleware closed")
    
    def require_auth(self, required_scopes: Optional[Set[str]] = None, required_roles: Optional[Set[str]] = None):
        """
        Decorator to require authentication for MCP methods
        Usage:
            @auth_middleware.require_auth(required_scopes={'read'})
            async def my_mcp_method(self, ...):
                pass
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(self, *args, **kwargs):
                # Extract headers from MCP context
                headers = self._extract_headers_from_context()
                
                # Authenticate request
                user_data = await self.auth_manager.authenticate_request(headers)
                if not user_data:
                    return self._create_error_response("Authentication required", 401)
                
                # Check if user is properly authenticated
                if not self.auth_manager.is_authenticated(user_data):
                    return self._create_error_response("Authentication failed", 401)
                
                # Check scopes if required
                if required_scopes and not self.auth_manager.check_permissions(user_data, required_scopes):
                    return self._create_error_response("Insufficient permissions", 403)
                
                # Check roles if required
                if required_roles and not self.auth_manager.check_role(user_data, required_roles):
                    return self._create_error_response("Insufficient role", 403)
                
                # Add user data to context for use in method
                self._current_user = user_data
                
                # Call original method
                return await func(self, *args, **kwargs)
            
            return wrapper
        return decorator
    
    def require_scope(self, scope: str):
        """Convenience decorator for single scope requirement"""
        return self.require_auth(required_scopes={scope})
    
    def require_role(self, role: str):
        """Convenience decorator for single role requirement"""
        return self.require_auth(required_roles={role})
    
    def require_admin(self):
        """Convenience decorator for admin role requirement"""
        return self.require_auth(required_roles={'admin', 'super_admin'})
    
    def optional_auth(self):
        """
        Decorator for optional authentication
        Sets self._current_user if authenticated, None otherwise
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(self, *args, **kwargs):
                # Extract headers from MCP context
                headers = self._extract_headers_from_context()
                
                # Try to authenticate (no error if fails)
                user_data = await self.auth_manager.authenticate_request(headers)
                self._current_user = user_data if user_data and self.auth_manager.is_authenticated(user_data) else None
                
                # Call original method
                return await func(self, *args, **kwargs)
            
            return wrapper
        return decorator
    
    def _extract_headers_from_context(self) -> Dict[str, str]:
        """
        Extract headers from MCP context
        This method should be overridden based on the MCP server implementation
        """
        # Default implementation - should be overridden
        return {}
    
    def _create_error_response(self, message: str, status_code: int) -> Dict[str, Any]:
        """Create error response for MCP"""
        return {
            "error": {
                "code": status_code,
                "message": message
            }
        }
    
    async def validate_request(self, headers: Dict[str, str], required_scopes: Optional[Set[str]] = None) -> Dict[str, Any]:
        """
        Validate request and return result
        Returns: {
            'valid': bool,
            'user_data': dict or None,
            'error': str or None
        }
        """
        try:
            # Authenticate request
            user_data = await self.auth_manager.authenticate_request(headers)
            if not user_data:
                return {
                    'valid': False,
                    'user_data': None,
                    'error': 'Authentication required'
                }
            
            # Check if user is properly authenticated
            if not self.auth_manager.is_authenticated(user_data):
                return {
                    'valid': False,
                    'user_data': None,
                    'error': 'Authentication failed'
                }
            
            # Check scopes if required
            if required_scopes and not self.auth_manager.check_permissions(user_data, required_scopes):
                return {
                    'valid': False,
                    'user_data': user_data,
                    'error': 'Insufficient permissions'
                }
            
            return {
                'valid': True,
                'user_data': user_data,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Request validation error: {e}")
            return {
                'valid': False,
                'user_data': None,
                'error': f'Validation error: {str(e)}'
            }
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current authenticated user (set by decorators)"""
        return getattr(self, '_current_user', None)
    
    def is_user_authenticated(self) -> bool:
        """Check if current user is authenticated"""
        user = self.get_current_user()
        return user is not None and self.auth_manager.is_authenticated(user)
    
    def has_scope(self, scope: str) -> bool:
        """Check if current user has specific scope"""
        user = self.get_current_user()
        if not user:
            return False
        return self.auth_manager.check_permissions(user, {scope})
    
    def has_role(self, role: str) -> bool:
        """Check if current user has specific role"""
        user = self.get_current_user()
        if not user:
            return False
        return self.auth_manager.check_role(user, {role})
    
    def is_admin(self) -> bool:
        """Check if current user is admin or super_admin"""
        user = self.get_current_user()
        if not user:
            return False
        return self.auth_manager.check_role(user, {'admin', 'super_admin'})
