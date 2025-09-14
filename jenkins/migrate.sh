#!/bin/bash
# Script to migrate from old Jenkins to new Jenkins

echo "=== Jenkins Migration Script ==="

# Backup old Jenkins data
echo "Backing up old Jenkins data..."
docker cp jenkins-container:/var/jenkins_home ./jenkins_backup_$(date +%Y%m%d_%H%M%S)

# Stop old Jenkins
echo "Stopping old Jenkins..."
docker stop jenkins-container
docker rm jenkins-container

# Update compose file to use standard ports
echo "Updating ports in docker-compose.yml..."
sed -i 's/9192:8080/9190:8080/g' docker-compose.yml
sed -i 's/9193:50000/9191:50000/g' docker-compose.yml

# Restart with new ports
echo "Restarting Jenkins with production ports..."
docker compose up -d jenkins

echo "Migration complete! New Jenkins is now on port 9190"