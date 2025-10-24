"""Stream type classes for tap-nationalgas."""

from typing import Any, Dict, Optional, Iterable
import requests
from singer_sdk import typing as th
from singer_sdk.streams import RESTStream


class GasQualityStream(RESTStream):
    """Define stream for gas quality data."""

    name = "GasQual"
    path = ""  # Empty path since url_base is the full URL
    primary_keys = ["timestamp", "siteId"]
    replication_key = "timestamp"
    
    # The API returns a simple list structure
    records_jsonpath = "$.data[*]"

    schema = th.PropertiesList(
        th.Property("timestamp", th.DateTimeType, required=True),
        th.Property("siteId", th.IntegerType, required=True),
        th.Property("siteName", th.StringType),
        th.Property("areaName", th.StringType),
        th.Property("cv24", th.NumberType),
        th.Property("sg24", th.NumberType),
        th.Property("cv", th.NumberType),
        th.Property("sg", th.NumberType),
        th.Property("wi", th.NumberType),
        th.Property("co2", th.NumberType),
        th.Property("n2", th.NumberType),
    ).to_dict()

    @property
    def url_base(self) -> str:
        """Return the API URL root."""
        return self.config["api_url"]

    def get_url_params(
        self, context: Optional[dict], next_page_token: Optional[Any]
    ) -> Dict[str, Any]:
        """Return a dictionary of values to be used in URL parameterization."""
        params: dict = {}
        return params

    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parse the response and return an iterator of result records."""
        json_response = response.json()
        
        # The API returns: {"publishedTime": "...", "gasQualityData": [...]}
        published_time = json_response.get("publishedTime")
        gas_quality_data = json_response.get("gasQualityData", [])
        
        for site in gas_quality_data:
            # Get site info
            site_id = site.get("siteId")
            site_name = site.get("siteName")
            
            # Flatten the structure using JSON attribute names
            record = {
                "timestamp": published_time,
                "siteId": site_id,
                "siteName": site_name,
                "areaName": site.get("areaName"),
            }
            
            # Add gas quality details (convert all to float)
            details = site.get("siteGasQualityDetail", {})
            
            def to_float(value):
                """Convert value to float, return None if conversion fails."""
                if value is None:
                    return None
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return None
            
            record.update({
                "cv24": to_float(details.get("cv24")),
                "sg24": to_float(details.get("sg24")),
                "cv": to_float(details.get("cv")),
                "sg": to_float(details.get("sg")),
                "wi": to_float(details.get("wi")),
                "co2": to_float(details.get("co2")),
                "n2": to_float(details.get("n2")),
            })
            
            yield record
