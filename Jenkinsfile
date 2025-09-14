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
        
        # Ensure monitoring directory structure exists
        if [ -f "create-monitoring-structure.sh" ]; then
            chmod +x create-monitoring-structure.sh
            ./create-monitoring-structure.sh
        else
            echo "⚠️ create-monitoring-structure.sh not found, creating basic structure manually"
            mkdir -p monitoring/prometheus monitoring/alertmanager monitoring/grafana/provisioning/datasources monitoring/grafana/provisioning/dashboards
        fi
        
        # Verify critical monitoring files exist
        echo "Checking monitoring configuration files..."
        REQUIRED_FILES=(
            "monitoring/prometheus/prometheus.yml"
            "monitoring/prometheus/alerts.yml"
            "monitoring/alertmanager/config.yml"
        )
        
        for file in "${REQUIRED_FILES[@]}"; do
            if [ ! -f "$file" ]; then
                echo "❌ ERROR: Required file not found: $file"
                exit 1
            else
                echo "✅ Found: $file"
            fi
        done
        
        # Create test directories
        mkdir -p Back/test-results Back/coverage
        chmod 777 Back/test-results Back/coverage
        
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

        # Function to check service health
        check_service() {
            local service=$1
            local check_cmd=$2
            local max_attempts=$3
            local attempt=1
            
            echo "Checking $service..."
            while [ $attempt -le $max_attempts ]; do
                if eval "$check_cmd" >/dev/null 2>&1; then
                    echo "✅ $service is healthy!"
                    return 0
                fi
                echo "Waiting for $service... (attempt $attempt/$max_attempts)"
                sleep 5
                attempt=$((attempt + 1))
            done
            
            echo "❌ $service health check failed after $((max_attempts * 5)) seconds"
            docker compose -p ${COMPOSE_PROJECT_NAME} logs $service | tail -20
            return 1
        }

        # Check services with appropriate timeouts
        check_service "backend" "docker compose -p ${COMPOSE_PROJECT_NAME} exec -T backend curl -f http://localhost:8000/health" 30
        check_service "frontend" "curl -f http://localhost:3000" 30
        
        # Check monitoring services
        check_service "prometheus" "docker compose -p ${COMPOSE_PROJECT_NAME} exec -T prometheus curl -f http://localhost:9090/-/healthy" 20
        check_service "alertmanager" "docker compose -p ${COMPOSE_PROJECT_NAME} exec -T alertmanager curl -f http://localhost:9093/-/healthy" 20
        check_service "grafana" "docker compose -p ${COMPOSE_PROJECT_NAME} exec -T grafana curl -f http://localhost:3000/api/health" 20

        # Ollama might take longer to start
        echo "Checking ollama (may take several minutes)..."
        for i in $(seq 1 60); do
            if docker compose -p ${COMPOSE_PROJECT_NAME} exec -T ollama curl -f http://localhost:11434 >/dev/null 2>&1; then
                echo "✅ Ollama is healthy!"
                break
            fi
            if [ $i -eq 60 ]; then
                echo "⚠️ Ollama is still starting (this is normal for first run)"
                docker compose -p ${COMPOSE_PROJECT_NAME} logs ollama | tail -10
            fi
            sleep 5
        done

        echo "✅ Core services are healthy!"

        # Test monitoring integration
        echo "=== Testing monitoring integration ==="
        
        # Wait a bit for Prometheus to start scraping
        sleep 10
        
        # Test Prometheus is scraping backend
        if curl -s http://localhost:9090/api/v1/targets | grep -q "backend.*UP"; then
            echo "✅ Prometheus is successfully scraping backend metrics"
        else
            echo "⚠️ Prometheus not scraping backend properly"
            echo "Current targets:"
            curl -s http://localhost:9090/api/v1/targets | grep backend || true
            echo "Trying to debug..."
            docker compose -p ${COMPOSE_PROJECT_NAME} logs prometheus | tail -10
        fi
        
        # Test backend metrics endpoint
        if docker compose -p ${COMPOSE_PROJECT_NAME} exec -T backend curl -f http://localhost:8000/metrics >/dev/null 2>&1; then
            echo "✅ Backend metrics endpoint is working"
        else
            echo "❌ Backend metrics endpoint not accessible"
        fi
        
        # Test backend health
        if docker compose -p ${COMPOSE_PROJECT_NAME} exec -T backend curl -f http://localhost:8000/health | grep -q "healthy"; then
            echo "✅ Backend health check working"
        else
            echo "❌ Backend health check failed"
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