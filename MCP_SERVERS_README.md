# UltraRAG MCP Servers

This document describes how to use the UltraRAG MCP (Model Context Protocol) servers with AI agents.

## Available Servers

UltraRAG provides 9 specialized MCP servers for different RAG operations:

### Core Servers
- **sayhello** - Simple greeting server for testing MCP connectivity
- **corpus** - Document parsing and chunking operations
- **retriever** - Document retrieval and embedding operations  
- **reranker** - Document reranking and scoring
- **generation** - Text generation with LLM models

### Utility Servers
- **custom** - Custom operations and utilities
- **evaluation** - Model evaluation and metrics calculation
- **prompt** - Prompt management and templating
- **benchmark** - Performance benchmarking and testing

## Quick Start

### Option 1: Start All Servers
```bash
# Start all MCP servers
./start_mcp_servers.sh start

# Or using Python
python start_mcp_servers.py
```

### Option 2: Start Individual Servers
```bash
# Start specific server
./start_mcp_servers.sh start sayhello

# Or directly
python servers/sayhello/src/sayhello.py
```

### Option 3: Using Docker
```bash
# Build and run with all MCP servers
docker build -f Dockerfile.ultra-minimal -t ultrarag-mcp .
docker run -it ultrarag-mcp
```

## Server Management

```bash
# Check server status
./start_mcp_servers.sh status

# Stop all servers
./start_mcp_servers.sh stop

# Restart all servers
./start_mcp_servers.sh restart

# List available servers
./start_mcp_servers.sh list
```

## AI Agent Integration

### MCP Configuration
Use the provided `mcp_config.json` to configure your AI agent:

```json
{
  "mcpServers": {
    "ultrarag-sayhello": {
      "command": "python",
      "args": ["servers/sayhello/src/sayhello.py"]
    }
    // ... other servers
  }
}
```

### Example Usage
Each server exposes specific tools that can be called by AI agents:

```python
# Example: Using the sayhello server
from ultrarag.client import UltraRAGClient

client = UltraRAGClient("sayhello")
result = client.call_tool("greet", {"name": "World"})
print(result)  # {"msg": "Hello, World!"}
```

## Server Details

### sayhello Server
- **Purpose**: Test MCP connectivity
- **Tools**: `greet(name: str) -> Dict[str, str]`
- **Example**: `greet("Alice")` returns `{"msg": "Hello, Alice!"}`

### corpus Server  
- **Purpose**: Document processing
- **Tools**: 
  - `parse_documents(file_path) -> raw_data`
  - `chunk_documents(chunk_strategy, chunk_size, raw_data) -> status`
- **Supports**: PDF, DOCX, TXT, MD files

### retriever Server
- **Purpose**: Document retrieval and embedding
- **Tools**:
  - `retriever_init()` - Initialize retriever
  - `retriever_embed()` - Generate embeddings
  - `retriever_search()` - Search documents
- **Supports**: Faiss, LanceDB, OpenAI embeddings

### generation Server
- **Purpose**: Text generation with LLMs
- **Tools**:
  - `generate(prompt_ls, model_name, base_url) -> ans_ls`
  - `multimodal_generate()` - For image+text generation
- **Supports**: vLLM, OpenAI API, local models

## Troubleshooting

### Server Won't Start
1. Check Python environment: `python --version`
2. Install dependencies: `pip install -e .`
3. Check server path: `ls servers/[server_name]/src/`

### Connection Issues
1. Verify MCP transport: All servers use `stdio`
2. Check server logs for errors
3. Test with sayhello server first

### Performance Issues
1. Monitor resource usage: `./start_mcp_servers.sh status`
2. Check GPU availability for GPU-enabled servers
3. Adjust batch sizes in server configurations

## Development

### Adding New Servers
1. Create directory: `servers/new_server/`
2. Add `parameter.yaml` configuration
3. Implement `src/new_server.py` with MCP tools
4. Update `start_mcp_servers.sh` and `mcp_config.json`

### Server Architecture
Each server follows this pattern:
```python
from ultrarag.server import UltraRAG_MCP_Server

app = UltraRAG_MCP_Server("server_name")

@app.tool(output="input->output")
def my_tool(input_param: str) -> Dict[str, str]:
    # Tool implementation
    return {"output": "result"}

if __name__ == "__main__":
    app.run(transport="stdio")
```

## Support

For issues and questions:
- Check server logs: `./start_mcp_servers.sh status`
- Review server-specific documentation in `servers/[name]/`
- Open issues on the UltraRAG GitHub repository
