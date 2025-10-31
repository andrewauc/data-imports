#!/bin/bash
# filepath: /Users/aaucott/src/encora/aws/terraform/test/scripts/deploy-and-start-meltano.sh
# Example deployment script for AWS infrastructure

set -euo pipefail

# Configuration
CONTAINER_NAME="meltano-nationalgas"
IMAGE_NAME="ghcr.io/andrewauc/data-imports:latest"
GHCR_USERNAME="andrewauc"

# Source common deployment functions
source "$(dirname "$0")/common-deployment.sh"

# Get InfluxDB token from AWS Secrets Manager
echo "Retrieving InfluxDB token from Secrets Manager..."
INFLUXDB_TOKEN=$(aws secretsmanager get-secret-value \
    --region "${AWS_REGION}" \
    --secret-id "${INFLUXDB_SECRET_NAME}" \
    --query SecretString --output text | jq -r .influx_admin_token)

# Get Elexon API key from Secrets Manager
echo "Retrieving Elexon API key from Secrets Manager..."
ELEXON_API_KEY=$(aws secretsmanager get-secret-value \
    --region "${AWS_REGION}" \
    --secret-id "${ELEXON_SECRET_NAME}" \
    --query SecretString --output text | jq -r .api_key)

# Get National Gas API key from Secrets Manager
echo "Retrieving National Gas API key from Secrets Manager..."
NATIONAL_GAS_API_KEY=$(aws secretsmanager get-secret-value \
    --region "${AWS_REGION}" \
    --secret-id "${NATIONAL_GAS_SECRET_NAME}" \
    --query SecretString --output text | jq -r .api_key)

# Container-specific environment variables
# NOTE: No --command needed! The image's default CMD runs all jobs automatically
CONTAINER_ENV_VARS=(
  "--env INFLUXDB_URL=http://${INFLUXDB_PETERLEE_PRIVATE_IP}:8086"
  "--env INFLUXDB_TOKEN=$INFLUXDB_TOKEN"
  "--env INFLUXDB_ORG=encora"
  "--env INFLUXDB_BUCKET=SystemData"
  "--env MELTANO_ENVIRONMENT=prod"
  "--env ELEXON_API_KEY=$ELEXON_API_KEY"
  "--env NATIONAL_GAS_API_KEY=$NATIONAL_GAS_API_KEY"
)

# Deploy and start the container
# The container will automatically run all active jobs every 30 minutes
deploy_container "$CONTAINER_NAME" "$IMAGE_NAME" "$GHCR_USERNAME" "${CONTAINER_ENV_VARS[@]}"

echo "Container deployed! It will automatically run all active Meltano jobs every 30 minutes."
echo "To view logs: docker logs -f $CONTAINER_NAME"
echo "To see which jobs are running: docker exec $CONTAINER_NAME meltano job list"
