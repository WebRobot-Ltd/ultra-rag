#!/usr/bin/env python3
"""
Test completo di tutti gli endpoint MCP per verificare la connettività
"""

import requests
import json
import time

class MCPEndpointTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False
        
    def test_endpoint(self, url, name):
        """Testa un singolo endpoint MCP"""
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
    
    def test_all_endpoints(self):
        """Testa tutti gli endpoint MCP"""
        print("=== Test Completo Endpoint MCP ===\n")
        
        # Lista di tutti gli endpoint MCP
        endpoints = [
            ("https://retriever-mcp-dev.metaglobe.finance/mcp", "Retriever Dev"),
            ("https://retriever-mcp.metaglobe.finance/mcp", "Retriever Prod"),
            ("https://generation-mcp-dev.metaglobe.finance/mcp", "Generation Dev"),
            ("https://generation-mcp.metaglobe.finance/mcp", "Generation Prod"),
            ("https://corpus-mcp-dev.metaglobe.finance/mcp", "Corpus Dev"),
            ("https://corpus-mcp.metaglobe.finance/mcp", "Corpus Prod"),
            ("https://reranker-mcp-dev.metaglobe.finance/mcp", "Reranker Dev"),
            ("https://reranker-mcp.metaglobe.finance/mcp", "Reranker Prod"),
            ("https://evaluation-mcp-dev.metaglobe.finance/mcp", "Evaluation Dev"),
            ("https://evaluation-mcp.metaglobe.finance/mcp", "Evaluation Prod"),
            ("https://benchmark-mcp-dev.metaglobe.finance/mcp", "Benchmark Dev"),
            ("https://benchmark-mcp.metaglobe.finance/mcp", "Benchmark Prod"),
            ("https://custom-mcp-dev.metaglobe.finance/mcp", "Custom Dev"),
            ("https://custom-mcp.metaglobe.finance/mcp", "Custom Prod"),
            ("https://prompt-mcp-dev.metaglobe.finance/mcp", "Prompt Dev"),
            ("https://prompt-mcp.metaglobe.finance/mcp", "Prompt Prod"),
            ("https://router-mcp-dev.metaglobe.finance/mcp", "Router Dev"),
            ("https://router-mcp.metaglobe.finance/mcp", "Router Prod"),
        ]
        
        results = []
        working_endpoints = []
        failed_endpoints = []
        
        for url, name in endpoints:
            success = self.test_endpoint(url, name)
            results.append((name, success))
            
            if success:
                working_endpoints.append((name, url))
            else:
                failed_endpoints.append((name, url))
            
            time.sleep(0.5)  # Pausa tra le richieste
        
        # Riepilogo finale
        print("\n" + "="*60)
        print("RIEPILOGO FINALE")
        print("="*60)
        
        print(f"\n✅ Endpoint Funzionanti ({len(working_endpoints)}):")
        for name, url in working_endpoints:
            print(f"  - {name}: {url}")
        
        print(f"\n❌ Endpoint con Problemi ({len(failed_endpoints)}):")
        for name, url in failed_endpoints:
            print(f"  - {name}: {url}")
        
        print(f"\n📊 Statistiche:")
        print(f"  - Totale endpoint: {len(endpoints)}")
        print(f"  - Funzionanti: {len(working_endpoints)}")
        print(f"  - Con problemi: {len(failed_endpoints)}")
        print(f"  - Percentuale successo: {len(working_endpoints)/len(endpoints)*100:.1f}%")
        
        return results

if __name__ == "__main__":
    tester = MCPEndpointTester()
    tester.test_all_endpoints()
