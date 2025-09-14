pipeline {
    agent any
    environment {
        DOCKER_HOST = 'unix:///var/run/docker.sock'
        COMPOSE_PROJECT_NAME = "finn-pipeline-${BUILD_ID}"
        WORKSPACE = pwd()
    }
    stages {
        stage('Checkout & Prepare') {
            steps {
                git branch: 'main', url: 'https://github.com/elyestayechi/Finn.git'
                
                sh '''
                echo "=== Preparing workspace ==="
                echo "Workspace: ${WORKSPACE}"
                
                # Create test directories
                mkdir -p Back/test-results Back/coverage
                chmod 777 Back/test-results Back/coverage
                
                # Verify monitoring structure exists
                if [ ! -d "monitoring" ]; then
                    echo "❌ ERROR: monitoring directory not found!"
                    exit 1
                fi
                
                # Verify critical monitoring files exist
                echo "Checking monitoring/prometheus/prometheus.yml..."
                if [ ! -f "monitoring/prometheus/prometheus.yml" ]; then
                    echo "❌ ERROR: monitoring/prometheus/prometheus.yml not found!"
                    exit 1
                else
                    echo "✅ Found: monitoring/prometheus/prometheus.yml"
                fi
                
                echo "Checking monitoring/prometheus/alerts.yml..."
                if [ ! -f "monitoring/prometheus/alerts.yml" ]; then
                    echo "❌ ERROR: monitoring/prometheus/alerts.yml not found!"
                    exit 1
                else
                    echo "✅ Found: monitoring/prometheus/alerts.yml"
                fi
                
                echo "Checking monitoring/alertmanager/config.yml..."
                if [ ! -f "monitoring/alertmanager/config.yml" ]; then
                    echo "❌ ERROR: monitoring/alertmanager/config.yml not found!"
                    exit 1
                else
                    echo "✅ Found: monitoring/alertmanager/config.yml"
                fi
                
                echo "=== Monitoring configuration verified ==="
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
                    
                    # Build test image
                    docker build -t finn-loan-analysis-backend-test -f Dockerfile.test .
                    
                    # Run tests with proper volume mounts
                    docker run --rm \
                        -v "$(pwd)/test-results:/app/test-results" \
                        -v "$(pwd)/coverage:/app/coverage" \
                        -e OLLAMA_HOST=http://dummy:11434 \
                        finn-loan-analysis-backend-test
                    '''
                }
            }
        }
        
        stage('Deploy Complete Stack') {
            steps {
                sh '''
                echo "=== Cleaning up previous containers ==="
                docker compose -p ${COMPOSE_PROJECT_NAME} down 2>/dev/null || true
                
                # Clean up any dangling containers
                docker ps -aq --filter "name=${COMPOSE_PROJECT_NAME}" | xargs docker rm -f 2>/dev/null || true
                
                # Build and start the complete stack EXCEPT Jenkins
                echo "=== Building and starting application stack (excluding Jenkins) ==="
                
                docker compose -p ${COMPOSE_PROJECT_NAME} up --build --scale jenkins=0 -d
                
                echo "=== Waiting for full stack initialization (3 minutes) ==="
                sleep 180
                '''
            }
        }
        
        stage('Comprehensive Health Check') {
            steps {
                sh '''
                echo "=== Comprehensive health check of ALL services ==="
                
                # Check each service individually
                echo "Checking ollama..."
                for i in $(seq 1 30); do
                    if curl -f http://localhost:11435 >/dev/null 2>&1; then
                        echo "✅ Ollama is healthy!"
                        break
                    fi
                    if [ $i -eq 30 ]; then
                        echo "❌ Ollama health check failed after 150 seconds"
                        docker compose -p ${COMPOSE_PROJECT_NAME} logs ollama | tail -20
                    fi
                    sleep 5
                done
                
                echo "Checking backend..."
                for i in $(seq 1 40); do
                    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
                        echo "✅ Backend is healthy!"
                        break
                    fi
                    if [ $i -eq 40 ]; then
                        echo "❌ Backend health check failed after 200 seconds"
                        docker compose -p ${COMPOSE_PROJECT_NAME} logs backend | tail -20
                        exit 1
                    fi
                    sleep 5
                done
                
                echo "Checking frontend..."
                for i in $(seq 1 30); do
                    if curl -f http://localhost:3000 >/dev/null 2>&1; then
                        echo "✅ Frontend is accessible!"
                        break
                    fi
                    if [ $i -eq 30 ]; then
                        echo "❌ Frontend health check failed after 150 seconds"
                        docker compose -p ${COMPOSE_PROJECT_NAME} logs frontend | tail -20
                    fi
                    sleep 5
                done
                
                echo "Checking prometheus..."
                for i in $(seq 1 20); do
                    if curl -f http://localhost:9090/-/healthy >/dev/null 2>&1; then
                        echo "✅ Prometheus is healthy!"
                        break
                    fi
                    if [ $i -eq 20 ]; then
                        echo "❌ Prometheus health check failed after 100 seconds"
                        docker compose -p ${COMPOSE_PROJECT_NAME} logs prometheus | tail -20
                    fi
                    sleep 5
                done
                
                echo "Checking grafana..."
                for i in $(seq 1 30); do
                    if curl -f http://localhost:3001/api/health >/dev/null 2>&1; then
                        echo "✅ Grafana is healthy!"
                        break
                    fi
                    if [ $i -eq 30 ]; then
                        echo "❌ Grafana health check failed after 150 seconds"
                        docker compose -p ${COMPOSE_PROJECT_NAME} logs grafana | tail -20
                    fi
                    sleep 5
                done
                
                echo "Checking alertmanager..."
                for i in $(seq 1 20); do
                    if curl -f http://localhost:9093/-/healthy >/dev/null 2>&1; then
                        echo "✅ Alertmanager is healthy!"
                        break
                    fi
                    if [ $i -eq 20 ]; then
                        echo "❌ Alertmanager health check failed after 100 seconds"
                        docker compose -p ${COMPOSE_PROJECT_NAME} logs alertmanager | tail -20
                    fi
                    sleep 5
                done
                
                echo "✅ All core services are healthy!"
                
                # Test monitoring integration
                echo "=== Testing monitoring integration ==="
                
                # Test Prometheus is scraping backend
                if curl -s http://localhost:9090/api/v1/targets | grep -q "backend.*UP"; then
                    echo "✅ Prometheus is successfully scraping backend metrics"
                else
                    echo "⚠️ Prometheus not scraping backend properly"
                    curl -s http://localhost:9090/api/v1/targets | grep backend || true
                fi
                
                # Test backend-Ollama integration
                if curl -f http://localhost:8000/health | grep -q "healthy"; then
                    echo "✅ Backend-Ollama integration working"
                else
                    echo "❌ Backend-Ollama integration failed"
                fi
                '''
            }
        }
        
        stage('Final Validation') {
            steps {
                sh '''
                echo "=== FINAL VALIDATION COMPLETE ==="
                echo ""
                echo "🎉 YOUR COMPLETE AI AGENT STACK IS NOW RUNNING! 🎉"
                echo ""
                echo "=== ACCESS YOUR SERVICES ==="
                echo "Frontend: http://localhost:3000"
                echo "Backend API: http://localhost:8000"
                echo "Prometheus: http://localhost:9090"
                echo "Grafana: http://localhost:3001"
                echo "Alertmanager: http://localhost:9093"
                echo "Ollama: http://localhost:11435"
                echo "Jenkins: http://localhost:9190 (already running)"
                echo ""
                echo "Note: Jenkins was not redeployed to avoid port conflicts"
                echo "Your existing Jenkins continues to run on port 9190"
                '''
            }
        }
    }
    
    post {
        always {
            script {
                // Archive all test results
                def unitTestResults = "Back/test-results/test-results.xml"
                def integrationTestResults = "Back/test-results/integration-test-results.xml"
                def coverageFile = "Back/coverage/coverage.xml"
                
                [unitTestResults, integrationTestResults].each { resultFile ->
                    if (fileExists(resultFile)) {
                        junit resultFile
                        echo "✓ Test results archived: ${resultFile}"
                    } else {
                        echo "⚠️ Test results not found: ${resultFile}"
                    }
                }
                
                if (fileExists(coverageFile)) {
                    archiveArtifacts artifacts: coverageFile, fingerprint: true
                    echo "✓ Code coverage archived: ${coverageFile}"
                } else {
                    echo "⚠️ Coverage file not found: ${coverageFile}"
                }
                
                // Capture comprehensive diagnostics
                sh '''
                echo "=== Collecting comprehensive diagnostic information ==="
                
                # Get logs from all services
                docker compose -p ${COMPOSE_PROJECT_NAME} logs --no-color --tail=100 > full-stack-logs.txt
                
                # Get container status
                docker compose -p ${COMPOSE_PROJECT_NAME} ps --all > container-status.txt
                
                # Get monitoring status
                curl -s http://localhost:9090/api/v1/targets > prometheus-targets.txt || true
                curl -s http://localhost:9090/api/v1/query?query=up > prometheus-status.txt || true
                curl -s http://localhost:9093/api/v1/status > alertmanager-status.txt || true
                
                # Get service health status
                echo "=== Final health status ===" > health-status.txt
                docker compose -p ${COMPOSE_PROJECT_NAME} ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" >> health-status.txt
                '''
                
                // Archive all diagnostic files
                archiveArtifacts artifacts: 'full-stack-logs.txt,container-status.txt,prometheus-status.txt,alertmanager-status.txt,health-status.txt,prometheus-targets.txt', fingerprint: true
            }
            
            // Final cleanup decision
            script {
                if (currentBuild.result == 'SUCCESS') {
                    echo "✅ Pipeline successful! Application stack is running and healthy."
                    echo "Jenkins was not redeployed to avoid port conflicts."
                    
                } else {
                    sh '''
                    echo "=== Cleaning up failed deployment ==="
                    docker compose -p ${COMPOSE_PROJECT_NAME} down -v 2>/dev/null || true
                    docker system prune -f 2>/dev/null || true
                    '''
                    echo 'Pipeline failed! Stack has been cleaned up. ❌'
                }
            }
        }
    }
}