# Singapore fertility BI project

**One project flow:** preserved government exports → extracted CSVs → Python exploratory analysis → Streamlit dashboard → findings and policy presentation.

Primary outcome: resident total fertility rate (TFR). Common six-factor period: **2005–2025**. Crude birth rate is a separate secondary outcome. The six factors are candidate indicators, and statistical associations do not establish causes.

## The four deliverables

| Assignment requirement | Deliverable | Starting point |
| --- | --- | --- |
| i. Find sources and extract CSVs | Five source datasets, reproducible extraction, provenance and data dictionary | `01_data/SOURCE_GUIDE.md`, `extract_data.py` and `01_data/processed/` |
| ii. Exploratory analysis using Python | Guided notebook, scripts, effect tables, diagnostics and backtest | `02_analysis/exploration.ipynb`, `run_analysis.py`, `02_analysis/results/` |
| iii. Interactive Streamlit dashboard | Five tabs, filters, source traceability and CSV downloads | `03_dashboard/app.py` |
| iv. Present findings | Findings report, editable presentation and presenter guide | `04_findings/` |

## Run the project

Use Python 3.11 or later. In a terminal, change into this package folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python run_pipeline.py
python -m streamlit run 03_dashboard/app.py
```

Open the localhost URL printed by Streamlit. The dashboard uses packaged CSVs and saved model results, so it can run without internet access. All project paths resolve relative to the package, not to the developer's computer. You can launch the Python scripts by absolute path from another directory.

The notebook uses only Python. Run it in Jupyter or VS Code with the same environment. It locates the package from the notebook directory or package root. To regenerate extraction from a different copy of the supplied original files, use:

```bash
python extract_data.py --source-dir "/path/to/original/group project"
python run_pipeline.py
```

The original filenames must match the mapping in `project_config.py`. The five raw inputs are already packaged, so this step is optional.

## Consistent definitions

`project_config.py` owns the period, outcome, six-factor selection, units and source mapping. `analysis_core.py` owns the transformations and statistics, shared by the scripts and dashboard. `run_pipeline.py` extracts data, runs analysis and generates the report. The slide deck represents the delivered snapshot. If you replace sources, regenerate the deck before presenting revised results.

Six candidate factors: female general marriage rate, all-items CPI, accommodation CPI, education CPI, household liabilities/assets and rail network length. Accommodation CPI starts in 2005. Actual-rent CPI starts in 2015 and is supplementary, with earlier values missing by design. All six main factors are complete in the common analysis window.

CPI annual values require all 12 months. Balance sheets use Q4 because they measure stocks. There is no imputation. 2026 partial observations stay in the source histories and never enter the common annual analysis.

The model uses prior-year indicators and calendar year. Penalty tuning uses 2016–2020, and the expanding backtest uses 2021–2025. The model tab has a fixed evaluation window independent of EDA filters. Retrospective source revisions and publication delays prevent treating this as a real-time forecast.

## Project interpretation

TFR fell from 1.24 in 2015 to 0.87 in 2025. The full analysis measures associations for all six variables, not causal policy impacts. Marriage changes have the strongest annual-change association, but the full-sample adjusted q-value is approximately 0.0545. Several strong level correlations weaken or reverse in annual changes. The ridge backtest only slightly improves on persistence. Read the report's limitations before using estimates in a presentation.

Employment, direct affordability, childcare fees, work schedules and intentions are missing. The report names these gaps and proposes evaluation steps. It does not claim to have used healthcare records or identified five proven causes.

## Validation and submission

Run `python validate_project.py` to check the key data mappings, annual aggregation, row counts, source hashes and analysis consistency. The dashboard was exercised using Streamlit's AppTest across outcomes, analysis methods, pandemic filtering and a short window. The presentation has editable charts and speaker notes.

`requirements.txt` gives compatible dependency ranges. `tested_versions.txt` records the environment used to validate this package. The original project folder remains unchanged. Redundant numbered CSVs, prior merge outputs and old charts are excluded from this consolidated package.

No claim of affiliation with McKinsey & Company is made. This is an independent consulting-style academic project.
