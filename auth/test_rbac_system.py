#!/usr/bin/env python3
"""
Test suite for RBAC (Role-Based Access Control) system
Tests user roles, permissions, and document access control
"""

import json
import sys
import os
from pathlib import Path

# Add the auth directory to the path
sys.path.append(str(Path(__file__).parent))

from rbac_manager import RBACManager, DocumentMetadata, SecurityLevel


def test_rbac_manager():
    """Test RBAC Manager functionality"""
    print("🧪 Testing RBAC Manager...")
    
    # Initialize RBAC manager
    rbac = RBACManager()
    
    # Test 1: Role retrieval
    print("\n1. Testing role retrieval...")
    test_users = [
        "admin_001",
        "mgr_001", 
        "eng_001",
        "analyst_001",
        "viewer_001",
        "unknown_user"
    ]
    
    for user_id in test_users:
        roles = rbac.get_user_roles(user_id)
        departments = rbac.get_user_departments(user_id)
        print(f"   {user_id}: roles={roles}, departments={departments}")
    
    # Test 2: Document access validation
    print("\n2. Testing document access validation...")
    test_documents = [
        ("public_doc_001", 1, "general"),
        ("internal_doc_001", 2, "engineering"),
        ("confidential_doc_001", 3, "engineering"),
        ("secret_doc_001", 4, "engineering")
    ]
    
    for user_id in test_users:
        print(f"\n   User: {user_id}")
        for doc_id, sec_level, dept in test_documents:
            can_access = rbac.validate_user_access(user_id, doc_id)
            print(f"     {doc_id} (level={sec_level}, dept={dept}): {'✓' if can_access else '✗'}")
    
    # Test 3: Milvus filter generation
    print("\n3. Testing Milvus filter generation...")
    test_cases = [
        (["admin"], ["*"], "admin_001"),
        (["manager"], ["engineering"], "mgr_001"),
        (["engineer"], ["engineering"], "eng_001"),
        (["viewer"], ["general"], "viewer_001")
    ]
    
    for roles, departments, user_id in test_cases:
        filter_expr = rbac.build_milvus_filter(roles, departments, user_id)
        print(f"   {user_id} ({roles}, {departments}): {filter_expr}")
    
    # Test 4: Document metadata creation
    print("\n4. Testing document metadata creation...")
    metadata = rbac.create_document_metadata(
        document_id="test_doc_001",
        document_type="technical_spec",
        department="engineering",
        security_level=3,
        owner_id="eng_001",
        allowed_roles=["engineer", "senior_engineer"],
        allowed_users=["eng_001", "senior_eng_001"],
        tags=["confidential", "engineering", "technical"],
        custom_metadata={"project": "webrobot", "version": "1.0"}
    )
    
    print(f"   Created metadata: {metadata}")
    
    # Test 5: Serialization for Milvus
    print("\n5. Testing Milvus serialization...")
    serialized = rbac.serialize_metadata_for_milvus(metadata)
    print(f"   Serialized metadata: {json.dumps(serialized, indent=2)}")
    
    print("\n✅ RBAC Manager tests completed!")


def test_document_access_scenarios():
    """Test various document access scenarios"""
    print("\n🔒 Testing Document Access Scenarios...")
    
    rbac = RBACManager()
    
    # Create test documents with different access levels
    documents = [
        DocumentMetadata(
            document_id="public_manual",
            document_type="manual",
            department="general",
            security_level=1,
            owner_id="admin_001",
            created_at=1234567890,
            updated_at=1234567890,
            allowed_roles=["*"],
            allowed_users=[],
            tags=["public", "manual"],
            custom_metadata={}
        ),
        DocumentMetadata(
            document_id="internal_engineering_doc",
            document_type="technical",
            department="engineering",
            security_level=2,
            owner_id="eng_001",
            created_at=1234567890,
            updated_at=1234567890,
            allowed_roles=["engineer", "senior_engineer"],
            allowed_users=[],
            tags=["internal", "engineering"],
            custom_metadata={}
        ),
        DocumentMetadata(
            document_id="confidential_sales_data",
            document_type="report",
            department="sales",
            security_level=3,
            owner_id="mgr_001",
            created_at=1234567890,
            updated_at=1234567890,
            allowed_roles=["manager"],
            allowed_users=["sales_001"],
            tags=["confidential", "sales"],
            custom_metadata={}
        ),
        DocumentMetadata(
            document_id="secret_admin_doc",
            document_type="policy",
            department="general",
            security_level=4,
            owner_id="admin_001",
            created_at=1234567890,
            updated_at=1234567890,
            allowed_roles=["admin"],
            allowed_users=[],
            tags=["secret", "admin"],
            custom_metadata={}
        )
    ]
    
    # Test users with different roles
    test_users = [
        ("admin_001", ["admin"], ["*"]),
        ("mgr_001", ["manager"], ["engineering", "sales"]),
        ("eng_001", ["engineer"], ["engineering"]),
        ("analyst_001", ["analyst"], ["data"]),
        ("viewer_001", ["viewer"], ["general"]),
        ("sales_001", ["sales_rep"], ["sales"])
    ]
    
    print("\nDocument Access Matrix:")
    print("=" * 80)
    print(f"{'User':<15} {'Public':<8} {'Internal':<10} {'Confidential':<15} {'Secret':<8}")
    print("-" * 80)
    
    for user_id, roles, departments in test_users:
        access_results = []
        for doc in documents:
            can_access = rbac.can_access_document(roles, departments, user_id, doc)
            access_results.append("✓" if can_access else "✗")
        
        print(f"{user_id:<15} {access_results[0]:<8} {access_results[1]:<10} {access_results[2]:<15} {access_results[3]:<8}")
    
    print("\n✅ Document Access Scenarios tests completed!")


def test_security_levels():
    """Test security level enforcement"""
    print("\n🛡️ Testing Security Level Enforcement...")
    
    rbac = RBACManager()
    
    # Test different security levels
    security_tests = [
        (1, "public", ["viewer", "engineer", "manager", "admin"]),
        (2, "internal", ["engineer", "manager", "admin"]),
        (3, "confidential", ["manager", "admin"]),
        (4, "secret", ["admin"])
    ]
    
    for level, name, expected_roles in security_tests:
        print(f"\n   Security Level {level} ({name}):")
        
        # Test each role
        for role_name in ["viewer", "engineer", "manager", "admin"]:
            role = rbac.get_role(role_name)
            if role:
                can_access = level in role.security_levels
                expected = role_name in expected_roles
                status = "✓" if can_access == expected else "✗"
                print(f"     {role_name}: {status} (can_access={can_access}, expected={expected})")
    
    print("\n✅ Security Level Enforcement tests completed!")


def test_department_access():
    """Test department-based access control"""
    print("\n🏢 Testing Department Access Control...")
    
    rbac = RBACManager()
    
    # Test department access
    department_tests = [
        ("admin_001", ["*"], "Should access all departments"),
        ("eng_001", ["engineering"], "Should access only engineering"),
        ("sales_001", ["sales"], "Should access only sales"),
        ("analyst_001", ["data", "engineering"], "Should access data and engineering")
    ]
    
    test_departments = ["engineering", "sales", "marketing", "data", "general"]
    
    for user_id, expected_depts, description in department_tests:
        print(f"\n   {user_id} ({description}):")
        user_departments = rbac.get_user_departments(user_id)
        
        for dept in test_departments:
            can_access = "*" in user_departments or dept in user_departments
            expected = "*" in expected_depts or dept in expected_depts
            status = "✓" if can_access == expected else "✗"
            print(f"     {dept}: {status} (can_access={can_access}, expected={expected})")
    
    print("\n✅ Department Access Control tests completed!")


def test_milvus_filter_generation():
    """Test Milvus filter expression generation"""
    print("\n🔍 Testing Milvus Filter Generation...")
    
    rbac = RBACManager()
    
    # Test various filter scenarios
    filter_tests = [
        (["admin"], ["*"], "admin_001", "Admin with all departments"),
        (["manager"], ["engineering", "sales"], "mgr_001", "Manager with specific departments"),
        (["engineer"], ["engineering"], "eng_001", "Engineer with single department"),
        (["viewer"], ["general"], "viewer_001", "Viewer with general access"),
        (["analyst"], ["data", "engineering"], "analyst_001", "Analyst with multiple departments")
    ]
    
    for roles, departments, user_id, description in filter_tests:
        filter_expr = rbac.build_milvus_filter(roles, departments, user_id)
        print(f"\n   {description}:")
        print(f"     User: {user_id}")
        print(f"     Roles: {roles}")
        print(f"     Departments: {departments}")
        print(f"     Filter: {filter_expr}")
    
    print("\n✅ Milvus Filter Generation tests completed!")


def main():
    """Run all RBAC tests"""
    print("🚀 Starting RBAC System Tests")
    print("=" * 50)
    
    try:
        test_rbac_manager()
        test_document_access_scenarios()
        test_security_levels()
        test_department_access()
        test_milvus_filter_generation()
        
        print("\n🎉 All RBAC tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)


