"""
RBAC-enabled Retriever for UltraRAG MCP
Extends the base retriever with role-based access control
"""

import json
import time
import uuid
from typing import Dict, List, Optional, Any
import numpy as np

from ultrarag.server import UltraRAG_MCP_Server
from auth.rbac_manager import RBACManager, DocumentMetadata, SecurityLevel


class RBACRetriever:
    """Retriever with Role-Based Access Control"""
    
    def __init__(self, mcp_inst: UltraRAG_MCP_Server):
        self.mcp_inst = mcp_inst
        self.rbac_manager = RBACManager()
        self.milvus_collection = None
        
        # Register RBAC-enabled tools
        self._register_rbac_tools()
    
    def _register_rbac_tools(self):
        """Register RBAC-enabled tools with the MCP server"""
        
        # RBAC-enabled search
        self.mcp_inst.tool(
            self.retriever_search_with_rbac,
            output="q_ls,top_k,user_roles,user_departments,user_id,collection_name,host,port->ret_psg",
        )
        
        # RBAC-enabled indexing
        self.mcp_inst.tool(
            self.retriever_index_with_rbac,
            output="embedding_path,collection_name,host,port,overwrite,user_roles,department,security_level,owner_id,allowed_roles,allowed_users,tags,custom_metadata->None",
        )
        
        # Document access validation
        self.mcp_inst.tool(
            self.validate_document_access,
            output="user_id,document_id,action->can_access",
        )
        
        # User role management
        self.mcp_inst.tool(
            self.get_user_roles,
            output="user_id->roles",
        )
        
        # Department management
        self.mcp_inst.tool(
            self.get_user_departments,
            output="user_id->departments",
        )
    
    async def retriever_search_with_rbac(
        self,
        query_list: List[str],
        top_k: int = 5,
        user_roles: List[str] = None,
        user_departments: List[str] = None,
        user_id: str = None,
        collection_name: str = "webrobot_knowledge_base",
        host: str = "localhost",
        port: int = 19530,
    ) -> Dict[str, List[List[str]]]:
        """
        Search with Role-Based Access Control
        
        Args:
            query_list: List of queries to search
            top_k: Number of top results to return
            user_roles: List of user roles
            user_departments: List of user departments
            user_id: User identifier
            collection_name: Milvus collection name
            host: Milvus host
            port: Milvus port
            
        Returns:
            Dictionary with search results filtered by RBAC
        """
        try:
            from pymilvus import connections, Collection, utility
        except ImportError:
            raise ImportError("pymilvus is not installed. Please install it with `pip install pymilvus`.")
        
        # Set default values
        if not user_roles:
            user_roles = ["viewer"]
        if not user_departments:
            user_departments = ["general"]
        if not user_id:
            user_id = "anonymous"
        
        # Connect to Milvus
        connections.connect("default", host=host, port=port)
        
        # Get collection
        if not utility.has_collection(collection_name):
            return {"ret_psg": [[] for _ in query_list]}
        
        collection = Collection(collection_name)
        collection.load()
        
        # Build RBAC filter
        rbac_filter = self.rbac_manager.build_milvus_filter(
            user_roles, user_departments, user_id
        )
        
        # Generate embeddings for queries
        # This is a simplified version - in practice you'd use your embedding model
        query_embeddings = []
        for query in query_list:
            # Mock embedding - replace with actual embedding generation
            embedding = np.random.rand(768).tolist()
            query_embeddings.append(embedding)
        
        # Search with RBAC filter
        search_params = {
            "metric_type": "IP",
            "params": {"nprobe": 10}
        }
        
        results = collection.search(
            data=query_embeddings,
            anns_field="vector",
            param=search_params,
            limit=top_k,
            expr=rbac_filter,
            output_fields=["text", "document_id", "department", "security_level"]
        )
        
        # Process results
        ret_psg = []
        for result in results:
            passages = []
            for hit in result:
                if hit.score > 0.5:  # Threshold for relevance
                    passages.append(hit.entity.get("text", ""))
            ret_psg.append(passages)
        
        return {"ret_psg": ret_psg}
    
    def retriever_index_with_rbac(
        self,
        embedding_path: str,
        collection_name: str = "webrobot_knowledge_base",
        host: str = "localhost",
        port: int = 19530,
        overwrite: bool = False,
        user_roles: List[str] = None,
        department: str = "general",
        security_level: int = 1,
        owner_id: str = "system",
        allowed_roles: List[str] = None,
        allowed_users: List[str] = None,
        tags: List[str] = None,
        custom_metadata: Dict[str, Any] = None
    ):
        """
        Index documents with RBAC metadata
        
        Args:
            embedding_path: Path to embedding file
            collection_name: Milvus collection name
            host: Milvus host
            port: Milvus port
            overwrite: Whether to overwrite existing collection
            user_roles: Default roles for document access
            department: Document department
            security_level: Document security level
            owner_id: Document owner
            allowed_roles: Specific roles that can access
            allowed_users: Specific users that can access
            tags: Document tags
            custom_metadata: Custom metadata
        """
        try:
            from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
        except ImportError:
            raise ImportError("pymilvus is not installed. Please install it with `pip install pymilvus`.")
        
        # Load embeddings
        embeddings = np.load(embedding_path)
        dim = embeddings.shape[1]
        num_vectors = embeddings.shape[0]
        
        # Connect to Milvus
        connections.connect("default", host=host, port=port)
        
        # Define extended schema with RBAC fields
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=dim),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
            
            # RBAC metadata fields
            FieldSchema(name="document_id", dtype=DataType.VARCHAR, max_length=255),
            FieldSchema(name="document_type", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="department", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="security_level", dtype=DataType.INT64),
            FieldSchema(name="owner_id", dtype=DataType.VARCHAR, max_length=255),
            FieldSchema(name="created_at", dtype=DataType.INT64),
            FieldSchema(name="updated_at", dtype=DataType.INT64),
            FieldSchema(name="allowed_roles", dtype=DataType.VARCHAR, max_length=2048),
            FieldSchema(name="allowed_users", dtype=DataType.VARCHAR, max_length=2048),
            FieldSchema(name="tags", dtype=DataType.VARCHAR, max_length=1024),
            FieldSchema(name="custom_metadata", dtype=DataType.VARCHAR, max_length=4096)
        ]
        
        schema = CollectionSchema(fields, f"RBAC-enabled collection for {collection_name}")
        
        # Create or get collection
        if utility.has_collection(collection_name):
            if overwrite:
                utility.drop_collection(collection_name)
            else:
                print(f"Collection '{collection_name}' already exists, skipping")
                return
        
        collection = Collection(collection_name, schema)
        print(f"Created RBAC-enabled collection '{collection_name}' with dimension {dim}")
        
        # Prepare data for insertion
        vectors = embeddings.tolist()
        texts = [f"Document {i}" for i in range(num_vectors)]
        
        # Create RBAC metadata for each document
        document_ids = [str(uuid.uuid4()) for _ in range(num_vectors)]
        document_types = ["document"] * num_vectors
        departments = [department] * num_vectors
        security_levels = [security_level] * num_vectors
        owner_ids = [owner_id] * num_vectors
        created_at = [int(time.time())] * num_vectors
        updated_at = [int(time.time())] * num_vectors
        allowed_roles_list = [json.dumps(allowed_roles or ["viewer"])] * num_vectors
        allowed_users_list = [json.dumps(allowed_users or [])] * num_vectors
        tags_list = [json.dumps(tags or [])] * num_vectors
        custom_metadata_list = [json.dumps(custom_metadata or {})] * num_vectors
        
        # Insert data with RBAC metadata
        data = [
            vectors,
            texts,
            document_ids,
            document_types,
            departments,
            security_levels,
            owner_ids,
            created_at,
            updated_at,
            allowed_roles_list,
            allowed_users_list,
            tags_list,
            custom_metadata_list
        ]
        
        collection.insert(data)
        collection.flush()
        print(f"Inserted {num_vectors} vectors with RBAC metadata into collection '{collection_name}'")
        
        # Create index
        index_params = {
            "metric_type": "IP",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 1024}
        }
        collection.create_index("vector", index_params)
        print("Created vector index")
        
        # Load collection
        collection.load()
        print("Collection loaded and ready for RBAC-enabled search")
        
        # Store collection reference
        self.milvus_collection = collection
        print("RBAC indexing success")
    
    def validate_document_access(
        self,
        user_id: str,
        document_id: str,
        action: str = "read"
    ) -> Dict[str, bool]:
        """
        Validate if user can access a specific document
        
        Args:
            user_id: User identifier
            document_id: Document identifier
            action: Action to perform (read, write, delete)
            
        Returns:
            Dictionary with access validation result
        """
        can_access = self.rbac_manager.validate_user_access(user_id, document_id, action)
        return {"can_access": can_access}
    
    def get_user_roles(self, user_id: str) -> Dict[str, List[str]]:
        """
        Get roles for a specific user
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with user roles
        """
        roles = self.rbac_manager.get_user_roles(user_id)
        return {"roles": roles}
    
    def get_user_departments(self, user_id: str) -> Dict[str, List[str]]:
        """
        Get departments for a specific user
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with user departments
        """
        departments = self.rbac_manager.get_user_departments(user_id)
        return {"departments": departments}


# Example usage
if __name__ == "__main__":
    # Create MCP server instance
    app = UltraRAG_MCP_Server("rbac-retriever")
    
    # Initialize RBAC retriever
    rbac_retriever = RBACRetriever(app)
    
    print("RBAC Retriever initialized successfully!")
    print("Available tools:")
    print("- retriever_search_with_rbac")
    print("- retriever_index_with_rbac")
    print("- validate_document_access")
    print("- get_user_roles")
    print("- get_user_departments")


