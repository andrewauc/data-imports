"""B1610 tap class."""

from typing import List
from singer_sdk import Tap, Stream
from singer_sdk import typing as th
from tap_elexon_b1610.streams import B1610Stream


class TapElexonB1610(Tap):
    """Singer tap for B1610 Actual Generation Output data."""

    name = "tap-elexon-b1610"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "api_url",
            th.StringType,
            default="https://data.elexon.co.uk/bmrs/api/v1",
            description="Base URL for Elexon BMRS API"
        ),
        th.Property(
            "bm_units",
            th.ArrayType(th.StringType),
            required=True,
            description="List of BM Unit IDs to extract data for"
        ),
        th.Property(
            "start_date",
            th.DateTimeType,
            description="Start date for initial data extraction (ISO 8601 format)"
        ),
    ).to_dict()

    def discover_streams(self) -> List[Stream]:
        """Return a list of discovered streams."""
        return [B1610Stream(self)]


if __name__ == "__main__":
    TapElexonB1610.cli()
