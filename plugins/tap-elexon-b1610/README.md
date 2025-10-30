# tap-elexon-b1610

Singer tap for extracting B1610 Actual Generation Output per BM Unit data from Elexon BMRS API.

## Configuration

- `api_url`: Base URL for Elexon API (default: https://data.elexon.co.uk/bmrs/api/v1)
- `bm_units`: List of BM unit IDs to extract data for
- `start_date`: Start date for initial data extraction (ISO 8601 format)

## Output Schema

The tap outputs records with the following fields:
- Tags: `dataset`, `psrType`, `bmUnit`, `nationalGridBmUnitId`, `settlementDate`, `settlementPeriod`
- Timestamp: `halfHourEndTime`
- Field: `quantity` (output as `Gen_MV_MW`)
