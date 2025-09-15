#!/bin/bash

# Script per aggiornare tutti gli ingress MCP rimuovendo l'autenticazione Basic Auth
# e mantenendo solo il middleware CORS

echo "=== Aggiornamento Ingress MCP - Rimozione Autenticazione Basic Auth ==="

# Lista degli ingress "secure" da aggiornare
INGRESS_LIST=(
    "ultrarag-mcp-benchmark-secure"
    "ultrarag-mcp-corpus-secure"
    "ultrarag-mcp-custom-secure"
    "ultrarag-mcp-evaluation-secure"
    "ultrarag-mcp-generation-secure"
    "ultrarag-mcp-prompt-secure"
    "ultrarag-mcp-reranker-secure"
    "ultrarag-mcp-retriever-secure"
    "ultrarag-mcp-router-secure"
)

# Funzione per aggiornare un singolo ingress
update_ingress() {
    local ingress_name=$1
    echo "Aggiornando $ingress_name..."
    
    # Rimuove il middleware di autenticazione, mantiene solo CORS
    kubectl patch ingress "$ingress_name" --type='json' -p='[{"op": "replace", "path": "/metadata/annotations/traefik.ingress.kubernetes.io~1router.middlewares", "value": "default-ultrarag-mcp-cors@kubernetescrd"}]'
    
    if [ $? -eq 0 ]; then
        echo "✅ $ingress_name aggiornato con successo"
    else
        echo "❌ Errore nell'aggiornamento di $ingress_name"
    fi
}

# Aggiorna tutti gli ingress
for ingress in "${INGRESS_LIST[@]}"; do
    update_ingress "$ingress"
    echo ""
done

echo "=== Verifica finale ==="
echo "Controllo degli ingress aggiornati:"
kubectl get ingress | grep mcp | grep secure

echo ""
echo "=== Test di connettività ==="
echo "Testando alcuni endpoint per verificare che funzionino..."

# Test di alcuni endpoint principali
test_endpoints=(
    "https://retriever-mcp.metaglobe.finance/mcp"
    "https://generation-mcp.metaglobe.finance/mcp"
    "https://corpus-mcp.metaglobe.finance/mcp"
)

for endpoint in "${test_endpoints[@]}"; do
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
echo "=== Aggiornamento completato ==="
