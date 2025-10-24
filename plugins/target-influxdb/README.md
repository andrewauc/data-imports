# Target InfluxDB

A Singer target for loading data into InfluxDB 2.x.

Built with the [Meltano Target SDK](https://sdk.meltano.com) for Singer Targets.

## Installation

```bash
pip install -e .
```

## Configuration

Configure this target using environment variables or command line arguments.

### Settings

- `influxdb_url`: InfluxDB server URL
- `influxdb_token`: Authentication token
- `influxdb_org`: Organization name
- `influxdb_bucket`: Bucket name to write data to

### Usage

```bash
target-influxdb --config config.json
```
