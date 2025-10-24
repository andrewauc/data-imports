# Project Structure

```
data-imports/
├── .github/
│   └── workflows/
│       └── deploy.yml              # GitHub Actions CI/CD workflow
│
├── plugins/                        # Custom Meltano plugins
│   ├── tap-nationalgas/           # Custom tap for National Gas API
│   │   ├── tap_nationalgas/
│   │   │   ├── __init__.py        # Package initialization
│   │   │   ├── tap.py             # Main tap class
│   │   │   └── streams.py         # Stream definitions
│   │   ├── MANIFEST.in            # Package manifest
│   │   ├── pyproject.toml         # Python project config
│   │   └── README.md              # Tap documentation
│   │
│   └── target-influxdb/           # Custom target for InfluxDB
│       ├── target_influxdb/
│       │   ├── __init__.py        # Package initialization
│       │   ├── target.py          # Main target class
│       │   └── sinks.py           # Sink implementation
│       ├── MANIFEST.in            # Package manifest
│       ├── pyproject.toml         # Python project config
│       └── README.md              # Target documentation
│
├── .env.example                   # Example environment variables
├── .gitignore                     # Git ignore patterns
├── docker-compose.yml             # Docker Compose configuration
├── docker-entrypoint.sh           # Container entrypoint script
├── Dockerfile                     # Container image definition
├── meltano.yml                    # Meltano project configuration
├── QUICKSTART.md                  # Quick reference guide
├── README.md                      # Main documentation
├── requirements.txt               # Python dependencies
├── run-etl.sh                     # ETL execution script
├── setup.sh                       # Setup automation script
└── test_setup.py                  # Environment test script
```

## Key Files Explained

### Configuration Files

- **meltano.yml**: Main Meltano configuration defining extractors, loaders, jobs, and schedules
- **.env.example**: Template for environment variables (copy to .env)
- **requirements.txt**: Python package dependencies
- **docker-compose.yml**: Multi-container Docker application setup

### Custom Plugins

#### tap-nationalgas
Custom Singer tap that extracts data from the National Gas API:
- **tap.py**: Defines the tap configuration and stream discovery
- **streams.py**: Implements the GasQualityStream with API interaction logic
- **pyproject.toml**: Python package metadata and dependencies

#### target-influxdb
Custom Singer target that loads data into InfluxDB 2.7:
- **target.py**: Defines the target configuration
- **sinks.py**: Implements batch writing to InfluxDB with Point conversion
- **pyproject.toml**: Python package metadata and dependencies

### Deployment Files

- **Dockerfile**: Builds containerized Meltano environment with custom plugins
- **docker-entrypoint.sh**: Manages container startup and command routing
- **run-etl.sh**: Bash script for cron-based scheduling
- **.github/workflows/deploy.yml**: GitHub Actions workflow for CI/CD

### Documentation

- **README.md**: Comprehensive project documentation
- **QUICKSTART.md**: Quick reference for common commands
- **plugins/*/README.md**: Individual plugin documentation

### Utilities

- **setup.sh**: Automated setup script for local development
- **test_setup.py**: Environment validation script

## Directory Structure After Setup

After running setup and the first pipeline execution:

```
data-imports/
├── [all files above]
├── .env                           # Your environment variables (git-ignored)
├── .meltano/                      # Meltano system files (git-ignored)
│   ├── meltano.db                 # Meltano state database
│   ├── logs/                      # Execution logs
│   ├── run/                       # Runtime files
│   └── state/                     # Pipeline state files
├── venv/                          # Python virtual environment (git-ignored)
└── output/                        # Output directory (if needed)
```

## Data Flow

```
┌─────────────────────────┐
│  National Gas API       │
│  (REST API - public)    │
└───────────┬─────────────┘
            │
            │ HTTP GET
            │ Every 30 min
            ▼
┌─────────────────────────┐
│  tap-nationalgas        │
│  (Custom Singer Tap)    │
│  - Fetches latest data  │
│  - Formats as records   │
└───────────┬─────────────┘
            │
            │ Singer Protocol
            │ (JSON messages)
            ▼
┌─────────────────────────┐
│  target-influxdb        │
│  (Custom Singer Target) │
│  - Batches records      │
│  - Converts to Points   │
└───────────┬─────────────┘
            │
            │ InfluxDB API
            │ (HTTP + Line Protocol)
            ▼
┌─────────────────────────┐
│  InfluxDB 2.7           │
│  (Time-series Database) │
│  - Stores measurements  │
│  - Enables querying     │
└─────────────────────────┘
```

## Deployment Architecture

```
┌──────────────────────────────────────┐
│  GitHub Repository                   │
│  - Source code                       │
│  - Configuration                     │
└────────────┬─────────────────────────┘
             │
             │ Git Push
             ▼
┌──────────────────────────────────────┐
│  GitHub Actions                      │
│  1. Build Docker image               │
│  2. Push to GitHub Container Registry│
│  3. Deploy to EC2                    │
└────────────┬─────────────────────────┘
             │
             │ SSH + Docker Pull
             ▼
┌──────────────────────────────────────┐
│  EC2 Instance                        │
│  ┌────────────────────────────────┐ │
│  │ Docker Container               │ │
│  │ - Meltano                      │ │
│  │ - Custom plugins               │ │
│  │ - Scheduled runs (30 min)     │ │
│  └────────────┬───────────────────┘ │
└───────────────┼─────────────────────┘
                │
                │ HTTP
                ▼
┌──────────────────────────────────────┐
│  InfluxDB Server                     │
│  - Stores time-series data           │
│  - Provides query API                │
└──────────────────────────────────────┘
```

## Environment-Specific Files

### Development (.env for local)
```
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=local-dev-token
MELTANO_ENVIRONMENT=dev
MELTANO_CLI_LOG_LEVEL=debug
```

### Production (GitHub Secrets)
- EC2_HOST
- EC2_USER
- EC2_SSH_KEY
- INFLUXDB_URL
- INFLUXDB_TOKEN
- INFLUXDB_ORG
- INFLUXDB_BUCKET

## Extending the Project

To add a new data source:

1. Create new tap in `plugins/tap-<source>/`
2. Add tap configuration to `meltano.yml`
3. Create new job using the tap
4. Update `requirements.txt` if needed
5. Rebuild Docker image

To modify data transformation:

1. Edit `plugins/target-influxdb/target_influxdb/sinks.py`
2. Adjust the `_record_to_point()` method
3. Customize tag/field mapping logic
