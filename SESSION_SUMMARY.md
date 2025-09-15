# Sessione Chat - Implementazione Autenticazione UltraRAG MCP Servers

## Obiettivo
Implementare e verificare un meccanismo di autenticazione robusto (API Key e JWT) per i server UltraRAG MCP, garantendo che gli endpoint rispondano con `401 Unauthorized` quando non vengono fornite credenziali valide.

## Problemi Risolti

### 1. Integrazione Autenticazione nel Core Server
- **Problema**: L'autenticazione Flask middleware non veniva chiamata perché il server MCP usava `app.run()` invece di `retriever_app.run()`
- **Soluzione**: Integrata l'autenticazione direttamente nella classe `UltraRAG_MCP_Server` in `src/ultrarag/server.py`
- **Implementazione**: Aggiunto middleware personalizzato che intercetta le richieste HTTP e chiama `authenticate_request()` prima di passare la richiesta al prossimo handler

### 2. Configurazione Jenkins Pipeline
- **Problema**: Parametri di autenticazione non riconosciuti dal job Jenkins
- **Soluzione**: Aggiunti parametri `ENABLE_AUTH`, `DATABASE_URL`, `JWT_SECRET` nel Jenkinsfile
- **Fix**: Corretto tipo parametro da `stringParam` a `string` e risolto conflitto `valueFrom`/`value` spostando i parametri in un ConfigMap

### 3. Configurazione Kubernetes
- **Problema**: Variabili d'ambiente non propagate correttamente ai pod
- **Soluzione**: Creato ConfigMap `ultrarag-config` per gestire le variabili di autenticazione
- **Database URL**: Corretto per puntare al PostgreSQL del cluster (`postgresql://nuvolaris:73a4ww5n5gHq@nuvolaris-postgres.nuvolaris.svc.cluster.local:5432/nuvolaris`)

### 4. Ottimizzazione Caddy Load Balancing
- **Problema**: Errori `502 Bad Gateway` intermittenti
- **Soluzione**: Configurato `lb_policy first`, `max_fails 1`, `fail_duration 3s` per failover aggressivo

### 5. Stabilità Server Retriever
- **Problema**: `TypeError: FastMCP.run_http_async() got an unexpected keyword argument 'json_response'`
- **Soluzione**: Rimosso parametro `json_response=True` non supportato da `app.run()`

## File Modificati

### `src/ultrarag/server.py`
- Aggiunto import moduli di autenticazione con gestione errori
- Modificato `__init__` per inizializzare `AuthManager` e `APIKeyValidator` se `enable_auth=True`
- Implementato middleware personalizzato `AuthMiddleware` per autenticazione HTTP
- Integrato middleware nella lista middleware del server

### `Jenkinsfile`
- Aggiunti parametri build per autenticazione:
  ```groovy
  booleanParam(name: 'ENABLE_AUTH', defaultValue: false)
  string(name: 'DATABASE_URL', defaultValue: 'postgresql://...')
  string(name: 'JWT_SECRET', defaultValue: 'your-secret-key')
  ```
- Creato ConfigMap `ultrarag-config` per variabili di autenticazione
- Aggiornato deployment Kubernetes per leggere variabili dal ConfigMap

### `/etc/caddy/Caddyfile` (bastion host)
- Configurato load balancing aggressivo:
  ```caddy
  reverse_proxy 10.1.20.12:80 10.1.20.13:80 10.1.20.11:80 {
    lb_policy first
    max_fails 1
    fail_duration 3s
  }
  ```

## Stato Attuale

### ✅ Completato
- Integrazione autenticazione nel core server
- Configurazione Jenkins pipeline
- Configurazione Kubernetes con ConfigMap
- Ottimizzazione Caddy load balancing
- Fix stabilità server retriever

### ⚠️ Problema Rimanente
- **Moduli di autenticazione mancanti**: I file `auth/auth_manager.py`, `auth/api_key_validator.py`, `auth/database_client.py` non sono presenti nel codebase
- **Impatto**: Il server mostra warning "Authentication requested but auth modules not available" e non applica l'autenticazione
- **Test fallito**: L'endpoint MCP risponde con 200 invece di 401 quando `ENABLE_AUTH=true`

## Prossimi Passi Necessari

1. **Creare moduli di autenticazione**:
   - `src/auth/auth_manager.py`
   - `src/auth/api_key_validator.py` 
   - `src/auth/database_client.py`

2. **Testare autenticazione**:
   - Verificare che endpoint MCP ritorni 401 senza credenziali
   - Testare con API key valida
   - Testare con JWT valido

3. **Deploy e verifica**:
   - Build e deploy con moduli di autenticazione
   - Verificare funzionamento in produzione

## Configurazione Attuale

### Variabili d'Ambiente (Pod)
```
ENABLE_AUTH=true
DATABASE_URL=postgresql://nuvolaris:73a4ww5n5gHq@nuvolaris-postgres.nuvolaris.svc.cluster.local:5432/nuvolaris
JWT_SECRET=UltraRAG-JWT-Secret-2025
```

### Endpoint Testati
- `https://retriever-mcp.metaglobe.finance/mcp` - Risponde 200 (dovrebbe essere 401)

### Log Server
```
Authentication requested but auth modules not available
```

## Note Tecniche

- **Framework**: FastMCP con middleware personalizzato
- **Database**: PostgreSQL in namespace `nuvolaris`
- **Load Balancer**: Caddy con failover aggressivo
- **CI/CD**: Jenkins con parametri dinamici
- **Container**: Docker con supervisor per gestione processi MCP
