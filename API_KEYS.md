# API Keys per UltraRAG MCP Servers

## Test API Key Generata

**Data di creazione:** $(date)
**Scopo:** Testing autenticazione UltraRAG MCP Servers
**Stato:** Attiva

### Dettagli API Key

```
API Key ID: M7YjfDoD
API Key Secret: 9N9n10uxAe60M6ieGwOuPPRIDzlZooJu
API Key Completa: M7YjfDoD:9N9n10uxAe60M6ieGwOuPPRIDzlZooJu
```

### Utilizzo

Per testare l'autenticazione sui servizi MCP UltraRAG, utilizzare questa API key nell'header:

```bash
curl -H "X-API-Key: M7YjfDoD:9N9n10uxAe60M6ieGwOuPPRIDzlZooJu" \
     -X POST "https://retriever-mcp.metaglobe.finance/mcp" \
     -H 'Content-Type: application/json' \
     -d '{"jsonrpc": "2.0", "method": "initialize", "params": {}, "id": 1}'
```

### Endpoint Testabili

- **Retriever:** `https://retriever-mcp.metaglobe.finance:8100/mcp`
- **Generation:** `https://generation-mcp.metaglobe.finance:8101/mcp`
- **Corpus:** `https://corpus-mcp.metaglobe.finance:8102/mcp`
- **Reranker:** `https://reranker-mcp.metaglobe.finance:8103/mcp`
- **Evaluation:** `https://evaluation-mcp.metaglobe.finance:8104/mcp`
- **Benchmark:** `https://benchmark-mcp.metaglobe.finance:8105/mcp`
- **Custom:** `https://custom-mcp.metaglobe.finance:8106/mcp`
- **Prompt:** `https://prompt-mcp.metaglobe.finance:8107/mcp`
- **Router:** `https://router-mcp.metaglobe.finance:8108/mcp`

### Database

- **Host:** nuvolaris-postgres.nuvolaris.svc.cluster.local
- **Port:** 5432
- **Database:** webrobotdb
- **User:** postgres
- **Tabella:** api_keys

### Note

- Questa API key è stata generata per scopi di testing
- È valida per tutti gli endpoint MCP UltraRAG
- Per produzione, generare nuove API keys con scadenza appropriata
- L'API key è stata inserita nel database PostgreSQL del cluster Kubernetes
