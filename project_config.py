"""One set of definitions shared by extraction, analysis and dashboard."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / '01_data' / 'raw'
DATA = ROOT / '01_data' / 'processed'
RESULTS = ROOT / '02_analysis' / 'results'
START, END = 2005, 2025
TARGET = 'tfr'
FEATURES = ['female_marriage_rate', 'cpi_all_items', 'cpi_accommodation',
            'cpi_education', 'household_debt_asset_pct', 'rail_length_km']
LABELS = {
    'tfr': 'Total fertility rate (births per woman)',
    'crude_birth_rate': 'Crude birth rate (per 1,000 residents)',
    'resident_live_births': 'Resident live births (number)',
    'female_marriage_rate': 'Female general marriage rate',
    'cpi_all_items': 'General consumer prices',
    'cpi_actual_rent': 'Actual housing rental prices',
    'cpi_accommodation': 'Accommodation prices',
    'cpi_education': 'Education prices',
    'household_debt_asset_pct': 'Household liabilities / assets',
    'rail_length_km': 'Rail network length',
}
UNITS = {'tfr': 'births per woman', 'crude_birth_rate': 'per 1,000 residents',
         'resident_live_births': 'number', 'female_marriage_rate': 'per 1,000 unmarried resident women aged 15–49',
         'cpi_all_items': 'index, 2024=100', 'cpi_actual_rent': 'index, 2024=100', 'cpi_accommodation': 'index, 2024=100',
         'cpi_education': 'index, 2024=100', 'household_debt_asset_pct': '%',
         'rail_length_km': 'km'}
SOURCES = [
    dict(file='births.xlsx', original='Births And Fertility Rates.xlsx', table='M810091',
         title='Births And Fertility Rates, Annual', agency='DOS / ICA', frequency='annual',
         url='https://tablebuilder.singstat.gov.sg/table/TS/M810091'),
    dict(file='marriages.xlsx', original='marriage rate singapore WANGYANG(1).xlsx', table='M830102',
         title='Marriage Rates, Annual', agency='DOS', frequency='annual',
         url='https://tablebuilder.singstat.gov.sg/table/TS/M830102'),
    dict(file='cpi_monthly.xlsx', original='CPI_2024_BaseYear(1).xlsx', table='M213751',
         title='Consumer Price Index, 2024 As Base Year, Monthly', agency='DOS', frequency='monthly',
         url='https://tablebuilder.singstat.gov.sg/table/TS/M213751'),
    dict(file='transport.xlsx', original='Public Transport Operation And Ridership.xlsx', table='M651351',
         title='Public Transport Operation And Ridership, Annual', agency='LTA', frequency='annual',
         url='https://tablebuilder.singstat.gov.sg/table/TS/M651351'),
    dict(file='household_balance_sheet.csv', original='Household balance sheet.csv', table='M700981',
         title='Household Sector Balance Sheet (End Of Period), Quarterly', agency='DOS',
         frequency='quarterly, not seasonally adjusted', url='https://tablebuilder.singstat.gov.sg/table/TS/M700981',
         verification_url='https://data.gov.sg/datasets/d_7cb92e23305b005daf1cebd9774516d4/view',
         verification='Official table identified from title and matching 2026 Q2 Assets of 3826110.2. Original CSV has no embedded download metadata.'),
]
