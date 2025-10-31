#!/bin/bash
# Script to run all active Meltano jobs in a loop
# This dynamically discovers jobs from meltano.yml instead of hardcoding them

set -e

cd /app 2>/dev/null || cd "$(dirname "$0")" || true

echo "$(date): Starting continuous ETL loop..."

# Function to get all active job names from meltano.yml
get_active_jobs() {
    meltano job list --format=json 2>/dev/null | jq -r '.[].name' || \
    meltano schedule list --format=json 2>/dev/null | jq -r '.[].job' | sort -u || \
    grep -A1 "^jobs:" meltano.yml | grep "name:" | sed 's/.*name: //' | grep -v "^#"
}

while true; do
    echo "$(date): Fetching active jobs..."
    
    # Get all active jobs
    JOBS=$(get_active_jobs)
    
    if [ -z "$JOBS" ]; then
        echo "$(date): No jobs found, using fallback list..."
        # Fallback to known jobs if discovery fails
        JOBS="nationalgas-to-influxdb elexon-disebsp-to-influxdb elexon-b1610-to-influxdb elexon-midp-to-influxdb"
    fi
    
    echo "$(date): Running jobs: $(echo $JOBS | tr '\n' ' ')"
    
    # Run each job
    for job in $JOBS; do
        echo "$(date): Running job: $job"
        if meltano run "$job"; then
            echo "$(date): ✓ Completed: $job"
        else
            echo "$(date): ✗ Failed: $job (continuing with remaining jobs)"
        fi
    done
    
    echo "$(date): All jobs completed. Sleeping for 30 minutes..."
    sleep 1800
done
