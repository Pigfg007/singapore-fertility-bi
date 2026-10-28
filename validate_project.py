"""Checks that protect source interpretation and the reported conclusions."""
import hashlib
import json
import numpy as np
import pandas as pd
from project_config import RAW, DATA, RESULTS, FEATURES, START, END, ROOT
from analysis_core import backtest, transform


def main():
    d=pd.read_csv(DATA/'analysis_dataset.csv',index_col='year')
    assert d.index.to_list()==list(range(START,END+1))
    assert not d[['tfr']+FEATURES].isna().any().any()
    assert len(d)==21 and np.isclose(d.loc[2015,'tfr'],1.24) and np.isclose(d.loc[2025,'tfr'],.87)
    for source in json.loads((DATA/'source_manifest.json').read_text()):
        assert hashlib.sha256((RAW/source['file']).read_bytes()).hexdigest()==source['sha256']
    monthly=pd.read_csv(DATA/'cpi_monthly.csv')
    for year in [2005,2015,2025]:
        m=monthly.loc[monthly.year.eq(year)]
        assert m.month.nunique()==12
        for col in ['cpi_all_items','cpi_accommodation','cpi_education']:
            assert np.isclose(m[col].mean(),d.loc[year,col])
    assert monthly.loc[monthly.year.eq(2026),'month'].nunique()<12
    cpi=pd.read_csv(DATA/'cpi_annual.csv',index_col='year')
    assert cpi.loc[2026].isna().all()
    raw=pd.read_csv(RAW/'household_balance_sheet.csv')
    raw.columns=raw.columns.str.strip()
    for year in [2005,2015,2025]:
        row=raw.loc[raw['Data Series'].str.strip().eq(f'{year} 4Q')].iloc[0]
        assert np.isclose(100*float(row.Liabilities)/float(row.Assets),d.loc[year,'household_debt_asset_pct'])
    gap=transform(d.drop(index=[2020,2021]),'Annual changes')
    assert gap.loc[2022,FEATURES].isna().all(), 'Do not bridge pandemic gaps'
    associations=pd.read_csv(RESULTS/'associations.csv')
    assert len(associations)==18
    changes=associations[associations['mode'].eq('Annual changes')]
    assert changes.n.eq(20).all() and changes.bh_q.gt(.05).all()
    for row in changes.itertuples():
        independent=np.corrcoef(d[row.variable].diff().dropna(),d.tfr.diff().dropna())[0,1]
        assert np.isclose(row.correlation,independent)
    prediction,scores,tuning,alpha=backtest(d)
    modified=d.copy();modified.loc[2025,FEATURES]=modified.loc[2025,FEATURES]*10
    no_leak,*_=backtest(modified)
    assert np.allclose(prediction.ridge,no_leak.ridge), 'Current-year inputs cannot change forecasts'
    saved=pd.read_csv(RESULTS/'backtest_predictions.csv')
    assert np.allclose(prediction.ridge,saved.ridge)
    assert prediction.year.to_list()==[2021,2022,2023,2024,2025]
    assert np.allclose(prediction.persistence,d.loc[2020:2024,'tfr'])
    report=(ROOT/'04_findings'/'findings_report.md').read_text()
    assert '29.8%' in report and '0.0545' in report and '2005–2025' in report
    print('PASS: source hashes, coverage, annual aggregation, Q4 stocks, gap handling, correlations, forecast leakage and report consistency.')


if __name__=='__main__':main()
