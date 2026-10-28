"""Deliverable 2: EDA, robustness and chronological predictive backtesting."""
import json
import os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR', str(Path(__file__).resolve().parent/'.build'/'matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from project_config import DATA, RESULTS, FEATURES, LABELS, START, END
from analysis_core import association_table, backtest


def main():
    RESULTS.mkdir(parents=True,exist_ok=True)
    d = pd.read_csv(DATA/'analysis_dataset.csv',index_col='year')
    if d.index.duplicated().any() or not d.index.is_monotonic_increasing:
        raise ValueError('Years must be unique and ordered')
    required = ['tfr']+FEATURES
    if d[required].isna().any().any():
        raise ValueError('Main analysis panel has missing values. Review data_quality.csv.')
    tables = [association_table(d,mode=mode) for mode in ['Levels','Annual changes','After removing linear trends']]
    associations = pd.concat(tables,ignore_index=True)
    associations.to_csv(RESULTS/'associations.csv',index=False)
    associations.loc[associations['mode'].eq('Annual changes')].to_csv(RESULTS/'six_variable_effects.csv',index=False)
    d.describe().T.to_csv(RESULTS/'descriptive_statistics.csv')
    d[['tfr']+FEATURES].corr().to_csv(RESULTS/'correlation_levels.csv')
    d[['tfr']+FEATURES].diff().corr().to_csv(RESULTS/'correlation_changes.csv')
    # Prespecified pandemic sensitivity and target sensitivity, reported for all six.
    sensitivity = association_table(d.drop(index=[2020,2021]),mode='Annual changes')
    sensitivity.to_csv(RESULTS/'pandemic_sensitivity.csv',index=False)
    association_table(d,target='crude_birth_rate',mode='Annual changes').to_csv(RESULTS/'crude_birth_rate_sensitivity.csv',index=False)
    lag = d[FEATURES].shift(1).join(d[['tfr']])
    association_table(lag,mode='Levels').to_csv(RESULTS/'lagged_associations.csv',index=False)
    predictions,scores,tuning,alpha = backtest(d)
    predictions.to_csv(RESULTS/'backtest_predictions.csv',index=False)
    scores.to_csv(RESULTS/'backtest_scores.csv',index=False)
    tuning.to_csv(RESULTS/'ridge_tuning.csv',index=False)
    summary = dict(start=START,end=END,n=len(d),tfr_2015=float(d.loc[2015,'tfr']),
        tfr_latest=float(d.loc[END,'tfr']),decade_pct_change=float((d.loc[END,'tfr']/d.loc[2015,'tfr']-1)*100),
        crude_birth_rate_latest=float(d.loc[END,'crude_birth_rate']),
        resident_live_births_latest=int(d.loc[END,'resident_live_births']),ridge_alpha=alpha,
        model_test_years=[2021,2025],best_backtest_model=scores.sort_values('mae').iloc[0]['model'])
    (RESULTS/'summary.json').write_text(json.dumps(summary,indent=2))
    plt.rcParams.update({'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False,'axes.labelsize':11})
    fig,ax=plt.subplots(figsize=(10,4.5)); ax.plot(d.index,d.tfr,color='#073B4C',lw=2.5)
    ax.scatter([2015,END],d.loc[[2015,END],'tfr'],color='#B64B35')
    for year in [2015,END]:ax.annotate(f'{year}: {d.loc[year,"tfr"]:.2f}',(year,d.loc[year,'tfr']),xytext=(0,14),textcoords='offset points',ha='center')
    ax.set(ylabel='TFR (births per woman)',xlabel='Year',title=f'Singapore resident fertility, {START}–{END}',ylim=(0.6,1.8));fig.tight_layout();fig.savefig(RESULTS/'fertility_trend.png',dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(11,5.5))
    for j,mode in enumerate(['Levels','Annual changes','After removing linear trends']):
        t=associations[associations['mode'].eq(mode)].set_index('variable').reindex(FEATURES)
        ax.barh(np.arange(6)+(j-1)*0.24,t.correlation,height=.23,label=mode,color=['#073B4C','#B64B35','#8AA3AD'][j])
    ax.set_yticks(range(6),[LABELS[x] for x in FEATURES]);ax.axvline(0,color='gray',lw=.8);ax.set(xlim=(-1,1),xlabel='Pearson correlation with TFR',title='How much survives after accounting for time trends?');ax.legend(loc='lower left',fontsize=9);fig.tight_layout();fig.savefig(RESULTS/'associations.png',dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,4.5))
    agecols=['asfr_20_24','asfr_25_29','asfr_30_34','asfr_35_39','asfr_40_44']
    for c in agecols:ax.plot(d.index,d[c],label=c.replace('asfr_','').replace('_','–'))
    ax.set(ylabel='Births per 1,000 women in age group',xlabel='Year',title='Age-specific fertility patterns');ax.legend(title='Age');fig.tight_layout();fig.savefig(RESULTS/'age_specific_fertility.png',dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,4.5))
    for name in ['actual','persistence','linear_trend','ridge']:ax.plot(predictions.year,predictions[name],marker='o',label=name.replace('_',' ').title())
    ax.set(ylabel='TFR (births per woman)',xlabel='Target year',title='One-year-ahead retrospective backtest');ax.set_xticks(predictions.year);ax.legend();fig.tight_layout();fig.savefig(RESULTS/'backtest.png',dpi=180);plt.close(fig)
    print(json.dumps(summary,indent=2));print(scores.to_string(index=False))


if __name__=='__main__':main()
