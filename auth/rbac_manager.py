"""
Role-Based Access Control (RBAC) Manager for UltraRAG MCP
Manages user roles, permissions, and document access control
"""

import json
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security levels for document access control"""
    PUBLIC = 1
    INTERNAL = 2
    CONFIDENTIAL = 3
    SECRET = 4


@dataclass
class UserRole:
    """User role definition"""
    name: str
    level: int
    departments: List[str]
    security_levels: List[int]
    permissions: List[str]


@dataclass
class DocumentMetadata:
    """Document metadata for RBAC"""
    document_id: str
    document_type: str
    department: str
    security_level: int
    owner_id: str
    created_at: int
    updated_at: int
    allowed_roles: List[str]
    allowed_users: List[str]
    tags: List[str]
    custom_metadata: Dict[str, Any]


class RBACManager:
    """Role-Based Access Control Manager"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.roles = self._load_default_roles()
        self.departments = self._load_default_departments()
        
    def _load_default_roles(self) -> Dict[str, UserRole]:
        """Load default role definitions"""
        return {
            "admin": UserRole(
                name="admin",
                level=4,
                departments=["*"],  # All departments
                security_levels=[1, 2, 3, 4],
                permissions=["read", "write", "delete", "admin"]
            ),
            "manager": UserRole(
                name="manager",
                level=3,
                departments=["engineering", "sales", "marketing"],
                security_levels=[1, 2, 3],
                permissions=["read", "write"]
            ),
            "analyst": UserRole(
                name="analyst",
                level=2,
                departments=["engineering", "data"],
                security_levels=[1, 2],
                permissions=["read"]
            ),
            "viewer": UserRole(
                name="viewer",
                level=1,
                departments=["engineering"],
                security_levels=[1],
                permissions=["read"]
            )
        }
    
    def _load_default_departments(self) -> Dict[str, Dict[str, Any]]:
        """Load default department definitions"""
        return {
            "engineering": {
                "parent": None,
                "permissions": ["read", "write"],
                "description": "Engineering department"
            },
            "sales": {
                "parent": None,
                "permissions": ["read"],
                "description": "Sales department"
            },
            "marketing": {
                "parent": None,
                "permissions": ["read"],
                "description": "Marketing department"
            },
            "data": {
                "parent": None,
                "permissions": ["read", "write"],
                "description": "Data analytics department"
            },
            "general": {
                "parent": None,
                "permissions": ["read"],
                "description": "General access"
            }
        }
    
    def get_user_roles(self, user_id: str) -> List[str]:
        """Get roles for a specific user"""
        # In a real implementation, this would query the database
        # For now, return default roles based on user_id pattern
        if user_id.startswith("admin_"):
            return ["admin"]
        elif user_id.startswith("mgr_"):
            return ["manager"]
        elif user_id.startswith("analyst_"):
            return ["analyst"]
        else:
            return ["viewer"]
    
    def get_user_departments(self, user_id: str) -> List[str]:
        """Get departments for a specific user"""
        # In a real implementation, this would query the database
        if user_id.startswith("admin_"):
            return ["*"]  # Admin has access to all departments
        elif user_id.startswith("eng_"):
            return ["engineering"]
        elif user_id.startswith("sales_"):
            return ["sales"]
        elif user_id.startswith("mkt_"):
            return ["marketing"]
        else:
            return ["general"]
    
    def can_access_document(
        self, 
        user_roles: List[str], 
        user_departments: List[str], 
        user_id: str,
        document_metadata: DocumentMetadata
    ) -> bool:
        """Check if user can access a specific document"""
        
        # Check security level
        user_max_level = max(
            self.roles[role].level for role in user_roles 
            if role in self.roles
        )
        
        if document_metadata.security_level > user_max_level:
            return False
        
        # Check department access
        if "*" not in user_departments:
            if document_metadata.department not in user_departments:
                return False
        
        # Check specific role access
        if document_metadata.allowed_roles:
            if not any(role in document_metadata.allowed_roles for role in user_roles):
                return False
        
        # Check specific user access
        if document_metadata.allowed_users:
            if user_id not in document_metadata.allowed_users:
                return False
        
        return True
    
    def build_milvus_filter(
        self, 
        user_roles: List[str], 
        user_departments: List[str], 
        user_id: str
    ) -> str:
        """Build Milvus filter expression for RBAC"""
        
        conditions = []
        
        # Get user's maximum security level
        user_max_level = max(
            self.roles[role].level for role in user_roles 
            if role in self.roles
        )
        
        # Filter by security level
        conditions.append(f"security_level <= {user_max_level}")
        
        # Filter by departments
        if "*" not in user_departments:
            dept_conditions = " OR ".join([
                f'department == "{dept}"' for dept in user_departments
            ])
            conditions.append(f"({dept_conditions})")
        
        # Filter by allowed roles
        role_conditions = []
        for role in user_roles:
            role_conditions.append(f'JSON_CONTAINS(allowed_roles, "{role}")')
        
        if role_conditions:
            conditions.append(f"({' OR '.join(role_conditions)})")
        
        # Filter by allowed users
        conditions.append(f'JSON_CONTAINS(allowed_users, "{user_id}")')
        
        return " AND ".join(conditions)
    
    def create_document_metadata(
        self,
        document_id: str,
        document_type: str = "document",
        department: str = "general",
        security_level: int = 1,
        owner_id: str = "system",
        allowed_roles: List[str] = None,
        allowed_users: List[str] = None,
        tags: List[str] = None,
        custom_metadata: Dict[str, Any] = None
    ) -> DocumentMetadata:
        """Create document metadata for RBAC"""
        
        current_time = int(time.time())
        
        return DocumentMetadata(
            document_id=document_id,
            document_type=document_type,
            department=department,
            security_level=security_level,
            owner_id=owner_id,
            created_at=current_time,
            updated_at=current_time,
            allowed_roles=allowed_roles or ["viewer"],
            allowed_users=allowed_users or [],
            tags=tags or [],
            custom_metadata=custom_metadata or {}
        )
    
    def serialize_metadata_for_milvus(self, metadata: DocumentMetadata) -> Dict[str, Any]:
        """Serialize metadata for Milvus insertion"""
        return {
            "document_id": metadata.document_id,
            "document_type": metadata.document_type,
            "department": metadata.department,
            "security_level": metadata.security_level,
            "owner_id": metadata.owner_id,
            "created_at": metadata.created_at,
            "updated_at": metadata.updated_at,
            "allowed_roles": json.dumps(metadata.allowed_roles),
            "allowed_users": json.dumps(metadata.allowed_users),
            "tags": json.dumps(metadata.tags),
            "custom_metadata": json.dumps(metadata.custom_metadata)
        }
    
    def add_role(self, role: UserRole) -> None:
        """Add a new role"""
        self.roles[role.name] = role
        logger.info(f"Added role: {role.name}")
    
    def remove_role(self, role_name: str) -> None:
        """Remove a role"""
        if role_name in self.roles:
            del self.roles[role_name]
            logger.info(f"Removed role: {role_name}")
    
    def get_role(self, role_name: str) -> Optional[UserRole]:
        """Get role by name"""
        return self.roles.get(role_name)
    
    def list_roles(self) -> List[str]:
        """List all available roles"""
        return list(self.roles.keys())
    
    def validate_user_access(
        self, 
        user_id: str, 
        document_id: str, 
        action: str = "read"
    ) -> bool:
        """Validate if user can perform action on document"""
        
        user_roles = self.get_user_roles(user_id)
        user_departments = self.get_user_departments(user_id)
        
        # In a real implementation, you would fetch document metadata from database
        # For now, we'll simulate based on document_id pattern
        if document_id.startswith("confidential_"):
            doc_security_level = 3
            doc_department = "engineering"
        elif document_id.startswith("internal_"):
            doc_security_level = 2
            doc_department = "general"
        else:
            doc_security_level = 1
            doc_department = "general"
        
        # Create mock document metadata
        doc_metadata = DocumentMetadata(
            document_id=document_id,
            document_type="document",
            department=doc_department,
            security_level=doc_security_level,
            owner_id="system",
            created_at=int(time.time()),
            updated_at=int(time.time()),
            allowed_roles=["viewer"],
            allowed_users=[],
            tags=[],
            custom_metadata={}
        )
        
        return self.can_access_document(
            user_roles, user_departments, user_id, doc_metadata
        )


# Example usage and testing
if __name__ == "__main__":
    # Initialize RBAC manager
    rbac = RBACManager()
    
    # Test user access
    test_users = [
        ("admin_001", ["admin"], ["*"]),
        ("mgr_001", ["manager"], ["engineering"]),
        ("analyst_001", ["analyst"], ["engineering"]),
        ("viewer_001", ["viewer"], ["general"])
    ]
    
    test_documents = [
        "public_doc_001",
        "internal_doc_001", 
        "confidential_doc_001"
    ]
    
    print("RBAC Access Test Results:")
    print("=" * 50)
    
    for user_id, roles, departments in test_users:
        print(f"\nUser: {user_id} (Roles: {roles}, Departments: {departments})")
        for doc_id in test_documents:
            can_access = rbac.validate_user_access(user_id, doc_id)
            print(f"  {doc_id}: {'✓' if can_access else '✗'}")
    
    # Test Milvus filter generation
    print("\nMilvus Filter Examples:")
    print("=" * 50)
    
    for user_id, roles, departments in test_users:
        filter_expr = rbac.build_milvus_filter(roles, departments, user_id)
        print(f"\n{user_id}: {filter_expr}")
