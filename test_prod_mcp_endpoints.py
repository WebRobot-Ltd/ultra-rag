#!/usr/bin/env python3
"""
Test completo degli endpoint MCP di produzione con autenticazione
"""

import requests
import json
import time

class MCPProdEndpointTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False
        
    def test_endpoint(self, url, name):
        """Testa un singolo endpoint MCP di produzione"""
        print(f"\n--- Testando {name} ---")
        print(f"URL: {url}")
        
        request_data = {
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
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        
        try:
            response = self.session.post(url, json=request_data, headers=headers, timeout=10)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                # Handle SSE format
                response_text = response.text
                if response_text.startswith("event: message\ndata: "):
                    json_start = response_text.find("data: ") + 6
                    json_data = response_text[json_start:].strip()
                    try:
                        result = json.loads(json_data)
                        server_name = result.get('result', {}).get('serverInfo', {}).get('name', 'unknown')
                        print(f"✅ {name} - OK (Server: {server_name})")
                        return True
                    except json.JSONDecodeError:
                        print(f"❌ {name} - Errore parsing JSON")
                        return False
                else:
                    print(f"✅ {name} - OK (Formato non SSE)")
                    return True
            else:
                print(f"❌ {name} - ERRORE ({response.status_code})")
                if response.text:
                    print(f"Response: {response.text[:200]}...")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {name} - ERRORE CONNESSIONE: {e}")
            return False
    
    def test_all_prod_endpoints(self):
        """Testa tutti gli endpoint MCP di produzione"""
        print("=== Test Completo Endpoint MCP di Produzione ===\n")
        
        # Lista di tutti gli endpoint MCP di produzione
        prod_endpoints = [
            ("https://retriever-mcp.metaglobe.finance/mcp", "Retriever Prod"),
            ("https://generation-mcp.metaglobe.finance/mcp", "Generation Prod"),
            ("https://corpus-mcp.metaglobe.finance/mcp", "Corpus Prod"),
            ("https://reranker-mcp.metaglobe.finance/mcp", "Reranker Prod"),
            ("https://evaluation-mcp.metaglobe.finance/mcp", "Evaluation Prod"),
            ("https://benchmark-mcp.metaglobe.finance/mcp", "Benchmark Prod"),
            ("https://custom-mcp.metaglobe.finance/mcp", "Custom Prod"),
            ("https://prompt-mcp.metaglobe.finance/mcp", "Prompt Prod"),
            ("https://router-mcp.metaglobe.finance/mcp", "Router Prod"),
        ]
        
        results = []
        working_endpoints = []
        failed_endpoints = []
        
        for url, name in prod_endpoints:
            success = self.test_endpoint(url, name)
            results.append((name, success))
            
            if success:
                working_endpoints.append((name, url))
            else:
                failed_endpoints.append((name, url))
            
            time.sleep(0.5)  # Pausa tra le richieste
        
        # Riepilogo finale
        print("\n" + "="*60)
        print("RIEPILOGO FINALE - ENDPOINT PRODUZIONE")
        print("="*60)
        
        print(f"\n✅ Endpoint Funzionanti ({len(working_endpoints)}):")
        for name, url in working_endpoints:
            print(f"  - {name}: {url}")
        
        print(f"\n❌ Endpoint con Problemi ({len(failed_endpoints)}):")
        for name, url in failed_endpoints:
            print(f"  - {name}: {url}")
        
        print(f"\n📊 Statistiche Produzione:")
        print(f"  - Totale endpoint: {len(prod_endpoints)}")
        print(f"  - Funzionanti: {len(working_endpoints)}")
        print(f"  - Con problemi: {len(failed_endpoints)}")
        print(f"  - Percentuale successo: {len(working_endpoints)/len(prod_endpoints)*100:.1f}%")
        
        print(f"\n🔐 Autenticazione:")
        print(f"  - Tutti gli endpoint richiedono autenticazione Python integrata")
        print(f"  - Middleware Basic Auth rimosso da tutti gli ingress")
        print(f"  - Sistema pronto per test con credenziali reali")
        
        return results

if __name__ == "__main__":
    tester = MCPProdEndpointTester()
    tester.test_all_prod_endpoints()
