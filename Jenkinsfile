pipeline {
    agent any
    environment {
        DOCKER_HOST = 'unix:///var/run/docker.sock'
        COMPOSE_PROJECT_NAME = "finn-pipeline-${BUILD_ID}"
    }
    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/elyestayechi/Finn.git'
            }
        }
        
        stage('Build Backend') {
            steps {
                dir('Back') {
                    sh 'docker build -t finn-loan-analysis-backend -f Dockerfile .'
                }
            }
        }
        
        stage('Build Frontend') {
            steps {
                dir('Front') {
                    sh 'docker build -t finn-loan-analysis-frontend -f Dockerfile .'
                }
            }
        }
        
        stage('Run Unit Tests') {
            steps {
                dir('Back') {
                    sh '''
                    rm -rf test-results coverage || true
                    mkdir -p test-results coverage
                    chmod 777 test-results coverage
                    '''
                    
                    sh 'docker build -t finn-loan-analysis-backend-test -f Dockerfile.test .'
                    
                    sh '''
                    docker run --rm \
                        -v "$(pwd)/test-results:/app/test-results" \
                        -v "$(pwd)/coverage:/app/coverage" \
                        finn-loan-analysis-backend-test
                    '''
                }
            }
        }
        
        stage('Deploy') {
            steps {
                sh '''
                echo "=== NETTOYAGE COMPLET DES CONTENEURS ==="
                docker compose -p ${COMPOSE_PROJECT_NAME} down 2>/dev/null || true
                
                PORTS="8000 3000 11434 11435 9090 3001 9093"
                for port in $PORTS; do
                    echo "Nettoyage du port $port"
                    CONTAINERS=$(docker ps -q --filter "publish=$port")
                    if [ ! -z "$CONTAINERS" ]; then
                        echo "Arrêt des conteneurs utilisant le port $port: $CONTAINERS"
                        docker stop $CONTAINERS 2>/dev/null || true
                        docker rm $CONTAINERS 2>/dev/null || true
                    fi
                done
                
                docker network prune -f 2>/dev/null || true
                echo "=== NETTOYAGE TERMINÉ ==="
                '''
                
                sh 'docker compose -p ${COMPOSE_PROJECT_NAME} up --no-build --scale jenkins=0 -d'
                sleep(time: 60, unit: 'SECONDS')
            }
        }
        
        stage('Health Check') {
            steps {
                sh '''
                # Health check du backend
                echo "=== Vérification du backend ==="
                BACKEND_CONTAINER=$(docker ps -q --filter "name=${COMPOSE_PROJECT_NAME}-backend")
                
                if [ -z "$BACKEND_CONTAINER" ]; then
                    echo "❌ Conteneur backend non trouvé"
                    docker ps -a
                    exit 1
                fi
                
                timeout 120 bash -c '
                for i in {1..24}; do
                    if docker exec $BACKEND_CONTAINER curl -f http://localhost:8000/health; then
                        echo "✅ Backend est healthy!"
                        exit 0
                    fi
                    echo "Tentative $i/24 - Backend non ready, attente 5 secondes..."
                    sleep 5
                done
                echo "❌ Échec: Backend non healthy après 2 minutes"
                docker compose -p ${COMPOSE_PROJECT_NAME} logs backend
                exit 1
                '
                
                # Health check du frontend
                echo "=== Vérification du frontend ==="
                FRONTEND_CONTAINER=$(docker ps -q --filter "name=${COMPOSE_PROJECT_NAME}-frontend")
                timeout 60 bash -c '
                for i in {1..12}; do
                    if docker exec $FRONTEND_CONTAINER wget -q --spider http://localhost:3000; then
                        echo "✅ Frontend est accessible!"
                        exit 0
                    fi
                    echo "Tentative $i/12 - Frontend non ready, attente 5 secondes..."
                    sleep 5
                done
                echo "❌ Échec: Frontend non accessible après 1 minute"
                exit 1
                '
                
                echo "=== Tous les services sont opérationnels ==="
                '''
            }
        }
    }
    
    post {
        always {
            script {
                if (fileExists("Back/test-results/test-results.xml")) {
                    junit "Back/test-results/test-results.xml"
                    echo "✓ Test results archivés"
                } else {
                    echo "⚠️ Fichier de résultats de tests non trouvé"
                }
                
                if (fileExists("Back/coverage/coverage.xml")) {
                    archiveArtifacts artifacts: "Back/coverage/coverage.xml", fingerprint: true
                    echo "✓ Couverture de code archivée"
                } else {
                    echo "⚠️ Fichier de couverture non trouvé"
                }
            }
            
            sh '''
            echo "=== NETTOYAGE FINAL ==="
            docker compose -p ${COMPOSE_PROJECT_NAME} logs --no-color > docker-logs.txt 2>/dev/null || true
            docker compose -p ${COMPOSE_PROJECT_NAME} down 2>/dev/null || true
            docker system prune -f --filter "label!=com.docker.compose.project=jenkins" 2>/dev/null || true
            '''
            
            archiveArtifacts artifacts: 'docker-logs.txt', fingerprint: true
        }
        success {
            echo 'Pipeline réussi ! ✅'
        }
        failure {
            echo 'Pipeline échoué ! ❌'
        }
    }
}