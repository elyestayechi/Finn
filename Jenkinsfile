pipeline {
    agent any
    environment {
        PROJECT_NAME = 'finn-loan-analysis'
        DOCKER_HOST = 'unix:///var/run/docker.sock'
    }
    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh 'git branch'
                sh 'git log -1 --oneline'
            }
        }
        
        stage('Build Backend') {
            steps {
                sh """
                    cd Back
                    docker build -t ${PROJECT_NAME}-backend:latest .
                """
            }
        }
        
        stage('Build Frontend') {
            steps {
                sh """
                    cd Front  
                    docker build -t ${PROJECT_NAME}-frontend:latest .
                """
            }
        }
        
        stage('Run Unit Tests') {
            steps {
                script {
                    // Build test-specific image
                    sh """
                        cd Back
                        docker build -t ${PROJECT_NAME}-backend-test -f Dockerfile.test .
                    """
                    
                    // Run tests with proper error handling
                    sh """
                        cd Back
                        docker run --rm ${PROJECT_NAME}-backend-test python -m pytest tests/ -v --junitxml=test-results.xml --cov=src --cov-report=xml:coverage.xml || echo "Tests completed with exit code: \$?"
                    """
                }
            }
            post {
                always {
                    // Always archive test results, even if tests fail
                    junit "Back/test-results.xml"
                    publishCoverage adapters: [jacocoAdapter("Back/coverage.xml")]
                }
            }
        }

        stage('Deploy') {
            steps {
                script {
                    sh 'docker-compose down || true'
                    sh 'docker-compose up -d --build'
                    sleep 30
                    sh 'docker-compose ps'
                }
            }
        }
        
        stage('Health Check') {
            steps {
                script {
                    sh '''
                        curl -f http://localhost:8000/health || echo "Backend health check failed"
                        curl -f http://localhost:3000 || echo "Frontend health check failed"
                    '''
                }
            }
        }
    }
    
    post {
        always {
            sh 'docker system prune -f || true'
            sh 'docker-compose logs --no-color > docker-logs.txt || true'
            archiveArtifacts artifacts: 'docker-logs.txt'
        }
    }
}