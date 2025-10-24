#!/bin/bash
# Script to run the ETL job every 30 minutes using cron

# This script should be added to crontab:
# */30 * * * * /path/to/run-etl.sh >> /var/log/meltano-etl.log 2>&1

set -e

cd /app

echo "$(date): Starting ETL run..."

# Run the Meltano job
meltano run nationalgas-to-influxdb

echo "$(date): ETL run completed."
