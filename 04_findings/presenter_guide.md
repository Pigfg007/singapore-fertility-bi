# Presenter guide

Suggested duration: 12–15 minutes, plus questions. Use the editable slide deck and a short dashboard demonstration.

## Opening message

“Singapore's TFR fell almost 30% from 2015 to 2025. Our project screens six candidate indicators using government export snapshots. We find that several striking long-term correlations weaken when we analyse annual changes. Marriage formation merits further investigation, and direct data on housing, childcare and work are needed before estimating policy effects.”

## Presentation sequence

1. Explain the policy question and the difference between TFR, crude birth rate and birth counts.
2. Show the five data sources and the common 2005–2025 window. Explain annual CPI averages and Q4 balance-sheet stocks.
3. Describe the fertility decline and age-specific pattern.
4. Compare correlations in levels with annual changes. Use rail length as the clearest illustration of a shared trend.
5. Quantify all six factors. Explain slopes as statistical associations and report approximate uncertainty and adjusted q-values.
6. Explain why marriage formation deserves further study. Keep the borderline full-sample result alongside pandemic sensitivity.
7. Show the predictive backtest. The improvement over persistence is small and the model misses the 2025 decline.
8. Separate proposed policy evaluation from demonstrated effects. Identify direct data needs, owners and the 12-month plan.

## Dashboard demonstration (about 3 minutes)

Start with the full window, TFR and annual changes. Show fertility trends, then select rail length. Switch between Levels and Annual changes. Select marriage rate, inspect the scatter, and toggle the pandemic exclusion. Show that the backtest remains fixed at 2021–2025. Finish with source traceability and the CSV download.

## Likely questions

**Did you identify the causes of declining births?**

We identified associations and data gaps. National annual observations cannot separate all confounders or estimate intervention effects. We propose direct data collection and evaluation to investigate mechanisms.

**Why use TFR when the assignment says birth rate?**

TFR captures prevailing fertility rates across reproductive ages. Crude birth rate also reflects population structure. We use TFR consistently as the primary outcome and provide crude-birth-rate sensitivity.

**Why six variables and only 21 years?**

The variables represent available policy themes and satisfy the requirement to quantify at least five. Accommodation CPI begins in 2005, defining the shared window. We avoid imputation and a large model built from dozens of related columns.

**Does higher education cost cause fewer births?**

The negative level correlation weakens or reverses after addressing trends. The index also does not isolate childcare or household affordability. This project cannot estimate that causal effect.

**Is the marriage result statistically significant?**

The full-sample annual-change adjusted q-value is about 0.0545, above 0.05. An unadjusted interval excludes zero, and the pandemic sensitivity is stronger. We present the complete evidence as exploratory.

**How reliable is the model?**

The model's five-year MAE is about 0.0516 versus 0.0540 for persistence. The improvement is small, and five test years are insufficient for stable performance claims. The backtest uses revised snapshots, not real-time release vintages.

**What is actionable within 12 months?**

Agree source definitions, obtain direct measures, design pilots, track uptake and burden, and report early evaluation. Fertility outcomes need a longer follow-up. Existing 2026 policies should be evaluated rather than described as novel recommendations.
