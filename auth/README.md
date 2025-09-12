# UltraRAG MCP Authentication Module

Sistema di autenticazione Python per server MCP che replica la logica delle API Jersey esistenti.

## 🎯 Caratteristiche

- **JWT Authentication**: Supporto completo per token JWT emessi da Strapi CMS
- **API Key Authentication**: Validazione API keys con hash SHA256 e scopes granulari
- **Database Integration**: Connessione diretta a PostgreSQL (stesso DB di Strapi)
- **Role-based Access Control**: Supporto per ruoli (super_admin, admin, developer, viewer)
- **Scope-based Permissions**: Controllo granulare delle autorizzazioni
- **Development Mode**: Credenziali dev per testing locale

## 🚀 Installazione

```bash
# Installa le dipendenze
pip install -r requirements.txt

# Configura le variabili d'ambiente
export DATABASE_HOST=localhost
export DATABASE_PORT=5432
export DATABASE_NAME=strapi
export DATABASE_USERNAME=strapi
export DATABASE_PASSWORD=strapi
export JWT_SECRET=your-jwt-secret
export STRAPI_BASE_URL=http://localhost:1337
```

## 📖 Utilizzo Base

### 1. Integrazione con Server MCP Esistente

```python
from auth.auth_middleware import AuthMiddleware
from auth.database_client import DatabaseConfig

# Inizializza il middleware
auth_middleware = AuthMiddleware()

# Nel tuo server MCP
class MyMCPServer:
    def __init__(self):
        self.auth_middleware = auth_middleware
    
    async def initialize(self):
        await self.auth_middleware.initialize()
    
    @auth_middleware.require_scope("read")
    async def search_documents(self, query: str):
        # Questo metodo richiede scope "read"
        user = self.auth_middleware.get_current_user()
        print(f"User {user['username']} searching: {query}")
        # ... logica di ricerca
```

### 2. Decoratori Disponibili

```python
# Richiede autenticazione con scope specifico
@auth_middleware.require_scope("read")
async def read_method(self): pass

# Richiede ruolo admin
@auth_middleware.require_admin()
async def admin_method(self): pass

# Richiede ruolo specifico
@auth_middleware.require_role("developer")
async def dev_method(self): pass

# Autenticazione opzionale
@auth_middleware.optional_auth()
async def optional_method(self): 
    if self.auth_middleware.is_user_authenticated():
        # Utente autenticato
        pass
    else:
        # Utente non autenticato
        pass
```

### 3. Validazione Manuale

```python
# Valida richiesta manualmente
headers = {"Authorization": "Bearer jwt-token"}
result = await auth_middleware.validate_request(headers, required_scopes={"read"})

if result['valid']:
    user_data = result['user_data']
    print(f"Authenticated user: {user_data['username']}")
else:
    print(f"Authentication failed: {result['error']}")
```

## 🔐 Metodi di Autenticazione

### JWT Token (Bearer)
```bash
curl -H "Authorization: Bearer your-jwt-token" \
     https://your-mcp-server.com/api/search
```

### API Key
```bash
# Header X-API-Key (Strapi: key_id:secret format)
curl -H "X-API-Key: key_id:secret" \
     https://your-mcp-server.com/api/search

# Authorization: ApiKey
curl -H "Authorization: ApiKey key_id:secret" \
     https://your-mcp-server.com/api/search
```

## 🗄️ Schema Database

Il modulo si connette alle stesse tabelle di Strapi:

### Tabella `up_users` (Strapi Users)
- `id`, `username`, `email`, `password`, `provider`
- `confirmed`, `blocked`, `role` (FK a `up_roles`)
- `organization` (FK a `organizations`)
- `created_at`, `updated_at`

### Tabella `api_keys` (Strapi API Keys)
- `id`, `label`, `key_id`, `secret_hash`, `scopes`, `role`, `status`
- `organization_id`, `owner_id` (FK a `up_users`)
- `expires_at`, `last_used_at`, `created_at`, `updated_at`

### Tabella `up_roles` (Strapi Roles)
- `id`, `name`, `type` (super_admin, admin, developer, viewer)
- `description`, `created_at`, `updated_at`

### Relazione API Key - Utente
- **1:N**: Un utente può avere molte API keys
- **Separata**: API keys in tabella dedicata
- **Granulare**: Scopes e ruoli per ogni API key
- **Flessibile**: Supporto multi-tenancy con organizzazioni

## ⚙️ Configurazione

### Variabili d'Ambiente

```bash
# Database
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=strapi
DATABASE_USERNAME=strapi
DATABASE_PASSWORD=strapi
DATABASE_SSL=false

# JWT
JWT_SECRET=your-jwt-secret

# Strapi
STRAPI_BASE_URL=http://localhost:1337
INTERNAL_TOKEN=your-internal-token

# Development
DEV_API_KEY=dev-api-key-12345
DEV_USER_ID=dev-user
DEV_ROLE=super_admin
DEV_SCOPES=read,write,admin
```

### Configurazione Programmatica

```python
from auth.database_client import DatabaseConfig
from auth.auth_middleware import AuthMiddleware

# Configurazione personalizzata
db_config = DatabaseConfig(
    host="localhost",
    port=5432,
    database="strapi",
    username="strapi",
    password="strapi"
)

auth_middleware = AuthMiddleware(db_config)
```

## 🔒 Sicurezza

- **Hash SHA256** per API keys (matching Jersey)
- **JWT validation** con secret condiviso
- **Scope-based permissions** granulari
- **Role-based access control** gerarchico
- **Multi-tenancy** con isolamento organizzazioni
- **Development mode** con credenziali sicure

## 🧪 Testing

```python
# Test con credenziali dev
export DEV_API_KEY=test-key
export DEV_USER_ID=test-user
export DEV_ROLE=super_admin

# Test JWT
headers = {"Authorization": "Bearer valid-jwt-token"}

# Test API Key
headers = {"X-API-Key": "test-key"}
```

## 📝 Esempi Completi

Vedi `example_integration.py` per un esempio completo di integrazione con server MCP.

## 🚨 Troubleshooting

### 1. Database Connection Failed
```bash
# Verifica connessione database
psql -h localhost -p 5432 -U webrobot -d webrobot

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
# Verifica API key nel database (Strapi)
psql -h localhost -p 5432 -U strapi -d strapi -c "
SELECT ak.key_id, ak.status, ak.role, ak.scopes, u.username, u.email 
FROM api_keys ak 
JOIN up_users u ON ak.owner_id = u.id 
WHERE ak.key_id = 'your-key-id';
"
```

## 🚨 Note Importanti

1. **Database**: Assicurati che il database PostgreSQL sia accessibile
2. **JWT Secret**: Usa lo stesso secret di Strapi per la validazione JWT
3. **API Keys**: Le API keys sono nel formato `key_id:secret`
4. **Scopes**: Gli scope sono granulari per ogni API key
5. **Development**: Le credenziali dev sono solo per testing locale

## 🔄 Integrazione con Cursor MCP

Per usare con Cursor, configura il client MCP con le credenziali:

```json
{
  "mcpServers": {
    "ultrarag-retriever": {
      "command": "python",
      "args": ["path/to/retriever.py"],
      "env": {
        "DATABASE_HOST": "your-db-host",
        "JWT_SECRET": "your-jwt-secret"
      }
    }
  }
}
```

Poi usa l'header di autenticazione nelle richieste MCP.
