#!/usr/bin/env bash
set -euo pipefail

# Define the Docker image name
export DOCKER_NAME=streamlitapp

# Build the image
docker build -t ${DOCKER_NAME}:1.0 .

# Base location for your Docker registry (same as mcp_servers)
export BASE_LOCATION=asia-south1-docker.pkg.dev/smartifacts-446410/smdocker

# Tag and push latest
docker tag "${DOCKER_NAME}:1.0" "${BASE_LOCATION}/${DOCKER_NAME}:latest"
docker push "${BASE_LOCATION}/${DOCKER_NAME}:latest"
