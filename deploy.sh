#!/bin/bash

# Pull the latest images
docker-compose pull

# Stop and remove existing containers
docker-compose down

# Start new containers
docker-compose up -d

# Clean up old images
docker image prune -f

echo "Deployment completed successfully!"