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
                ls -la
                mkdir -p Back/test-results Back/coverage
                chmod 777 Back/test-results Back/coverage
                
                # Ensure monitoring directories exist with proper structure
                mkdir -p monitoring/prometheus monitoring/alertmanager monitoring/grafana/provisioning/dashboards monitoring/grafana/provisioning/datasources
                
                # Create minimal configs if they don't exist (for CI)
                if [ ! -f monitoring/prometheus/prometheus.yml ]; then
                    cat > monitoring/prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - alerts.yml

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'backend'
    metrics_path: /metrics
    static_configs:
      - targets: ['backend:8000']
    scrape_interval: 10s

EOF
                fi

                if [ ! -f monitoring/alertmanager/config.yml ]; then
                    cat > monitoring/alertmanager/config.yml << 'EOF'
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'webhook'

receivers:
  - name: 'webhook'
    webhook_configs:
      - url: 'http://webhook:5000/'
        send_resolved: true

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'dev', 'instance']

EOF
                fi

                if [ ! -f monitoring/grafana/provisioning/datasources/datasource.yml ]; then
                    cat > monitoring/grafana/provisioning/datasources/datasource.yml << 'EOF'

apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    version: 1
    editable: false
EOF
                fi
                '''
            }
        }
        
        stage('Build All Images') {
            steps {
                parallel {
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
                    stage('Build Jenkins') {
                        steps {
                            dir('jenkins') {
                                sh 'docker build -t finn-jenkins -f Dockerfile .'
                            }
                        }
                    }
                }
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
                
                # Build and start the complete stack
                echo "=== Building and starting complete application stack ==="
                docker compose -p ${COMPOSE_PROJECT_NAME} up --build -d
                
                echo "=== Waiting for full stack initialization (2 minutes) ==="
                sleep 120
                '''
            }
        }
        
        stage('Comprehensive Health Check') {
            steps {
                sh '''
                echo "=== Comprehensive health check of all services ==="
                
                # Define services to check
                services=(
                    "ollama:11434"
                    "backend:8000/health"
                    "frontend:3000"
                    "prometheus:9090/-/healthy"
                    "grafana:3000/api/health"
                    "alertmanager:9093/-/healthy"
                )
                
                # Check each service
                all_healthy=true
                for service in "${services[@]}"; do
                    IFS=':' read -r service_name port_path <<< "$service"
                    echo "Checking $service_name..."
                    
                    for i in $(seq 1 20); do
                        if curl -f "http://localhost:${port_path}" >/dev/null 2>&1; then
                            echo "✅ $service_name is healthy!"
                            break
                        fi
                        
                        if [ $i -eq 20 ]; then
                            echo "❌ $service_name health check failed"
                            docker compose -p ${COMPOSE_PROJECT_NAME} logs $service_name
                            all_healthy=false
                        fi
                        sleep 3
                    done
                done
                
                if [ "$all_healthy" = false ]; then
                    echo "❌ Some services failed health check"
                    exit 1
                fi
                
                echo "✅ All services are healthy!"
                
                # Additional integration test: verify backend can connect to Ollama
                echo "=== Testing Ollama integration ==="
                if curl -f http://localhost:8000/health | grep -q "healthy"; then
                    echo "✅ Backend-Ollama integration working"
                else
                    echo "❌ Backend-Ollama integration failed"
                    exit 1
                fi
                
                # Test monitoring integration
                echo "=== Testing monitoring integration ==="
                if curl -f http://localhost:9090/api/v1/targets | grep -q "backend"; then
                    echo "✅ Prometheus scraping backend metrics"
                else
                    echo "⚠️ Prometheus not scraping backend (might need more time)"
                fi
                '''
            }
        }
        
        stage('Integration Tests') {
            steps {
                dir('Back') {
                    sh '''
                    echo "=== Running integration tests ==="
                    # Run integration tests against the running stack
                    docker run --rm \
                        --network ${COMPOSE_PROJECT_NAME}_default \
                        -e API_BASE_URL=http://backend:8000 \
                        -e OLLAMA_HOST=http://ollama:11434 \
                        -v "$(pwd)/test-results:/app/test-results" \
                        finn-loan-analysis-backend-test \
                        python -m pytest tests/test_integration/ -v \
                        --junitxml=/app/test-results/integration-test-results.xml
                    '''
                }
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
                
                // Capture logs and metrics
                sh '''
                echo "=== Collecting diagnostic information ==="
                
                # Get logs from all services
                docker compose -p ${COMPOSE_PROJECT_NAME} logs --no-color > full-stack-logs.txt
                
                # Get container status
                docker compose -p ${COMPOSE_PROJECT_NAME} ps > container-status.txt
                
                # Get basic metrics
                curl -s http://localhost:9090/api/v1/query?query=up > prometheus-status.txt || true
                
                # Get service health status
                echo "=== Final health status ===" > health-status.txt
                docker compose -p ${COMPOSE_PROJECT_NAME} ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" >> health-status.txt
                '''
                
                // Archive all diagnostic files
                archiveArtifacts artifacts: 'full-stack-logs.txt,container-status.txt,prometheus-status.txt,health-status.txt', fingerprint: true
            }
            
            // Always clean up, but keep the stack running if successful for inspection
            script {
                if (currentBuild.result == 'SUCCESS') {
                    echo "✅ Pipeline successful! Keeping stack running for inspection."
                    echo "Access your services at:"
                    echo "Frontend: http://localhost:3000"
                    echo "Backend: http://localhost:8000"
                    echo "Prometheus: http://localhost:9090"
                    echo "Grafana: http://localhost:3001 (admin/admin)"
                    echo "Jenkins: http://localhost:9190"
                } else {
                    sh '''
                    echo "=== Cleaning up failed deployment ==="
                    docker compose -p ${COMPOSE_PROJECT_NAME} down -v 2>/dev/null || true
                    docker system prune -f 2>/dev/null || true
                    '''
                }
            }
        }
        success {
            echo 'Pipeline successful! Complete stack is running and healthy. ✅'
        }
        failure {
            echo 'Pipeline failed! Stack has been cleaned up. ❌'
        }
    }
}