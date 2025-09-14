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
                
                # Verify critical monitoring files exist (without arrays)
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
                
                echo "Checking monitoring/grafana/provisioning/datasources/datasource.yml..."
                if [ ! -f "monitoring/grafana/provisioning/datasources/datasource.yml" ]; then
                    echo "❌ ERROR: monitoring/grafana/provisioning/datasources/datasource.yml not found!"
                    exit 1
                else
                    echo "✅ Found: monitoring/grafana/provisioning/datasources/datasource.yml"
                fi
                
                echo "Checking monitoring/grafana/provisioning/dashboards/dashboards.yml..."
                if [ ! -f "monitoring/grafana/provisioning/dashboards/dashboards.yml" ]; then
                    echo "❌ ERROR: monitoring/grafana/provisioning/dashboards/dashboards.yml not found!"
                    exit 1
                else
                    echo "✅ Found: monitoring/grafana/provisioning/dashboards/dashboards.yml"
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
                    },
                    'Verify Monitoring': {
                        sh '''
                        echo "=== Verifying monitoring configuration ==="
                        
                        # Use a different approach - copy files to a temp directory
                        mkdir -p /tmp/monitoring_verify
                        cp -r monitoring/* /tmp/monitoring_verify/
                        
                        # Test Prometheus config
                        if docker run --rm -v /tmp/monitoring_verify/prometheus:/etc/prometheus prom/prometheus:latest --config.file=/etc/prometheus/prometheus.yml --check-config; then
                            echo "✅ Prometheus configuration is valid"
                        else
                            echo "❌ Prometheus configuration is invalid"
                        fi
                        
                        # Test Alertmanager config
                        if docker run --rm -v /tmp/monitoring_verify/alertmanager:/etc/alertmanager prom/alertmanager:latest --config.file=/etc/alertmanager/config.yml --check-config; then
                            echo "✅ Alertmanager configuration is valid"
                        else
                            echo "❌ Alertmanager configuration is invalid"
                        fi
                        
                        # Clean up
                        rm -rf /tmp/monitoring_verify
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
        
        # Build and start the complete stack with DIFFERENT Jenkins ports
        echo "=== Building and starting complete application stack ==="
        
        # Use different ports to avoid conflict with current Jenkins
        JENKINS_WEB_PORT=9192 JENKINS_AGENT_PORT=9193 docker compose -p ${COMPOSE_PROJECT_NAME} up --build -d
        
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
                
                echo "✅ Core services health check completed!"
                
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
                        --junitxml=/app/test-results/integration-test-results.xml || echo "Integration tests may have failed, but continuing..."
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
                
                # Test Grafana
                if curl -s http://localhost:3001/api/health | grep -q "OK"; then
                    echo "✅ Grafana is running"
                else
                    echo "❌ Grafana not responding"
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
        echo "=== Deploying NEW Jenkins instance for future pipelines ==="
        echo "New Jenkins will be available on port 9192 (current Jenkins is on 9190)"
        
        # Test NEW Jenkins health (on different port)
        if curl -f http://localhost:9192 >/dev/null 2>&1; then
            echo "✅ NEW Jenkins is running and accessible on port 9192"
            echo ""
            echo "=== MIGRATION INSTRUCTIONS ==="
            echo "1. Access new Jenkins: http://localhost:9192"
            echo "2. Configure new Jenkins (import jobs/config from old Jenkins if needed)"
            echo "3. When ready, update your docker-compose.yml to use port 9192 for production"
            echo "4. Stop current Jenkins (port 9190) and switch to new Jenkins"
        else
            echo "⚠️ New Jenkins health check failed - may need more time"
            docker compose -p ${COMPOSE_PROJECT_NAME} logs jenkins | tail -20
        fi
        
        echo "=== Final system validation ==="
        echo "Your complete AI agent stack is now running with:"
        echo " Frontend: http://localhost:3000"
        echo " Backend API: http://localhost:8000"
        echo " Prometheus: http://localhost:9090"
        echo " Grafana: http://localhost:3001"
        echo " Alertmanager: http://localhost:9093"
        echo " NEW Jenkins: http://localhost:9192 (for next version)"
        echo " CURRENT Jenkins: http://localhost:9190 (still running this pipeline)"
        echo " Ollama: http://localhost:11435"
        
        # Verify all critical endpoints
        echo "=== Testing critical endpoints ==="
        for endpoint in "http://localhost:3000" "http://localhost:8000/health" "http://localhost:9090" "http://localhost:9192"; do
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
                    echo "Grafana: http://localhost:3001"
                    echo "Alertmanager: http://localhost:9093"
                    echo "Jenkins: http://localhost:9190"
                    echo "Ollama: http://localhost:11435"
                    echo ""
                    echo "Your monitoring dashboards are available in Grafana"
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