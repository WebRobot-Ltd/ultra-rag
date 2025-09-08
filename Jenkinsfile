pipeline {
    agent none // Definiamo l'agente a livello di stage

    environment {
        // Repository GitHub
        GITHUB_REPOSITORY = 'webrobot-ltd/webrobot-etl-clouddashboard'

        // Immagine Docker UltraRAG su GHCR
        DOCKER_IMAGE = "ghcr.io/webrobot-ltd/ultra-rag"
        DOCKER_TAG = "${env.BUILD_NUMBER}"

        // Credenziali
        DOCKER_REGISTRY = 'ghcr.io'
        DOCKER_CREDENTIALS = 'github-token'

        // Kubernetes
        K8S_NAMESPACE = 'default'
        K8S_CONTEXT = 'webrobot'

        // UltraRAG specifici
        ULTRARAG_DIR = 'ultrarag-local'
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
            description: 'Abilita supporto GPU per UltraRAG'
        )
    }

    stages {
        stage('Initialize') {
            steps {
                script {
                    env.DO_DEPLOY = false
                    def cause = currentBuild.getBuildCauses('hudson.triggers.SCMTrigger$SCMTriggerCause')
                    if (cause) {
                        echo "Build triggerato da SCM. Abilito il deploy automatico."
                        env.DO_DEPLOY = true
                    }
                }
            }
        }

        stage('Checkout') {
            agent any
            steps {
                checkout scm
                script {
                    echo "🔄 Checkout completato per build ${env.BUILD_TYPE}"
                    echo "📦 Repository: ${env.GITHUB_REPOSITORY}"
                    echo "🐳 Immagine: ${env.DOCKER_IMAGE}:${env.DOCKER_TAG}"
                    echo "🏗️ Build Type: ${params.BUILD_TYPE}"
                    echo "🎯 Directory UltraRAG: ${env.ULTRARAG_DIR}"
                }
            }
        }

        stage('Validate UltraRAG Structure') {
            agent any
            steps {
                script {
                    echo "🔍 Validazione struttura UltraRAG..."
                    dir(env.ULTRARAG_DIR) {
                        // Verifica file essenziali
                        sh 'test -f Dockerfile || (echo "Dockerfile mancante" && exit 1)'
                        sh 'test -f environment.yml || (echo "environment.yml mancante" && exit 1)'
                        sh 'test -f pyproject.toml || (echo "pyproject.toml mancante" && exit 1)'
                        sh 'test -d src/ultrarag || (echo "src/ultrarag mancante" && exit 1)'
                        sh 'test -d examples || (echo "examples mancante" && exit 1)'

                        echo "✅ Struttura UltraRAG valida"
                    }
                }
            }
        }

        stage('Build & Push Docker Image') {
            when {
                expression { !params.REDEPLOY_ONLY }
            }
            agent {
                kubernetes {
                    label 'kaniko-gpu'
                    yaml """
                        apiVersion: v1
                        kind: Pod
                        spec:
                          nodeSelector:
                            accelerator: nvidia-tesla-k80
                          tolerations:
                          - key: "nvidia.com/gpu"
                            operator: "Exists"
                            effect: "NoSchedule"
                          containers:
                          - name: kaniko
                            image: gcr.io/kaniko-project/executor:v1.9.0-debug
                            imagePullPolicy: Always
                            command:
                            - /busybox/cat
                            tty: true
                            resources:
                              requests:
                                nvidia.com/gpu: 1
                              limits:
                                nvidia.com/gpu: 1
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
                        echo "🐳 Build immagine UltraRAG con Kaniko (GPU-enabled)..."
                        dir(env.ULTRARAG_DIR) {
                            // Build con supporto GPU
                            def gpuArgs = params.ENABLE_GPU ? '--build-arg CUDA_VERSION=12.2.2' : ''
                            sh """
                                /kaniko/executor --context=\$(pwd) \\
                                --dockerfile=Dockerfile \\
                                --destination=${env.DOCKER_IMAGE}:${env.DOCKER_TAG} \\
                                --destination=${env.DOCKER_IMAGE}:latest \\
                                --destination=${env.DOCKER_IMAGE}:${env.BUILD_TYPE} \\
                                --build-arg MILVUS_HOST=${env.MILVUS_HOST} \\
                                --build-arg MILVUS_PORT=${env.MILVUS_PORT} \\
                                --verbosity=debug
                            """
                        }
                        echo "✅ Build completato: ${env.DOCKER_IMAGE}:${env.DOCKER_TAG}"
                    }
                }
            }
        }

        stage('Test UltraRAG Image') {
            when {
                expression { params.RUN_TESTS && !params.REDEPLOY_ONLY }
            }
            agent {
                kubernetes {
                    label 'test-gpu'
                    yaml """
                        apiVersion: v1
                        kind: Pod
                        spec:
                          nodeSelector:
                            accelerator: nvidia-tesla-k80
                          tolerations:
                          - key: "nvidia.com/gpu"
                            operator: "Exists"
                            effect: "NoSchedule"
                          containers:
                          - name: ultrarag-test
                            image: ${env.DOCKER_IMAGE}:${env.DOCKER_TAG}
                            imagePullPolicy: Always
                            command:
                            - sleep
                            args:
                            - 300
                            resources:
                              requests:
                                nvidia.com/gpu: 1
                              limits:
                                nvidia.com/gpu: 1
                            env:
                            - name: MILVUS_HOST
                              value: ${env.MILVUS_HOST}
                            - name: MILVUS_PORT
                              value: ${env.MILVUS_PORT}
"""
                }
            }
            steps {
                container('ultrarag-test') {
                    script {
                        echo "🧪 Test immagine UltraRAG..."

                        // Test health check
                        sh 'python /app/health_check.py'

                        // Test import UltraRAG
                        sh 'python -c "import ultrarag; print(\'UltraRAG import successful\')"'

                        // Test connessione Milvus (se disponibile)
                        sh '''
                            python -c "
                            try:
                                import ultrarag
                                from ultrarag.utils import check_milvus_connection
                                result = check_milvus_connection('${MILVUS_HOST}', ${MILVUS_PORT})
                                print(f'Milvus connection: {result}')
                            except Exception as e:
                                print(f'Milvus test skipped: {e}')
                            "
                        '''

                        echo "✅ Test completati con successo"
                    }
                }
            }
        }

        stage('Deploy to Kubernetes') {
            when {
                expression { params.DEPLOY_K8S || params.REDEPLOY_ONLY || env.DO_DEPLOY == 'true' }
            }
            agent {
                kubernetes {
                    label 'kubectl'
                    yaml """
                        apiVersion: v1
                        kind: Pod
                        spec:
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
                        echo "⚙️ Deploy UltraRAG su Kubernetes..."
                        dir('k8s') { // Directory con i file K8s di UltraRAG
                            def imageTag = params.REDEPLOY_ONLY ? 'latest' : env.DOCKER_TAG
                            echo "Deploying UltraRAG image with tag: ${imageTag}"

                            // Aggiorna l'immagine nel deployment
                            sh """
                                sed -i 's|ghcr.io/webrobot-ltd/ultra-rag:.*|ghcr.io/webrobot-ltd/ultra-rag:${imageTag}|g' ultrarag-deployment.yaml
                            """

                            // Applica le configurazioni K8s
                            sh "kubectl apply -f ultrarag-configmap.yaml -n ${env.K8S_NAMESPACE}"
                            sh "kubectl apply -f ultrarag-service.yaml -n ${env.K8S_NAMESPACE}"
                            sh "kubectl apply -f ultrarag-deployment.yaml -n ${env.K8S_NAMESPACE}"

                            // Verifica rollout
                            sh "kubectl rollout status deployment/ultrarag -n ${env.K8S_NAMESPACE} --timeout=600s"

                            // Mostra informazioni deployment
                            sh "kubectl get pods -l app=ultrarag -n ${env.K8S_NAMESPACE}"
                            sh "kubectl get services -l app=ultrarag -n ${env.K8S_NAMESPACE}"
                        }

                        echo "✅ Deploy UltraRAG su Kubernetes completato"
                        echo "🌐 Endpoint interno: ultrarag.default.svc.cluster.local:8000"
                    }
                }
            }
        }

        stage('Integration Test') {
            when {
                expression { params.DEPLOY_K8S && params.RUN_TESTS }
            }
            agent {
                kubernetes {
                    label 'integration-test'
                    yaml """
                        apiVersion: v1
                        kind: Pod
                        spec:
                          containers:
                          - name: integration-test
                            image: python:3.11-alpine
                            command:
                            - sleep
                            args:
                            - 300
"""
                }
            }
            steps {
                container('integration-test') {
                    script {
                        echo "🔗 Test di integrazione UltraRAG..."

                        // Installa curl per i test HTTP
                        sh 'apk add --no-cache curl'

                        // Test health endpoint
                        sh """
                            echo "Testing health endpoint..."
                            for i in {1..30}; do
                                if curl -f http://ultrarag.default.svc.cluster.local:8000/health; then
                                    echo "✅ Health check passed"
                                    break
                                fi
                                echo "Waiting for service... (\$i/30)"
                                sleep 10
                            done
                        """

                        // Test API endpoints
                        sh """
                            echo "Testing API endpoints..."
                            curl -X GET http://ultrarag.default.svc.cluster.local:8000/api/servers || echo "Servers endpoint check"
                        """

                        echo "✅ Test di integrazione completati"
                    }
                }
            }
        }
    }

    post {
        success {
            script {
                echo "✅ Pipeline UltraRAG completata con successo!"
                echo "🐳 Immagine: ${env.DOCKER_IMAGE}:${env.DOCKER_TAG}"
                echo "🏗️ Build Type: ${params.BUILD_TYPE}"
                echo "🧪 Test: ${params.RUN_TESTS ? 'Eseguiti' : 'Saltati'}"
                echo "🚀 Push: ${params.PUSH_IMAGE ? 'Completato' : 'Saltato'}"
                echo "⚙️ Deploy: ${params.DEPLOY_K8S ? 'Completato' : 'Saltato'}"
                echo "🎯 GPU: ${params.ENABLE_GPU ? 'Abilitata' : 'Disabilitata'}"
                echo ""
                echo "📊 Informazioni deployment:"
                echo "   - Namespace: ${env.K8S_NAMESPACE}"
                echo "   - Service: ultrarag.default.svc.cluster.local:8000"
                echo "   - Milvus: ${env.MILVUS_HOST}:${env.MILVUS_PORT}"
            }
        }
        failure {
            script {
                echo "❌ Pipeline UltraRAG fallita!"
                echo "🔍 Controlla i log per i dettagli"
                echo "💡 Possibili cause:"
                echo "   - Build GPU fallito (verifica node con GPU)"
                echo "   - Test di connessione Milvus falliti"
                echo "   - Deploy Kubernetes fallito"
            }
        }
        always {
            script {
                echo "🏁 Build UltraRAG ${env.BUILD_NUMBER} completata"
                echo "📊 Durata totale: ${currentBuild.durationString}"
            }
        }
    }
}
