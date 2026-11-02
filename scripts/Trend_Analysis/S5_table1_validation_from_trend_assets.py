# -*- coding: utf-8 -*-
"""
S5 - Independent recomputation of Table 1 from the trend assets.
New for Review (2026). Reads the per-capital trend images produced by the
original trend notebook (NEW_Trends_RSEI_2026_Luana_V3_multiplos_assets.ipynb,
bands RSEI_tau, RSEI_p_value, RSEI_sen_slope, RSEI_mean, RSEI_median, RSEI_stdDev)
and computes, at 30 m, the share of the municipal area with a statistically
significant negative trend (degradation: tau < 0 and p <= 0.05), after clipping
the products to the official IBGE municipal boundary (Capitais.shp), significant
positive trend (improvement: tau > 0 and p <= 0.05) and no significant trend
(p > 0.05), plus the shares of negative, null and positive tau regardless of
significance (the three classes of the 'RSEI trend' maps). Also records the number of annual observations used (property
n_images / years), the mean Sen's slope and summary statistics.
Output: out_S5_table1_recomputed.csv
"""
import sys
import os
import csv
import ee
sys.path.insert(0, '.')
import ee_common as C
import municipal_geometries as MG

TREND_ROOT = os.environ.get('TREND_ROOT', 'projects/rnvuefsppgm/assets/RSEI_TRENDS_2026_new_new')
P = 0.05

C.init()
ids = C.list_images(TREND_ROOT)
GEOMS = MG.ee_geometries()
print(len(ids), 'trend images', flush=True)
rows = []
for i, aid in enumerate(sorted(ids), 1):
    img = ee.Image(aid)
    mun_name = img.get('municipio').getInfo()
    region = GEOMS[mun_name]
    img = img.clip(region)
    tau = img.select('RSEI_tau')
    p = img.select('RSEI_p_value')
    deg = tau.lt(0).And(p.lte(P))
    imp = tau.gt(0).And(p.lte(P))
    nsig = p.gt(P).Or(tau.eq(0))
    valid = tau.mask()
    px = ee.Image.pixelArea().divide(1e6)
    area = ee.Image.cat([px.updateMask(deg).rename('deg'), px.updateMask(imp).rename('imp'),
                         px.updateMask(nsig).rename('nsig'), px.updateMask(valid).rename('tot'),
                         px.updateMask(tau.lt(0)).rename('neg'), px.updateMask(tau.eq(0)).rename('zero'),
                         px.updateMask(tau.gt(0)).rename('pos')])
    a = area.reduceRegion(ee.Reducer.sum(), region, 30, maxPixels=1e13, tileScale=4)
    st = img.select(['RSEI_sen_slope', 'RSEI_tau', 'RSEI_mean', 'RSEI_median', 'RSEI_stdDev']).reduceRegion(
        ee.Reducer.mean().combine(ee.Reducer.median(), sharedInputs=True), region, 30, maxPixels=1e13, tileScale=4)
    sig_share = p.lte(P).reduceRegion(ee.Reducer.mean(), region, 30, maxPixels=1e13, tileScale=4)
    d = ee.Dictionary(a).combine(st).combine(sig_share).combine(
        {'n_images': img.get('n_images'), 'years': img.get('years'), 'municipio': img.get('municipio'),
         'source_asset': img.get('source_asset')}).getInfo()
    tot = d['tot']
    row = {'asset': aid.split('/')[-1], 'municipio': d.get('municipio'), 'n_images': d.get('n_images'),
           'years': d.get('years'), 'area_km2_valid': tot,
           'degradation_pct': 100 * d['deg'] / tot, 'no_significant_trend_pct': 100 * d['nsig'] / tot,
           'improvement_pct': 100 * d['imp'] / tot, 'share_p_le_0.05': d.get('RSEI_p_value'),
           'tau_negative_pct': 100 * d['neg'] / tot, 'tau_zero_pct': 100 * d['zero'] / tot,
           'tau_positive_pct': 100 * d['pos'] / tot,
           'sen_slope_mean': d.get('RSEI_sen_slope_mean'), 'sen_slope_median': d.get('RSEI_sen_slope_median'),
           'tau_mean': d.get('RSEI_tau_mean'), 'RSEI_mean_of_means': d.get('RSEI_mean_mean'),
           'RSEI_median_of_medians': d.get('RSEI_median_median'), 'RSEI_stdDev_mean': d.get('RSEI_stdDev_mean'),
           'source_asset': d.get('source_asset')}
    rows.append(row)
    print(f"[{i}/{len(ids)}] {row['municipio']}: n={row['n_images']} deg={row['degradation_pct']:.2f} "
          f"nsig={row['no_significant_trend_pct']:.2f} imp={row['improvement_pct']:.2f} sen={row['sen_slope_mean']}", flush=True)
    with open('out_S5_table1_recomputed.csv', 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
print('done', flush=True)
