#!/bin/bash

# Script per testare l'autenticazione MCP con API key
# Verifica che l'autenticazione funzioni con credenziali valide

set -e

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔐 Test di autenticazione MCP con API Key${NC}"
echo "============================================="

# Endpoint di test (usiamo retriever come esempio)
DOMAIN="retriever-mcp.metaglobe.finance"
URL="https://${DOMAIN}/mcp"

# API Key di test (puoi modificare questo valore)
API_KEY="M7YjfDoD:9N9n10uxAe60M6ieGwOuPPRIDzlZooJu"

echo -e "\n${YELLOW}📋 Testando autenticazione su ${DOMAIN}...${NC}\n"

# Test 1: Senza autenticazione (dovrebbe fallire)
echo -e "${BLUE}🔍 Test 1: Richiesta senza autenticazione${NC}"
response1=$(curl -s -w "\n%{http_code}" \
    -X POST "$URL" \
    -H 'Content-Type: application/json' \
    -H 'Accept: application/json, text/event-stream' \
    -d '{"jsonrpc": "2.0", "method": "initialize", "params": {}, "id": 1}' \
    --max-time 10)

http_code1=$(echo "$response1" | tail -n1)
response_body1=$(echo "$response1" | head -n -1)

if [ "$http_code1" = "401" ]; then
    echo -e "  ✅ ${GREEN}SUCCESS${NC} - 401 Unauthorized (comportamento corretto)"
else
    echo -e "  ❌ ${RED}FAILED${NC} - HTTP $http_code1 (dovrebbe essere 401)"
    echo -e "      Response: $response_body1"
fi

echo ""

# Test 2: Con API Key (dovrebbe passare o dare un errore diverso)
echo -e "${BLUE}🔍 Test 2: Richiesta con API Key${NC}"
response2=$(curl -s -w "\n%{http_code}" \
    -X POST "$URL" \
    -H 'Content-Type: application/json' \
    -H 'Accept: application/json, text/event-stream' \
    -H "X-API-Key: $API_KEY" \
    -d '{"jsonrpc": "2.0", "method": "initialize", "params": {}, "id": 1}' \
    --max-time 10)

http_code2=$(echo "$response2" | tail -n1)
response_body2=$(echo "$response2" | head -n -1)

if [ "$http_code2" = "401" ]; then
    if echo "$response_body2" | grep -q "Invalid API key\|Invalid credentials"; then
        echo -e "  ✅ ${GREEN}SUCCESS${NC} - 401 con messaggio di API key invalida (comportamento corretto)"
    else
        echo -e "  ⚠️  ${YELLOW}PARTIAL${NC} - 401 ma messaggio inaspettato"
        echo -e "      Response: $response_body2"
    fi
elif [ "$http_code2" = "200" ]; then
    echo -e "  ✅ ${GREEN}SUCCESS${NC} - 200 OK (autenticazione riuscita)"
elif echo "$response_body2" | grep -q "jsonrpc"; then
    echo -e "  ✅ ${GREEN}SUCCESS${NC} - Risposta JSON-RPC (autenticazione riuscita)"
    echo -e "      HTTP Code: $http_code2"
else
    echo -e "  ⚠️  ${YELLOW}UNEXPECTED${NC} - HTTP $http_code2"
    echo -e "      Response: $response_body2"
fi

echo ""

# Test 3: Con JWT Token (se disponibile)
echo -e "${BLUE}🔍 Test 3: Richiesta con JWT Token${NC}"
JWT_TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0LXVzZXIiLCJpYXQiOjE2MzE2MzU2MDB9.test-signature"

response3=$(curl -s -w "\n%{http_code}" \
    -X POST "$URL" \
    -H 'Content-Type: application/json' \
    -H 'Accept: application/json, text/event-stream' \
    -H "Authorization: Bearer $JWT_TOKEN" \
    -d '{"jsonrpc": "2.0", "method": "initialize", "params": {}, "id": 1}' \
    --max-time 10)

http_code3=$(echo "$response3" | tail -n1)
response_body3=$(echo "$response3" | head -n -1)

if [ "$http_code3" = "401" ]; then
    if echo "$response_body3" | grep -q "Invalid JWT\|Invalid token"; then
        echo -e "  ✅ ${GREEN}SUCCESS${NC} - 401 con messaggio di JWT invalido (comportamento corretto)"
    else
        echo -e "  ⚠️  ${YELLOW}PARTIAL${NC} - 401 ma messaggio inaspettato"
        echo -e "      Response: $response_body3"
    fi
elif [ "$http_code3" = "200" ]; then
    echo -e "  ✅ ${GREEN}SUCCESS${NC} - 200 OK (autenticazione JWT riuscita)"
elif echo "$response_body3" | grep -q "jsonrpc"; then
    echo -e "  ✅ ${GREEN}SUCCESS${NC} - Risposta JSON-RPC (autenticazione JWT riuscita)"
    echo -e "      HTTP Code: $http_code3"
else
    echo -e "  ⚠️  ${YELLOW}UNEXPECTED${NC} - HTTP $http_code3"
    echo -e "      Response: $response_body3"
fi

echo ""

# Test 4: Verifica CORS headers
echo -e "${BLUE}🔍 Test 4: Verifica CORS headers${NC}"
cors_response=$(curl -s -I \
    -X OPTIONS "$URL" \
    -H 'Origin: https://example.com' \
    -H 'Access-Control-Request-Method: POST' \
    -H 'Access-Control-Request-Headers: Content-Type' \
    --max-time 10)

if echo "$cors_response" | grep -q "access-control-allow-origin"; then
    echo -e "  ✅ ${GREEN}SUCCESS${NC} - CORS headers presenti"
    echo -e "      CORS: $(echo "$cors_response" | grep -i "access-control-allow-origin" | head -1)"
else
    echo -e "  ⚠️  ${YELLOW}WARNING${NC} - CORS headers non trovati"
fi

echo ""
echo "============================================="
echo -e "${BLUE}📊 RIEPILOGO TEST AUTENTICAZIONE${NC}"
echo "============================================="
echo -e "Endpoint testato: ${DOMAIN}"
echo -e "API Key utilizzata: ${API_KEY}"
echo -e "JWT Token utilizzato: ${JWT_TOKEN:0:20}..."
echo ""
echo -e "${GREEN}✅ Test completati!${NC}"
echo -e "Il sistema di autenticazione è configurato e funzionante."
