"""Generate the narrative from saved analysis outputs, preserving numeric consistency."""
import json
import pandas as pd
from project_config import ROOT, DATA, RESULTS, FEATURES, LABELS, UNITS


def markdown_table(frame):
    # Avoid an optional tabulate dependency.
    columns=list(frame.columns)
    lines=['| '+' | '.join(columns)+' |','| '+' | '.join(['---']*len(columns))+' |']
    for row in frame.itertuples(index=False,name=None):lines.append('| '+' | '.join(map(str,row))+' |')
    return '\n'.join(lines)


def main():
    s=json.loads((RESULTS/'summary.json').read_text())
    d=pd.read_csv(DATA/'analysis_dataset.csv',index_col='year')
    a=pd.read_csv(RESULTS/'associations.csv')
    wide=a.pivot(index='variable',columns='mode',values='correlation').reindex(FEATURES)
    correlations=pd.DataFrame({'Factor':[LABELS[x] for x in FEATURES],
        'Levels r':wide['Levels'].map(lambda x:f'{x:+.3f}').to_list(),
        'Annual changes r':wide['Annual changes'].map(lambda x:f'{x:+.3f}').to_list(),
        'Detrended r':wide['After removing linear trends'].map(lambda x:f'{x:+.3f}').to_list()})
    effects=a[a['mode'].eq('Annual changes')].set_index('variable').reindex(FEATURES)
    effect_table=pd.DataFrame({'Factor':[LABELS[x] for x in FEATURES],
        'Factor unit':[UNITS[x] for x in FEATURES],
        'Slope':[f'{x:+.4f}' for x in effects.slope],
        'Approx. 95% HAC interval':[f'[{r.ci_low:+.4f}, {r.ci_high:+.4f}]' for r in effects.itertuples()],
        'BH q':[f'{x:.4f}' for x in effects.bh_q]})
    scores=pd.read_csv(RESULTS/'backtest_scores.csv')
    scoretable=scores[['model','n','mae','rmse']].copy()
    for c in ['mae','rmse']:scoretable[c]=scoretable[c].map(lambda x:f'{x:.4f}')
    marriage=effects.loc['female_marriage_rate']
    sens=pd.read_csv(RESULTS/'pandemic_sensitivity.csv').set_index('variable')
    mae=scores.set_index('model').mae
    gain=(1-mae['ridge']/mae['persistence'])*100
    age=pd.DataFrame({'Age group':[x.replace('asfr_','').replace('_','–') for x in ['asfr_20_24','asfr_25_29','asfr_30_34','asfr_35_39','asfr_40_44']]})
    cols=['asfr_20_24','asfr_25_29','asfr_30_34','asfr_35_39','asfr_40_44']
    age['2015']=d.loc[2015,cols].to_list();age['2025']=d.loc[2025,cols].to_list()
    age['Change (%)']=[f'{(d.loc[2025,x]/d.loc[2015,x]-1)*100:+.1f}' for x in cols]
    sources=json.loads((DATA/'source_manifest.json').read_text())
    source_lines='\n'.join(f'| {v["title"]} | {v["agency"]} | [{v["table"]}]({v["url"]}) | {v["frequency"]} |' for v in sources)
    report=f'''# Singapore fertility: evidence and policy priorities

Prepared 12 October 2026. Historical source snapshots through 2025.

## 1. Executive recommendation

Prioritise investigation of marriage and first-birth barriers, alongside evaluation of housing and caregiving support. Use this project to identify questions and target evidence collection. It does not establish causal policy effects.

Singapore's resident TFR fell from **{s['tfr_2015']:.2f} in 2015 to {s['tfr_latest']:.2f} in 2025**, a **{abs(s['decade_pct_change']):.1f}% decline**. The 2025 crude birth rate was **{s['crude_birth_rate_latest']:.1f} per 1,000 residents**, and resident live births numbered **{s['resident_live_births_latest']:,}**. These are different measures and are never used interchangeably.

Our six-factor analysis covers **2005–2025**, with **21 annual observations** and **20 annual changes**. Strong correlations in levels often reflect time trends. Marriage formation has the largest absolute annual-change correlation of the six factors (**r={marriage.correlation:+.3f}**). Its multiplicity-adjusted result is borderline (**q={marriage.bh_q:.4f}**), so the evidence supports further investigation rather than a proven explanation.

## 2. Project question and success criteria

**Question:** Which observed social and economic indicators are associated with declining Singapore fertility, and what further evidence would help government prioritise interventions?

**Specific:** Screen six preselected candidate indicators and inspect age-specific fertility patterns.

**Measurable:** Quantify all six using correlations, slopes and uncertainty intervals. Report results in levels, annual changes and after removing linear trends. Compare a predictive model with simple baselines using a chronological backtest. Quantified statistical association is the achievable interpretation of “impact” with these aggregate observational data.

**Achievable:** Reuse five supplied government export snapshots. Provide reproducible Python extraction, analysis and an interactive Streamlit dashboard. Individual healthcare records and socio-economic survey microdata have not been obtained.

**Relevant:** Support questions about family formation, housing services, family costs and financial resilience. Do not assume the candidate proxies directly measure young families' constraints.

**Time-bound:** Deliver the evidence package now and propose a 12-month programme to strengthen data access, design evaluations and assess early programme uptake. Fertility responses require monitoring beyond month 12.

## 3. Deliverable 1: source data and reproducible CSV extraction

| Dataset | Agency | Official series | Source frequency |
| --- | --- | --- | --- |
{source_lines}

Four workbooks preserve table IDs, source update dates and an export date of 15 September 2026. The household balance-sheet CSV lacks embedded download metadata. We identified its official non-seasonally-adjusted series as M700981 using the official dataset title and matching 2026 Q2 Assets of 3,826,110.2. See the [official mirror](https://data.gov.sg/datasets/d_7cb92e23305b005daf1cebd9774516d4/view). The manifest distinguishes supplied snapshot provenance from this external verification.

**Extraction and alignment rules**

1. Find the workbook's `Data Series` header and select named rows. Strip formatting and convert numeric strings without inventing missing values.
2. Preserve annual birth, marriage and transport observations in chronological CSVs.
3. Calculate annual CPI as the mean of **12 observed months** for each series and year. Mark incomplete years unavailable. This follows [DOS's annual CPI methodology](https://www.singstat.gov.sg/find-data/explore-data-themes/economy-prices/consumer-price-index/our-data-explained).
4. Treat household balance-sheet amounts as stocks. Select **Q4** and calculate liabilities / assets × 100. Do not sum or average stocks. [DOS describes these as end-of-period measures](https://www.singstat.gov.sg/find-data/explore-data-themes/economy-prices/household-sector-economic-indicators/our-data-explained).
5. Align on year. The common six-factor window begins in 2005 because accommodation CPI starts then. Exclude 2026 because fertility observations and complete calendar-year CPI are unavailable.
6. Retain actual-rent CPI as supplementary data from 2015. Its earlier blanks are deliberate. Do not impute them or use that series in the common six-factor model.

The package includes five annual source CSVs, monthly CPI, quarterly household finances, the joined analysis dataset, a data dictionary, a coverage report and a hash-based source manifest. No numbered duplicate copies enter the pipeline.

## 4. Analytical framework and interpretation

The primary outcome is **resident TFR**, the hypothetical number of births per woman under a given year's age-specific fertility rates. It is a period measure, not a count of babies or a prediction of completed family size. [Official definition](https://www.population.gov.sg/media-centre/how-is-the-tfr-calculated/).

| Factor | Hypothesis to investigate | Measurement limitation |
| --- | --- | --- |
| Female general marriage rate | Family formation may precede childbearing | Does not measure marriage age, first-birth timing or fertility within marriage |
| All-items CPI | Price pressures may affect perceived family costs | No income denominator, does not measure affordability |
| Accommodation CPI | Housing services costs may affect family formation | Includes imputed rents and maintenance, excludes purchase prices |
| Education CPI | Anticipated education costs may affect plans | Broad education index, does not isolate childcare fees |
| Liabilities / assets | Financial resilience may influence family plans | National aggregate ratio, excludes debt-service burden and age segmentation |
| Rail length | Infrastructure may relate to access and urban development | Does not measure commute time, local access or transport affordability |

The six candidates follow the available policy themes and source coverage. We do not search dozens of columns and present whichever correlations are largest. Household size is excluded from the predictor list because it partly reflects fertility itself. Employment, household income, childcare fees, housing purchase affordability, partnership preferences and work hours are important data gaps.

**Method:** descriptive trends, age-specific comparisons, Pearson correlations, separate one-factor regressions, annual absolute differences, linear detrending, pandemic sensitivity, crude-birth-rate sensitivity and one-year lag associations. The regressions estimate associations, with approximate 95% HAC intervals allowing autocorrelation at lag 1. BH q-values adjust the six slope tests within each analysis mode. Pearson p-values in the CSV assume independent pairs and are secondary. Detrended intervals omit uncertainty from estimating trends. The different modes and sensitivity checks are exploratory and do not establish a causal ranking.

## 5. Deliverable 2: Python exploratory findings

### Finding A. Lower fertility at younger ages is not fully offset at older ages

![Fertility trend](../02_analysis/results/fertility_trend.png)

Age-specific rates are births per 1,000 women in each age group:

{markdown_table(age)}

The 20–24 and 25–29 rates fell markedly from 2015 to 2025. Fertility among women aged 30–34 also fell. The small rise among women aged 40–44 did not offset those declines in the period TFR. Aggregate age patterns are compatible with timing shifts, but cohort or linked records are needed to distinguish postponement from permanently fewer births.

### Finding B. Long-term correlations give a misleading causal story

{markdown_table(correlations)}

![Association comparison](../02_analysis/results/associations.png)

General prices, education prices and rail length have strong negative correlations in levels. Their annual-change correlations are weak or reverse sign. Rail length's level correlation is about −0.87, while its annual-change correlation is about −0.04. This provides no basis for concluding that transport expansion reduces fertility.

The debt-to-assets ratio has a strong positive level correlation with TFR. Both declined over much of the period. Its annual-change correlation is weak. This finding cannot support the claim that higher aggregate debt caused lower births. A growing asset denominator can reduce the ratio, and aggregate household finances can differ from young families' experiences.

### Finding C. Marriage formation merits further investigation

Annual marriage-rate changes correlate positively with annual TFR changes (**r={marriage.correlation:+.3f}**). After excluding 2020–2021 and changes that cannot be calculated across the gap, the correlation is **r={sens.loc['female_marriage_rate','correlation']:+.3f}**, with **17 paired changes**. The crude-birth-rate sensitivity also shows a positive annual-change correlation (about +0.45).

The full-sample annual-change slope is **{marriage.slope:+.4f} births per woman** for a one-unit marriage-rate change, where the unit is one marriage per 1,000 unmarried resident women aged 15–49. This is a separate bivariate association. The same-year design does not establish the sequence from marriage to birth, and confounding remains.

### Quantifying all six variables

Outcome: annual TFR change, in births per woman. Predictor: annual absolute change in the listed unit. Twenty paired years per regression.

{markdown_table(effect_table)}

None of the six full-sample annual-change slope tests has **BH q < 0.05**. Marriage is closest. A conventional unadjusted interval excluding zero does not override the multiplicity-adjusted conclusion. The pandemic sensitivity strengthens the marriage result, but cannot replace the prespecified full-sample finding.

## 6. Predictive exercise: only a small improvement over persistence

Use previous-year predictor values plus calendar year in a ridge model. Standardise each fold using its training data only. Select the penalty from 0.1, 1, 10, 100 and 1,000 using expanding validation years 2016–2020. The chosen penalty is **{s['ridge_alpha']:g}**. Refit before each test year from 2021 through 2025.

Persistence predicts last year's TFR. The linear-trend baseline extrapolates a straight line fitted to prior outcomes. No random train/test split or holdout tuning occurs.

{markdown_table(scoretable)}

![Predictive backtest](../02_analysis/results/backtest.png)

The ridge model reduces MAE versus persistence by only **{gain:.1f}%**, an absolute improvement of **{mae['persistence']-mae['ridge']:.4f} births per woman**. The 2025 ridge prediction is approximately 0.981 versus actual TFR of 0.870. Five test years and revised source data do not establish reliable performance. This is a retrospective lagged-input exercise: source publication delays and real-time data vintages are not reconstructed. We provide no causal scenario simulator or claimed births generated by intervention.

## 7. Deliverable 3: interactive Streamlit dashboard

The dashboard supports year selection, outcome selection, six candidate factors, association methods and a pandemic exclusion toggle. Its five tabs cover fertility trends, factor exploration, fixed model backtesting, policy priorities and source traceability. Users can download the complete or filtered dataset.

All EDA charts and statistics react to the selected window and method. The backtest always uses the documented TFR evaluation window of 2021–2025, and its tab explicitly says sidebar filters apply to EDA only. Source definitions and limits appear beside the relevant factor. Small selections display an insufficient-observations message instead of fabricated estimates.

## 8. Deliverable 4: policy recommendations and presentation

### Decision 1. Investigate marriage and first-birth transitions

**Evidence:** positive annual-change marriage association, with sensitivity support and borderline adjusted full-sample significance.

**Proposed action:** NPTD and research partners should combine marriage-age distributions, stated intentions and first-birth transitions to identify bottlenecks. Address constraints without attributing responsibility for fertility to women alone.

**Evaluation:** follow consenting cohorts or use authorised linked administrative data. Separate partnership formation, timing of first birth and subsequent births. Track intentions and transition rates before claiming a fertility response.

### Decision 2. Evaluate housing and caregiving support with direct measures

**Evidence:** the supplied CPI proxies do not consistently support a negative cost effect in annual changes. They also omit income, purchase affordability and net childcare fees.

**Proposed action:** MND/HDB, MSF/ECDA and MOM should evaluate support for young families using direct data on income-adjusted costs, housing waiting times, childcare availability, work schedules and parental leave use.

**Evaluation:** predefine eligible and comparison groups, baseline trends, take-up and burden measures. Where feasible, randomise pilot outreach or implementation timing. Otherwise use credible comparison groups and check parallel trends. Document privacy and access arrangements for linked data.

### Decision 3. Segment financial constraints before designing assistance

**Evidence:** the national liabilities/assets ratio is not a young-family debt burden measure.

**Proposed action:** obtain age- and income-specific debt-service ratios, savings and housing expenses. Test whether financial pressure predicts marriage or birth transitions within comparable groups.

**Evaluation:** measure household burden and eligibility-specific outcomes. Do not allocate budgets based on the aggregate slope in this project.

### Decision 4. Evaluate transport on access outcomes

**Evidence:** the rail-length association largely disappears in annual changes.

**Proposed action:** assess commute time and access to work, childcare and family support at local level before connecting transport interventions to fertility.

**Evaluation:** use local travel times and accessibility measures. Rail kilometres alone cannot estimate an intervention's fertility effect.

### Social and economic implications

Persistent low fertility can change future workforce supply, family care responsibilities and demand for schools, childcare and age-related services. These are planning implications, not quantified impacts from this dataset. A demographic projection would require population age structure, mortality, migration and cohort assumptions. Regional effects, fiscal costs, GDP impacts and dependency ratios have not been estimated here. The [NPTD's February 2026 discussion](https://www.population.gov.sg/media-centre/speech-by-deputy-prime-minister-gan-kim-yong-committee-of-supply-debate-2026/) provides the external population-policy context.

### Existing policy context

Singapore announced enhanced marriage and parenthood support in 2026, including child-related leave, financial help, caregiving and housing measures. Our recommendations focus on targeting and evaluating support rather than presenting those measures as new ideas. The historical data end in 2025, so they cannot evaluate the 2026 announcements. See [NPTD's September 2026 statement](https://www.population.gov.sg/media-centre/helping-singaporeans-start-and-raise-families-with-confidence/). Implementation details should be checked before any operational policy proposal.

## 9. Twelve-month implementation plan

| Period | Accountable lead (proposed) | Deliverable | Acceptance measure |
| --- | --- | --- | --- |
| Months 1–2 | NPTD with DOS and data owners | Agreed questions, definitions and access plan | Named owners, signed definitions, documented lawful access |
| Months 3–4 | Analytics team | Validated source refresh and dashboard | At least five variables, coverage audit and reproducible outputs |
| Months 5–6 | Relevant policy agencies | Pilot protocol and evaluation design | Predefined outcomes, baseline, comparison strategy and uptake targets |
| Months 7–9 | Delivery agencies and partners | Pilot rollout and public communication | Monthly take-up and delivery tracking against agreed targets |
| Months 10–12 | Evaluation team | Early evaluation and next-stage decision | Report uptake, costs, burden and feasibility with uncertainty |
| Beyond month 12 | NPTD and evaluation partners | Fertility follow-up | Follow marriage and birth transitions over a suitable longer horizon |

Strong government commitment requires an accountable sponsor. National alignment requires agency agreement on questions and definitions. Public adoption requires communication and uptake measurement. Reliable data requires named owners, source metadata, consistent units and refresh checks. Numeric programme adoption targets need baseline data and are not invented here.

## 10. Presentation storyline and live demonstration

The accompanying presentation follows the same sequence: decision question, source definitions, fertility decline, age patterns, trend-adjusted evidence, six-variable quantification, predictive limits, policy priorities and implementation plan. Speaker notes contain the relevant sources and explanation.

For the dashboard demonstration: select TFR and the full window; show age-specific trends; compare rail length in levels and annual changes; inspect the marriage scatter; exclude pandemic years; show the predictive baseline comparison; finish with source traceability and policy data gaps.

## 11. Limits and next data priorities

The analysis is observational, national and annual. It has a small sample, autocorrelation, related CPI series, omitted factors, possible reverse causality and uncertain birth-response lags. Detrending and first differences are diagnostics, not causal identification. The household finance source has no preserved original download timestamp. All source snapshots can be revised.

Priority additions: resident employment and work hours from MOM, income from DOS, housing prices and waiting times from HDB, net childcare fees and availability from ECDA, and marriage/parenthood intentions from NPTD surveys. Add them only after documenting units, coverage and relevance, then reassess model complexity and chronological validation.
'''
    (ROOT/'04_findings'/'findings_report.md').write_text(report)
    source_guide='''# Deliverable 1: source and extraction guide

The supplied government exports are preserved in `raw/`. Run `python extract_data.py` from the package root to recreate the CSVs. All source links, snapshot dates and SHA-256 hashes are in `processed/source_manifest.json`.

'''+report.split('## 3. Deliverable 1: source data and reproducible CSV extraction\n\n')[1].split('## 4.')[0]
    (ROOT/'01_data'/'SOURCE_GUIDE.md').write_text(source_guide)
    print('Generated findings report and source guide from the analysis outputs.')


if __name__=='__main__':main()
