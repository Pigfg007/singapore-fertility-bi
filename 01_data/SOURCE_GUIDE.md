# Deliverable 1: source and extraction guide

The supplied government exports are preserved in `raw/`. Run `python extract_data.py` from the package root to recreate the CSVs. All source links, snapshot dates and SHA-256 hashes are in `processed/source_manifest.json`.

| Dataset | Agency | Official series | Source frequency |
| --- | --- | --- | --- |
| Births And Fertility Rates, Annual | DOS / ICA | [M810091](https://tablebuilder.singstat.gov.sg/table/TS/M810091) | annual |
| Marriage Rates, Annual | DOS | [M830102](https://tablebuilder.singstat.gov.sg/table/TS/M830102) | annual |
| Consumer Price Index, 2024 As Base Year, Monthly | DOS | [M213751](https://tablebuilder.singstat.gov.sg/table/TS/M213751) | monthly |
| Public Transport Operation And Ridership, Annual | LTA | [M651351](https://tablebuilder.singstat.gov.sg/table/TS/M651351) | annual |
| Household Sector Balance Sheet (End Of Period), Quarterly | DOS | [M700981](https://tablebuilder.singstat.gov.sg/table/TS/M700981) | quarterly, not seasonally adjusted |

Four workbooks preserve table IDs, source update dates and an export date of 15 September 2026. The household balance-sheet CSV lacks embedded download metadata. We identified its official non-seasonally-adjusted series as M700981 using the official dataset title and matching 2026 Q2 Assets of 3,826,110.2. See the [official mirror](https://data.gov.sg/datasets/d_7cb92e23305b005daf1cebd9774516d4/view). The manifest distinguishes supplied snapshot provenance from this external verification.

**Extraction and alignment rules**

1. Find the workbook's `Data Series` header and select named rows. Strip formatting and convert numeric strings without inventing missing values.
2. Preserve annual birth, marriage and transport observations in chronological CSVs.
3. Calculate annual CPI as the mean of **12 observed months** for each series and year. Mark incomplete years unavailable. This follows [DOS's annual CPI methodology](https://www.singstat.gov.sg/find-data/explore-data-themes/economy-prices/consumer-price-index/our-data-explained).
4. Treat household balance-sheet amounts as stocks. Select **Q4** and calculate liabilities / assets × 100. Do not sum or average stocks. [DOS describes these as end-of-period measures](https://www.singstat.gov.sg/find-data/explore-data-themes/economy-prices/household-sector-economic-indicators/our-data-explained).
5. Align on year. The common six-factor window begins in 2005 because accommodation CPI starts then. Exclude 2026 because fertility observations and complete calendar-year CPI are unavailable.
6. Retain actual-rent CPI as supplementary data from 2015. Its earlier blanks are deliberate. Do not impute them or use that series in the common six-factor model.

The package includes five annual source CSVs, monthly CPI, quarterly household finances, the joined analysis dataset, a data dictionary, a coverage report and a hash-based source manifest. No numbered duplicate copies enter the pipeline.

