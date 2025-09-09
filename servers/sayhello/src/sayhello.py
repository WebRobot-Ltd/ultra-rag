from typing import Dict

from ultrarag.server import UltraRAG_MCP_Server

app = UltraRAG_MCP_Server("sayhello")


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
