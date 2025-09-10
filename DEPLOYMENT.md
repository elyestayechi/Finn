# Finn AI Agent Deployment Guide

## Prerequisites
- Docker and Docker Compose
- Git

## Local Development
1. Clone the repository
2. Run `docker-compose up -d`
3. Access:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Grafana: http://localhost:3001 (admin/admin)
   - Prometheus: http://localhost:9090

## Production Deployment
1. Set environment variables:
   - `DOCKERHUB_USERNAME`: Your Docker Hub username
   - `DOCKERHUB_TOKEN`: Your Docker Hub access token
   - `SERVER_HOST`: Production server IP/hostname
   - `SERVER_USER`: SSH user for production
   - `SERVER_SSH_KEY`: SSH private key

2. Push to main branch to trigger automated deployment

## Monitoring
The system includes:
- Prometheus for metrics collection
- Grafana for visualization
- Health checks for all services

Key metrics tracked:
- Request latency and count
- Service health status
- Error rates