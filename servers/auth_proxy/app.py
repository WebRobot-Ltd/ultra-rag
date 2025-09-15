import os
import asyncio
from typing import Dict, Any

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, StreamingResponse, Response
from starlette.routing import Route
import aiohttp


# Try to import existing auth modules (aligned with Strapi schema)
try:
    from auth.auth_manager import AuthManager
    from auth.api_key_validator import APIKeyValidator
    AUTH_AVAILABLE = True
except Exception:
    AUTH_AVAILABLE = False
    AuthManager = None  # type: ignore
    APIKeyValidator = None  # type: ignore


UPSTREAM_URL = os.getenv("UPSTREAM_URL", "http://127.0.0.1:8002/mcp")


def _accept_header_valid(request: Request) -> bool:
    accept = request.headers.get("accept", "").lower()
    return ("application/json" in accept) and ("text/event-stream" in accept)


async def _auth_ok(headers: Dict[str, str]) -> bool:
    if not AUTH_AVAILABLE:
        return False

    # Import database client here to avoid circular imports
    try:
        from auth.database_client import DatabaseClient
        from auth.config import get_database_config
        
        db_config = get_database_config()
        db_client = DatabaseClient(db_config)
    except Exception as e:
        print(f"Failed to initialize database client: {e}")
        return False

    api_key = headers.get("x-api-key") or headers.get("authorization")
    if api_key:
        if api_key.startswith("Bearer "):
            token = api_key[7:]
            # Try JWT first
            try:
                manager = AuthManager()
                if await manager.validate_jwt_token(token):
                    return True
            except Exception as e:
                print(f"JWT validation failed: {e}")
                pass
            # Fallback to raw API key validation
            try:
                validator = APIKeyValidator()
                result = await validator.validate_api_key(token, db_client)
                if result:
                    return True
            except Exception as e:
                print(f"API key validation failed: {e}")
                pass
        else:
            try:
                validator = APIKeyValidator()
                result = await validator.validate_api_key(api_key, db_client)
                if result:
                    return True
            except Exception as e:
                print(f"API key validation failed: {e}")
                pass

    return False


async def mcp_proxy(request: Request) -> Response:
    # Enforce required Accept header for MCP
    if not _accept_header_valid(request):
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "id": "server-error",
                "error": {
                    "code": -32600,
                    "message": "Not Acceptable: Client must accept both application/json and text/event-stream",
                },
            },
            status_code=406,
        )

    # Enforce authentication
    if not await _auth_ok({k.lower(): v for k, v in request.headers.items()}):
        return JSONResponse(
            {
                "error": "Unauthorized",
                "message": "Authentication required. Provide valid API key or JWT.",
            },
            status_code=401,
        )

    # Forward to upstream MCP server, streaming the response for SSE
    body = await request.body()
    forward_headers: Dict[str, str] = {}
    for k, v in request.headers.items():
        # Filter hop-by-hop headers; keep content and accept headers
        if k.lower() in {"content-type", "accept", "authorization", "x-api-key"}:
            forward_headers[k] = v

    async def streamer() -> Any:
        timeout = aiohttp.ClientTimeout(total=None)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(UPSTREAM_URL, data=body, headers=forward_headers) as resp:
                # Propagate headers important for SSE
                content_type = resp.headers.get("content-type", "application/json")
                # Stream chunks
                async for chunk in resp.content.iter_chunked(1024):
                    yield chunk

    # We do an initial HEAD request to get status and headers would require buffering; instead,
    # perform a single request and stream body; use 200 OK as typical for MCP initialize.
    # If upstream returns non-200, clients typically handle JSON error as a stream as well.
    return StreamingResponse(streamer(), media_type="text/event-stream")


routes = [Route("/mcp", mcp_proxy, methods=["POST"])]
app = Starlette(routes=routes)


