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
        // Use unique project name to avoid conflicts
        sh 'docker compose -p finn-pipeline-${BUILD_ID} up --no-build --scale jenkins=0 -d'
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