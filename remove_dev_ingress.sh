#!/bin/bash

# Script per rimuovere tutti gli ingress MCP di sviluppo
# Manteniamo solo quelli di produzione con autenticazione

echo "=== Rimozione Ingress MCP di Sviluppo ==="

# Lista degli ingress "dev" da rimuovere
DEV_INGRESS_LIST=(
    "ultrarag-mcp-benchmark-dev"
    "ultrarag-mcp-corpus-dev"
    "ultrarag-mcp-custom-dev"
    "ultrarag-mcp-evaluation-dev"
    "ultrarag-mcp-generation-dev"
    "ultrarag-mcp-prompt-dev"
    "ultrarag-mcp-reranker-dev"
    "ultrarag-mcp-retriever-dev"
    "ultrarag-mcp-router-dev"
)

# Funzione per rimuovere un singolo ingress
remove_ingress() {
    local ingress_name=$1
    echo "Rimuovendo $ingress_name..."
    
    kubectl delete ingress "$ingress_name"
    
    if [ $? -eq 0 ]; then
        echo "✅ $ingress_name rimosso con successo"
    else
        echo "❌ Errore nella rimozione di $ingress_name"
    fi
}

# Rimuove tutti gli ingress dev
for ingress in "${DEV_INGRESS_LIST[@]}"; do
    remove_ingress "$ingress"
    echo ""
done

echo "=== Verifica finale ==="
echo "Ingress MCP rimanenti (solo produzione):"
kubectl get ingress | grep mcp

echo ""
echo "=== Test endpoint di produzione ==="
echo "Testando alcuni endpoint di produzione per verificare che funzionino..."

# Test di alcuni endpoint di produzione
prod_endpoints=(
    "https://retriever-mcp.metaglobe.finance/mcp"
    "https://generation-mcp.metaglobe.finance/mcp"
    "https://corpus-mcp.metaglobe.finance/mcp"
    "https://benchmark-mcp.metaglobe.finance/mcp"
    "https://custom-mcp.metaglobe.finance/mcp"
    "https://router-mcp.metaglobe.finance/mcp"
)

for endpoint in "${prod_endpoints[@]}"; do
    echo "Testando $endpoint..."
    response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$endpoint" \
        -H 'Content-Type: application/json' \
        -H 'Accept: application/json, text/event-stream' \
        -d '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test-client", "version": "1.0.0"}}}' \
        -k)
    
    if [ "$response" = "200" ]; then
        echo "✅ $endpoint - OK (200)"
    else
        echo "❌ $endpoint - ERRORE ($response)"
    fi
done

echo ""
echo "=== Rimozione completata ==="
echo "Solo gli endpoint di produzione con autenticazione sono ora attivi"
