"""InfluxDB target class."""

from singer_sdk import typing as th
from singer_sdk.target_base import Target

from target_influxdb.sinks import InfluxDBSink


class TargetInfluxDB(Target):
    """Singer target for InfluxDB."""

    name = "target-influxdb"
    
    config_jsonschema = th.PropertiesList(
        th.Property(
            "influxdb_url",
            th.StringType,
            required=True,
            description="InfluxDB server URL (e.g., http://localhost:8086)",
        ),
        th.Property(
            "influxdb_token",
            th.StringType,
            required=True,
            secret=True,
            description="InfluxDB authentication token",
        ),
        th.Property(
            "influxdb_org",
            th.StringType,
            required=True,
            description="InfluxDB organization name",
        ),
        th.Property(
            "influxdb_bucket",
            th.StringType,
            required=True,
            description="InfluxDB bucket name",
        ),
        th.Property(
            "batch_size",
            th.IntegerType,
            default=1000,
            description="Maximum number of records to write in a single batch",
        ),
    ).to_dict()

    default_sink_class = InfluxDBSink


if __name__ == "__main__":
    TargetInfluxDB.cli()
