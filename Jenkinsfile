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
                echo "=== Preparing workspace with REAL monitoring config ==="
                ls -la monitoring/
                
                # Verify monitoring structure exists
                if [ ! -d "monitoring" ]; then
                    echo "❌ ERROR: monitoring directory not found!"
                    exit 1
                fi
                
                # Create test directories
                mkdir -p Back/test-results Back/coverage
                chmod 777 Back/test-results Back/coverage
                
                # Verify critical monitoring files exist
                required_files=(
                    "monitoring/prometheus/prometheus.yml"
                    "monitoring/prometheus/alerts.yml"
                    "monitoring/alertmanager/config.yml"
                    "monitoring/grafana/provisioning/datasources/datasource.yml"
                    "monitoring/grafana/provisioning/dashboards/dashboards.yml"
                )
                
                for file in "${required_files[@]}"; do
                    if [ ! -f "$file" ]; then
                        echo "❌ ERROR: Required monitoring file not found: $file"
                        exit 1
                    else
                        echo "✅ Found: $file"
                    fi
                done
                
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
                    },
                    'Verify Monitoring': {
                        sh '''
                        echo "=== Verifying monitoring configuration ==="
                        
                        # Test Prometheus config
                        if docker run --rm -v $(pwd)/monitoring/prometheus:/etc/prometheus prom/prometheus:latest --config.file=/etc/prometheus/prometheus.yml --check-config; then
                            echo "✅ Prometheus configuration is valid"
                        else
                            echo "❌ Prometheus configuration is invalid"
                            exit 1
                        fi
                        
                        # Test Alertmanager config
                        if docker run --rm -v $(pwd)/monitoring/alertmanager:/etc/alertmanager prom/alertmanager:latest --config.file=/etc/alertmanager/config.yml --check-config; then
                            echo "✅ Alertmanager configuration is valid"
                        else
                            echo "❌ Alertmanager configuration is invalid"
                            exit 1
                        fi
                        '''
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
                
                # Build and start the complete stack with YOUR monitoring
                echo "=== Building and starting complete application stack ==="
                echo "Using your REAL monitoring configuration:"
                echo "- Prometheus: $(cat monitoring/prometheus/prometheus.yml | head -5)"
                echo "- Alertmanager: $(cat monitoring/alertmanager/config.yml | head -5)"
                
                docker compose -p ${COMPOSE_PROJECT_NAME} up --build -d
                
                echo "=== Waiting for full stack initialization (3 minutes) ==="
                sleep 180
                '''
            }
        }
        
        stage('Comprehensive Health Check') {
            steps {
                sh '''
                echo "=== Comprehensive health check of ALL services ==="
                
                # Define services to check with proper endpoints
                services=(
                    "ollama:11434"                          # Ollama health
                    "backend:8000/health"                   # Backend health
                    "frontend:3000"                         # Frontend
                    "prometheus:9090/-/healthy"             # Prometheus health
                    "grafana:3000/api/health"               # Grafana health  
                    "alertmanager:9093/-/healthy"           # Alertmanager health
                )
                
                # Check each service
                all_healthy=true
                for service in "${services[@]}"; do
                    IFS=':' read -r service_name port_path <<< "$service"
                    echo "Checking $service_name..."
                    
                    for i in $(seq 1 30); do
                        if curl -f "http://localhost:${port_path}" >/dev/null 2>&1; then
                            echo "✅ $service_name is healthy!"
                            break
                        fi
                        
                        if [ $i -eq 30 ]; then
                            echo "❌ $service_name health check failed after 150 seconds"
                            docker compose -p ${COMPOSE_PROJECT_NAME} logs $service_name | tail -20
                            all_healthy=false
                        fi
                        sleep 5
                    done
                done
                
                if [ "$all_healthy" = false ]; then
                    echo "❌ Some services failed health check"
                    exit 1
                fi
                
                echo "✅ All core services are healthy!"
                
                # Test monitoring integration
                echo "=== Testing monitoring integration ==="
                
                # Test Prometheus is scraping backend
                if curl -s http://localhost:9090/api/v1/targets | grep -q "backend.*UP"; then
                    echo "✅ Prometheus is successfully scraping backend metrics"
                else
                    echo "⚠️ Prometheus not scraping backend properly"
                    curl -s http://localhost:9090/api/v1/targets | grep backend
                fi
                
                # Test Grafana can connect to Prometheus
                if curl -s http://localhost:3001/api/health | grep -q "OK"; then
                    echo "✅ Grafana is healthy and running"
                else
                    echo "⚠️ Grafana health check issue"
                fi
                
                # Test backend-Ollama integration
                if curl -f http://localhost:8000/health | grep -q "healthy"; then
                    echo "✅ Backend-Ollama integration working"
                else
                    echo "❌ Backend-Ollama integration failed"
                    exit 1
                fi
                '''
            }
        }
        
        stage('Integration Tests & Monitoring Validation') {
            steps {
                dir('Back') {
                    sh '''
                    echo "=== Running integration tests against real stack ==="
                    
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
                
                sh '''
                echo "=== Validating monitoring functionality ==="
                
                # Test that metrics are being collected
                if curl -s "http://localhost:9090/api/v1/query?query=up{instance='backend:8000'}" | grep -q "value.*1"; then
                    echo "✅ Backend metrics are being collected"
                else
                    echo "⚠️ Backend metrics not found in Prometheus"
                fi
                
                # Test that dashboards are loaded in Grafana
                if curl -s -u admin:admin http://localhost:3001/api/dashboards/uid/finn-compact-dashboard | grep -q "dashboard"; then
                    echo "✅ Finn compact dashboard is loaded in Grafana"
                else
                    echo "⚠️ Finn compact dashboard not found in Grafana"
                fi
                
                # Test alertmanager configuration
                if curl -s http://localhost:9093/api/v1/status | grep -q "config"; then
                    echo "✅ Alertmanager is running with configuration"
                else
                    echo "⚠️ Alertmanager configuration issue"
                fi
                '''
            }
        }
        
        stage('Deploy Jenkins & Final Validation') {
            steps {
                sh '''
                echo "=== Deploying Jenkins for future pipelines ==="
                
                # Start Jenkins (was built but not started initially to avoid port conflicts)
                docker compose -p ${COMPOSE_PROJECT_NAME} up -d jenkins
                
                echo "Waiting for Jenkins to start..."
                sleep 60
                
                # Test Jenkins health
                if curl -f http://localhost:9190/login >/dev/null 2>&1; then
                    echo "✅ Jenkins is running and accessible"
                    
                    # Get Jenkins initial admin password
                    JENKINS_PASSWORD=$(docker compose -p ${COMPOSE_PROJECT_NAME} exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword 2>/dev/null || echo "not-available")
                    echo "Jenkins initial admin password: $JENKINS_PASSWORD"
                    
                else
                    echo "⚠️ Jenkins health check failed - may need more time"
                    docker compose -p ${COMPOSE_PROJECT_NAME} logs jenkins | tail -20
                fi
                
                echo "=== Final system validation ==="
                echo "Your complete AI agent stack is now running with:"
                echo "🎯 Frontend: http://localhost:3000"
                echo "🔧 Backend API: http://localhost:8000"
                echo "📊 Prometheus: http://localhost:9090"
                echo "📈 Grafana: http://localhost:3001 (admin/admin)"
                echo "🚨 Alertmanager: http://localhost:9093"
                echo "⚙️ Jenkins: http://localhost:9190"
                echo "🤖 Ollama: http://localhost:11435"
                
                # Verify all critical endpoints
                echo "=== Testing critical endpoints ==="
                for endpoint in "http://localhost:3000" "http://localhost:8000/health" "http://localhost:9090"; do
                    if curl -f "$endpoint" >/dev/null 2>&1; then
                        echo "✅ $endpoint is accessible"
                    else
                        echo "❌ $endpoint is not accessible"
                    fi
                done
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
                
                # Get monitoring configs for reference
                cp monitoring/prometheus/prometheus.yml prometheus-config.txt || true
                cp monitoring/alertmanager/config.yml alertmanager-config.txt || true
                '''
                
                // Archive all diagnostic files
                archiveArtifacts artifacts: 'full-stack-logs.txt,container-status.txt,prometheus-status.txt,alertmanager-status.txt,health-status.txt,prometheus-targets.txt,prometheus-config.txt,alertmanager-config.txt', fingerprint: true
            }
            
            // Final cleanup decision
            script {
                if (currentBuild.result == 'SUCCESS') {
                    echo "✅ Pipeline successful! Complete stack is running and healthy."
                    echo ""
                    echo "=== ACCESS YOUR DEPLOYED SERVICES ==="
                    echo "Frontend: http://localhost:3000"
                    echo "Backend API: http://localhost:8000"
                    echo "Prometheus: http://localhost:9090"
                    echo "Grafana: http://localhost:3001 (admin/admin)"
                    echo "Alertmanager: http://localhost:9093"
                    echo "Jenkins: http://localhost:9190"
                    echo "Ollama: http://localhost:11435"
                    echo ""
                    echo "Your monitoring dashboards are available in Grafana:"
                    echo "- Finn Compact Dashboard"
                    echo "- Finn Executive Dashboard"
                    echo ""
                    echo "Jenkins is ready for future pipeline executions!"
                    
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
        success {
            echo 'Pipeline successful! Complete production-ready stack is running. ✅'
        }
        failure {
            echo 'Pipeline failed! Investigate logs and try again. ❌'
        }
    }
}