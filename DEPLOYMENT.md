# Deployment Guide

## Overview

This project uses Docker to run Meltano ETL jobs continuously. The deployment automatically discovers and runs all active jobs defined in `meltano.yml`.

## Key Features

- **Automatic Job Discovery**: The deployment script (`run-all-jobs.sh`) dynamically discovers all jobs from `meltano.yml`, so you don't need to update deployment scripts when adding/removing jobs.
- **No State Tracking for B1610**: The `tap-elexon-b1610` tap always fetches the last 365 days of data, ignoring any saved state.
- **30-minute Loop**: All jobs run in sequence every 30 minutes.
- **Graceful Error Handling**: If one job fails, the remaining jobs continue to run.

## Docker Usage

### Build the Image

```bash
docker build -t meltano-etl .
```

### Run with Docker

```bash
docker run -d \
  -e INFLUXDB_URL=<your-influxdb-url> \
  -e INFLUXDB_TOKEN=<your-token> \
  -e INFLUXDB_ORG=<your-org> \
  -e INFLUXDB_BUCKET=<your-bucket> \
  -e ELEXON_API_KEY=<your-api-key> \
  -e NATIONAL_GAS_API_KEY=<your-api-key> \
  --name meltano-etl \
  meltano-etl
```

### Run with Docker Compose

Create a `docker-compose.yml`:

```yaml
version: '3.8'

services:
  meltano:
    build: .
    environment:
      - INFLUXDB_URL=${INFLUXDB_URL}
      - INFLUXDB_TOKEN=${INFLUXDB_TOKEN}
      - INFLUXDB_ORG=${INFLUXDB_ORG}
      - INFLUXDB_BUCKET=${INFLUXDB_BUCKET}
      - ELEXON_API_KEY=${ELEXON_API_KEY}
      - NATIONAL_GAS_API_KEY=${NATIONAL_GAS_API_KEY}
    restart: unless-stopped
```

Then run:

```bash
docker-compose up -d
```

## Adding New Jobs

To add a new job:

1. Define the job in `meltano.yml` under the `jobs:` section:

```yaml
jobs:
  - name: my-new-job
    tasks:
      - tap-my-source target-influxdb
```

2. Install any new custom plugins in the `Dockerfile`:

```dockerfile
RUN pip install -e ./plugins/tap-my-source
```

3. Rebuild and redeploy:

```bash
docker build -t meltano-etl .
docker-compose up -d --force-recreate
```

The new job will automatically be discovered and run in the loop - no need to update `run-all-jobs.sh`!

## Disabling Jobs

To disable a job without deleting it, comment it out in `meltano.yml`:

```yaml
jobs:
  # - name: disabled-job
  #   tasks:
  #     - tap-disabled target-influxdb
```

## State Management

### B1610 Tap (No State)

The `tap-elexon-b1610` has state tracking disabled (`replication_key = None`). It **always** fetches the last 365 days of data, regardless of any saved state. This ensures:

- Consistent data availability
- No state management issues between environments
- Simple deployment (no need to manage state between runs)

### Other Taps (With State)

Other taps like `tap-elexon-disebsp`, `tap-nationalgas`, etc. use normal incremental state tracking. State is stored in the Meltano SQLite database at `/app/.meltano/meltano.db`.

To reset state for a specific tap:

```bash
# Inside the container
meltano state clear <state-id>

# Example
meltano state clear prod:tap-nationalgas-to-target-influxdb
```

## Monitoring

View logs:

```bash
docker logs -f meltano-etl
```

The logs show:
- Which jobs are being run
- Success/failure status for each job
- Data being written to InfluxDB
- Any errors encountered

## Troubleshooting

### Jobs not running

Check that jobs are defined in `meltano.yml`:

```bash
docker exec meltano-etl meltano job list
```

### State issues

If you need to reset state for all taps:

```bash
# Stop the container
docker-compose down

# Remove the volume (if using one) or delete the database
docker volume rm meltano_data

# Restart
docker-compose up -d
```

### InfluxDB connection issues

Verify environment variables are set correctly:

```bash
docker exec meltano-etl env | grep INFLUXDB
```

## Architecture

```
┌─────────────────────────────────────────────┐
│           run-all-jobs.sh (loop)            │
│  Discovers jobs → Runs each → Sleep 30min  │
└─────────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   ┌─────────┐  ┌─────────┐  ┌─────────┐
   │  Job 1  │  │  Job 2  │  │  Job 3  │
   └─────────┘  └─────────┘  └─────────┘
        │            │            │
        └────────────┼────────────┘
                     ▼
             ┌───────────────┐
             │   InfluxDB    │
             └───────────────┘
```
