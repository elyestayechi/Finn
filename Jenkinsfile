pipeline {
    agent any
    environment {
        DOCKER_HOST = 'unix:///var/run/docker.sock'
        COMPOSE_PROJECT_NAME = "finn-pipeline-${BUILD_ID}"
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
                    // Clean previous test results
                    sh '''
                    rm -rf test-results coverage || true
                    mkdir -p test-results coverage
                    chmod 777 test-results coverage
                    '''
                    
                    // Build and run tests
                    sh 'docker build -t finn-loan-analysis-backend-test -f Dockerfile.test .'
                    
                    sh '''
                    docker run --rm \
                        -v "$(pwd)/test-results:/app/test-results" \
                        -v "$(pwd)/coverage:/app/coverage" \
                        finn-loan-analysis-backend-test
                    '''
                }
            }
        }
        
        stage('Deploy') {
            steps {
                // Clean up any potential conflicts first
                sh '''
                docker compose -p ${COMPOSE_PROJECT_NAME} down 2>/dev/null || true
                # Stop any existing ollama container that might be using port 11434
                docker stop ollama 2>/dev/null || true
                docker rm ollama 2>/dev/null || true
                '''
                
                // Deploy with unique project name
                sh 'docker compose -p ${COMPOSE_PROJECT_NAME} up --no-build --scale jenkins=0 -d'
                sleep(time: 30, unit: 'SECONDS')
            }
        }
        
        stage('Health Check') {
            steps {
                sh '''
                timeout 120 bash -c 'until curl -f http://localhost:8000/health; do sleep 5; done'
                timeout 60 bash -c 'until curl -f http://localhost:3000; do sleep 5; done'
                '''
            }
        }
    }
    
    post {
        always {
            script {
                // Archive test results with correct path
                if (fileExists("Back/test-results/test-results.xml")) {
                    junit "Back/test-results/test-results.xml"
                    echo "✓ Test results archived from: Back/test-results/test-results.xml"
                } else {
                    echo "⚠️ Test results file not found"
                    sh 'find . -name "test-results.xml" -type f 2>/dev/null | head -5 || true'
                }
                
                if (fileExists("Back/coverage/coverage.xml")) {
                    archiveArtifacts artifacts: "Back/coverage/coverage.xml", fingerprint: true
                    echo "✓ Coverage archived from: Back/coverage/coverage.xml"
                } else {
                    echo "⚠️ Coverage file not found"
                    sh 'find . -name "coverage.xml" -type f 2>/dev/null | head -5 || true'
                }
            }
            
            // Cleanup with the same project name
            sh 'docker compose -p ${COMPOSE_PROJECT_NAME} logs --no-color > docker-logs.txt 2>/dev/null || true'
            archiveArtifacts artifacts: 'docker-logs.txt', fingerprint: true
            sh 'docker compose -p ${COMPOSE_PROJECT_NAME} down 2>/dev/null || true'
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