# Define the Docker image name
export DOCKER_NAME=mcpsanatana
docker build -t $DOCKER_NAME:1.0 .

# Base location for your Docker registry
# export BASE_LOCATION=us-central1-docker.pkg.dev/testproject-433710/sm-docker
export BASE_LOCATION=asia-south1-docker.pkg.dev/smartifacts-446410/smdocker


# Tag the image for pushing to the registry
docker tag "${DOCKER_NAME}:1.0" "${BASE_LOCATION}/${DOCKER_NAME}:latest"

# Push the image to the Docker registry
docker push "${BASE_LOCATION}/${DOCKER_NAME}:latest"