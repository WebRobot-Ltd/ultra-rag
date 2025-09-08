# UltraRAG Deployment Guide

Questa guida spiega come fare il deploy di UltraRAG su Kubernetes utilizzando Jenkins CI/CD.

## 📋 Prerequisiti

### Ambiente Jenkins
- Jenkins con supporto Kubernetes
- Credenziali GitHub configurate (`github-token`)
- Secret Docker configurato (`docker-config-secret`)
- Node con GPU NVIDIA disponibili nel cluster

### Cluster Kubernetes
- Namespace `default` (o configurato)
- Milvus attivo su `milvus.webrobot.svc.cluster.local:19530`
- Node con GPU per il deployment
- Storage per dati persistenti (opzionale)

## 🚀 Deployment con Jenkins

### 1. Configurazione Pipeline

La pipeline Jenkins è configurata in `ultrarag-local/Jenkinsfile` con i seguenti parametri:

| Parametro | Default | Descrizione |
|-----------|---------|-------------|
| `BUILD_TYPE` | `dev` | Tipo di build (dev/staging/production) |
| `REDEPLOY_ONLY` | `false` | Solo redeploy senza rebuild |
| `RUN_TESTS` | `true` | Eseguire test automatizzati |
| `PUSH_IMAGE` | `true` | Push immagine su GHCR |
| `DEPLOY_K8S` | `true` | Deploy su Kubernetes |
| `ENABLE_GPU` | `true` | Abilita supporto GPU |

### 2. Trigger Pipeline

#### Automatico (Raccomandato)
```bash
# Push su branch principale triggera deploy automatico
git push origin main
```

#### Manuale
1. Vai su Jenkins → Pipeline UltraRAG
2. Clicca "Build with Parameters"
3. Configura i parametri desiderati
4. Clicca "Build"

### 3. Workflow Pipeline

```
Checkout → Validate Structure → Build Docker → Test → Deploy K8s → Integration Test
```

## 🐳 Build Docker

### Immagine Prodotta
- **Repository**: `ghcr.io/webrobot-ltd/ultra-rag`
- **Tags**: `{BUILD_NUMBER}`, `latest`, `{BUILD_TYPE}`
- **Base**: NVIDIA CUDA 12.2.2
- **GPU**: Supporto completo per GPU NVIDIA

### Caratteristiche Build
- ✅ Build con Kaniko (no Docker daemon)
- ✅ Supporto GPU nativo
- ✅ Multi-stage build ottimizzato
- ✅ Health check integrato
- ✅ Configurazione produzione
- ✅ User non-root per sicurezza

## ⚙️ Deployment Kubernetes

### Componenti Deployati

#### 1. ConfigMap (`ultrarag-configmap.yaml`)
```yaml
# Configurazione UltraRAG
ULTRARAG_ENV: "production"
MCP_SERVER_PORT: "8000"
MILVUS_HOST: "milvus.webrobot.svc.cluster.local"
MILVUS_PORT: "19530"
```

#### 2. Service (`ultrarag-service.yaml`)
```yaml
# Service interno al cluster
apiVersion: v1
kind: Service
metadata:
  name: ultrarag
spec:
  type: ClusterIP
  ports:
  - port: 8000
    name: http
  - port: 3000
    name: mcp
```

#### 3. Deployment (`ultrarag-deployment.yaml`)
```yaml
# Deployment con GPU support
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ultrarag
spec:
  replicas: 1
  template:
    spec:
      nodeSelector:
        accelerator: nvidia-tesla-k80
      containers:
      - name: ultrarag
        image: ghcr.io/webrobot-ltd/ultra-rag:latest
        resources:
          requests:
            nvidia.com/gpu: 1
          limits:
            nvidia.com/gpu: 1
```

### 4. Secrets (`ultrarag-secrets.yaml`)
```yaml
# API Keys (da configurare)
apiVersion: v1
kind: Secret
metadata:
  name: ultrarag-secrets
type: Opaque
data:
  anthropic-api-key: <base64-encoded>
  openai-api-key: <base64-encoded>
```

## 🔧 Configurazione Secrets

### 1. Codifica API Keys
```bash
# Anthropic API Key
echo -n "your-anthropic-key" | base64

# OpenAI API Key
echo -n "your-openai-key" | base64
```

### 2. Aggiorna Secret
```bash
kubectl apply -f k8s/ultrarag-secrets.yaml
```

### 3. Docker Registry Secret
```yaml
# Assicurati che esista nel namespace
kubectl get secret docker-config-secret -n default
```

## 🧪 Test e Validazione

### Test Automatici
1. **Health Check**: Verifica import UltraRAG
2. **Milvus Connection**: Test connessione database
3. **API Endpoints**: Validazione endpoint REST
4. **GPU Detection**: Verifica supporto GPU

### Test Manuali
```bash
# Health check
curl http://ultrarag.default.svc.cluster.local:8000/health

# Lista server MCP
curl http://ultrarag.default.svc.cluster.local:8000/api/servers

# Test RAG pipeline
curl -X POST http://ultrarag.default.svc.cluster.local:8000/api/run \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline": "rag.yaml",
    "query": "Cos'\''è UltraRAG?"
  }'
```

## 📊 Monitoraggio

### Logs
```bash
# Logs del pod
kubectl logs -l app=ultrarag -n default -f

# Logs Jenkins
# Vai su Jenkins → Pipeline → Console Output
```

### Metriche
```bash
# Stato deployment
kubectl get deployment ultrarag -n default

# Risorse utilizzate
kubectl top pods -l app=ultrarag -n default

# Eventi del cluster
kubectl get events -n default --sort-by=.metadata.creationTimestamp
```

### Health Checks
- **Readiness**: `/health` endpoint
- **Liveness**: Import UltraRAG module
- **Startup**: Tempo di avvio servizio

## 🚨 Troubleshooting

### Problemi Comuni

#### 1. Build GPU Fallito
```bash
# Verifica node con GPU
kubectl get nodes --show-labels | grep accelerator

# Verifica GPU resources
kubectl describe node <gpu-node-name>
```

**Soluzione**:
- Assicurati che ci siano node con GPU nel cluster
- Verifica tolerations nel deployment
- Controlla se il node selector corrisponde

#### 2. Connessione Milvus Fallita
```bash
# Test connessione diretta
kubectl run test-milvus --image=busybox --rm -it --restart=Never \
  -- nc -z milvus.webrobot.svc.cluster.local 19530
```

**Soluzione**:
- Verifica che Milvus sia attivo
- Controlla DNS resolution
- Verifica network policies

#### 3. Immagine Non Trovata
```bash
# Verifica immagine su GHCR
docker pull ghcr.io/webrobot-ltd/ultra-rag:latest

# Verifica credenziali
kubectl get secret docker-config-secret -n default -o yaml
```

#### 4. Pod in CrashLoopBackOff
```bash
# Vedi logs dettagliati
kubectl logs -l app=ultrarag -n default --previous

# Descrivi pod
kubectl describe pod -l app=ultrarag -n default
```

**Cause comuni**:
- API keys mancanti
- Memoria insufficiente
- GPU non disponibile

#### 5. Timeout Deploy
```bash
# Aumenta timeout rollout
kubectl rollout status deployment/ultrarag -n default --timeout=900s

# Verifica init containers
kubectl get pods -l app=ultrarag -n default -o yaml
```

### Debug Commands
```bash
# Shell nel pod
kubectl exec -it deployment/ultrarag -n default -- /bin/bash

# Port forward per debug
kubectl port-forward svc/ultrarag 8000:8000 -n default

# Test GPU nel pod
kubectl exec deployment/ultrarag -n default -- nvidia-smi
```

## 🔄 Rollback

### Rollback Automatico
```bash
# Torna alla versione precedente
kubectl rollout undo deployment/ultrarag -n default

# Vedi storico rollout
kubectl rollout history deployment/ultrarag -n default
```

### Rollback Manuale
```bash
# Deploy versione specifica
kubectl set image deployment/ultrarag ultrarag=ghcr.io/webrobot-ltd/ultra-rag:v1.0 -n default
```

## 📈 Ottimizzazioni

### Performance
- **GPU**: Utilizzo ottimizzato per inference
- **Memory**: 4Gi richiesta, 8Gi limite
- **CPU**: 2 core richiesta, 4 core limite
- **Storage**: EmptyDir per dati temporanei

### Scalabilità
- **Horizontal Pod Autoscaler**: Configurabile
- **Resource Quotas**: Impostate per namespace
- **Node Affinity**: Per GPU nodes dedicati

### Sicurezza
- **Non-root user**: User `ultrarag` (UID 1000)
- **Read-only filesystem**: Solo `/app` scrivibile
- **Network policies**: Isolate dal resto del cluster
- **Secret management**: API keys in secrets

## 📞 Supporto

### Contatti
- **Team**: WebRobot Ltd
- **Repository**: https://github.com/webrobot-ltd/webrobot-etl-clouddashboard
- **Jenkins**: Configurato per auto-deploy

### Documentazione Aggiuntiva
- [UltraRAG Official Docs](https://ultrarag.openbmb.cn)
- [Kaniko Documentation](https://github.com/GoogleContainerTools/kaniko)
- [Kubernetes GPU Support](https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/)

---

## 🎯 Checklist Deploy

- [ ] Credenziali GitHub configurate su Jenkins
- [ ] Secret Docker configurato (`docker-config-secret`)
- [ ] Node GPU disponibili nel cluster
- [ ] Milvus attivo e raggiungibile
- [ ] API keys configurate nei secrets
- [ ] Namespace `default` esistente
- [ ] Network policies configurate (se necessarie)

**Deploy Ready!** 🚀
