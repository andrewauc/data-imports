"""Stream classes for Elexon MIDP data."""

from datetime import datetime, timedelta
from singer_sdk import typing as th
from singer_sdk.streams import RESTStream


class MIDPStream(RESTStream):
    """Stream for Market Index Data Provider (MIDP) pricing data."""

    name = "MIDP"
    path = ""
    primary_keys = ["dataProvider", "settlementDate", "settlementPeriod", "startTime"]
    replication_key = None

    schema = th.PropertiesList(
        th.Property("startTime", th.DateTimeType),
        th.Property("settlementDate", th.DateType),
        th.Property("settlementPeriod", th.IntegerType),
        th.Property("dataProvider", th.StringType),
        th.Property("price", th.NumberType),
        th.Property("volume", th.NumberType),
    ).to_dict()

    @property
    def url_base(self) -> str:
        """Return the API base URL."""
        return self.config.get("api_url", "https://data.elexon.co.uk/bmrs/api/v1/balancing/pricing/market-index")

    def get_url_params(self, context, next_page_token):
        """Build URL parameters for the API request."""
        # Get start date from config or default to 1 hour ago
        start_date = self.config.get("start_date")
        if start_date:
            if isinstance(start_date, str):
                from_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            else:
                from_dt = start_date
        else:
            from_dt = datetime.now() - timedelta(hours=1)
        
        # Format times for API (minute precision, UTC)
        from_str = from_dt.strftime("%Y-%m-%dT%H:%M") + "Z"
        to_str = datetime.now().strftime("%Y-%m-%dT%H:%M") + "Z"
        
        return {
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
