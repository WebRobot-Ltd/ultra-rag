"""
JWT validation for MCP servers
Replicates Jersey JwtAuthFilter logic
"""

import os
import jwt
import hashlib
from typing import Optional, Dict, Any, Set
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class JWTValidator:
    """JWT token validator matching Jersey implementation"""
    
    def __init__(self, secret: Optional[str] = None):
        self.secret = secret or os.getenv('JWT_SECRET', 'dev-secret-change-me')
        self.secret_bytes = self.secret.encode('utf-8')
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate JWT token and extract claims
        Returns user info dict or None if invalid
        """
        try:
            # Decode JWT token (matching Jersey Jwts.parserBuilder logic)
            payload = jwt.decode(
                token, 
                self.secret_bytes, 
                algorithms=['HS256'],
                options={"verify_exp": True}
            )
            
            # Extract user ID (matching Jersey claims extraction)
            user_id = payload.get('id') or payload.get('sub')
            if not user_id:
                logger.warning("JWT token missing subject/id")
                return None
            
            # Extract role, scopes, org from claims (matching Jersey logic)
            role = payload.get('role', 'authenticated')
            scopes = self._normalize_scopes(payload.get('scopes') or payload.get('scope'))
            org_id = payload.get('organization_id') or payload.get('orgId')
            
            return {
                'user_id': str(user_id),
                'role': role,
                'scopes': scopes,
                'organization_id': org_id,
                'email': payload.get('email'),
                'username': payload.get('username'),
                'iat': payload.get('iat'),
                'exp': payload.get('exp')
            }
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
        except Exception as e:
            logger.error(f"JWT validation error: {e}")
            return None
    
    def _normalize_scopes(self, scopes_claim: Any) -> Set[str]:
        """
        Normalize scopes to Set[str] (matching Jersey normalizeScopes)
        """
        if not scopes_claim:
            return set()
        
        if isinstance(scopes_claim, str):
            # Split comma-separated string
            return {scope.strip() for scope in scopes_claim.split(',') if scope.strip()}
        elif isinstance(scopes_claim, list):
            # Convert list to set
            return {str(scope).strip() for scope in scopes_claim if scope}
        else:
            return set()
    
    def is_token_expired(self, token: str) -> bool:
        """Check if token is expired without full validation"""
        try:
            # Decode without verification to check expiration
            payload = jwt.decode(token, options={"verify_signature": False})
            exp = payload.get('exp')
            if exp:
                exp_time = datetime.fromtimestamp(exp, tz=timezone.utc)
                return exp_time < datetime.now(timezone.utc)
            return False
        except:
            return True
    
    def extract_user_id(self, token: str) -> Optional[str]:
        """Extract user ID from token without full validation"""
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload.get('id') or payload.get('sub')
        except:
            return None
