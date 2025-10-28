"""Stream classes for Elexon BM data."""

from datetime import datetime, timedelta
from singer_sdk import typing as th
from singer_sdk.streams import RESTStream


class BOALFStream(RESTStream):
    """Stream for Balancing Mechanism Acceptances (BOALF) data."""

    name = "BOALF"
    path = "/balancing/acceptances"
    primary_keys = ["bmUnit", "acceptanceNumber", "timeFrom"]
    replication_key = None

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
        # Get start date from config or default to last hour
        start_date = self.config.get("start_date")
        if start_date:
            if isinstance(start_date, str):
                from_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            else:
                from_dt = start_date
        else:
            # Default: last hour to now
            from_dt = datetime.now() - timedelta(hours=1)
        
        # Format times for API (minute precision, UTC)
        from_str = from_dt.strftime("%Y-%m-%dT%H:%M") + "Z"
        to_str = datetime.now().strftime("%Y-%m-%dT%H:%M") + "Z"
        
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
        """Override to iterate over each BM unit."""
        bm_units = self.config.get("bm_units", [])
        
        for bm_unit in bm_units:
            self.logger.info(f"Fetching BOALF data for BM unit: {bm_unit}")
            context = context or {}
            context["bm_unit"] = bm_unit
            
            # Call parent get_records with this context
            yield from super().get_records(context)

    @staticmethod
    def _to_float(value):
        """Convert value to float, return None if conversion fails."""
        try:
            return float(value) if value is not None else None
        except (ValueError, TypeError):
            return None
