# Quick Reference Guide

## Common Commands

### Local Development

```bash
# Activate virtual environment
source venv/bin/activate

# Run the ETL pipeline once
meltano run nationalgas-to-influxdb

# Run with debug logging
meltano run nationalgas-to-influxdb --log-level debug

# Test tap only
meltano invoke tap-nationalgas --discover

# Test target only
meltano invoke target-influxdb --about

# List all configurations
meltano config list

# Set a configuration value
meltano config target-influxdb set influxdb_url http://localhost:8086
```

### Docker Commands

```bash
# Build image
docker build -t meltano-nationalgas .

# Run container (single execution)
docker run --env-file .env meltano-nationalgas run nationalgas-to-influxdb

# Run with 30-min schedule
docker run -d --name meltano-nationalgas --restart unless-stopped \
  --env-file .env \
  meltano-nationalgas \
  /bin/sh -c "while true; do meltano run nationalgas-to-influxdb; sleep 1800; done"

# View logs
docker logs -f meltano-nationalgas

# Stop container
docker stop meltano-nationalgas

# Remove container
docker rm meltano-nationalgas
```

### Docker Compose Commands

```bash
# Start all services (production mode)
docker-compose up -d

# Start with local InfluxDB
docker-compose --profile local up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

### EC2 Deployment

```bash
# SSH to EC2
ssh -i your-key.pem ec2-user@your-ec2-host

# View container logs
docker logs -f meltano-nationalgas

# Restart container
docker restart meltano-nationalgas

# Pull latest image and redeploy
docker pull ghcr.io/your-org/your-repo:latest
docker stop meltano-nationalgas
docker rm meltano-nationalgas
docker run -d --name meltano-nationalgas --restart unless-stopped \
  --env-file ~/meltano-etl/.env \
  ghcr.io/your-org/your-repo:latest \
  /bin/sh -c "while true; do meltano run nationalgas-to-influxdb; sleep 1800; done"
```

## Configuration

### Environment Variables (.env)

```env
# Required
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your-token-here
INFLUXDB_ORG=your-org
INFLUXDB_BUCKET=nationalgas

# Optional
MELTANO_ENVIRONMENT=dev
MELTANO_CLI_LOG_LEVEL=info
```

### GitHub Secrets (for CI/CD)

- `EC2_HOST` - EC2 instance IP or hostname
- `EC2_USER` - SSH username (e.g., ec2-user)
- `EC2_SSH_KEY` - Private SSH key content
- `INFLUXDB_URL` - InfluxDB server URL
- `INFLUXDB_TOKEN` - InfluxDB auth token
- `INFLUXDB_ORG` - InfluxDB organization
- `INFLUXDB_BUCKET` - InfluxDB bucket name

## Troubleshooting

### Check API Connection
```bash
curl -v https://api.nationalgas.com/operationaldata/v1/gasquality/latestdata
```

### Check InfluxDB Connection
```bash
# Ping InfluxDB
curl -I http://localhost:8086/ping

# Or with Python
python3 << EOF
from influxdb_client import InfluxDBClient
client = InfluxDBClient(url="http://localhost:8086", token="your-token", org="your-org")
print("Connected:", client.ping())
client.close()
EOF
```

### Debug Pipeline
```bash
# Enable debug logging
export MELTANO_CLI_LOG_LEVEL=debug

# Run with verbose output
meltano run nationalgas-to-influxdb --log-level debug

# Check Meltano state
meltano state list

# Reset state (if needed)
meltano state clear nationalgas-to-influxdb
```

### View Data in InfluxDB
```bash
# Using InfluxDB CLI
influx query 'from(bucket: "nationalgas") |> range(start: -1h) |> limit(n: 10)' \
  --host http://localhost:8086 \
  --org your-org \
  --token your-token

# Or via web UI
# Open http://localhost:8086 in browser
```

## Scheduling Options

### Option 1: Docker Loop (Recommended)
```bash
docker run -d --name meltano-nationalgas --restart unless-stopped \
  --env-file .env \
  meltano-nationalgas \
  /bin/sh -c "while true; do meltano run nationalgas-to-influxdb; sleep 1800; done"
```

### Option 2: Cron Job
```bash
# Add to crontab: crontab -e
*/30 * * * * cd /path/to/project && ./run-etl.sh >> /var/log/meltano.log 2>&1
```

### Option 3: Systemd Timer (EC2/Linux)
```bash
# Create /etc/systemd/system/meltano-etl.service
[Unit]
Description=Meltano National Gas ETL
After=docker.service

[Service]
Type=oneshot
ExecStart=/usr/bin/docker exec meltano-nationalgas meltano run nationalgas-to-influxdb

[Install]
WantedBy=multi-user.target

# Create /etc/systemd/system/meltano-etl.timer
[Unit]
Description=Run Meltano ETL every 30 minutes

[Timer]
OnBootSec=5min
OnUnitActiveSec=30min

[Install]
WantedBy=timers.target

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable meltano-etl.timer
sudo systemctl start meltano-etl.timer
```

## File Locations

- **Project config**: `meltano.yml`
- **Environment**: `.env`
- **Logs**: `.meltano/logs/`
- **State**: `.meltano/state/`
- **Custom plugins**: `plugins/`

## Useful Links

- [Meltano Documentation](https://docs.meltano.com)
- [Singer Spec](https://hub.meltano.com/singer/spec)
- [InfluxDB Python Client](https://github.com/influxdata/influxdb-client-python)
- [National Gas API](https://api.nationalgas.com/)
