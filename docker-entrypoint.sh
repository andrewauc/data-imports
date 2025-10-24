#!/bin/bash
set -e

# Run Meltano command
if [ "$1" = "schedule" ]; then
    echo "Starting Meltano scheduler..."
    exec meltano schedule list
    exec meltano "$@"
elif [ "$1" = "run" ]; then
    echo "Running Meltano job..."
    exec meltano "$@"
else
    exec "$@"
fi
