from typing import Dict

from ultrarag.server import UltraRAG_MCP_Server

# Initialize server with authentication enabled
enable_auth = os.environ.get('ENABLE_AUTH', 'false').lower() == 'true'
auth_config = {
    'database_url': os.environ.get('DATABASE_URL', 'postgresql://user:password@localhost:5432/strapi'),
    'jwt_secret': os.environ.get('JWT_SECRET', 'your-secret-key'),
    'api_key_header': 'X-API-Key'
}

app = UltraRAG_MCP_Server(
    "sayhello",
    enable_auth=enable_auth,
    auth_config=auth_config
)


@app.tool(output="name->msg")
def greet(name: str) -> Dict[str, str]:
    ret = f"Hello, {name}!"
    app.logger.info(ret)
    return {"msg": ret}


if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='UltraRAG MCP Server - SayHello')
    parser.add_argument('--transport', default='stdio', choices=['stdio', 'http'], help='Transport type')
    parser.add_argument('--port', type=int, default=8000, help='Port for HTTP transport')
    parser.add_argument('--host', default='0.0.0.0', help='Host for HTTP transport')
    
    args = parser.parse_args()
    
    if args.transport == 'http':
        app.run(transport="http", host=args.host, port=args.port)
    else:
        app.run(transport="stdio")
