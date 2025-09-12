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
                    '''
                    
                    // Run tests with volume mounting to avoid space issues
                    sh '''
                    docker run --rm \
                        -v "$(pwd)/test-results:/app/test-results" \
                        -v "$(pwd)/coverage:/app/coverage" \
                        finn-loan-analysis-backend-test \
                        python -m pytest tests/ -v \
                        --junitxml=/app/test-results/test-results.xml \
                        --cov=src \
                        --cov-report=xml:/app/coverage/coverage.xml
                    '''
                }
            }
        }
        
        stage('Deploy') {
            steps {
                // Use docker compose (modern syntax)
                sh 'docker compose up -d --build'
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
                // Debug: Check what files were created
                sh 'ls -la Back/test-results/ || true'
                sh 'ls -la Back/coverage/ || true'
                
                // Archive test results from the correct locations
                def testResultsFile = "Back/test-results/test-results.xml"
                def coverageFile = "Back/coverage/coverage.xml"
                
                if (fileExists(testResultsFile)) {
                    junit testResultsFile
                    echo "✓ Test results archived successfully"
                } else {
                    echo "⚠️ Test results file not found at ${testResultsFile}"
                    // Try to find the file anywhere
                    sh 'find . -name "test-results.xml" -type f | head -5 || true'
                }
                
                if (fileExists(coverageFile)) {
                    archiveArtifacts artifacts: coverageFile, fingerprint: true
                    echo "✓ Coverage results archived successfully"
                } else {
                    echo "⚠️ Coverage file not found at ${coverageFile}"
                    // Try to find the file anywhere
                    sh 'find . -name "coverage.xml" -type f | head -5 || true'
                }
            }
            
            // Cleanup using docker compose
            sh 'docker compose logs --no-color > docker-logs.txt || true'
            archiveArtifacts artifacts: 'docker-logs.txt', fingerprint: true
            sh 'docker compose down || true'
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