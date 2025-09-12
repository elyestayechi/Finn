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
                    
                    // Create directories for test results
                    sh 'mkdir -p test-results coverage'
                    
                    // Run tests with proper volume mounting
                    sh '''
                    docker run --rm \
                        -v "${WORKSPACE}/Back/test-results:/app/test-results" \
                        -v "${WORKSPACE}/Back/coverage:/app/coverage" \
                        finn-loan-analysis-backend-test \
                        python -m pytest tests/ -v \
                        --junitxml=/app/test-results/test-results.xml \
                        --cov=src \
                        --cov-report=xml:/app/coverage/coverage.xml
                    '''
                }
            }
            post {
                always {
                    // Archive test results
                    junit 'Back/test-results/test-results.xml'
                    archiveArtifacts artifacts: 'Back/coverage/coverage.xml', fingerprint: true
                }
            }
        }
        
        stage('Deploy') {
            steps {
                sh 'docker-compose up -d --build'
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
            // Cleanup and collect logs
            sh 'docker-compose logs --no-color > docker-logs.txt || true'
            archiveArtifacts artifacts: 'docker-logs.txt', fingerprint: true
            sh 'docker-compose down || true'
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