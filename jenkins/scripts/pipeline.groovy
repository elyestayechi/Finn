pipeline {
    agent any
    environment {
        DOCKER_REGISTRY = '' // Leave empty for local development
        PROJECT_NAME = 'finn-loan-analysis'
    }
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Build Backend') {
            steps {
                script {
                    dir('Back') {
                        sh 'docker build -t ${PROJECT_NAME}-backend .'
                    }
                }
            }
        }
        
        stage('Build Frontend') {
            steps {
                script {
                    dir('Front') {
                        sh 'docker build -t ${PROJECT_NAME}-frontend .'
                    }
                }
            }
        }
        
        stage('Run Unit Tests') {
            steps {
                script {
                    // Backend tests
                    dir('Back') {
                        sh '''
                          docker run --rm ${PROJECT_NAME}-backend \
                          python -m pytest tests/ -v --junitxml=test-results.xml || true
                        '''
                        junit 'test-results.xml'
                    }
                    
                    // Frontend tests (when available)
                    dir('Front') {
                        sh '''
                          # Add frontend tests when available
                          echo "Frontend tests would run here"
                        '''
                    }
                }
            }
        }
        
        stage('Security Scan') {
            steps {
                script {
                    // Scan backend for vulnerabilities
                    sh 'docker scan ${PROJECT_NAME}-backend --file Back/Dockerfile || true'
                    
                    // Scan frontend for vulnerabilities  
                    sh 'docker scan ${PROJECT_NAME}-frontend --file Front/Dockerfile || true'
                }
            }
        }
        
        stage('Deploy to Development') {
            when {
                branch 'main'
            }
            steps {
                script {
                    echo 'Deploying to development environment'
                    
                    // Stop and remove existing containers
                    sh 'docker-compose down || true'
                    
                    // Build and start new containers
                    sh 'docker-compose up -d --build'
                    
                    // Wait for services to be ready
                    sleep 30
                    
                    // Run database migrations
                    sh 'docker-compose exec backend python migrate_data.py'
                    
                    // Run integration tests
                    sh '''
                      docker-compose exec backend \
                      python -m pytest integration_tests/ -v --junitxml=integration-results.xml || true
                    '''
                    junit 'integration-results.xml'
                }
            }
        }
    }
    
    post {
        always {
            // Clean up
            sh 'docker system prune -f || true'
            
            // Archive test results
            archiveArtifacts artifacts: '**/test-results.xml, **/integration-results.xml', fingerprint: true
            
            // Save docker logs
            sh 'docker-compose logs --no-color > docker-logs.txt || true'
            archiveArtifacts artifacts: 'docker-logs.txt', fingerprint: true
        }
        
        success {
            echo 'Pipeline completed successfully'
            // You can add Slack/email notifications here
        }
        
        failure {
            echo 'Pipeline failed'
            // You can add rollback procedures here
        }
        
        unstable {
            echo 'Pipeline completed with test failures'
        }
    }
}