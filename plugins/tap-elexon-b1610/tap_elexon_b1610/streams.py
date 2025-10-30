"""Stream classes for B1610 data."""

from datetime import datetime, timedelta, timezone
from singer_sdk import typing as th
from singer_sdk.streams import RESTStream


class B1610Stream(RESTStream):
    """Stream for B1610 Actual Generation Output per BM Unit."""

    name = "B1610"
    path = "/datasets/B1610/stream"
    primary_keys = ["bmUnit", "settlementDate", "settlementPeriod"]
    replication_key = "halfHourEndTime"

    schema = th.PropertiesList(
        th.Property("dataset", th.StringType),
        th.Property("psrType", th.StringType),
        th.Property("bmUnit", th.StringType),
        th.Property("nationalGridBmUnitId", th.StringType),
        th.Property("settlementDate", th.DateType),
        th.Property("settlementPeriod", th.IntegerType),
        th.Property("halfHourEndTime", th.DateTimeType),
        th.Property("quantity", th.NumberType),
    ).to_dict()

    def compare_start_date(self, value, start_date_value):
        """Override to avoid timezone comparison issues.
        
        We use lookback-based sync instead of state-based, so we don't
        need to compare with start_date. Just return the value as-is.
        """
        return value

    @property
    def url_base(self) -> str:
        """Return the API base URL."""
        return self.config.get("api_url", "https://data.elexon.co.uk/bmrs/api/v1")

    def get_url_params(self, context, next_page_token):
        """Build URL parameters for the API request."""
        # Get date range from context (set by get_records)
        from_dt = context.get("from_date")
        to_dt = context.get("to_date")
        
        # B1610 uses simple from/to date format (YYYY-MM-DD)
        from_str = from_dt.strftime("%Y-%m-%d")
        to_str = to_dt.strftime("%Y-%m-%d")
        
        # Get all bmUnits from context
        bm_units = context.get("bm_units", [])
        
        # Build params with multiple bmUnit values
        params = {
            "from": from_str,
            "to": to_str,
            "format": "json"
        }
        
        return params
    
    def prepare_request(self, context, next_page_token):
        """Prepare the request with multiple bmUnit parameters."""
        http_method = self.rest_method
        url = self.get_url(context)
        params = self.get_url_params(context, next_page_token)
        
        # Add multiple bmUnit parameters
        bm_units = context.get("bm_units", [])
        if bm_units:
            # Create a list of tuples for multiple same-key params
            param_list = [(k, v) for k, v in params.items()]
            for unit in bm_units:
                param_list.append(("bmUnit", unit))
            params = param_list
        
        request_data = self.prepare_request_payload(context, next_page_token)
        headers = self.http_headers
        
        return self.build_prepared_request(
            method=http_method,
            url=url,
            params=params,
            headers=headers,
            json=request_data,
        )

    def parse_response(self, response):
        """Parse the API response."""
        data = response.json()
        if isinstance(data, dict):
            records = data.get("data", [])
        else:
            records = data
        
        # Log first record to debug
        if records:
            self.logger.info(f"Sample API response record: {records[0]}")
        
        yield from records

    def post_process(self, row, context):
        """Process record - quantity field should already be present from API."""
        # Check if quantity exists and log
        has_quantity = "quantity" in row
        if not has_quantity:
            # Only log first few to avoid spam
            if not hasattr(self, '_logged_missing_count'):
                self._logged_missing_count = 0
            if self._logged_missing_count < 3:
                self.logger.warning(f"Record missing 'quantity' field. Keys: {list(row.keys())}")
                self._logged_missing_count += 1
        
        return row

    def get_records(self, context):
        """Fetch records for all BM units in a single request for the last 365 days."""
        bm_units = self.config.get("bm_units", [])
        
        if not bm_units:
            self.logger.warning("No BM units configured, skipping sync")
            return
        
        # Always fetch last 365 days
        end_dt = datetime.now(timezone.utc)
        start_dt = end_dt - timedelta(days=365)
        
        self.logger.info(f"Fetching last 365 days from {start_dt.date()} to {end_dt.date()}")
        
        # Set context for all BM units
        context = context or {}
        context["bm_units"] = bm_units
        context["from_date"] = start_dt
        context["to_date"] = end_dt
        
        self.logger.info(f"Fetching B1610 data for {len(bm_units)} BM units: {', '.join(bm_units)}")
        
        # Call parent get_records with this context - single API call for all units
        yield from super().get_records(context)
