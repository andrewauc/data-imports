"""Tap for Elexon BM data."""

from singer_sdk import Tap, Stream
from singer_sdk import typing as th

from tap_elexon_bm.streams import (
    BOALFStream,
    BODStream,
    PhysicalStream,
    DynamicStream,
    B1610Stream,
)


class TapElexonBM(Tap):
    """Elexon BM data tap."""

    name = "tap-elexon-bm"

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
            description="List of BM units to fetch data for"
        ),
        th.Property(
            "start_date",
            th.DateTimeType,
            description="Start date for data fetch (defaults to yesterday)"
        ),
    ).to_dict()

    def discover_streams(self) -> list[Stream]:
        """Return a list of discovered streams."""
        return [
            BOALFStream(self),
            BODStream(self),
            PhysicalStream(self),
            DynamicStream(self),
            B1610Stream(self),
        ]


if __name__ == "__main__":
    TapElexonBM.cli()
