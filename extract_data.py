"""Deliverable 1: reproducible extraction from the supplied government exports."""
import argparse
import hashlib
import json
import re
import shutil
import pandas as pd
from project_config import RAW, DATA, START, END, SOURCES, LABELS, UNITS, FEATURES


def number(values):
    return pd.to_numeric(values.astype(str).str.replace(',', '', regex=False).str.strip(), errors='coerce')


def read_export(path):
    """Find the Data Series row rather than hard-code a spreadsheet row number."""
    sheet = pd.read_excel(path, header=None, dtype=object)
    headers = sheet.index[sheet.iloc[:, 0].astype(str).str.strip().eq('Data Series')]
    if len(headers) != 1:
        raise ValueError(f'{path.name}: expected one Data Series row')
    h = int(headers[0])
    periods = sheet.iloc[h, 1:].astype(str).str.strip()
    valid = periods.str.match(r'^\d{4}(?:\s+[A-Za-z]{3})?$')
    rows = sheet.iloc[h+1:, :].copy()
    rows.index = rows.iloc[:, 0].astype(str).str.strip()
    values = rows.iloc[:, 1:].loc[:, valid.to_numpy()]
    values.columns = periods[valid].to_list()
    return values, sheet


def selected_export(path, mapping, monthly=False):
    values, metadata = read_export(path)
    output = pd.DataFrame(index=values.columns)
    for key, source_label in mapping.items():
        if source_label not in values.index:
            raise ValueError(f'{path.name}: missing {source_label}')
        row = values.loc[source_label]
        if isinstance(row, pd.DataFrame):
            # Footnote labels can repeat. A data series must be unique with values.
            row = row.loc[row.apply(lambda x: number(x).notna().any(), axis=1)]
            if len(row) != 1:
                raise ValueError(f'{path.name}: ambiguous {source_label}')
            row = row.iloc[0]
        output[key] = number(row).to_numpy()
    output['year'] = output.index.str[:4].astype(int)
    if monthly:
        output['month'] = pd.to_datetime(output.index, format='%Y %b').month
        output = output.reset_index(drop=True).sort_values(['year', 'month'])
        output.to_csv(DATA / 'cpi_monthly.csv', index=False)
        counts = output.groupby('year')[list(mapping)].count()
        annual = output.groupby('year')[list(mapping)].mean()
        annual[counts != 12] = float('nan')
        counts.to_csv(DATA / 'cpi_months_per_year.csv')
    else:
        annual = output.set_index('year')[list(mapping)].sort_index()
    if annual.index.duplicated().any():
        raise ValueError(f'{path.name}: duplicate years')
    return annual


def main(source_dir=None):
    RAW.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    if source_dir:
        source_dir = __import__('pathlib').Path(source_dir)
        for source in SOURCES:
            shutil.copy2(source_dir / source['original'], RAW / source['file'])
    manifest = []
    for source in SOURCES:
        path = RAW / source['file']
        if not path.exists():
            raise FileNotFoundError(f'{path}: run with --source-dir pointing to the original project')
        entry = dict(source, sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                     package_prepared='2026-10-12', acquisition='user-supplied export, preserved snapshot')
        if path.suffix == '.xlsx':
            _, meta = read_export(path)
            text = '\n'.join(meta.iloc[:, 0].dropna().astype(str))
            for key, pattern in [('data_last_updated', r'Data last updated: ([^\n]+)'),
                                 ('export_generated', r'Date generated: ([^\n]+)')]:
                match = re.search(pattern, text)
                entry[key] = match.group(1) if match else 'not supplied'
        else:
            entry['data_last_updated'] = entry['export_generated'] = 'not supplied'
        manifest.append(entry)
    (DATA / 'source_manifest.json').write_text(json.dumps(manifest, indent=2))

    births = selected_export(RAW/'births.xlsx', {
        'tfr': 'Total Fertility Rate (TFR) (Per Female)',
        'crude_birth_rate': 'Crude Birth Rate (Per Thousand Residents)',
        'resident_live_births': 'Resident Live-Births (Number)',
        'asfr_20_24': '20 - 24 Years (Per Thousand Females)',
        'asfr_25_29': '25 - 29 Years (Per Thousand Females)',
        'asfr_30_34': '30 - 34 Years (Per Thousand Females)',
        'asfr_35_39': '35 - 39 Years (Per Thousand Females)',
        'asfr_40_44': '40 - 44 Years (Per Thousand Females)',
    })
    marriages = selected_export(RAW/'marriages.xlsx', {
        'female_marriage_rate': 'Female General Marriage Rate (Per 1,000 Unmarried Resident Females Aged 15-49 Years)'})
    cpi = selected_export(RAW/'cpi_monthly.xlsx', {'cpi_all_items': 'All Items',
        'cpi_actual_rent': 'Actual Rentals For Housing', 'cpi_accommodation': 'Accommodation', 'cpi_education': 'Education'}, monthly=True)
    transport = selected_export(RAW/'transport.xlsx', {'rail_length_km': 'Rail Length (Kilometres)'})
    hbs = pd.read_csv(RAW/'household_balance_sheet.csv')
    hbs.columns = hbs.columns.str.strip()
    periods = hbs['Data Series'].astype(str).str.extract(r'^(\d{4})\s+([1-4])Q\s*$')
    hbs['year'] = pd.to_numeric(periods[0], errors='coerce')
    hbs['quarter'] = pd.to_numeric(periods[1], errors='coerce')
    hbs = hbs.dropna(subset=['year', 'quarter']).copy()
    hbs['year'] = hbs['year'].astype(int)
    if hbs.duplicated(['year', 'quarter']).any():
        raise ValueError('Duplicate household balance-sheet quarters')
    for col in ['Assets', 'Liabilities', 'Household Net Worth']:
        hbs[col] = number(hbs[col])
    if (hbs['Assets'].dropna() <= 0).any():
        raise ValueError('Assets must be positive')
    # Balance sheets are stocks: use Q4 rather than sum or average quarterly balances.
    stocks = hbs.loc[hbs.quarter.eq(4)].set_index('year')
    debt = pd.DataFrame({'household_debt_asset_pct': 100*stocks.Liabilities/stocks.Assets})
    hbs.to_csv(DATA/'household_balance_sheet_quarterly.csv', index=False)

    tables = {'births_annual': births, 'marriages_annual': marriages, 'cpi_annual': cpi,
              'transport_annual': transport, 'household_finances_annual': debt}
    coverage = []
    combined = pd.DataFrame(index=pd.Index(range(START, END+1), name='year'))
    for name, table in tables.items():
        table.index.name = 'year'
        table.to_csv(DATA/f'{name}.csv')
        combined = combined.join(table, how='left')
        for col in table:
            available = table[col].dropna()
            coverage.append(dict(dataset=name, variable=col, first_year=int(available.index.min()),
                last_complete_year=int(available.index.max()), available_years=len(available),
                missing_in_analysis=int(combined[col].isna().sum())))
    combined.to_csv(DATA/'analysis_dataset.csv')
    pd.DataFrame(coverage).to_csv(DATA/'data_quality.csv', index=False)
    limitations = {
        'female_marriage_rate': 'Marriage formation proxy. Does not measure marriage timing or fertility within marriage.',
        'cpi_all_items': 'Consumer price level. Does not measure household affordability or wages.',
        'cpi_actual_rent': 'Rental price proxy. Excludes house purchase prices and income. Does not measure housing affordability.',
        'cpi_accommodation': 'Housing services price proxy, including imputed rents and maintenance. Excludes house purchase prices and income. Does not measure affordability.',
        'cpi_education': 'Broad education price proxy. Does not isolate preschool or childcare fees.',
        'household_debt_asset_pct': 'National aggregate ratio, Q4 stocks. Does not measure young couples or debt service. Original download timestamp unavailable.',
        'rail_length_km': 'Infrastructure proxy. Does not measure commute time, local accessibility or transport affordability.',
    }
    dictionary = []
    for col in combined:
        label = LABELS.get(col, col.replace('asfr_', 'Age-specific fertility rate ').replace('_', '–'))
        dictionary.append(dict(variable=col, label=label, unit=UNITS.get(col,'births per 1,000 women in age group'),
                               role='candidate predictor' if col in FEATURES else 'outcome / diagnostic',
                               limitation=limitations.get(col,'Period fertility measure; national annual aggregate.')))
    pd.DataFrame(dictionary).to_csv(DATA/'data_dictionary.csv', index=False)
    print(f'Extracted {len(tables)} annual CSVs. Main dataset: {combined.shape}.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-dir', help='Folder containing the original supplied exports')
    main(parser.parse_args().source_dir)
