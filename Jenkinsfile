pipeline {
    agent any
    
    environment {
        DOCKERHUB_CREDENTIALS = credentials('docker-hub-credentials')
        GIT_REPO = 'https://github.com/elyestayechi/Finn-AI-Loan-Analysis-Agent-.git'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Build Backend') {
            steps {
                dir('Back') {
                    script {
                        docker.build("finn-backend:${env.BUILD_ID}", "--build-arg BUILD_ID=${env.BUILD_ID} .")
                    }
                }
            }
        }
        
        stage('Build Frontend') {
            steps {
                dir('Front') {
                    script {
                        docker.build("finn-frontend:${env.BUILD_ID}", "--build-arg BUILD_ID=${env.BUILD_ID} .")
                    }
                }
            }
        }
        
        stage('Run Tests') {
            steps {
                dir('Back') {
                    script {
                        // Run Python tests
                        sh 'python -m pytest tests/ -v'
                    }
                }
            }
        }
        
        stage('Push to Docker Hub') {
            steps {
                script {
                    docker.withRegistry('https://index.docker.io/v1/', 'docker-hub-credentials') {
                        docker.image("finn-backend:${env.BUILD_ID}").push()
                        docker.image("finn-frontend:${env.BUILD_ID}").push()
                    }
                }
            }
        }
        
        stage('Deploy to Staging') {
            steps {
                script {
                    sh 'docker-compose -f docker-compose.yml up -d --build'
                }
            }
        }
        
        stage('Run Integration Tests') {
            steps {
                script {
                    // Wait for services to be ready
                    sleep 60
                    
                    // Run integration tests
                    sh 'python -m pytest integration_tests/ -v'
                }
            }
        }
    }
    
    post {
        always {
            // Clean up
            sh 'docker-compose -f docker-compose.yml down'
            sh 'docker system prune -f'
            
            // Clean workspace
            cleanWs()
        }
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed!'
        }
    }
}