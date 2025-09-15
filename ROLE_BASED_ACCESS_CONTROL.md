# Role-Based Access Control (RBAC) per UltraRAG MCP

## Panoramica

Questo documento descrive l'implementazione del controllo accesso basato sui ruoli (RBAC) per il sistema UltraRAG MCP, utilizzando meta attributi durante l'indicizzazione per filtrare i risultati in base ai permessi dell'utente.

## Architettura Proposta

### 1. Schema Milvus Esteso

Lo schema attuale verrà esteso per includere metadati di controllo accesso:

```python
# Schema attuale
fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=dim),
    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535)
]

# Schema esteso con RBAC
fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=dim),
    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
    
    # Metadati per controllo accesso
    FieldSchema(name="document_id", dtype=DataType.VARCHAR, max_length=255),
    FieldSchema(name="document_type", dtype=DataType.VARCHAR, max_length=100),
    FieldSchema(name="department", dtype=DataType.VARCHAR, max_length=100),
    FieldSchema(name="security_level", dtype=DataType.INT64),  # 1=public, 2=internal, 3=confidential, 4=secret
    FieldSchema(name="owner_id", dtype=DataType.VARCHAR, max_length=255),
    FieldSchema(name="created_at", dtype=DataType.INT64),
    FieldSchema(name="updated_at", dtype=DataType.INT64),
    
    # Lista di ruoli che possono accedere (JSON array)
    FieldSchema(name="allowed_roles", dtype=DataType.VARCHAR, max_length=2048),
    
    # Lista di utenti specifici che possono accedere (JSON array)
    FieldSchema(name="allowed_users", dtype=DataType.VARCHAR, max_length=2048),
    
    # Tag per categorizzazione
    FieldSchema(name="tags", dtype=DataType.VARCHAR, max_length=1024),
    
    # Metadati personalizzati (JSON)
    FieldSchema(name="custom_metadata", dtype=DataType.VARCHAR, max_length=4096)
]
```

### 2. Struttura Ruoli e Permessi

```python
# Esempio di struttura ruoli
ROLES = {
    "admin": {
        "level": 4,  # Accesso a tutto
        "departments": ["*"],  # Tutti i dipartimenti
        "security_levels": [1, 2, 3, 4]
    },
    "manager": {
        "level": 3,
        "departments": ["engineering", "sales"],
        "security_levels": [1, 2, 3]
    },
    "analyst": {
        "level": 2,
        "departments": ["engineering"],
        "security_levels": [1, 2]
    },
    "viewer": {
        "level": 1,
        "departments": ["engineering"],
        "security_levels": [1]
    }
}
```

### 3. Filtri di Ricerca Basati sui Ruoli

```python
def build_role_filter(user_roles: List[str], user_departments: List[str], user_id: str) -> str:
    """
    Costruisce un filtro Milvus basato sui ruoli dell'utente
    """
    conditions = []
    
    # Filtro per livello di sicurezza
    max_security_level = max(ROLES[role]["level"] for role in user_roles)
    conditions.append(f"security_level <= {max_security_level}")
    
    # Filtro per dipartimenti
    if "*" not in user_departments:
        dept_conditions = " OR ".join([f'department == "{dept}"' for dept in user_departments])
        conditions.append(f"({dept_conditions})")
    
    # Filtro per ruoli specifici
    role_conditions = []
    for role in user_roles:
        role_conditions.append(f'JSON_CONTAINS(allowed_roles, "{role}")')
    
    if role_conditions:
        conditions.append(f"({' OR '.join(role_conditions)})")
    
    # Filtro per utenti specifici
    conditions.append(f'JSON_CONTAINS(allowed_users, "{user_id}")')
    
    return " AND ".join(conditions)
```

## Implementazione

### 1. Modifica del Server Retriever

```python
class RoleBasedRetriever(Retriever):
    def __init__(self, mcp_inst: UltraRAG_MCP_Server):
        super().__init__(mcp_inst)
        
        # Aggiungi tool per ricerca con filtri RBAC
        mcp_inst.tool(
            self.retriever_search_with_rbac,
            output="q_ls,top_k,user_roles,user_departments,user_id,collection_name,host,port->ret_psg",
        )
    
    async def retriever_search_with_rbac(
        self,
        query_list: List[str],
        top_k: int = 5,
        user_roles: List[str] = None,
        user_departments: List[str] = None,
        user_id: str = None,
        collection_name: str = "webrobot_knowledge_base",
        host: str = "localhost",
        port: int = 19530,
    ) -> Dict[str, List[List[str]]]:
        """
        Ricerca con controllo accesso basato sui ruoli
        """
        if not user_roles:
            user_roles = ["viewer"]  # Ruolo di default
        
        if not user_departments:
            user_departments = ["engineering"]  # Dipartimento di default
        
        # Costruisci filtro RBAC
        rbac_filter = build_role_filter(user_roles, user_departments, user_id)
        
        # Esegui ricerca con filtro
        results = await self._search_with_filter(
            query_list, top_k, rbac_filter, collection_name, host, port
        )
        
        return results
```

### 2. Modifica del Processo di Indicizzazione

```python
def index_document_with_rbac(
    document: Document,
    metadata: Dict[str, Any],
    user_roles: List[str] = None,
    security_level: int = 1,
    department: str = "general"
):
    """
    Indicizza un documento con metadati RBAC
    """
    # Estrai testo e genera embedding
    text = document.text
    embedding = generate_embedding(text)
    
    # Prepara metadati RBAC
    rbac_metadata = {
        "document_id": metadata.get("id", str(uuid.uuid4())),
        "document_type": metadata.get("type", "document"),
        "department": department,
        "security_level": security_level,
        "owner_id": metadata.get("owner_id", "system"),
        "created_at": int(time.time()),
        "updated_at": int(time.time()),
        "allowed_roles": json.dumps(user_roles or ["viewer"]),
        "allowed_users": json.dumps(metadata.get("allowed_users", [])),
        "tags": json.dumps(metadata.get("tags", [])),
        "custom_metadata": json.dumps(metadata.get("custom", {}))
    }
    
    # Inserisci in Milvus con metadati
    collection.insert([embedding], [text], **rbac_metadata)
```

### 3. Integrazione con Sistema di Autenticazione

```python
class AuthenticatedRetriever:
    def __init__(self, auth_manager: AuthManager):
        self.auth_manager = auth_manager
        self.retriever = RoleBasedRetriever()
    
    async def search_with_user_context(
        self,
        query: str,
        api_key: str = None,
        jwt_token: str = None
    ) -> Dict[str, Any]:
        """
        Ricerca con contesto utente autenticato
        """
        # Autentica utente
        user_info = await self.auth_manager.authenticate_user(api_key, jwt_token)
        
        if not user_info:
            raise AuthenticationError("Invalid credentials")
        
        # Estrai ruoli e permessi utente
        user_roles = user_info.get("roles", ["viewer"])
        user_departments = user_info.get("departments", ["general"])
        user_id = user_info.get("user_id")
        
        # Esegui ricerca con filtri RBAC
        results = await self.retriever.retriever_search_with_rbac(
            query_list=[query],
            user_roles=user_roles,
            user_departments=user_departments,
            user_id=user_id
        )
        
        return results
```

## Vantaggi dell'Approccio

### 1. **Performance**
- Filtri applicati a livello di database (Milvus)
- Nessun post-processing necessario
- Scalabilità ottimale

### 2. **Sicurezza**
- Controllo granulare per documento
- Supporto per livelli di sicurezza multipli
- Audit trail completo

### 3. **Flessibilità**
- Metadati personalizzabili
- Ruoli dinamici
- Supporto per dipartimenti e progetti

### 4. **Compliance**
- Rispetto delle normative sulla privacy
- Controllo accesso granulare
- Tracciamento degli accessi

## Esempi di Utilizzo

### 1. Indicizzazione con RBAC

```python
# Documento confidenziale per dipartimento engineering
document = Document(text="Sensitive engineering data...")
metadata = {
    "type": "technical_spec",
    "owner_id": "user123",
    "tags": ["confidential", "engineering"]
}

index_document_with_rbac(
    document=document,
    metadata=metadata,
    user_roles=["manager", "senior_engineer"],
    security_level=3,  # Confidential
    department="engineering"
)
```

### 2. Ricerca con Controllo Accesso

```python
# Utente con ruolo "analyst" nel dipartimento "engineering"
results = await retriever.retriever_search_with_rbac(
    query_list=["machine learning algorithms"],
    user_roles=["analyst"],
    user_departments=["engineering"],
    user_id="user456"
)

# Solo documenti accessibili all'utente verranno restituiti
```

### 3. Filtri Avanzati

```python
# Ricerca solo documenti pubblici
results = await retriever.retriever_search_with_rbac(
    query_list=["general information"],
    user_roles=["viewer"],
    user_departments=["*"],
    user_id="guest_user"
)
```

## Configurazione

### 1. Variabili d'Ambiente

```bash
# Abilita RBAC
ENABLE_RBAC=true

# Configurazione ruoli
RBAC_ROLES_CONFIG=/path/to/roles.json

# Livelli di sicurezza
SECURITY_LEVELS=public,internal,confidential,secret
```

### 2. File di Configurazione Ruoli

```json
{
  "roles": {
    "admin": {
      "level": 4,
      "departments": ["*"],
      "security_levels": [1, 2, 3, 4]
    },
    "manager": {
      "level": 3,
      "departments": ["engineering", "sales"],
      "security_levels": [1, 2, 3]
    }
  },
  "departments": {
    "engineering": {
      "parent": null,
      "permissions": ["read", "write"]
    },
    "sales": {
      "parent": null,
      "permissions": ["read"]
    }
  }
}
```

## Testing

### 1. Test di Controllo Accesso

```python
def test_rbac_filtering():
    """Test che i filtri RBAC funzionino correttamente"""
    
    # Crea documenti con diversi livelli di accesso
    doc1 = create_document("Public info", security_level=1, department="general")
    doc2 = create_document("Internal info", security_level=2, department="engineering")
    doc3 = create_document("Confidential info", security_level=3, department="engineering")
    
    # Test utente con accesso limitato
    results = search_with_user(
        query="information",
        user_roles=["viewer"],
        user_departments=["general"]
    )
    
    # Dovrebbe restituire solo doc1
    assert len(results) == 1
    assert "Public info" in results[0]
```

## Conclusioni

L'implementazione del controllo accesso basato sui ruoli tramite meta attributi durante l'indicizzazione offre:

1. **Sicurezza Granulare**: Controllo preciso su chi può accedere a cosa
2. **Performance Ottimali**: Filtri applicati a livello di database
3. **Flessibilità**: Supporto per ruoli, dipartimenti e livelli di sicurezza
4. **Compliance**: Rispetto delle normative sulla privacy e sicurezza
5. **Scalabilità**: Architettura che si adatta a organizzazioni di qualsiasi dimensione

Questo approccio risolve efficacemente il problema della "informazione filtrata in funzione dei ruoli dell'utente" mantenendo alte performance e sicurezza.
