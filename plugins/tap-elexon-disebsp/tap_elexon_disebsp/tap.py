"""Elexon DISEBSP tap class."""

from typing import List

from singer_sdk import Tap, Stream
from singer_sdk import typing as th

from tap_elexon_disebsp.streams import SystemPricesStream


class TapElexonDISEBSP(Tap):
    """Elexon DISEBSP tap class."""

    name = "tap-elexon-disebsp"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "api_url",
            th.StringType,
            required=True,
            default="https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/system-prices",
            description="The Elexon BMRS API endpoint URL",
        ),
        th.Property(
            "start_date",
            th.DateTimeType,
            description="The earliest record date to sync",
        ),
    ).to_dict()

    def discover_streams(self) -> List[Stream]:
        """Return a list of discovered streams."""
        return [
            SystemPricesStream(tap=self),
        ]


if __name__ == "__main__":
    TapElexonDISEBSP.cli()
