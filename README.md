# National Gas ETL Pipeline

A simple ETL pipeline using [Meltano](https://meltano.com/) to extract data from the National Gas API and load it into InfluxDB 2.7.

## Overview

This project extracts gas quality data from the National Gas API every 30 minutes and stores it in InfluxDB for time-series analysis and visualization.

### Architecture

- **Extractor**: Custom Singer tap for National Gas API
- **Loader**: Custom Singer target for InfluxDB 2.7
- **Orchestration**: Meltano
- **Containerization**: Docker
- **Deployment**: GitHub Actions → EC2

## Quick Start

### Prerequisites

- Python 3.8+
- Docker and Docker Compose (for containerized deployment)
- InfluxDB 2.7 instance
- GitHub account (for CI/CD)
- EC2 instance (for production deployment)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd data-imports
   ```

2. **Create and configure environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your InfluxDB credentials
   ```

3. **Install dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Install Meltano plugins**
   ```bash
   meltano install
   ```

5. **Run the pipeline manually**
   ```bash
   meltano run nationalgas-to-influxdb
   ```

### Docker Deployment

#### Local Testing with Docker

Run the entire stack locally including InfluxDB:

```bash
# Start InfluxDB and Meltano
docker-compose --profile local up -d

# Check logs
docker-compose logs -f meltano

# Stop the stack
docker-compose down
```

#### Production Docker Deployment

```bash
# Build the image
docker build -t meltano-nationalgas .

# Run the container
docker run -d \
  --name meltano-nationalgas \
  --env-file .env \
  --restart unless-stopped \
  meltano-nationalgas
```

## Configuration

### Environment Variables

Configure the following in your `.env` file:

```env
# InfluxDB Configuration
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your-influxdb-token
INFLUXDB_ORG=your-org
INFLUXDB_BUCKET=nationalgas

# Meltano Configuration
MELTANO_ENVIRONMENT=dev
MELTANO_CLI_LOG_LEVEL=info
```

### Meltano Configuration

The `meltano.yml` file defines:

- **Extractors**: tap-nationalgas (custom)
- **Loaders**: target-influxdb (custom)
- **Jobs**: nationalgas-to-influxdb
- **Schedules**: Runs every 30 minutes

## Custom Plugins

### tap-nationalgas

A Singer tap that extracts data from the National Gas API endpoint:
- **Endpoint**: `https://api.nationalgas.com/operationaldata/v1/gasquality/latestdata`
- **Authentication**: None required
- **Data**: Gas quality measurements including Wobbe index, calorific value, composition

**Location**: `plugins/tap-nationalgas/`

### target-influxdb

A Singer target that loads data into InfluxDB 2.7:
- **Protocol**: InfluxDB Line Protocol
- **Batching**: Configurable batch size (default: 1000)
- **Tags**: Automatically extracts string fields as tags
- **Fields**: Numeric and boolean values as fields

**Location**: `plugins/target-influxdb/`

## CI/CD with GitHub Actions

### Setup

1. **Configure GitHub Secrets**

   Go to your repository → Settings → Secrets and add:

   - `EC2_HOST`: Your EC2 instance IP or hostname
   - `EC2_USER`: SSH username (e.g., `ec2-user`, `ubuntu`)
   - `EC2_SSH_KEY`: Private SSH key for EC2 access
   - `INFLUXDB_URL`: InfluxDB server URL
   - `INFLUXDB_TOKEN`: InfluxDB authentication token
   - `INFLUXDB_ORG`: InfluxDB organization
   - `INFLUXDB_BUCKET`: InfluxDB bucket name

2. **Enable GitHub Container Registry**

   The workflow automatically publishes Docker images to GitHub Container Registry (ghcr.io).

3. **Prepare EC2 Instance**

   ```bash
   # SSH into your EC2 instance
   ssh ec2-user@your-ec2-host

   # Install Docker
   sudo yum update -y
   sudo yum install -y docker
   sudo service docker start
   sudo usermod -a -G docker ec2-user

   # Create directory for app
   mkdir -p ~/meltano-etl
   ```

4. **Trigger Deployment**

   Push to `main` branch or manually trigger the workflow:
   ```bash
   git push origin main
   ```

### Workflow Steps

1. Builds Docker image
2. Pushes to GitHub Container Registry
3. SSH into EC2
4. Pulls latest image
5. Stops old container
6. Starts new container with 30-minute schedule

## Manual Deployment to EC2

If you prefer manual deployment:

1. **Build and push image**
   ```bash
   docker build -t your-registry/meltano-nationalgas .
   docker push your-registry/meltano-nationalgas
   ```

2. **SSH to EC2 and deploy**
   ```bash
   ssh ec2-user@your-ec2-host

   # Pull image
   docker pull your-registry/meltano-nationalgas

   # Create .env file
   cat > ~/meltano-etl/.env << EOF
   INFLUXDB_URL=http://your-influxdb:8086
   INFLUXDB_TOKEN=your-token
   INFLUXDB_ORG=your-org
   INFLUXDB_BUCKET=nationalgas
   MELTANO_ENVIRONMENT=prod
   EOF

   # Run container with 30-minute schedule
   docker run -d \
     --name meltano-nationalgas \
     --restart unless-stopped \
     --env-file ~/meltano-etl/.env \
     your-registry/meltano-nationalgas \
     /bin/sh -c "while true; do meltano run nationalgas-to-influxdb; sleep 1800; done"
   ```

3. **Monitor logs**
   ```bash
   docker logs -f meltano-nationalgas
   ```

## Alternative Scheduling Options

### Using Cron on EC2

1. Copy the `run-etl.sh` script to EC2
2. Add to crontab:
   ```bash
   */30 * * * * /path/to/run-etl.sh >> /var/log/meltano-etl.log 2>&1
   ```

### Using Meltano's Built-in Scheduler

Uncomment the scheduler command in `docker-compose.yml`:
```yaml
command: ["schedule", "run", "nationalgas-to-influxdb"]
```

## Data Schema

### National Gas API Response

The API returns gas quality data with fields like:
- `timestamp`: Measurement timestamp
- `location_code`: Location identifier
- `location_name`: Location name
- `wobbe_index`: Wobbe index value
- `gross_calorific_value`: GCV value
- `relative_density`: Density
- Gas composition: `methane`, `ethane`, `propane`, etc.

### InfluxDB Schema

**Measurement**: `gas_quality`

**Tags**:
- `location_code`
- `location_name`

**Fields**:
- `wobbe_index` (float)
- `gross_calorific_value` (float)
- `relative_density` (float)
- `carbon_dioxide` (float)
- `nitrogen` (float)
- `methane` (float)
- And other numeric measurements

**Timestamp**: From API or current time

## Monitoring and Troubleshooting

### View Logs

```bash
# Local
meltano run nationalgas-to-influxdb --log-level debug

# Docker
docker logs -f meltano-nationalgas

# Docker Compose
docker-compose logs -f meltano
```

### Test API Connection

```bash
curl https://api.nationalgas.com/operationaldata/v1/gasquality/latestdata
```

### Test InfluxDB Connection

```bash
# Using InfluxDB CLI
influx ping --host http://localhost:8086

# Using Python
python -c "
from influxdb_client import InfluxDBClient
client = InfluxDBClient(url='http://localhost:8086', token='your-token', org='your-org')
print(client.ping())
"
```

### Common Issues

1. **"Unable to connect to InfluxDB"**
   - Check INFLUXDB_URL is correct
   - Verify token has write permissions
   - Ensure bucket exists

2. **"No records extracted"**
   - Test API endpoint manually
   - Check API response format matches schema
   - Review tap logs with `--log-level debug`

3. **"Container keeps restarting"**
   - Check Docker logs: `docker logs meltano-nationalgas`
   - Verify all environment variables are set
   - Ensure plugins are installed correctly

## Extending the Pipeline

### Adding More Data Sources

1. Create a new tap in `plugins/tap-<source>/`
2. Add to `meltano.yml`:
   ```yaml
   extractors:
     - name: tap-newsource
       pip_url: -e ./plugins/tap-newsource
   ```
3. Create a new job:
   ```yaml
   jobs:
     - name: newsource-to-influxdb
       tasks:
         - tap-newsource target-influxdb
   ```

### Modifying the Target

Edit `plugins/target-influxdb/target_influxdb/sinks.py` to customize:
- Field mapping
- Tag selection
- Timestamp handling
- Batch size

## Project Structure

```
.
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions CI/CD
├── plugins/
│   ├── tap-nationalgas/        # Custom National Gas tap
│   │   ├── tap_nationalgas/
│   │   ├── pyproject.toml
│   │   └── README.md
│   └── target-influxdb/        # Custom InfluxDB target
│       ├── target_influxdb/
│       ├── pyproject.toml
│       └── README.md
├── .env.example                # Example environment configuration
├── .gitignore                  # Git ignore patterns
├── docker-compose.yml          # Docker Compose configuration
├── Dockerfile                  # Container image definition
├── docker-entrypoint.sh        # Container entrypoint script
├── meltano.yml                 # Meltano project configuration
├── README.md                   # This file
├── requirements.txt            # Python dependencies
└── run-etl.sh                  # ETL execution script
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## License

[Your License Here]

## Support

For issues or questions:
- Open an issue in the repository
- Check Meltano documentation: https://docs.meltano.com
- Review InfluxDB client docs: https://docs.influxdata.com/
