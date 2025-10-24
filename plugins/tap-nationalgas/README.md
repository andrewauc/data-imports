# Tap National Gas

A Singer tap for extracting data from the National Gas API.

Built with the [Meltano Tap SDK](https://sdk.meltano.com) for Singer Taps.

## Installation

```bash
pip install -e .
```

## Configuration

Configure this tap using environment variables or command line arguments.

### Settings

- `api_url`: The National Gas API endpoint URL
- `start_date`: The earliest record date to sync

### Usage

```bash
tap-nationalgas --config config.json
```
