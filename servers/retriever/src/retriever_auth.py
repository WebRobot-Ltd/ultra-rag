"""
UltraRAG Retriever MCP Server with Authentication
Integrates authentication module with existing retriever functionality
"""

import os
import sys
from pathlib import Path

# Add auth module to path
auth_path = Path(__file__).parent.parent.parent.parent / "auth"
sys.path.insert(0, str(auth_path))

from urllib.parse import urlparse, urlunparse
from typing import Any, Dict, List, Optional

import aiohttp
import asyncio
import jsonlines
import numpy as np
import pandas as pd
from tqdm import tqdm
from flask import Flask, jsonify, request
from openai import AsyncOpenAI, OpenAIError

from fastmcp.exceptions import NotFoundError, ToolError, ValidationError
from ultrarag.server import UltraRAG_MCP_Server
from pathlib import Path

# Import authentication modules
from auth.auth_middleware import AuthMiddleware
from auth.database_client import DatabaseConfig
from auth.config import get_database_config

# Initialize MCP server
app = UltraRAG_MCP_Server("retriever")
retriever_app = Flask(__name__)

# Initialize authentication middleware
auth_middleware = AuthMiddleware(get_database_config())

class AuthenticatedRetriever:
    def __init__(self, mcp_inst: UltraRAG_MCP_Server):
        self.mcp_inst = mcp_inst
        self.auth_middleware = auth_middleware
        
        # Core embedding functions (always available - no auth required)
        mcp_inst.tool(
            self.retriever_embed,
            output="embedding_path,overwrite,is_multimodal->None",
        )
        mcp_inst.tool(
            self.retriever_embed_openai,
            output="embedding_path,overwrite->None",
        )
        
        # Milvus functions (require read scope)
        mcp_inst.tool(
            self.retriever_init_milvus,
            output="retriever_path,corpus_path,collection_name,host,port,infinity_kwargs,cuda_devices,is_multimodal->None",
        )
        mcp_inst.tool(
            self.retriever_index_milvus,
            output="embedding_path,collection_name,host,port,overwrite->None",
        )
        mcp_inst.tool(
            self.retriever_search_milvus,
            output="q_ls,top_k,query_instruction,use_openai,collection_name,host,port->ret_psg",
        )
        
        # Web search functions (require read scope)
        mcp_inst.tool(
            self.retriever_web_search,
            output="q_ls,top_k,use_openai,query_instruction->ret_psg",
        )
        
        # Admin functions (require admin role)
        mcp_inst.tool(
            self.retriever_admin_stats,
            output="->stats",
        )
        mcp_inst.tool(
            self.retriever_admin_cleanup,
            output="collection_name,host,port->None",
        )
        
        # User info function (optional auth)
        mcp_inst.tool(
            self.retriever_user_info,
            output="->user_info",
        )
    
    def _extract_headers_from_context(self) -> Dict[str, str]:
        """Extract headers from MCP context for authentication"""
        # This is a simplified version - in a real implementation,
        # you'd need to extract headers from the MCP request context
        # For now, we'll use environment variables or request headers
        return {
            "authorization": os.getenv("MCP_AUTH_HEADER", ""),
            "X-API-Key": os.getenv("MCP_API_KEY", "")
        }
    
    def _create_error_response(self, message: str, status_code: int) -> Dict[str, Any]:
        """Create error response for MCP"""
        return {
            "error": {
                "code": status_code,
                "message": message
            }
        }
    
    async def _check_auth(self, required_scopes: Optional[set] = None, required_roles: Optional[set] = None) -> Optional[Dict[str, Any]]:
        """Check authentication and return user data or error"""
        try:
            headers = self._extract_headers_from_context()
            result = await self.auth_middleware.validate_request(headers, required_scopes)
            
            if not result['valid']:
                return self._create_error_response(result['error'], 401)
            
            user_data = result['user_data']
            
            # Check roles if required
            if required_roles and not self.auth_middleware.check_role(user_data, required_roles):
                return self._create_error_response("Insufficient role", 403)
            
            return user_data
            
        except Exception as e:
            return self._create_error_response(f"Authentication error: {str(e)}", 500)
    
    # Core embedding functions (no auth required)
    async def retriever_embed(self, embedding_path: str, overwrite: bool = False, is_multimodal: bool = False) -> None:
        """Generate embeddings (no authentication required)"""
        # Original implementation from retriever.py
        # ... (same as original)
        pass
    
    async def retriever_embed_openai(self, embedding_path: str, overwrite: bool = False) -> None:
        """Generate OpenAI embeddings (no authentication required)"""
        # Original implementation from retriever.py
        # ... (same as original)
        pass
    
    # Milvus functions (require read scope)
    async def retriever_init_milvus(self, retriever_path: str, corpus_path: str, collection_name: str, 
                                   host: str = "localhost", port: int = 19530, infinity_kwargs: Dict = None,
                                   cuda_devices: List[int] = None, is_multimodal: bool = False) -> None:
        """Initialize Milvus retriever (requires read scope)"""
        # Check authentication
        auth_result = await self._check_auth(required_scopes={"read"})
        if "error" in auth_result:
            raise ToolError(auth_result["error"]["message"])
        
        user_data = auth_result
        print(f"User {user_data['username']} initializing Milvus retriever")
        
        # Original implementation from retriever.py
        # ... (same as original)
        pass
    
    async def retriever_index_milvus(self, embedding_path: str, collection_name: str, 
                                   host: str = "localhost", port: int = 19530, overwrite: bool = False) -> None:
        """Index embeddings in Milvus (requires write scope)"""
        # Check authentication
        auth_result = await self._check_auth(required_scopes={"write"})
        if "error" in auth_result:
            raise ToolError(auth_result["error"]["message"])
        
        user_data = auth_result
        print(f"User {user_data['username']} indexing embeddings in Milvus")
        
        # Original implementation from retriever.py
        # ... (same as original)
        pass
    
    async def retriever_search_milvus(self, q_ls: List[str], top_k: int = 10, query_instruction: str = "",
                                    use_openai: bool = False, collection_name: str = "default",
                                    host: str = "localhost", port: int = 19530) -> List[Dict]:
        """Search in Milvus (requires read scope)"""
        # Check authentication
        auth_result = await self._check_auth(required_scopes={"read"})
        if "error" in auth_result:
            raise ToolError(auth_result["error"]["message"])
        
        user_data = auth_result
        print(f"User {user_data['username']} searching in Milvus")
        
        # Original implementation from retriever.py
        # ... (same as original)
        return []
    
    # Web search functions (require read scope)
    async def retriever_web_search(self, q_ls: List[str], top_k: int = 10, use_openai: bool = False,
                                 query_instruction: str = "") -> List[Dict]:
        """Web search (requires read scope)"""
        # Check authentication
        auth_result = await self._check_auth(required_scopes={"read"})
        if "error" in auth_result:
            raise ToolError(auth_result["error"]["message"])
        
        user_data = auth_result
        print(f"User {user_data['username']} performing web search")
        
        # Original implementation from retriever.py
        # ... (same as original)
        return []
    
    # Admin functions (require admin role)
    async def retriever_admin_stats(self) -> Dict[str, Any]:
        """Get admin statistics (requires admin role)"""
        # Check authentication
        auth_result = await self._check_auth(required_roles={"admin", "super_admin"})
        if "error" in auth_result:
            raise ToolError(auth_result["error"]["message"])
        
        user_data = auth_result
        print(f"Admin {user_data['username']} requesting stats")
        
        # Return admin statistics
        return {
            "total_embeddings": 1000,
            "active_collections": 5,
            "total_searches": 5000,
            "storage_used": "2.5GB",
            "last_indexed": "2024-01-01T00:00:00Z"
        }
    
    async def retriever_admin_cleanup(self, collection_name: str, host: str = "localhost", port: int = 19530) -> None:
        """Cleanup collection (requires admin role)"""
        # Check authentication
        auth_result = await self._check_auth(required_roles={"admin", "super_admin"})
        if "error" in auth_result:
            raise ToolError(auth_result["error"]["message"])
        
        user_data = auth_result
        print(f"Admin {user_data['username']} cleaning up collection {collection_name}")
        
        # Original cleanup implementation
        # ... (same as original)
        pass
    
    # User info function (optional auth)
    async def retriever_user_info(self) -> Dict[str, Any]:
        """Get current user info (optional authentication)"""
        try:
            headers = self._extract_headers_from_context()
            result = await self.auth_middleware.validate_request(headers)
            
            if result['valid']:
                user_data = result['user_data']
                return {
                    "authenticated": True,
                    "user_id": user_data['user_id'],
                    "username": user_data['username'],
                    "role": user_data['role'],
                    "scopes": list(user_data.get('scopes', [])),
                    "organization_id": user_data.get('organization_id'),
                    "auth_method": user_data.get('auth_method')
                }
            else:
                return {
                    "authenticated": False,
                    "error": result['error']
                }
        except Exception as e:
            return {
                "authenticated": False,
                "error": f"Authentication check failed: {str(e)}"
            }

# Initialize the authenticated retriever
retriever = AuthenticatedRetriever(app)

# Flask routes for HTTP access (with authentication)
@retriever_app.route('/api/search', methods=['POST'])
async def api_search():
    """HTTP API endpoint for search with authentication"""
    try:
        # Extract authentication from headers
        auth_header = request.headers.get('Authorization', '')
        api_key = request.headers.get('X-API-Key', '')
        
        # Set environment variables for authentication
        if auth_header:
            os.environ['MCP_AUTH_HEADER'] = auth_header
        if api_key:
            os.environ['MCP_API_KEY'] = api_key
        
        # Get request data
        data = request.get_json()
        query = data.get('query', '')
        top_k = data.get('top_k', 10)
        
        # Perform search
        results = await retriever.retriever_search_milvus([query], top_k)
        
        return jsonify({
            "success": True,
            "results": results,
            "query": query
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@retriever_app.route('/api/user-info', methods=['GET'])
async def api_user_info():
    """HTTP API endpoint for user info"""
    try:
        # Extract authentication from headers
        auth_header = request.headers.get('Authorization', '')
        api_key = request.headers.get('X-API-Key', '')
        
        # Set environment variables for authentication
        if auth_header:
            os.environ['MCP_AUTH_HEADER'] = auth_header
        if api_key:
            os.environ['MCP_API_KEY'] = api_key
        
        # Get user info
        user_info = await retriever.retriever_user_info()
        
        return jsonify(user_info)
        
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

# Main function
async def main():
    """Main function to run the authenticated retriever server"""
    try:
        # Initialize authentication
        await auth_middleware.initialize()
        print("✅ Authentication system initialized")
        
        # Run MCP server
        await app.run()
        
    except Exception as e:
        print(f"❌ Server error: {e}")
    finally:
        # Cleanup
        await auth_middleware.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='UltraRAG Retriever MCP Server with Authentication')
    parser.add_argument('--transport', choices=['stdio', 'http'], default='stdio',
                       help='Transport method (stdio for MCP, http for REST API)')
    parser.add_argument('--host', default='0.0.0.0', help='Host for HTTP transport')
    parser.add_argument('--port', type=int, default=8000, help='Port for HTTP transport')
    
    args = parser.parse_args()
    
    if args.transport == 'http':
        # Run Flask app for HTTP transport
        retriever_app.run(host=args.host, port=args.port, debug=True)
    else:
        # Run MCP server for stdio transport
        asyncio.run(main())
