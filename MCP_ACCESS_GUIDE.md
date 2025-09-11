# UltraRAG MCP Servers - Access Guide

## Panoramica

I server MCP (Model Context Protocol) di UltraRAG sono ora esposti tramite Ingress Kubernetes e accessibili da applicazioni esterne che supportano il protocollo MCP.

## Endpoints Disponibili

| Server | Porta | Endpoint | Descrizione |
|--------|-------|----------|-------------|
| Health | 8000 | `/health` | Health check e monitoraggio |
| SayHello | 8001 | `/sayhello` | Server di test e validazione |
| Retriever | 8002 | `/retriever` | Retrieval e indicizzazione documenti |
| Generation | 8003 | `/generation` | Generazione testo con LLM |
| Corpus | 8004 | `/corpus` | Parsing e preprocessing documenti |
| Reranker | 8005 | `/reranker` | Reranking risultati di ricerca |
| Evaluation | 8006 | `/evaluation` | Valutazione qualità risposte |
| Benchmark | 8007 | `/benchmark` | Benchmarking performance |
| Custom | 8008 | `/custom` | Funzionalità personalizzate |
| Prompt | 8009 | `/prompt` | Gestione prompt templates |
| Router | 8010 | `/router` | Routing richieste |

## Accesso

### URL Base (Produzione con Autenticazione)
```
https://ultrarag-mcp.webrobot.local
```

### URL Base (Sviluppo senza Autenticazione)
```
https://ultrarag-mcp-dev.webrobot.local
```

### Autenticazione (Solo per URL di produzione)
- **Username**: `admin`
- **Password**: `UltraRAG2025Secure`

### Esempi di URL Completi
```
# Produzione (con autenticazione)
https://ultrarag-mcp.webrobot.local/health
https://ultrarag-mcp.webrobot.local/retriever/mcp
https://ultrarag-mcp.webrobot.local/corpus/mcp

# Sviluppo (senza autenticazione)
https://ultrarag-mcp-dev.webrobot.local/health
https://ultrarag-mcp-dev.webrobot.local/retriever/mcp
https://ultrarag-mcp-dev.webrobot.local/corpus/mcp
```

## Configurazione per Applicazioni MCP

### 1. Configurazione FastMCP
```json
{
  "mcpServers": {
    "ultrarag-retriever": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-everything"],
      "env": {
        "MCP_SERVER_URL": "https://ultrarag-mcp.webrobot.local/retriever"
      }
    }
  }
}
```

### 2. Configurazione Claude Desktop
Aggiungi al file `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "ultrarag": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-everything"],
      "env": {
        "MCP_SERVER_URL": "https://ultrarag-mcp.webrobot.local/retriever"
      }
    }
  }
}
```

## Test degli Endpoint

### 1. Health Check (Produzione)
```bash
curl -u admin:UltraRAG2025Secure https://ultrarag-mcp.webrobot.local/health
```

### 2. Health Check (Sviluppo)
```bash
curl https://ultrarag-mcp-dev.webrobot.local/health
```

### 3. Test MCP Protocol (Produzione)
```bash
curl -u admin:UltraRAG2025Secure \
  -X POST https://ultrarag-mcp.webrobot.local/retriever/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {
        "name": "test-client",
        "version": "1.0.0"
      }
    }
  }'
```

### 4. Test MCP Protocol (Sviluppo)
```bash
curl -X POST https://ultrarag-mcp-dev.webrobot.local/retriever/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {
        "name": "test-client",
        "version": "1.0.0"
      }
    }
  }'
```

## Funzionalità Principali

### Retriever Server (Porta 8002)
- **Inizializzazione**: `retriever_init_milvus`
- **Embedding**: `retriever_embed`
- **Indicizzazione**: `retriever_index_milvus`
- **Ricerca**: `retriever_search_milvus`
- **Ricerca Web**: `retriever_exa_search`, `retriever_tavily_search`

### Corpus Server (Porta 8004)
- **Parsing**: `parse_documents` - Estrae testo da PDF, DOCX, TXT, MD
- **Chunking**: `chunk_documents` - Segmenta documenti in chunk

### Generation Server (Porta 8003)
- **Generazione**: `generate` - Genera testo da prompt
- **Multimodale**: `multimodal_generate` - Genera da prompt multimodali

## Esempio di Utilizzo

### 1. Parsing di un PDF
```python
import asyncio
from fastmcp import Client

async def parse_pdf():
    client = Client({
        "mcpServers": {
            "corpus": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-everything"],
                "env": {
                    "MCP_SERVER_URL": "https://ultrarag-mcp.webrobot.local/corpus"
                }
            }
        }
    })
    
    async with client:
        result = await client.call_tool(
            "corpus.parse_documents",
            {"file_path": "/path/to/document.pdf"}
        )
        print(f"Documento parsato: {len(result)} caratteri")

asyncio.run(parse_pdf())
```

### 2. Indicizzazione e Ricerca
```python
async def index_and_search():
    client = Client({
        "mcpServers": {
            "retriever": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-everything"],
                "env": {
                    "MCP_SERVER_URL": "https://ultrarag-mcp.webrobot.local/retriever"
                }
            }
        }
    })
    
    async with client:
        # Inizializza retriever
        await client.call_tool("retriever.retriever_init_milvus", {
            "retriever_path": "/tmp/retriever",
            "corpus_path": "/path/to/documents",
            "collection_name": "my_collection",
            "host": "localhost",
            "port": 19530
        })
        
        # Cerca documenti
        results = await client.call_tool("retriever.retriever_search_milvus", {
            "q_ls": ["query di ricerca"],
            "top_k": 5,
            "collection_name": "my_collection"
        })
        
        print(f"Trovati {len(results)} risultati")

asyncio.run(index_and_search())
```

## Sicurezza

- Tutti gli endpoint sono protetti con autenticazione Basic HTTP
- CORS è abilitato per consentire l'accesso da applicazioni web
- I timeout sono configurati per gestire operazioni lunghe
- La dimensione massima del body è impostata a 50MB

## Monitoraggio

- Health check disponibile su `/health`
- Log centralizzati in `/var/log/supervisor/`
- Tutti i server sono gestiti da Supervisor per auto-restart

## Supporto

Per problemi o domande:
- Controlla i log: `kubectl logs ultrarag-<pod-name>`
- Verifica lo stato: `kubectl get pods -l app=ultrarag`
- Testa la connettività: `curl -u admin:UltraRAG2025Secure https://ultrarag-mcp.webrobot.local/health`
