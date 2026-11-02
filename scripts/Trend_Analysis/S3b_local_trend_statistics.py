# -*- coding: utf-8 -*-
"""
S3b - Local trend statistics on the sampled pixel series and on the municipal
mean series (Part B of S3). New for Review (2026).
For every sampled pixel series (out_S3_pixel_samples.csv) and every municipal
annual mean series (out_S1_city_annual_series.csv) computes:
  * the original Mann-Kendall test as implemented in the Earth Engine notebook
    (variance without tie correction, continuity-corrected Z, two-tailed p);
  * the tie-corrected Mann-Kendall test (pymannkendall.original_test);
  * the Hamed & Rao (1998) variance-corrected test (pymannkendall.hamed_rao_modification_test);
  * the lag-1 autocorrelation of the series and of its Sen-detrended residuals;
  * Sen's slope.
Outputs: out_S3b_pixel_results.csv, out_S3b_pixel_summary_by_city.csv,
         out_S3b_city_series_results.csv
"""
import csv
import math
import numpy as np
import pandas as pd
import pymannkendall as mk
from scipy.stats import norm


def mk_gee(y):
    """Mann-Kendall exactly as in the original Earth Engine implementation."""
    y = np.asarray(y, float)
    n = len(y)
    s = 0
    for i in range(n - 1):
        d = y[i + 1:] - y[i]
        s += int((d > 0).sum()) - int((d < 0).sum())
    var = n * (n - 1) * (2 * n + 5) / 18.0
    z = (s - 1) / math.sqrt(var) if s > 0 else ((s + 1) / math.sqrt(var) if s < 0 else 0.0)
    p = 2 * (1 - norm.cdf(abs(z)))
    tau = s / (n * (n - 1) / 2.0)
    return s, var, z, p, tau


def lag1(x):
    x = np.asarray(x, float)
    x = x - x.mean()
    if len(x) < 3 or (x ** 2).sum() == 0:
        return np.nan
    return float((x[:-1] * x[1:]).sum() / (x ** 2).sum())


def analyse(years, vals):
    years = np.asarray(years, float)
    vals = np.asarray(vals, float)
    ok = np.isfinite(vals)
    years, vals = years[ok], vals[ok]
    n = len(vals)
    if n < 10:
        return None
    s, var, z, p, tau = mk_gee(vals)
    o = mk.original_test(vals)
    h = mk.hamed_rao_modification_test(vals)
    slope = o.slope  # pymannkendall Sen's slope (per time step; annual series)
    resid = vals - slope * (years - years[0])
    return {'n': n, 'S': s, 'tau_gee': tau, 'Z_gee': z, 'p_gee': p, 'p_ties': o.p, 'Z_ties': o.z,
            'p_hamed_rao': h.p, 'Z_hamed_rao': h.z, 'sen_slope': slope,
            'lag1_series': lag1(vals), 'lag1_residuals': lag1(resid)}


# ---------------- pixel samples ----------------
px = pd.read_csv('out_S3_pixel_samples.csv')
res = []
for (mun, pix), g in px.groupby(['NM_MUN', 'pixel']):
    g = g.sort_values('ANO')
    r = analyse(g['ANO'].values, g['RSEI'].values)
    if r:
        r.update({'NM_MUN': mun, 'pixel': pix})
        res.append(r)
pr = pd.DataFrame(res)
pr.to_csv('out_S3b_pixel_results.csv', index=False)

summ = []
for mun, g in pr.groupby('NM_MUN'):
    sig_gee = g['p_gee'] <= 0.05
    sig_ties = g['p_ties'] <= 0.05
    sig_hr = g['p_hamed_rao'] <= 0.05
    summ.append({'NM_MUN': mun, 'n_pixels': len(g), 'median_n_years': g['n'].median(),
                 'sig_pct_original': 100 * sig_gee.mean(), 'sig_pct_tie_corrected': 100 * sig_ties.mean(),
                 'sig_pct_hamed_rao': 100 * sig_hr.mean(),
                 'sig_deg_pct_original': 100 * (sig_gee & (g['tau_gee'] < 0)).mean(),
                 'sig_deg_pct_hamed_rao': 100 * (sig_hr & (g['tau_gee'] < 0)).mean(),
                 'sig_imp_pct_original': 100 * (sig_gee & (g['tau_gee'] > 0)).mean(),
                 'sig_imp_pct_hamed_rao': 100 * (sig_hr & (g['tau_gee'] > 0)).mean(),
                 'pct_lost_after_hamed_rao': 100 * (sig_gee & ~sig_hr).mean(),
                 'median_lag1_series': g['lag1_series'].median(), 'median_lag1_residuals': g['lag1_residuals'].median(),
                 'pct_lag1_resid_gt_0.3': 100 * (g['lag1_residuals'] > 0.3).mean(),
                 'median_sen_slope': g['sen_slope'].median()})
pd.DataFrame(summ).to_csv('out_S3b_pixel_summary_by_city.csv', index=False)

# ---------------- municipal mean series ----------------
s1 = pd.read_csv('out_S1_city_annual_series.csv')
cres = []
for mun, g in s1.groupby('NM_MUN'):
    g = g.sort_values('ANO')
    r = analyse(g['ANO'].values, g['RSEI_mean'].values)
    r.update({'NM_MUN': mun, 'mean_RSEI_1985_2025': g['RSEI_mean'].mean()})
    cres.append(r)
pd.DataFrame(cres).to_csv('out_S3b_city_series_results.csv', index=False)
print(pd.DataFrame(summ)[['NM_MUN', 'sig_pct_original', 'sig_pct_hamed_rao', 'pct_lost_after_hamed_rao', 'median_lag1_residuals']].round(2).to_string())
print(pd.DataFrame(cres)[['NM_MUN', 'n', 'tau_gee', 'p_gee', 'p_hamed_rao', 'sen_slope', 'lag1_residuals']].round(4).to_string())
