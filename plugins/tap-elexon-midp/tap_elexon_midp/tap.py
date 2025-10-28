"""Tap for Elexon MIDP (Market Index Data Provider) data."""

from singer_sdk import Tap, Stream
from singer_sdk import typing as th

from tap_elexon_midp.streams import MIDPStream


class TapElexonMIDP(Tap):
    """Elexon MIDP data tap."""

    name = "tap-elexon-midp"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "api_url",
            th.StringType,
            default="https://data.elexon.co.uk/bmrs/api/v1/balancing/pricing/market-index",
            description="URL for Elexon MIDP API"
        ),
        th.Property(
            "start_date",
            th.DateTimeType,
            description="Start date for data fetch (defaults to 1 hour ago)"
        ),
    ).to_dict()

    def discover_streams(self) -> list[Stream]:
        """Return a list of discovered streams."""
        return [
            MIDPStream(self),
        ]


if __name__ == "__main__":
    TapElexonMIDP.cli()
