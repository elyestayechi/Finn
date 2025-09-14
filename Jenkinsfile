pipeline {
    agent any
    environment {
        DOCKER_HOST = 'unix:///var/run/docker.sock'
        COMPOSE_PROJECT_NAME = "finn-pipeline-${BUILD_ID}"
    }
    
    stages {
        stage('Checkout & Prepare') {
            steps {
                git branch: 'main', url: 'https://github.com/elyestayechi/Finn.git'
                
                sh '''
                echo "=== Preparing workspace ==="
                # Ensure monitoring structure exists
                chmod +x create-monitoring-structure.sh
                ./create-monitoring-structure.sh
                
                # Create test directories
                mkdir -p Back/test-results Back/coverage
                chmod 777 Back/test-results Back/coverage
                '''
            }
        }
        
        stage('Build Images') {
            steps {
                parallel(
                    'Build Backend': {
                        dir('Back') {
                            sh 'docker build -t finn-loan-analysis-backend -f Dockerfile .'
                        }
                    },
                    'Build Frontend': {
                        dir('Front') {
                            sh 'docker build -t finn-loan-analysis-frontend -f Dockerfile .'
                        }
                    }
                )
            }
        }
        
        stage('Run Tests') {
            steps {
                dir('Back') {
                    sh '''
                    echo "=== Running unit tests ==="
                    docker build -t finn-loan-analysis-backend-test -f Dockerfile.test .
                    docker run --rm \
                        -v "$(pwd)/test-results:/app/test-results" \
                        -v "$(pwd)/coverage:/app/coverage" \
                        -e OLLAMA_HOST=http://dummy:11434 \
                        finn-loan-analysis-backend-test
                    '''
                }
            }
        }
        
        stage('Deploy Stack') {
            steps {
                sh '''
                echo "=== Cleaning up previous deployment ==="
                # Clean up any existing containers
                docker compose -p ${COMPOSE_PROJECT_NAME} down -v --remove-orphans 2>/dev/null || true
                
                # Free up ports
                for port in 8000 3000 9090 9093 3001 11435; do
                    docker ps -q --filter "publish=$port" | xargs -r docker rm -f 2>/dev/null || true
                done
                
                sleep 2
                
                echo "=== Deploying application stack ==="
                docker compose -p ${COMPOSE_PROJECT_NAME} up -d --scale jenkins=0
                
                echo "=== Waiting for services to start ==="
                sleep 30
                '''
            }
        }
        
        stage('Health Check') {
            steps {
                sh '''
                echo "=== Health Check ==="
                
                # Check backend
                if docker compose -p ${COMPOSE_PROJECT_NAME} exec -T backend curl -f http://localhost:8000/health; then
                    echo "✅ Backend is healthy"
                else
                    echo "❌ Backend health check failed"
                    exit 1
                fi
                
                # Check if services are running
                if docker compose -p ${COMPOSE_PROJECT_NAME} ps | grep -q "Up"; then
                    echo "✅ All services are running"
                else
                    echo "❌ Some services failed to start"
                    exit 1
                fi
                '''
            }
        }
    }
    
    post {
        always {
            script {
                // Archive test results
                junit 'Back/test-results/*.xml'
                
                // Capture logs
                sh '''
                docker compose -p ${COMPOSE_PROJECT_NAME} logs --no-color --tail=100 > deployment-logs.txt
                docker compose -p ${COMPOSE_PROJECT_NAME} ps > container-status.txt
                '''
                
                archiveArtifacts artifacts: 'deployment-logs.txt,container-status.txt', fingerprint: true
                
                // Cleanup on failure
                if (currentBuild.result != 'SUCCESS') {
                    sh '''
                    echo "=== Cleaning up failed deployment ==="
                    docker compose -p ${COMPOSE_PROJECT_NAME} down -v 2>/dev/null || true
                    '''
                }
            }
        }
        
        success {
            sh '''
            echo "🎉 DEPLOYMENT SUCCESSFUL! 🎉"
            echo "Access your services at:"
            echo "Frontend: http://localhost:3000"
            echo "Backend: http://localhost:8000"
            echo "Prometheus: http://localhost:9090"
            echo "Grafana: http://localhost:3001"
            '''
        }
    }
}