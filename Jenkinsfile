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
                    // Clean previous test results
                    sh '''
                    rm -rf test-results coverage || true
                    mkdir -p test-results coverage
                    chmod 777 test-results coverage
                    '''
                    
                    // Build and run tests
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
                // NETTOYAGE COMPLET - Arrêter TOUS les conteneurs qui pourraient bloquer les ports
                sh '''
                echo "=== NETTOYAGE COMPLET DES CONTENEURS ==="
                
                # Arrêter le projet actuel
                docker compose -p ${COMPOSE_PROJECT_NAME} down 2>/dev/null || true
                
                # Arrêter TOUS les conteneurs qui pourraient bloquer nos ports
                echo "Arrêt des conteneurs utilisant les ports 8000, 3000, 11434, 11435, 9090, 3001, 9093..."
                
                # Liste de tous les ports utilisés par notre application
                PORTS="8000 3000 11434 11435 9090 3001 9093"
                
                for port in $PORTS; do
                    echo "Nettoyage du port $port"
                    # Trouver et arrêter les conteneurs utilisant ce port
                    CONTAINERS=$(docker ps -q --filter "publish=$port")
                    if [ ! -z "$CONTAINERS" ]; then
                        echo "Arrêt des conteneurs utilisant le port $port: $CONTAINERS"
                        docker stop $CONTAINERS 2>/dev/null || true
                        docker rm $CONTAINERS 2>/dev/null || true
                    fi
                    
                    # Trouver et supprimer les conteneurs arrêtés utilisant ce port
                    STOPPED_CONTAINERS=$(docker ps -aq --filter "publish=$port")
                    if [ ! -z "$STOPPED_CONTAINERS" ]; then
                        echo "Suppression des conteneurs arrêtés utilisant le port $port: $STOPPED_CONTAINERS"
                        docker rm $STOPPED_CONTAINERS 2>/dev/null || true
                    fi
                done
                
                # Arrêter spécifiquement les conteneurs Ollama et backend
                echo "Arrêt des conteneurs Ollama et backend..."
                docker stop $(docker ps -q --filter "ancestor=ollama/ollama") 2>/dev/null || true
                docker stop $(docker ps -q --filter "ancestor=finn-loan-analysis-backend") 2>/dev/null || true
                docker rm $(docker ps -aq --filter "ancestor=ollama/ollama") 2>/dev/null || true
                docker rm $(docker ps -aq --filter "ancestor=finn-loan-analysis-backend") 2>/dev/null || true
                
                # Nettoyer les réseaux orphelins
                echo "Nettoyage des réseaux..."
                docker network prune -f 2>/dev/null || true
                
                echo "=== NETTOYAGE TERMINÉ ==="
                '''
                
                // Déploiement avec nom de projet unique
                sh 'docker compose -p ${COMPOSE_PROJECT_NAME} up --no-build --scale jenkins=0 -d'
                
                // Attendre plus longtemps pour qu'Ollama démarre
                sleep(time: 120, unit: 'SECONDS')
            }
        }
        
        stage('Health Check') {
            steps {
                sh '''
                # Attendre que le backend soit healthy
                echo "=== Vérification du backend ==="
                timeout 120 bash -c 'until curl -f http://localhost:8000/health; do sleep 5; echo "En attente du backend..."; done'
                
                # Attendre que le frontend soit accessible
                echo "=== Vérification du frontend ==="
                timeout 60 bash -c 'until curl -f http://localhost:3000 >/dev/null 2>&1; do sleep 5; echo "En attente du frontend..."; done'
                
                echo "=== Tous les services sont opérationnels ==="
                '''
            }
        }
    }
    
    post {
        always {
            script {
                // Archivage des résultats de tests
                def testResultsFile = "Back/test-results/test-results.xml"
                def coverageFile = "Back/coverage/coverage.xml"
                
                if (fileExists(testResultsFile)) {
                    junit testResultsFile
                    echo "✓ Test results archivés depuis: ${testResultsFile}"
                } else {
                    echo "⚠️ Fichier de résultats de tests non trouvé: ${testResultsFile}"
                    sh "find . -name 'test-results.xml' -type f | head -5 || true"
                }
                
                if (fileExists(coverageFile)) {
                    archiveArtifacts artifacts: coverageFile, fingerprint: true
                    echo "✓ Couverture de code archivée depuis: ${coverageFile}"
                } else {
                    echo "⚠️ Fichier de couverture non trouvé: ${coverageFile}"
                    sh "find . -name 'coverage.xml' -type f | head -5 || true"
                }
            }
            
            // Nettoyage final avec le même nom de projet
            sh '''
            echo "=== NETTOYAGE FINAL ==="
            docker compose -p ${COMPOSE_PROJECT_NAME} logs --no-color > docker-logs.txt 2>/dev/null || true
            docker compose -p ${COMPOSE_PROJECT_NAME} down 2>/dev/null || true
            
            # Nettoyage Docker complet mais PRÉSERVER JENKINS
            echo "Nettoyage système Docker (sauf Jenkins)..."
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