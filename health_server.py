#!/usr/bin/env python3
"""
UltraRAG Health Check HTTP Server
"""
import asyncio
import sys
import os
from aiohttp import web
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def health_check(request):
    """Health check endpoint"""
    try:
        # Basic health check - just return OK if server is running
        return web.json_response({
            "status": "healthy",
            "service": "ultrarag-mcp",
            "version": "2.0-supervisor"
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return web.json_response({
            "status": "unhealthy",
            "error": str(e)
        }, status=500)

async def create_app():
    """Create the health check web application"""
    app = web.Application()
    app.router.add_get('/health', health_check)
    app.router.add_get('/', health_check)  # Root path also returns health
    return app

async def main():
    """Main function to start the health server"""
    try:
        app = await create_app()
        
        # Get port from environment or default to 8080
        port = int(os.environ.get('HEALTH_PORT', 8080))
        host = os.environ.get('HEALTH_HOST', '0.0.0.0')
        
        logger.info(f"Starting health server on {host}:{port}")
        
        # Start the server
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(runner, host, port)
        await site.start()
        
        logger.info(f"Health server started successfully on {host}:{port}")
        
        # Keep the server running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down health server...")
        finally:
            await runner.cleanup()
            
    except Exception as e:
        logger.error(f"Failed to start health server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
