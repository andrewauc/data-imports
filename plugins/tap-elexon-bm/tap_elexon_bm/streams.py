"""Stream classes for Elexon BM data."""

from datetime import datetime, timedelta, timezone
from singer_sdk import typing as th
from singer_sdk.streams import RESTStream


class BOALFStream(RESTStream):
    """Stream for Balancing Mechanism Acceptances (BOALF) data."""

    name = "BOALF"
    path = "/balancing/acceptances"
    primary_keys = ["bmUnit", "acceptanceNumber", "timeFrom"]
    replication_key = "timeFrom"  # Use timeFrom for incremental syncs

    schema = th.PropertiesList(
        th.Property("timeFrom", th.DateTimeType),
        th.Property("timeTo", th.DateTimeType),
        th.Property("settlementDate", th.DateType),
        th.Property("settlementPeriodFrom", th.IntegerType),
        th.Property("settlementPeriodTo", th.IntegerType),
        th.Property("bmUnit", th.StringType),
        th.Property("nationalGridBmUnit", th.StringType),
        th.Property("acceptanceNumber", th.IntegerType),
        th.Property("acceptanceTime", th.DateTimeType),
        th.Property("levelFrom", th.NumberType),
        th.Property("levelTo", th.NumberType),
        th.Property("deemedBoFlag", th.BooleanType),
        th.Property("soFlag", th.BooleanType),
        th.Property("storFlag", th.BooleanType),
        th.Property("rrFlag", th.BooleanType),
    ).to_dict()

    @property
    def url_base(self) -> str:
        """Return the API base URL."""
        return self.config.get("api_url", "https://data.elexon.co.uk/bmrs/api/v1")

    def get_url_params(self, context, next_page_token):
        """Build URL parameters for the API request."""
        # Get date range from context (set by get_records)
        from_dt = context.get("from_date")
        to_dt = context.get("to_date")
        
        # Format times for API (minute precision, UTC)
        from_str = from_dt.strftime("%Y-%m-%dT%H:%M") + "Z"
        to_str = to_dt.strftime("%Y-%m-%dT%H:%M") + "Z"
        
        # Get bmUnit from context (set by partitions)
        bm_unit = context.get("bm_unit")
        
        return {
            "bmUnit": bm_unit,
            "from": from_str,
            "to": to_str,
            "format": "json"
        }

    def parse_response(self, response):
        """Parse the API response."""
        data = response.json()
        if isinstance(data, dict):
            records = data.get("data", [])
        else:
            records = data
        
        yield from records

    def get_records(self, context):
        """Override to iterate over each BM unit and chunk dates into 7-day periods."""
        bm_units = self.config.get("bm_units", [])
        
        # Get starting point from state (for incremental) or config (for initial load)
        # Check if we have a bookmark (state) for this stream
        state_value = self.get_starting_replication_key_value(context)
        
        if state_value:
            # Use state from last successful run (incremental load)
            # State value might be a string or datetime, so normalize it
            if isinstance(state_value, str):
                start_dt = datetime.fromisoformat(state_value.replace('Z', '+00:00'))
            else:
                start_dt = state_value
            self.logger.info(f"Incremental sync: starting from last bookmark {start_dt}")
        else:
            # Initial load: use start_date from config
            start_date = self.config.get("start_date")
            if start_date:
                if isinstance(start_date, str):
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                else:
                    start_dt = start_date
            else:
                # Default: last 7 days
                start_dt = datetime.now(timezone.utc) - timedelta(days=7)
            self.logger.info(f"Initial sync: starting from config start_date {start_dt}")
        
        # Ensure start_dt is timezone-aware
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=timezone.utc)
        
        end_dt = datetime.now(timezone.utc)
        
        # Chunk the date range into 7-day periods (API limit)
        chunk_size = timedelta(days=7)
        date_ranges = []
        
        current_start = start_dt
        while current_start < end_dt:
            current_end = min(current_start + chunk_size, end_dt)
            date_ranges.append((current_start, current_end))
            current_start = current_end
        
        self.logger.info(f"Split date range into {len(date_ranges)} chunks of max 7 days each")
        
        for bm_unit in bm_units:
            for from_date, to_date in date_ranges:
                self.logger.info(
                    f"Fetching BOALF data for BM unit: {bm_unit}, "
                    f"from {from_date.isoformat()} to {to_date.isoformat()}"
                )
                
                context = context or {}
                context["bm_unit"] = bm_unit
                context["from_date"] = from_date
                context["to_date"] = to_date
                
                # Call parent get_records with this context
                yield from super().get_records(context)

    @staticmethod
    def _to_float(value):
        """Convert value to float, return None if conversion fails."""
        try:
            return float(value) if value is not None else None
        except (ValueError, TypeError):
            return None
