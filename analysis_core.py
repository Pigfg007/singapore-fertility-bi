"""Shared statistical functions. All analysis runs in Python."""
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import pearsonr
from project_config import FEATURES, TARGET


def transform(frame, mode):
    frame = frame.sort_index().copy()
    if mode == 'Annual changes':
        # Reindex first so a missing year cannot become a multi-year 'annual' change.
        return frame.reindex(range(int(frame.index.min()), int(frame.index.max())+1)).diff()
    if mode == 'After removing linear trends':
        for col in frame:
            valid = frame[col].dropna()
            if len(valid) >= 3:
                fit = sm.OLS(valid.to_numpy(), sm.add_constant(valid.index.to_numpy(dtype=float))).fit()
                frame.loc[valid.index, col] = fit.resid
        return frame
    return frame


def association_table(frame, target=TARGET, features=FEATURES, mode='Levels'):
    transformed = transform(frame[[target]+features], mode)
    rows = []
    for feature in features:
        pair = transformed[[target, feature]].dropna()
        if len(pair) < 6 or pair[feature].nunique() < 2 or pair[target].nunique() < 2:
            continue
        r, p = pearsonr(pair[feature], pair[target])
        fit = sm.OLS(pair[target], sm.add_constant(pair[[feature]])).fit(cov_type='HAC', cov_kwds={'maxlags':1})
        lo, hi = fit.conf_int().loc[feature]
        rows.append(dict(variable=feature, mode=mode, n=len(pair), first_year=int(pair.index.min()),
            last_year=int(pair.index.max()), correlation=float(r), pearson_p=float(p),
            slope=float(fit.params[feature]), ci_low=float(lo), ci_high=float(hi), hac_p=float(fit.pvalues[feature]),
            slope_per_sd=float(fit.params[feature]*pair[feature].std(ddof=1))))
    result = pd.DataFrame(rows)
    if not result.empty:
        # Benjamini–Hochberg within the six comparisons in this mode.
        order = np.argsort(result.hac_p.to_numpy())
        ranked = result.hac_p.to_numpy()[order]
        adjusted = np.minimum.accumulate((ranked*len(ranked)/np.arange(1,len(ranked)+1))[::-1])[::-1]
        q = np.empty(len(ranked)); q[order] = np.minimum(adjusted,1)
        result['bh_q'] = q
    return result


def ridge_predict(train_x, train_y, test_x, alpha):
    means = train_x.mean(axis=0)
    scales = train_x.std(axis=0, ddof=0).replace(0,1)
    x = ((train_x-means)/scales).to_numpy()
    xt = ((test_x-means)/scales).to_numpy()
    y = train_y.to_numpy(); center = y.mean()
    coef = np.linalg.solve(x.T@x + alpha*np.eye(x.shape[1]), x.T@(y-center))
    return center+xt@coef


def backtest(frame):
    """One-year-ahead backtest. Previous year's predictor values only.

    Tune alpha using expanding validation windows ending by 2020. During 2021–25,
    refit using only data available before each target year. No holdout tuning.
    Annual source publication delays can exceed one year: this is a retrospective
    lagged-input exercise, not a real-time data-vintage forecast.
    """
    lagged = frame[FEATURES].reindex(range(int(frame.index.min()),int(frame.index.max())+1)).shift(1)
    lagged['calendar_year'] = lagged.index
    model = lagged.join(frame[[TARGET]]).dropna()
    xcols = FEATURES+['calendar_year']
    train = model.loc[model.index<=2020]
    validation_years = train.index[-5:]
    candidates = []
    for alpha in [0.1,1,10,100,1000]:
        errors = []
        for year in validation_years:
            before = train.loc[train.index<year]
            if len(before)<10: continue
            pred = ridge_predict(before[xcols],before[TARGET],train.loc[[year],xcols],alpha)[0]
            errors.append(abs(pred-train.loc[year,TARGET]))
        candidates.append(dict(alpha=alpha,validation_mae=float(np.mean(errors))))
    tuning = pd.DataFrame(candidates)
    alpha = float(tuning.sort_values(['validation_mae','alpha']).iloc[0].alpha)
    rows = []
    for year in range(2021,2026):
        if year not in model.index or year-1 not in frame.index: continue
        before = model.loc[model.index<year]
        prediction = ridge_predict(before[xcols],before[TARGET],model.loc[[year],xcols],alpha)[0]
        trend_data = frame.loc[frame.index<year,[TARGET]].dropna()
        trend = np.polyfit(trend_data.index.to_numpy(),trend_data[TARGET],1)
        rows.append(dict(year=year,actual=frame.loc[year,TARGET],
                         persistence=frame.loc[year-1,TARGET],linear_trend=np.polyval(trend,year),ridge=prediction))
    predictions = pd.DataFrame(rows)
    scores = []
    for name in ['persistence','linear_trend','ridge']:
        error = predictions[name]-predictions.actual
        scores.append(dict(model=name,n=len(error),mae=float(error.abs().mean()),rmse=float(np.sqrt((error**2).mean()))))
    return predictions,pd.DataFrame(scores),tuning,alpha
