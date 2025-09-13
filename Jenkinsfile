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
                // CLEANUP COMPLET - Arrêter TOUS les conteneurs qui utilisent les ports 11434 ou 11435
                sh '''
                echo "=== Nettoyage des conteneurs existants ==="
                # Arrêter le projet actuel
                docker compose -p ${COMPOSE_PROJECT_NAME} down 2>/dev/null || true
                
                # Arrêter TOUS les conteneurs Ollama qui pourraient bloquer les ports
                docker stop $(docker ps -q --filter "ancestor=ollama/ollama") 2>/dev/null || true
                docker rm $(docker ps -aq --filter "ancestor=ollama/ollama") 2>/dev/null || true
                
                # Arrêter les conteneurs utilisant les ports 11434 ou 11435
                docker stop $(docker ps -q --filter "publish=11434") 2>/dev/null || true
                docker stop $(docker ps -q --filter "publish=11435") 2>/dev/null || true
                docker rm $(docker ps -aq --filter "publish=11434") 2>/dev/null || true
                docker rm $(docker ps -aq --filter "publish=11435") 2>/dev/null || true
                
                # Nettoyer les réseaux orphelins
                docker network prune -f 2>/dev/null || true
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
                if (fileExists("Back/test-results/test-results.xml")) {
                    junit "Back/test-results/test-results.xml"
                    echo "✓ Test results archivés depuis: Back/test-results/test-results.xml"
                } else {
                    echo "⚠️ Fichier de résultats de tests non trouvé"
                    sh 'find . -name "test-results.xml" -type f 2>/dev/null | head -5 || true'
                }
                
                if (fileExists("Back/coverage/coverage.xml")) {
                    archiveArtifacts artifacts: "Back/coverage/coverage.xml", fingerprint: true
                    echo "✓ Couverture de code archivée depuis: Back/coverage/coverage.xml"
                } else {
                    echo "⚠️ Fichier de couverture non trouvé"
                    sh 'find . -name "coverage.xml" -type f 2>/dev/null | head -5 || true'
                }
            }
            
            // Nettoyage final avec le même nom de projet
            sh '''
            echo "=== Nettoyage final ==="
            docker compose -p ${COMPOSE_PROJECT_NAME} logs --no-color > docker-logs.txt 2>/dev/null || true
            docker compose -p ${COMPOSE_PROJECT_NAME} down 2>/dev/null || true
            
            # Nettoyage Docker complet mais PRÉSERVER JENKINS
            echo "=== Nettoyage système Docker (sauf Jenkins) ==="
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