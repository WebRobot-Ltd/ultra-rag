"""
Example integration of authentication with MCP servers
Shows how to integrate auth with existing retriever.py
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server

from auth_middleware import AuthMiddleware
from database_client import DatabaseConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthenticatedMCPServer:
    """
    Example MCP server with authentication
    Based on existing retriever.py structure
    """
    
    def __init__(self, server_name: str = "authenticated-mcp-server"):
        self.server = Server(server_name)
        self.auth_middleware = AuthMiddleware()
        self._setup_handlers()
    
    async def initialize(self):
        """Initialize authentication system"""
        await self.auth_middleware.initialize()
        logger.info("Authenticated MCP server initialized")
    
    async def close(self):
        """Close authentication system"""
        await self.auth_middleware.close()
        logger.info("Authenticated MCP server closed")
    
    def _setup_handlers(self):
        """Setup MCP handlers with authentication"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list:
            """List available tools (no auth required)"""
            return [
                {
                    "name": "search_documents",
                    "description": "Search documents in the knowledge base",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "limit": {"type": "integer", "description": "Maximum results", "default": 10}
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "get_document",
                    "description": "Get a specific document by ID",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "document_id": {"type": "string", "description": "Document ID"}
                        },
                        "required": ["document_id"]
                    }
                },
                {
                    "name": "admin_stats",
                    "description": "Get admin statistics (admin only)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                }
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
            """Handle tool calls with authentication"""
            
            if name == "search_documents":
                return await self._search_documents(arguments)
            elif name == "get_document":
                return await self._get_document(arguments)
            elif name == "admin_stats":
                return await self._admin_stats(arguments)
            else:
                return {"error": f"Unknown tool: {name}"}
    
    @AuthMiddleware.require_scope("read")
    async def _search_documents(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Search documents (requires read scope)"""
        query = arguments.get("query", "")
        limit = arguments.get("limit", 10)
        
        # Get current user info
        user = self.auth_middleware.get_current_user()
        logger.info(f"User {user['username']} searching for: {query}")
        
        # Simulate document search
        results = [
            {
                "id": f"doc_{i}",
                "title": f"Document {i}",
                "content": f"Content related to {query}",
                "score": 0.9 - (i * 0.1)
            }
            for i in range(min(limit, 5))
        ]
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Found {len(results)} documents for query '{query}'"
                }
            ],
            "results": results
        }
    
    @AuthMiddleware.require_scope("read")
    async def _get_document(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get specific document (requires read scope)"""
        document_id = arguments.get("document_id", "")
        
        # Get current user info
        user = self.auth_middleware.get_current_user()
        logger.info(f"User {user['username']} requesting document: {document_id}")
        
        # Simulate document retrieval
        document = {
            "id": document_id,
            "title": f"Document {document_id}",
            "content": f"This is the content of document {document_id}",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Retrieved document {document_id}"
                }
            ],
            "document": document
        }
    
    @AuthMiddleware.require_admin()
    async def _admin_stats(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get admin statistics (requires admin role)"""
        user = self.auth_middleware.get_current_user()
        logger.info(f"Admin {user['username']} requesting stats")
        
        # Simulate admin statistics
        stats = {
            "total_documents": 1000,
            "total_users": 50,
            "active_sessions": 12,
            "storage_used": "2.5GB"
        }
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": "Admin statistics retrieved"
                }
            ],
            "stats": stats
        }
    
    async def run(self):
        """Run the MCP server"""
        try:
            await self.initialize()
            
            # Run with stdio transport
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="authenticated-mcp-server",
                        server_version="1.0.0",
                        capabilities=self.server.get_capabilities(
                            notification_options=None,
                            experimental_capabilities={}
                        )
                    )
                )
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            await self.close()

# Example usage
async def main():
    """Main function to run the authenticated MCP server"""
    server = AuthenticatedMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
