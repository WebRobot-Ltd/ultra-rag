pipeline {
    agent none

    environment {
        GITHUB_REPOSITORY = 'WebRobot-Ltd/ultra-rag'
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
            choices: ['dev', 'staging', 'production'],
            description: 'Tipo di build da eseguire'
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
            agent {
                kubernetes {
                    yaml """
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: git
    image: alpine/git:latest
    command:
    - cat
    tty: true
"""
                }
            }
            steps {
                checkout scm
            }
        }

        stage('Validate UltraRAG Structure') {
            agent {
                kubernetes {
                    yaml """
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: git
    image: alpine/git:latest
    command:
    - cat
    tty: true
"""
                }
            }
            steps {
                script {
                    echo "🔍 Validazione struttura UltraRAG..."
                    
                    sh '''
                        test -f Dockerfile || (echo "Dockerfile mancante" && exit 1)
                        test -f pyproject.toml || (echo "pyproject.toml mancante" && exit 1)
                        test -d src || (echo "Directory src mancante" && exit 1)
                        echo "✅ Struttura UltraRAG valida"
                    '''
                }
            }
        }

        stage('Build & Push Docker Image') {
            when {
                not { params.REDEPLOY_ONLY }
            }
            agent {
                kubernetes {
                    yaml """
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: kaniko
    image: gcr.io/kaniko-project/executor:latest
    command:
    - cat
    tty: true
    volumeMounts:
    - name: docker-config
      mountPath: /kaniko/.docker
  volumes:
  - name: docker-config
    secret:
      secretName: docker-config
"""
                }
            }
            steps {
                script {
                    echo "🐳 Build Docker image UltraRAG..."
                    
                    sh '''
                        /kaniko/executor \
                            --context=. \
                            --dockerfile=Dockerfile \
                            --destination=${DOCKER_IMAGE}:${DOCKER_TAG} \
                            --destination=${DOCKER_IMAGE}:latest \
                            --cache=true \
                            --cache-ttl=24h
                    '''
                    
                    echo "✅ Immagine Docker buildata: ${env.DOCKER_IMAGE}:${env.DOCKER_TAG}"
                }
            }
        }

        stage('Deploy to Kubernetes') {
            when {
                params.DEPLOY_K8S
            }
            agent {
                kubernetes {
                    yaml """
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: kubectl
    image: bitnami/kubectl:latest
    command:
    - cat
    tty: true
"""
                }
            }
            steps {
                script {
                    echo "☸️ Deploy UltraRAG su Kubernetes..."
                    
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
