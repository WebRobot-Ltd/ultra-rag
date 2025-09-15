#!/usr/bin/env python3
"""
Test script per verificare l'autenticazione MCP con credenziali reali
"""

import requests
import json
import base64

class MCPAuthClient:
    def __init__(self, base_url: str, username: str = None, password: str = None):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.verify = False
        self._request_id = 0
    
    def _get_next_id(self) -> int:
        self._request_id += 1
        return self._request_id
    
    def _make_request(self, method: str, params: dict = None) -> dict:
        """Effettua una richiesta MCP"""
        request_data = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": method,
            "params": params or {}
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        
        # Aggiungi autenticazione Basic se fornita
        if self.username and self.password:
            auth_string = f"{self.username}:{self.password}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            headers["Authorization"] = f"Basic {auth_b64}"
        
        print(f"Invio richiesta a {self.base_url}/mcp")
        print(f"Metodo: {method}")
        print(f"Parametri: {json.dumps(params, indent=2)}")
        if self.username:
            print(f"Autenticazione: {self.username}:***")
        
        response = self.session.post(
            f"{self.base_url}/mcp",
            json=request_data,
            headers=headers
        )
        response_text = response.text
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response_text}")
        
        if response.status_code == 200:
            try:
                # Handle Server-Sent Events (SSE) format
                if response_text.startswith("event: message\ndata: "):
                    # Extract JSON from SSE format
                    json_start = response_text.find("data: ") + 6
                    json_data = response_text[json_start:].strip()
                    return json.loads(json_data)
                else:
                    # Regular JSON response
                    return json.loads(response_text)
            except json.JSONDecodeError as e:
                print(f"Errore nel parsing JSON: {e}")
                return {"error": "Invalid JSON response"}
        else:
            return {"error": f"HTTP {response.status_code}: {response_text}"}
    
    def initialize(self) -> dict:
        """Inizializza la connessione MCP"""
        params = {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-auth-client",
                "version": "1.0.0"
            }
        }
        return self._make_request("initialize", params)
    
    def list_tools(self) -> dict:
        """Lista gli strumenti disponibili"""
        return self._make_request("tools/list")
    
    def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """Chiama uno strumento specifico"""
        params = {
            "name": tool_name,
            "arguments": arguments
        }
        return self._make_request("tools/call", params)
    
    def close(self):
        """Chiude la sessione"""
        self.session.close()

def test_authentication():
    """Test dell'autenticazione con credenziali reali"""
    
    # Credenziali di test (da sostituire con quelle reali)
    test_credentials = [
        {"username": "admin", "password": "WebRobot2025Secure"},
        {"username": "test_user", "password": "test_password"},
        {"username": "mcp_user", "password": "mcp_password"},
    ]
    
    # URL di test
    dev_url = "https://retriever-mcp-dev.metaglobe.finance"
    prod_url = "https://retriever-mcp.metaglobe.finance"
    
    print("=== Test Autenticazione MCP Retriever ===\n")
    
    # 1. Test endpoint di sviluppo (senza autenticazione)
    print("1. Test endpoint di sviluppo (senza autenticazione)")
    print("=" * 50)
    client_dev = MCPAuthClient(dev_url)
    try:
        result = client_dev.initialize()
        print(f"Risultato inizializzazione: {json.dumps(result, indent=2)}")
        
        if "error" not in result:
            tools = client_dev.list_tools()
            print(f"Strumenti disponibili: {len(tools.get('result', {}).get('tools', []))}")
    except Exception as e:
        print(f"Errore: {e}")
    finally:
        client_dev.close()
    
    print("\n" + "=" * 50 + "\n")
    
    # 2. Test endpoint di produzione (con autenticazione)
    print("2. Test endpoint di produzione (con autenticazione)")
    print("=" * 50)
    
    for i, creds in enumerate(test_credentials, 1):
        print(f"\n--- Test credenziali {i}: {creds['username']} ---")
        client_prod = MCPAuthClient(prod_url, creds['username'], creds['password'])
        try:
            result = client_prod.initialize()
            print(f"Risultato inizializzazione: {json.dumps(result, indent=2)}")
            
            if "error" not in result:
                tools = client_prod.list_tools()
                print(f"Strumenti disponibili: {len(tools.get('result', {}).get('tools', []))}")
                break  # Se funziona, esci dal loop
        except Exception as e:
            print(f"Errore: {e}")
        finally:
            client_prod.close()
    
    print("\n" + "=" * 50 + "\n")

if __name__ == "__main__":
    test_authentication()
