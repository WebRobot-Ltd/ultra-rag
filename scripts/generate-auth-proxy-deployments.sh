#!/bin/bash
# Generate deployment manifests for all MCP servers with auth proxy

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
K8S_DIR="$PROJECT_ROOT/k8s"

# Server configurations: name, original_port, proxy_port, server_path
declare -A SERVERS=(
    ["retriever"]="8002:8100:servers/retriever/src/retriever.py"
    ["reranker"]="8003:8101:servers/reranker/src/reranker.py"
    ["router"]="8004:8102:servers/router/src/router.py"
    ["corpus"]="8005:8103:servers/corpus/src/corpus.py"
    ["prompt"]="8006:8104:servers/prompt/src/prompt.py"
    ["generation"]="8007:8105:servers/generation/src/generation.py"
    ["evaluation"]="8008:8106:servers/evaluation/src/evaluation.py"
    ["benchmark"]="8009:8107:servers/benchmark/src/benchmark.py"
    ["custom"]="8010:8108:servers/custom/src/custom.py"
    ["sayhello"]="8011:8109:servers/sayhello/src/sayhello.py"
)

mkdir -p "$K8S_DIR"

for server_name in "${!SERVERS[@]}"; do
    IFS=':' read -r original_port proxy_port server_path <<< "${SERVERS[$server_name]}"
    
    cat > "$K8S_DIR/deployment-${server_name}-with-auth.yaml" << EOF
# Deployment for ${server_name} MCP server with auth proxy sidecar
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ultrarag-mcp-${server_name}
  namespace: default
  labels:
    app: ultrarag-mcp-${server_name}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ultrarag-mcp-${server_name}
  template:
    metadata:
      labels:
        app: ultrarag-mcp-${server_name}
    spec:
      containers:
      # Main MCP server container
      - name: mcp-server
        image: ghcr.io/webrobot/ultrarag:latest
        ports:
        - containerPort: ${original_port}
          name: mcp-port
        env:
        - name: ENABLE_AUTH
          value: "false"  # Disable auth in main container since proxy handles it
        - name: DATABASE_URL
          valueFrom:
            configMapKeyRef:
              name: ultrarag-config
              key: DATABASE_URL
        - name: JWT_SECRET
          valueFrom:
            configMapKeyRef:
              name: ultrarag-config
              key: JWT_SECRET
        command: ["/opt/miniconda/envs/ultrarag/bin/python"]
        args: ["${server_path}", "--transport", "http", "--port", "${original_port}", "--host", "0.0.0.0"]
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
      
      # Auth proxy sidecar
      - name: auth-proxy
        image: ghcr.io/webrobot/ultrarag:latest
        ports:
        - containerPort: ${proxy_port}
          name: proxy-port
        env:
        - name: UPSTREAM_URL
          value: "http://127.0.0.1:${original_port}/mcp"
        - name: DATABASE_URL
          valueFrom:
            configMapKeyRef:
              name: ultrarag-config
              key: DATABASE_URL
        - name: JWT_SECRET
          valueFrom:
            configMapKeyRef:
              name: ultrarag-config
              key: JWT_SECRET
        command: ["/opt/miniconda/envs/ultrarag/bin/uvicorn"]
        args: ["servers.auth_proxy.app:app", "--host", "0.0.0.0", "--port", "${proxy_port}"]
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "250m"
        livenessProbe:
          httpGet:
            path: /mcp
            port: ${proxy_port}
            httpHeaders:
            - name: Accept
              value: application/json, text/event-stream
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /mcp
            port: ${proxy_port}
            httpHeaders:
            - name: Accept
              value: application/json, text/event-stream
          initialDelaySeconds: 5
          periodSeconds: 5

---
# Service pointing to auth proxy
apiVersion: v1
kind: Service
metadata:
  name: ultrarag-mcp-${server_name}-service
  namespace: default
  labels:
    app: ultrarag-mcp-${server_name}
spec:
  selector:
    app: ultrarag-mcp-${server_name}
  ports:
  - name: mcp
    port: 80
    targetPort: ${proxy_port}  # Point to auth proxy instead of main server
    protocol: TCP
  type: ClusterIP
EOF

    echo "Generated deployment for ${server_name}: $K8S_DIR/deployment-${server_name}-with-auth.yaml"
done

echo "All deployment manifests generated successfully!"
echo "To deploy all servers with auth proxy, run:"
echo "kubectl apply -f $K8S_DIR/deployment-*-with-auth.yaml"
