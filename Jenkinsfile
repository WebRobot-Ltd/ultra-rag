pipeline {
    agent none

    environment {
        GITHUB_REPOSITORY = 'webrobot-ltd/ultra-rag'
        DOCKER_IMAGE = "ghcr.io/webrobot-ltd/ultra-rag"
        DOCKER_TAG = "${env.BUILD_NUMBER}"
        DOCKER_REGISTRY = 'ghcr.io'
        DOCKER_CREDENTIALS = 'github-token'
        K8S_NAMESPACE = 'default'
        K8S_CONTEXT = 'webrobot'
        MILVUS_HOST = 'milvus.webrobot.svc.cluster.local'
        MILVUS_PORT = '19530'
    }

    parameters {
        choice(
            name: 'BUILD_TYPE',
            choices: ['dev', 'staging', 'production', 'supervisor'],
            description: 'Tipo di build da eseguire (supervisor = Supervisor process management)'
        )
        booleanParam(
            name: 'REDEPLOY_ONLY',
            defaultValue: false,
            description: 'Salta build e test, esegui solo il deploy K8s'
        )
        booleanParam(
            name: 'RUN_TESTS',
            defaultValue: true,
            description: 'Eseguire i test prima del build'
        )
        booleanParam(
            name: 'PUSH_IMAGE',
            defaultValue: true,
            description: 'Push dell\'immagine Docker su GHCR'
        )
        booleanParam(
            name: 'DEPLOY_K8S',
            defaultValue: true,
            description: 'Deploy automatico su Kubernetes'
        )
        booleanParam(
            name: 'ENABLE_GPU',
            defaultValue: true,
            description: 'Abilita supporto GPU nel deployment'
        )
        booleanParam(
            name: 'ENABLE_AUTH',
            defaultValue: false,
            description: 'Abilita autenticazione Python integrata sui server MCP'
        )
        string(
            name: 'DATABASE_URL',
            defaultValue: 'postgresql://user:password@localhost:5432/strapi',
            description: 'URL del database per autenticazione'
        )
        string(
            name: 'JWT_SECRET',
            defaultValue: 'your-secret-key',
            description: 'Chiave segreta per validazione JWT'
        )
    }

    stages {
        stage('Initialize') {
            steps {
                script {
                    echo "🚀 Checkout completato per build ${params.BUILD_TYPE}"
                    echo "📦 Repository: ${env.GITHUB_REPOSITORY}"
                    echo "🐳 Immagine: ${env.DOCKER_IMAGE}:${env.DOCKER_TAG}"
                    echo "🏗️ Build Type: ${params.BUILD_TYPE}"
                }
            }
        }

        stage('Checkout') {
            agent any
            steps {
                checkout scm
                script {
                    echo "🔄 Checkout completato per build ${params.BUILD_TYPE}"
                    echo "📦 Repository: ${env.GITHUB_REPOSITORY}"
                    echo "🐳 Immagine: ${env.DOCKER_IMAGE}:${env.DOCKER_TAG}"
                    echo "🏗️ Build Type: ${params.BUILD_TYPE}"
                }
            }
        }

        stage('Validate UltraRAG Structure') {
            agent any
            steps {
                script {
                    echo "🔍 Validazione struttura UltraRAG..."
                    
                    sh '''
                        test -f Dockerfile || (echo "Dockerfile mancante" && exit 1)
                        test -f pyproject.toml || (echo "pyproject.toml mancante" && exit 1)
                        test -d src || (echo "Directory src mancante" && exit 1)
                        test -f supervisord.conf || (echo "supervisord.conf mancante" && exit 1)
                        echo "✅ Struttura UltraRAG valida"
                    '''
                }
            }
        }

        stage('Build & Push Docker Image') {
            when {
                expression { return !params.REDEPLOY_ONLY }
            }
            agent {
                kubernetes {
                    yaml """
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: kaniko
    image: gcr.io/kaniko-project/executor:v1.9.0-debug
    imagePullPolicy: Always
    command:
    - /busybox/cat
    tty: true
    resources:
      requests:
        memory: "2Gi"
        cpu: "500m"
      limits:
        memory: "4Gi"
        cpu: "1"
    volumeMounts:
      - name: jenkins-docker-cfg
        mountPath: /kaniko/.docker
  volumes:
    - name: jenkins-docker-cfg
      projected:
        sources:
        - secret:
            name: docker-config-secret
            items:
              - key: .dockerconfigjson
                path: config.json
"""
                }
            }
            steps {
                container('kaniko') {
                    script {
                        echo "🐳 Build Docker image UltraRAG con Kaniko..."
                        sh """
                            # Use Supervisor Dockerfile for all builds
                            DOCKERFILE="Dockerfile.supervisor"
                            echo "🐳 Using Supervisor Dockerfile for robust process management"
                            
                            /kaniko/executor --context=\$(pwd) \\
                                --dockerfile=\$DOCKERFILE \\
                                --destination=${DOCKER_IMAGE}:${DOCKER_TAG} \\
                                --destination=${DOCKER_IMAGE}:latest \\
                                --build-arg BUILD_TYPE=${params.BUILD_TYPE} \\
                                --verbosity=info
                        """
                    }
                }
            }
        }

        stage('Deploy to Kubernetes') {
            when {
                expression { return params.DEPLOY_K8S }
            }
            agent {
                kubernetes {
                    yaml """
apiVersion: v1
kind: Pod
spec:
  serviceAccountName: jenkins
  containers:
  - name: kubectl
    image: alpine/k8s:1.28.2
    command:
    - sleep
    args:
    - 99d
"""
                }
            }
            steps {
                container('kubectl') {
                    script {
                        echo "☸️ Deploy UltraRAG su Kubernetes..."
                        
                        withEnv(["ENABLE_AUTH=${params.ENABLE_AUTH}", "DATABASE_URL=${params.DATABASE_URL}", "JWT_SECRET=${params.JWT_SECRET}"]) {
                        sh '''
                            # Crea namespace se non esiste
                            kubectl create namespace ${K8S_NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -
                            
                            # Deploy ConfigMap
                            cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: ultrarag-config
  namespace: ${K8S_NAMESPACE}
data:
  MILVUS_HOST: "${MILVUS_HOST}"
  MILVUS_PORT: "${MILVUS_PORT}"
  ENABLE_AUTH: "${ENABLE_AUTH}"
  DATABASE_URL: "${DATABASE_URL}"
  JWT_SECRET: "${JWT_SECRET}"
EOF
                            
                            # Deploy Secret (placeholder)
                            cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: ultrarag-secrets
  namespace: ${K8S_NAMESPACE}
type: Opaque
data:
  ANTHROPIC_API_KEY: cGxhY2Vob2xkZXI=
EOF
                            
                            # Service is deployed via k8s/deployment-single-pod.yaml
                            
                            # Deploy new single pod deployment with auth proxy
                            kubectl apply -f k8s/deployment-single-pod.yaml
                            
                            # Deploy production ingress with auth proxy ports
                            kubectl apply -f k8s-mcp-ingress-prod.yaml
                            
                            # Legacy deployment (keeping for reference)
                            cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ultrarag
  namespace: ${K8S_NAMESPACE}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ultrarag
  template:
    metadata:
      labels:
        app: ultrarag
    spec:
      imagePullSecrets:
      - name: docker-config-secret
      containers:
      - name: ultrarag
        image: ${DOCKER_IMAGE}:${DOCKER_TAG}
        ports:
        - containerPort: 8000
          name: health
        - containerPort: 8001
          name: sayhello
        - containerPort: 8002
          name: retriever
        - containerPort: 8003
          name: generation
        - containerPort: 8004
          name: corpus
        - containerPort: 8005
          name: reranker
        - containerPort: 8006
          name: evaluation
        - containerPort: 8007
          name: benchmark
        - containerPort: 8008
          name: custom
        - containerPort: 8009
          name: prompt
        - containerPort: 8010
          name: router
        env:
        - name: MILVUS_HOST
          valueFrom:
            configMapKeyRef:
              name: ultrarag-config
              key: MILVUS_HOST
        - name: MILVUS_PORT
          valueFrom:
            configMapKeyRef:
              name: ultrarag-config
              key: MILVUS_PORT
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: ultrarag-secrets
              key: ANTHROPIC_API_KEY
        - name: EXA_API_KEY
          valueFrom:
            secretKeyRef:
              name: search-apis-secret
              key: exa-api-key
        - name: TAVILY_API_KEY
          valueFrom:
            secretKeyRef:
              name: search-apis-secret
              key: tavily-api-key
        - name: ENABLE_AUTH
          valueFrom:
            configMapKeyRef:
              name: ultrarag-config
              key: ENABLE_AUTH
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
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
EOF
                            
                            # MCP Service is deployed via k8s/deployment-single-pod.yaml
                            
                            # Verify MCP Authentication Secret exists
                            if ! kubectl get secret ultrarag-mcp-auth -n ${K8S_NAMESPACE} &>/dev/null; then
                                echo "⚠️  MCP authentication secret not found. Creating it..."
                                kubectl create secret generic ultrarag-mcp-auth \
                                    --from-literal=username=admin \
                                    --from-literal=password=UltraRAG2025Secure \
                                    --from-literal=api-key=UltraRAG-MCP-API-Key-2025 \
                                    --from-literal=jwt-secret=UltraRAG-JWT-Secret-2025 \
                                    --namespace=${K8S_NAMESPACE}
                                echo "✅ MCP authentication secret created"
                            else
                                echo "✅ MCP authentication secret already exists"
                            fi
                            
                            # Verify Search APIs Secret exists
                            if ! kubectl get secret search-apis-secret -n ${K8S_NAMESPACE} &>/dev/null; then
                                echo "⚠️  Search APIs secret not found. Creating placeholder..."
                                kubectl create secret generic search-apis-secret \
                                    --from-literal=exa-api-key=placeholder-exa-key \
                                    --from-literal=tavily-api-key=placeholder-tavily-key \
                                    --namespace=${K8S_NAMESPACE}
                                echo "✅ Search APIs secret created (please update with real keys)"
                            else
                                echo "✅ Search APIs secret already exists"
                            fi
                            
                            # Deploy Traefik Middleware for Basic Auth
                            cat <<EOF | kubectl apply -f -
apiVersion: traefik.containo.us/v1alpha1
kind: Middleware
metadata:
  name: ultrarag-mcp-auth
  namespace: ${K8S_NAMESPACE}
spec:
  basicAuth:
    secret: ultrarag-mcp-auth
    realm: "UltraRAG MCP Servers - Authentication Required"
EOF
                            
                            # Deploy Traefik Middleware for CORS
                            cat <<EOF | kubectl apply -f -
apiVersion: traefik.containo.us/v1alpha1
kind: Middleware
metadata:
  name: ultrarag-mcp-cors
  namespace: ${K8S_NAMESPACE}
spec:
  headers:
    accessControlAllowMethods:
      - GET
      - POST
      - PUT
      - DELETE
      - OPTIONS
    accessControlAllowOriginList:
      - "*"
    accessControlAllowHeaders:
      - "DNT"
      - "User-Agent"
      - "X-Requested-With"
      - "If-Modified-Since"
      - "Cache-Control"
      - "Content-Type"
      - "Range"
      - "Authorization"
      - "Accept"
    accessControlMaxAge: 100
    addVaryHeader: true
EOF
                            
                            # Deploy Traefik Middleware for Strip Prefix
                            cat <<EOF | kubectl apply -f -
apiVersion: traefik.containo.us/v1alpha1
kind: Middleware
metadata:
  name: ultrarag-mcp-strip-prefix
  namespace: ${K8S_NAMESPACE}
spec:
  stripPrefix:
    prefixes:
      - "/health"
      - "/sayhello"
      - "/retriever"
      - "/generation"
      - "/corpus"
      - "/reranker"
      - "/evaluation"
      - "/benchmark"
      - "/custom"
      - "/prompt"
      - "/router"
EOF
                            
                            # Deploy Traefik Middleware Chain
                            cat <<EOF | kubectl apply -f -
apiVersion: traefik.containo.us/v1alpha1
kind: Middleware
metadata:
  name: ultrarag-mcp-chain
  namespace: ${K8S_NAMESPACE}
spec:
  chain:
    middlewares:
      - name: ultrarag-mcp-auth
      - name: ultrarag-mcp-cors
      - name: ultrarag-mcp-strip-prefix
EOF
                            
                            # Deploy Traefik Ingress for MCP servers with authentication
                            cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ultrarag-mcp-auth-ingress
  namespace: ${K8S_NAMESPACE}
  annotations:
    kubernetes.io/ingress.class: "traefik"
    traefik.ingress.kubernetes.io/transport.respondingTimeouts.idleTimeout: "600"
    traefik.ingress.kubernetes.io/transport.respondingTimeouts.readTimeout: "600"
    traefik.ingress.kubernetes.io/transport.respondingTimeouts.writeTimeout: "600"
    traefik.ingress.kubernetes.io/custom-request-headers: "X-Forwarded-Proto:%[req.scheme]"
    traefik.ingress.kubernetes.io/router.middlewares: ${K8S_NAMESPACE}-ultrarag-mcp-chain@kubernetescrd
spec:
  rules:
  - host: ultrarag-mcp.webrobot.eu
    http:
      paths:
      - path: /health
        pathType: Prefix
        backend:
          service:
            name: ultrarag-mcp-service
            port:
              number: 8000
      - path: /sayhello
        pathType: Prefix
        backend:
          service:
            name: ultrarag-mcp-service
            port:
              number: 8001
      - path: /retriever
        pathType: Prefix
        backend:
          service:
            name: ultrarag-mcp-service
            port:
              number: 8002
      - path: /generation
        pathType: Prefix
        backend:
          service:
            name: ultrarag-mcp-service
            port:
              number: 8003
      - path: /corpus
        pathType: Prefix
        backend:
          service:
            name: ultrarag-mcp-service
            port:
              number: 8004
      - path: /reranker
        pathType: Prefix
        backend:
          service:
            name: ultrarag-mcp-service
            port:
              number: 8005
      - path: /evaluation
        pathType: Prefix
        backend:
          service:
            name: ultrarag-mcp-service
            port:
              number: 8006
      - path: /benchmark
        pathType: Prefix
        backend:
          service:
            name: ultrarag-mcp-service
            port:
              number: 8007
      - path: /custom
        pathType: Prefix
        backend:
          service:
            name: ultrarag-mcp-service
            port:
              number: 8008
      - path: /prompt
        pathType: Prefix
        backend:
          service:
            name: ultrarag-mcp-service
            port:
              number: 8009
      - path: /router
        pathType: Prefix
        backend:
          service:
            name: ultrarag-mcp-service
            port:
              number: 8010
EOF
                            
                            # Deploy Traefik Ingress for MCP servers without authentication (dev/test)
                            cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ultrarag-mcp-no-auth-ingress
  namespace: ${K8S_NAMESPACE}
  annotations:
    kubernetes.io/ingress.class: "traefik"
    traefik.ingress.kubernetes.io/transport.respondingTimeouts.idleTimeout: "600"
    traefik.ingress.kubernetes.io/transport.respondingTimeouts.readTimeout: "600"
    traefik.ingress.kubernetes.io/transport.respondingTimeouts.writeTimeout: "600"
    traefik.ingress.kubernetes.io/custom-request-headers: "X-Forwarded-Proto:%[req.scheme]"
    traefik.ingress.kubernetes.io/router.middlewares: ${K8S_NAMESPACE}-ultrarag-mcp-cors@kubernetescrd
spec:
  rules:
  - host: ultrarag-mcp-dev.webrobot.eu
    http:
      paths:
      - path: /health
        pathType: Prefix
        backend:
          service:
            name: ultrarag-mcp-service
            port:
              number: 8000
      - path: /sayhello
        pathType: Prefix
        backend:
          service:
            name: ultrarag-mcp-service
            port:
              number: 8001
      - path: /retriever
        pathType: Prefix
        backend:
          service:
            name: ultrarag-mcp-service
            port:
              number: 8002
      - path: /generation
        pathType: Prefix
        backend:
          service:
            name: ultrarag-mcp-service
            port:
              number: 8003
      - path: /corpus
        pathType: Prefix
        backend:
          service:
            name: ultrarag-mcp-service
            port:
              number: 8004
      - path: /reranker
        pathType: Prefix
        backend:
          service:
            name: ultrarag-mcp-service
            port:
              number: 8005
      - path: /evaluation
        pathType: Prefix
        backend:
          service:
            name: ultrarag-mcp-service
            port:
              number: 8006
      - path: /benchmark
        pathType: Prefix
        backend:
          service:
            name: ultrarag-mcp-service
            port:
              number: 8007
      - path: /custom
        pathType: Prefix
        backend:
          service:
            name: ultrarag-mcp-service
            port:
              number: 8008
      - path: /prompt
        pathType: Prefix
        backend:
          service:
            name: ultrarag-mcp-service
            port:
              number: 8009
      - path: /router
        pathType: Prefix
        backend:
          service:
            name: ultrarag-mcp-service
            port:
              number: 8010
EOF
                            
                            echo "✅ Deploy Kubernetes completato con Ingress Traefik"
                        '''
                        }
                    }
                }
            }
        }
    }

    post {
        always {
            script {
                echo "🏁 Build UltraRAG ${env.BUILD_NUMBER} completata"
                echo "⏱️ Durata totale: ${currentBuild.durationString}"
            }
        }
        failure {
            script {
                echo "❌ Pipeline UltraRAG fallita!"
                echo "📋 Controlla i log per i dettagli"
            }
        }
        success {
            script {
                echo "✅ Pipeline UltraRAG completata con successo!"
                echo "🌐 UltraRAG disponibile su: ultrarag-service.${K8S_NAMESPACE}.svc.cluster.local:8000"
                echo ""
                echo "🔗 MCP Servers URLs:"
                echo "   📊 Produzione (con autenticazione): https://ultrarag-mcp.webrobot.eu"
                echo "   🛠️ Sviluppo (senza autenticazione): https://ultrarag-mcp-dev.webrobot.eu"
                echo ""
                echo "🔐 Credenziali di accesso:"
                echo "   Username: admin"
                echo "   Password: UltraRAG2025Secure"
                echo ""
                echo "📋 Endpoints disponibili:"
                echo "   /health, /sayhello, /retriever, /generation, /corpus, /reranker"
                echo "   /evaluation, /benchmark, /custom, /prompt, /router"
            }
        }
    }
}