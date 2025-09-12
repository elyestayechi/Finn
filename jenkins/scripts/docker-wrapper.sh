#!/bin/bash
# Use the actual Docker binary path (not the symlink)
/Applications/Docker.app/Contents/Resources/bin/docker -H unix:///var/run/docker.sock "$@"