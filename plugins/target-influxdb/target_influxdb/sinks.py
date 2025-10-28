"""InfluxDB target sink class."""

from typing import Any, Dict, List, Optional
from datetime import datetime, date, timezone

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from singer_sdk.sinks import BatchSink


class InfluxDBSink(BatchSink):
    """InfluxDB target sink class."""

    max_size = 1000  # Maximum records to write per batch

    def __init__(self, *args, **kwargs):
        """Initialize the sink."""
        super().__init__(*args, **kwargs)
        self._client: Optional[InfluxDBClient] = None
        self._write_api = None

    @property
    def client(self) -> InfluxDBClient:
        """Get or create InfluxDB client."""
        if self._client is None:
            self._client = InfluxDBClient(
                url=self.config["influxdb_url"],
                token=self.config["influxdb_token"],
                org=self.config["influxdb_org"],
            )
            self._write_api = self._client.write_api(write_options=SYNCHRONOUS)
        return self._client

    @property
    def write_api(self):
        """Get write API."""
        if self._write_api is None:
            _ = self.client  # Initialize client which also initializes write_api
        return self._write_api

    def process_batch(self, context: dict) -> None:
        """Write a batch of records to InfluxDB.
        
        Args:
            context: Stream partition or context dictionary.
        """
        records = context["records"]
        points = []

        for record in records:
            point = self._record_to_point(record)
            if point:
                points.append(point)

        if points:
            try:
                self.write_api.write(
                    bucket=self.config["influxdb_bucket"],
                    org=self.config["influxdb_org"],
                    record=points,
                )
                self.logger.info(f"Successfully wrote {len(points)} points to InfluxDB")
            except Exception as e:
                self.logger.error(f"Error writing to InfluxDB: {e}")
                raise

    def _record_to_point(self, record: Dict[str, Any]) -> Optional[Point]:
        """Convert a record to an InfluxDB Point.
        
        Args:
            record: The record dictionary.
            
        Returns:
            An InfluxDB Point object or None if conversion fails.
        """
        try:
            # Use stream name as measurement
            measurement = self.stream_name
            
            # Create point
            point = Point(measurement)
            
            # Add timestamp - prioritize startTime for DISEBSP, then timestamp, then _sdc_extracted_at
            timestamp = None
            if "startTime" in record and record["startTime"] is not None:
                timestamp = self._parse_timestamp(record["startTime"])
            elif "timestamp" in record and record["timestamp"] is not None:
                timestamp = self._parse_timestamp(record["timestamp"])
            elif "_sdc_extracted_at" in record:
                timestamp = self._parse_timestamp(record["_sdc_extracted_at"])
            
            if timestamp:
                point.time(timestamp, WritePrecision.NS)
            
            # Process fields: separate tags from fields
            tags = {}
            fields = {}
            
            for key, value in record.items():
                # Skip metadata fields
                if key.startswith("_sdc_"):
                    continue
                    
                # Skip timestamp fields as they're already handled
                if key in ("timestamp", "startTime"):
                    continue
                
                # Skip None values
                if value is None:
                    continue
                
                # Numeric values (int/float) are fields
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    fields[key] = value
                # Boolean values are fields
                elif isinstance(value, bool):
                    fields[key] = value
                # Date and datetime objects -> convert to ISO string tags
                elif isinstance(value, (datetime, date)):
                    # Convert datetime/date to ISO format string and store as tag
                    tags[key] = value.isoformat()
                # String values are tags (for indexing and filtering)
                elif isinstance(value, str):
                    tags[key] = value
                else:
                    # Fallback: try to convert to float, otherwise skip
                    try:
                        fields[key] = float(value)
                    except (ValueError, TypeError):
                        self.logger.warning(f"Skipping field {key} with unsupported type: {type(value)}")
            
            # Add tags to point
            for tag_key, tag_value in tags.items():
                point.tag(tag_key, tag_value)
            
            # Add fields to point
            for field_key, field_value in fields.items():
                point.field(field_key, field_value)
            
            # Ensure we have at least one field
            if not fields:
                self.logger.warning(f"Record has no valid fields, skipping: {record}")
                return None
            
            return point
            
        except Exception as e:
            self.logger.error(f"Error converting record to Point: {e}, record: {record}")
            return None

    def _parse_timestamp(self, timestamp_value: Any) -> datetime:
        """Parse a timestamp value to datetime.
        
        Args:
            timestamp_value: The timestamp value (string or datetime).
            
        Returns:
            A datetime object with timezone info.
        """
        if isinstance(timestamp_value, datetime):
            # Ensure timezone aware
            if timestamp_value.tzinfo is None:
                return timestamp_value.replace(tzinfo=timezone.utc)
            return timestamp_value
        
        if isinstance(timestamp_value, str):
            try:
                # Try parsing ISO format
                dt = datetime.fromisoformat(timestamp_value.replace('Z', '+00:00'))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                pass
        
        # Default to current time
        return datetime.now(timezone.utc)

    def clean_up(self) -> None:
        """Clean up resources."""
        if self._write_api:
            self._write_api.close()
        if self._client:
            self._client.close()
        self.logger.info("Closed InfluxDB connection")
