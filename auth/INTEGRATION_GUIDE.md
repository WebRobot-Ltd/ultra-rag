# Guida Integrazione Autenticazione MCP

Questa guida spiega come integrare il sistema di autenticazione con i server MCP UltraRAG.

## 🎯 Panoramica

Il sistema di autenticazione Python replica la logica delle API Jersey esistenti:
- **JWT Authentication**: Token JWT emessi da Strapi CMS
- **API Key Authentication**: Chiavi API con hash SHA256 e scopes granulari
- **Database Integration**: Connessione diretta a PostgreSQL (stesso DB di Strapi)
- **Role-based Access Control**: Ruoli gerarchici (super_admin, admin, developer, viewer)
- **Scope-based Permissions**: Controllo granulare delle autorizzazioni

## 🚀 Installazione

### 1. Installa Dipendenze

```bash
cd crewai-backend-new/ultrarag-local/auth
pip install -r requirements.txt
```

### 2. Configura Variabili d'Ambiente

```bash
# Copia il file di esempio
cp env.example .env

# Modifica con i tuoi valori
nano .env
```

### 3. Configura Database

Assicurati che PostgreSQL sia accessibile con le credenziali configurate.

## 🔧 Integrazione con Server MCP Esistenti

### 1. Modifica il Server MCP

```python
# Nel tuo server MCP (es. retriever.py)
import sys
from pathlib import Path

# Aggiungi il modulo auth al path
auth_path = Path(__file__).parent.parent.parent / "auth"
sys.path.insert(0, str(auth_path))

from auth.auth_middleware import AuthMiddleware
from auth.database_client import DatabaseConfig
from auth.config import get_database_config

# Inizializza il middleware
auth_middleware = AuthMiddleware(get_database_config())

class YourMCPServer:
    def __init__(self):
        self.auth_middleware = auth_middleware
    
    async def initialize(self):
        await self.auth_middleware.initialize()
    
    # Aggiungi autenticazione ai tuoi metodi
    async def your_method(self, ...):
        # Check authentication
        headers = self._extract_headers_from_context()
        result = await self.auth_middleware.validate_request(headers, required_scopes={"read"})
        
        if not result['valid']:
            raise ToolError(result['error'])
        
        user_data = result['user_data']
        print(f"User {user_data['username']} calling method")
        
        # ... tua logica qui
```

### 2. Usa Decoratori (Opzionale)

```python
from auth.auth_middleware import AuthMiddleware

# Crea un'istanza del middleware
auth_middleware = AuthMiddleware()

# Usa i decoratori
@auth_middleware.require_scope("read")
async def search_method(self, query: str):
    # Questo metodo richiede scope "read"
    user = self.auth_middleware.get_current_user()
    print(f"User {user['username']} searching: {query}")

@auth_middleware.require_admin()
async def admin_method(self):
    # Questo metodo richiede ruolo admin
    user = self.auth_middleware.get_current_user()
    print(f"Admin {user['username']} calling admin method")
```

## 🔐 Metodi di Autenticazione

### JWT Token (Bearer)

```bash
# Usa token JWT da Strapi
curl -H "Authorization: Bearer your-jwt-token" \
     https://your-mcp-server.com/api/search
```

### API Key

```bash
# Header X-API-Key
curl -H "X-API-Key: key_id:secret" \
     https://your-mcp-server.com/api/search

# Authorization: ApiKey
curl -H "Authorization: ApiKey key_id:secret" \
     https://your-mcp-server.com/api/search
```

## 🧪 Testing

### 1. Test Database Connection

```bash
cd auth
python test_auth.py
```

### 2. Test con Credenziali Dev

```bash
# Usa credenziali dev per testing
export DEV_API_KEY=dev-api-key-12345
export MCP_AUTH_HEADER="Bearer your-jwt-token"

python test_auth.py
```

### 3. Test con Server MCP

```bash
# Test retriever con autenticazione
python servers/retriever/src/retriever_auth.py --transport http --port 8000

# Test con curl
curl -H "X-API-Key: dev-api-key-12345" \
     -X POST http://localhost:8000/api/search \
     -d '{"query": "test query", "top_k": 5}'
```

## 🔄 Integrazione con Cursor MCP

### 1. Configura Cursor

Aggiungi la configurazione MCP a Cursor:

```json
{
  "mcpServers": {
    "ultrarag-retriever-auth": {
      "command": "python",
      "args": ["path/to/retriever_auth.py"],
      "env": {
        "DATABASE_HOST": "localhost",
        "DATABASE_PORT": "5432",
        "DATABASE_NAME": "strapi",
        "DATABASE_USERNAME": "strapi",
        "DATABASE_PASSWORD": "strapi",
        "JWT_SECRET": "your-jwt-secret",
        "MCP_AUTH_HEADER": "Bearer your-jwt-token"
      }
    }
  }
}
```

### 2. Usa con Cursor

```python
# Cursor userà automaticamente l'autenticazione
# quando chiama i metodi MCP
```

## 📊 Monitoraggio e Logging

### 1. Abilita Logging

```python
import logging
logging.basicConfig(level=logging.INFO)
```

### 2. Monitora Autenticazioni

```python
# Il sistema logga automaticamente:
# - Tentativi di autenticazione
# - Errori di autenticazione
# - Accessi utente
# - Violazioni di permessi
```

## 🚨 Troubleshooting

### 1. Database Connection Failed

```bash
# Verifica connessione database
psql -h localhost -p 5432 -U strapi -d strapi

# Controlla variabili d'ambiente
echo $DATABASE_HOST
echo $DATABASE_PORT
echo $DATABASE_NAME
```

### 2. JWT Validation Failed

```bash
# Verifica JWT secret
echo $JWT_SECRET

# Testa token JWT
python -c "
import jwt
token = 'your-jwt-token'
secret = 'your-jwt-secret'
try:
    payload = jwt.decode(token, secret, algorithms=['HS256'])
    print('JWT valid:', payload)
except Exception as e:
    print('JWT invalid:', e)
"
```

### 3. API Key Validation Failed

```bash
# Verifica API key nel database
psql -h localhost -p 5432 -U strapi -d strapi -c "
SELECT key_id, status, role, scopes FROM api_keys 
WHERE key_id = 'your-key-id';
"
```

## 🔒 Sicurezza

### 1. Configurazione Produzione

```bash
# Usa HTTPS in produzione
export REQUIRE_HTTPS=true

# Usa secret JWT sicuri
export JWT_SECRET=your-secure-jwt-secret

# Disabilita credenziali dev
unset DEV_API_KEY
```

### 2. Monitoraggio Accessi

```python
# Il sistema logga automaticamente:
# - Tentativi di accesso
# - Errori di autenticazione
# - Violazioni di permessi
# - Accessi admin
```

## 📝 Esempi Completi

Vedi i file di esempio:
- `example_integration.py` - Esempio completo di integrazione
- `retriever_auth.py` - Retriever con autenticazione
- `test_auth.py` - Test completi del sistema

## 🎉 Risultato Finale

Con questa integrazione avrai:
- ✅ Autenticazione JWT e API Key
- ✅ Controllo accessi granulare
- ✅ Integrazione con database Strapi
- ✅ Compatibilità con Cursor MCP
- ✅ Logging e monitoraggio
- ✅ Sicurezza enterprise-grade
