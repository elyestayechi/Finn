pipeline {
    agent any
    environment {
        DOCKER_HOST = 'unix:///var/run/docker.sock'
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
                    // Build test image
                    sh 'docker build -t finn-loan-analysis-backend-test -f Dockerfile.test .'
                    
                    // Clean previous test results and create directories
                    sh '''
                    rm -rf test-results coverage || true
                    mkdir -p test-results coverage
                    chmod 777 test-results coverage  # Ensure write permissions
                    '''
                    
                    // Run tests using the Dockerfile CMD
                    sh '''
                    echo "Running tests with Docker CMD..."
                    
                    docker run --rm \
                        -v "$(pwd)/test-results:/app/test-results" \
                        -v "$(pwd)/coverage:/app/coverage" \
                        finn-loan-analysis-backend-test
                    '''
                    
                    // Debug: Check what was created
                    sh '''
                    echo "=== Test results directory ==="
                    ls -la test-results/
                    echo "=== Coverage directory ==="
                    ls -la coverage/
                    echo "=== File contents ==="
                    cat test-results/test-results.xml 2>/dev/null | head -3 || echo "No test results file"
                    cat coverage/coverage.xml 2>/dev/null | head -3 || echo "No coverage file"
                    '''
                }
            }
        }
        
        stage('Deploy') {
    steps {
        // Deploy only the application services, not Jenkins
        sh '''
        # Create a custom docker-compose file without Jenkins
        cat > docker-compose-app.yml << 'EOF'
services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0:11434
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434"]
      interval: 30s
      timeout: 30s
      retries: 10
      start_period: 120s

  backend:
    image: finn-loan-analysis-backend
    ports:
      - "8000:8000"
    volumes:
      - ./Back/Data:/app/Data
      - ./Back/PDF Loans:/app/PDF Loans
      - ./Back/loans_vector.db:/app/loans_vector.db
      - ./Back/loan_analysis.db:/app/loan_analysis.db
    environment:
      - PYTHONPATH=/app
      - OLLAMA_HOST=http://ollama:11434
      - PROMETHEUS_MULTIPROC_DIR=/tmp
    depends_on:
      ollama:
        condition: service_healthy
    restart: unless-stopped

  frontend:
    image: finn-loan-analysis-frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    environment:
      - VITE_API_BASE_URL=http://backend:8000
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus:/etc/prometheus
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    restart: unless-stopped
    depends_on:
      - backend

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    restart: unless-stopped
    depends_on:
      - prometheus

  alertmanager:
    image: prom/alertmanager:latest
    ports:
      - "9093:9093"
    volumes:
      - ./monitoring/alertmanager:/etc/alertmanager
    command:
      - '--config.file=/etc/alertmanager/config.yml'
      - '--storage.path=/alertmanager'
    restart: unless-stopped
    depends_on:
      - prometheus

volumes:
  ollama_data:
  prometheus_data:
  grafana_data:
EOF

        # Deploy only the application services
        docker compose -f docker-compose-app.yml up -d --build
        '''
        sleep(time: 30, unit: 'SECONDS')
    }
}
        
        stage('Health Check') {
            steps {
                sh '''
                # Wait for backend to be healthy
                timeout 120 bash -c 'until curl -f http://localhost:8000/health; do sleep 5; done'
                
                # Wait for frontend to be accessible
                timeout 60 bash -c 'until curl -f http://localhost:3000; do sleep 5; done'
                '''
            }
        }
    }
    
    post {
        always {
            script {
                // Debug: Show directory structure
                sh '''
                echo "=== Workspace structure ==="
                pwd
                ls -la
                echo "=== Back directory ==="
                ls -la Back/
                '''
                
                // Check for test results in multiple possible locations
                def possibleTestPaths = [
                    "Back/test-results/test-results.xml",
                    "test-results/test-results.xml"
                ]
                
                def testResultsFound = false
                for (path in possibleTestPaths) {
                    if (fileExists(path)) {
                        junit path
                        echo "✓ Test results archived from: ${path}"
                        testResultsFound = true
                        break
                    }
                }
                
                if (!testResultsFound) {
                    echo "⚠️ Test results file not found in expected locations"
                    sh 'find . -name "test-results.xml" -type f 2>/dev/null | head -5 || true'
                }
                
                // Check for coverage in multiple possible locations
                def possibleCoveragePaths = [
                    "Back/coverage/coverage.xml",
                    "coverage/coverage.xml"
                ]
                
                def coverageFound = false
                for (path in possibleCoveragePaths) {
                    if (fileExists(path)) {
                        archiveArtifacts artifacts: path, fingerprint: true
                        echo "✓ Coverage archived from: ${path}"
                        coverageFound = true
                        break
                    }
                }
                
                if (!coverageFound) {
                    echo "⚠️ Coverage file not found in expected locations"
                    sh 'find . -name "coverage.xml" -type f 2>/dev/null | head -5 || true'
                }
            }
            
            // Cleanup
            sh 'docker compose logs --no-color > docker-logs.txt 2>/dev/null || true'
            archiveArtifacts artifacts: 'docker-logs.txt', fingerprint: true
            sh 'docker compose down 2>/dev/null || true'
            sh 'docker system prune -f || true'
        }
        success {
            echo 'Pipeline succeeded! ✅'
        }
        failure {
            echo 'Pipeline failed! ❌'
        }
    }
}