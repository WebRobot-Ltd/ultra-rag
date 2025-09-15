#!/bin/bash

# Script per testare tutti gli endpoint MCP UltraRAG su metaglobe.finance
# Verifica che l'autenticazione funzioni correttamente su tutti i domini

set -e

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Test di tutti gli endpoint MCP UltraRAG${NC}"
echo "=================================================="

# Array degli endpoint da testare
declare -A endpoints=(
    ["retriever"]="retriever-mcp.metaglobe.finance"
    ["generation"]="generation-mcp.metaglobe.finance"
    ["corpus"]="corpus-mcp.metaglobe.finance"
    ["reranker"]="reranker-mcp.metaglobe.finance"
    ["evaluation"]="evaluation-mcp.metaglobe.finance"
    ["benchmark"]="benchmark-mcp.metaglobe.finance"
    ["custom"]="custom-mcp.metaglobe.finance"
    ["prompt"]="prompt-mcp.metaglobe.finance"
    ["router"]="router-mcp.metaglobe.finance"
)

# Contatori per statistiche
total_tests=0
successful_tests=0
failed_tests=0

echo -e "\n${YELLOW}📋 Testando autenticazione su tutti gli endpoint...${NC}\n"

# Funzione per testare un singolo endpoint
test_endpoint() {
    local service_name=$1
    local domain=$2
    local url="https://${domain}/mcp"
    
    echo -e "${BLUE}🔍 Testando ${service_name} (${domain})${NC}"
    
    # Test senza autenticazione (dovrebbe restituire 401)
    local response
    local http_code
    local response_body
    
    response=$(curl -s -w "\n%{http_code}" \
        -X POST "$url" \
        -H 'Content-Type: application/json' \
        -H 'Accept: application/json, text/event-stream' \
        -d '{"jsonrpc": "2.0", "method": "initialize", "params": {}, "id": 1}' \
        --max-time 10 \
        --connect-timeout 5)
    
    http_code=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | head -n -1)
    
    total_tests=$((total_tests + 1))
    
    if [ "$http_code" = "401" ]; then
        if echo "$response_body" | grep -q "Authentication required"; then
            echo -e "  ✅ ${GREEN}SUCCESS${NC} - 401 Unauthorized con messaggio di autenticazione"
            successful_tests=$((successful_tests + 1))
        else
            echo -e "  ⚠️  ${YELLOW}PARTIAL${NC} - 401 OK ma messaggio inaspettato"
            echo -e "      Response: $response_body"
            successful_tests=$((successful_tests + 1))
        fi
    elif [ "$http_code" = "404" ]; then
        echo -e "  ❌ ${RED}FAILED${NC} - 404 Not Found (ingress non configurato)"
        failed_tests=$((failed_tests + 1))
    elif [ "$http_code" = "000" ]; then
        echo -e "  ❌ ${RED}FAILED${NC} - Timeout o connessione fallita"
        failed_tests=$((failed_tests + 1))
    else
        echo -e "  ❌ ${RED}FAILED${NC} - HTTP $http_code (comportamento inaspettato)"
        echo -e "      Response: $response_body"
        failed_tests=$((failed_tests + 1))
    fi
    
    echo ""
}

# Testa tutti gli endpoint
for service in "${!endpoints[@]}"; do
    test_endpoint "$service" "${endpoints[$service]}"
done

# Statistiche finali
echo "=================================================="
echo -e "${BLUE}📊 RISULTATI FINALI${NC}"
echo "=================================================="
echo -e "Totale test: $total_tests"
echo -e "Successi: ${GREEN}$successful_tests${NC}"
echo -e "Fallimenti: ${RED}$failed_tests${NC}"

if [ $failed_tests -eq 0 ]; then
    echo -e "\n🎉 ${GREEN}TUTTI I TEST SUPERATI!${NC}"
    echo -e "L'autenticazione è configurata correttamente su tutti gli endpoint."
    exit 0
else
    echo -e "\n⚠️  ${YELLOW}ALCUNI TEST FALLITI${NC}"
    echo -e "Verificare la configurazione degli ingress per gli endpoint falliti."
    exit 1
fi
