"""Stream type classes for tap-elexon."""

from typing import Any, Dict, Optional, Iterable
from datetime import datetime, timedelta
import requests
from singer_sdk import typing as th
from singer_sdk.streams import RESTStream


class SystemPricesStream(RESTStream):
    """Define stream for Elexon settlement system prices data."""

    name = "DISEBSP"
    primary_keys = ["settlementDate", "startTime"]
    replication_key = None
    
    records_jsonpath = "$.data[*]"

    schema = th.PropertiesList(
        th.Property("settlementDate", th.DateType, required=True),
        th.Property("startTime", th.DateTimeType, required=True),
        th.Property("systemSellPrice", th.NumberType),
        th.Property("netImbalanceVolume", th.NumberType),
        th.Property("totalAcceptedOfferVolume", th.NumberType),
        th.Property("totalAcceptedBidVolume", th.NumberType),
        th.Property("totalAdjustmentSellVolume", th.NumberType),
        th.Property("totalAdjustmentBuyVolume", th.NumberType),
    ).to_dict()

    @property
    def url_base(self) -> str:
        """Return the API URL root."""
        return self.config["api_url"]

    @property
    def path(self) -> str:
        """Return the API path with date for previous day."""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        return f"/{yesterday}"

    def get_url_params(
        self, context: Optional[dict], next_page_token: Optional[Any]
    ) -> Dict[str, Any]:
        """Return a dictionary of values to be used in URL parameterization."""
        return {"format": "json"}

    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parse the response and return an iterator of result records."""
        json_response = response.json()
        
        data = json_response.get("data", [])
        
        for record in data:
            yield {
                "settlementDate": record.get("settlementDate"),
                "startTime": record.get("startTime"),
                "systemSellPrice": self._to_float(record.get("systemSellPrice")),
                "netImbalanceVolume": self._to_float(record.get("netImbalanceVolume")),
                "totalAcceptedOfferVolume": self._to_float(record.get("totalAcceptedOfferVolume")),
                "totalAcceptedBidVolume": self._to_float(record.get("totalAcceptedBidVolume")),
                "totalAdjustmentSellVolume": self._to_float(record.get("totalAdjustmentSellVolume")),
                "totalAdjustmentBuyVolume": self._to_float(record.get("totalAdjustmentBuyVolume")),
            }

    def _to_float(self, value: Any) -> Optional[float]:
        """Convert value to float, return None if conversion fails."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
