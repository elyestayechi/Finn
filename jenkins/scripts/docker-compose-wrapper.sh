#!/bin/bash
# Use the actual Docker Compose binary path (not the symlink)  
/Applications/Docker.app/Contents/Resources/cli-plugins/docker-compose -H unix:///var/run/docker.sock "$@"