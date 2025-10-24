"""National Gas tap class."""

from typing import List

from singer_sdk import Tap, Stream
from singer_sdk import typing as th

from tap_nationalgas.streams import GasQualityStream


class TapNationalGas(Tap):
    """National Gas tap class."""

    name = "tap-nationalgas"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "api_url",
            th.StringType,
            required=True,
            default="https://api.nationalgas.com/operationaldata/v1/gasquality/latestdata",
            description="The National Gas API endpoint URL",
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
            GasQualityStream(tap=self),
        ]


if __name__ == "__main__":
    TapNationalGas.cli()
