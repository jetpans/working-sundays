#!/bin/bash
# deploy-sundays.sh
# Deploys Working Sundays application (backend Flask API + frontend Next.js)
# Uses Docker named volumes for persistent data (no relative paths)

set -e

# -------- CONFIGURATION --------
BACKEND_IMAGE="jetpans/working-sundays:backend-latest"
FRONTEND_IMAGE="jetpans/working-sundays:frontend-latest"

BACKEND_CONTAINER="working-sundays-api"
FRONTEND_CONTAINER="working-sundays-web"

# Ports: use 5001 (backend) and 3001 (frontend) to avoid conflicts with xqzite
BACKEND_PORT="5001:5000"
FRONTEND_PORT="3001:3000"

# Docker named volumes (Docker manages these automatically)
BACKEND_JOBS_VOLUME="working-sundays-jobs"
BACKEND_AUTH_VOLUME="working-sundays-auth"

# Ensure required environment variables are set
if [ -z "$JWT_SECRET_KEY" ]; then
    echo "ERROR: JWT_SECRET_KEY environment variable is not set."
    echo "Set it on your server before running this script:"
    echo "  export JWT_SECRET_KEY='your-secret-here'"
    exit 1
fi

# -------- INSTALL DOCKER IF MISSING --------
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Installing..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl enable docker
    systemctl start docker
fi

# -------- PULL IMAGES --------
echo "Pulling Docker images..."
docker pull $BACKEND_IMAGE || echo "Warning: Could not pull $BACKEND_IMAGE"
docker pull $FRONTEND_IMAGE || echo "Warning: Could not pull $FRONTEND_IMAGE"

# -------- STOP AND REMOVE EXISTING CONTAINERS --------
for CONTAINER in $BACKEND_CONTAINER $FRONTEND_CONTAINER; do
    if [ "$(docker ps -aq -f name=^${CONTAINER}$)" ]; then
        echo "Stopping and removing existing container $CONTAINER..."
        docker stop $CONTAINER 2>/dev/null || true
        docker rm $CONTAINER 2>/dev/null || true
    fi
done

# -------- CREATE VOLUMES IF THEY DON'T EXIST --------
echo "Ensuring Docker volumes exist..."
docker volume create $BACKEND_JOBS_VOLUME 2>/dev/null || true
docker volume create $BACKEND_AUTH_VOLUME 2>/dev/null || true

# -------- RUN BACKEND CONTAINER --------
echo "Starting backend container..."
docker run -d \
  --name $BACKEND_CONTAINER \
  -p $BACKEND_PORT \
  -e FLASK_ENV=production \
  -e DEBUG=false \
  -e PORT=5000 \
  -e WORKSPACE_ROOT=/app \
  -e RUNS_DIR=/app/api/jobs \
  -e LEGACY_RUNS_DIR=/app/api/runs \
  -e AUTH_DIR=/app/api/auth \
  -e AUTH_USERS_FILE=/app/api/auth/users.json \
  -e JAVA_BIN=java \
  -e JAVA_JAR=/app/api/algorithm.jar \
  -e JWT_SECRET_KEY="$JWT_SECRET_KEY" \
  -e ALLOWED_ORIGINS="https://sundays.jetpans.com" \
  -e JWT_ACCESS_TOKEN_EXPIRES_HOURS=12 \
  -v $BACKEND_JOBS_VOLUME:/app/api/jobs \
  -v $BACKEND_AUTH_VOLUME:/app/api/auth \
  --restart unless-stopped \
  $BACKEND_IMAGE

# -------- RUN FRONTEND CONTAINER --------
echo "Starting frontend container..."
docker run -d \
  --name $FRONTEND_CONTAINER \
  -p $FRONTEND_PORT \
  -e NODE_ENV=production \
  -e NEXT_TELEMETRY_DISABLED=1 \
  --restart unless-stopped \
  $FRONTEND_IMAGE

echo "Deployment complete!"
echo ""
echo "Running containers:"
docker ps --filter name=working-sundays
echo ""
echo "Access the application at: https://sundays.jetpans.com"
echo "Backend API: https://sundays.jetpans.com/api"
echo "Backend logs: docker logs $BACKEND_CONTAINER"
echo "Frontend logs: docker logs $FRONTEND_CONTAINER"
