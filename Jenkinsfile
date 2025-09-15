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
        
        stage('Build All Images') {
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
                    },
                    'Build Jenkins': {
                        dir('jenkins') {
                            sh 'docker build -t finn-jenkins -f Dockerfile .'
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
                docker compose -p ${COMPOSE_PROJECT_NAME} up -d --build --scale jenkins=0
                
                echo "=== Waiting for services to start ==="
                sleep 60
                '''
            }
        }
        
        stage('Health Check') {
    steps {
        sh '''
        echo "=== Health Check ==="
        sleep 30  # Give services more time to start
        
        # Check backend with retries
        for i in {1..5}; do
            if docker compose -p ${COMPOSE_PROJECT_NAME} exec -T backend curl -f http://localhost:8000/health; then
                echo "✅ Backend is healthy"
                break
            else
                echo "⚠️ Backend health check attempt $i/5 failed, retrying..."
                if [ $i -eq 5 ]; then
                    echo "❌ Backend health check failed after 5 attempts"
                    docker compose -p ${COMPOSE_PROJECT_NAME} logs backend
                    exit 1
                fi
                sleep 10
            fi
        done
        
        # Check frontend with retries
        for i in {1..5}; do
            if curl -f http://localhost:3000 >/dev/null 2>&1; then
                echo "✅ Frontend is accessible"
                break
            else
                echo "⚠️ Frontend check attempt $i/5 failed, retrying..."
                if [ $i -eq 5 ]; then
                    echo "❌ Frontend check failed after 5 attempts"
                    docker compose -p ${COMPOSE_PROJECT_NAME} logs frontend
                    exit 1
                fi
                sleep 10
            fi
        done
        
        # Check if services are running
        if docker compose -p ${COMPOSE_PROJECT_NAME} ps | grep -q "Up"; then
            echo "✅ All services are running"
        else
            echo "❌ Some services failed to start"
            docker compose -p ${COMPOSE_PROJECT_NAME} ps
            exit 1
        fi
        '''
    }
}
        
        stage('Verify Monitoring') {
            steps {
                sh '''
                echo "=== Verifying monitoring services ==="
                
                # Check Prometheus configuration
                if docker compose -p ${COMPOSE_PROJECT_NAME} exec -T prometheus promtool check config /etc/prometheus/prometheus.yml; then
                    echo "✅ Prometheus configuration is valid"
                else
                    echo "❌ Prometheus configuration is invalid"
                    docker compose -p ${COMPOSE_PROJECT_NAME} logs prometheus
                fi
                
                # Check Alertmanager configuration
                if docker compose -p ${COMPOSE_PROJECT_NAME} exec -T alertmanager amtool check-config /etc/alertmanager/config.yml; then
                    echo "✅ Alertmanager configuration is valid"
                else
                    echo "❌ Alertmanager configuration is invalid"
                    docker compose -p ${COMPOSE_PROJECT_NAME} logs alertmanager
                fi
                '''
            }
        }
    }
    
    post {
    always {
        script {
            // Archive test results - fix the path
            junit 'Back/test-results/test-results.xml'
            
            // Also archive coverage if available
            archiveArtifacts artifacts: 'Back/coverage/coverage.xml', fingerprint: true
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
            echo "Alertmanager: http://localhost:9093"
            echo "Ollama: http://localhost:11435"
            '''
        }
    }
}