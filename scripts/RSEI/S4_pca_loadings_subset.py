# -*- coding: utf-8 -*-
"""
S4 - PC1 loadings and explained variance of the per-capital, per-year PCA.
New for Review (2026). Re-executes the normalisation and PCA steps of the
original processing script (NEW_RSEI_2026_Luana_v3.py; functions copied verbatim
into rsei_core.py) for every capital in three reference years (1985, 2005, 2025), and records the
eigenvalues (variance explained) and the PC1 loadings on the four normalised
components. Large polygons that time out at 30 m are recomputed at 90 m
(the scale used is recorded). Output: out_S4_pca_loadings.csv (Table S4).
"""
import sys
import csv
import ee
import os
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, '.')
import ee_common as C
import rsei_core as R

C.init()
col, ids = C.load_merged_collection()
muns = C.municipalities(col)
YEARS = [1985, 2005, 2025]
IC = ee.ImageCollection(C.LANDSAT_IC)
SCALE, TS = 30, 4
FIELDS = ['NM_MUN', 'ANO', 'scale_m', 'eig1', 'eig2', 'eig3', 'eig4', 'PC1_var_explained_pct',
          'load_nNDVI', 'load_nWET', 'load_nNDSI_inv', 'load_nLST_inv']

rows = []
done = set()
if os.path.exists('out_S4_pca_loadings.csv'):
    with open('out_S4_pca_loadings.csv', encoding='utf-8') as fh:
        for r in csv.DictReader(fh):
            if r['eig1']:
                rows.append(r)
                done.add((r['NM_MUN'], int(r['ANO'])))


def one(task, scale=SCALE):
    mun, y = task
    row = {k: None for k in FIELDS}
    row.update({'NM_MUN': mun, 'ANO': y, 'scale_m': scale})
    SCALE_ = scale
    try:
        first = ee.Image(col.filter(ee.Filter.eq('NM_MUN', mun)).first())
        region = first.geometry()
        start = ee.Date.fromYMD(y, 1, 1)
        annual = IC.filterDate(start, start.advance(1, 'year')).median().clip(region)
        annual = R.fill_thermal_gaps(annual, region, SCALE_, TS)
        annual = R.add_indices(annual, y)
        stack = ee.Image.cat([
            R.min_max_norm(annual, 'NDVI', region, SCALE_, False, TS),
            R.min_max_norm(annual, 'WET', region, SCALE_, False, TS),
            R.min_max_norm(annual, 'NDSI', region, SCALE_, True, TS),
            R.min_max_norm(annual, 'LST', region, SCALE_, True, TS)]).rename(['n_NDVI', 'n_WET', 'n_NDSI', 'n_LST'])
        covar = stack.toArray().reduceRegion(ee.Reducer.centeredCovariance(), region, SCALE_, maxPixels=1e13, bestEffort=True, tileScale=TS)
        info = ee.Array(covar.get('array')).eigen().getInfo()
        evals = [r[0] for r in info]
        tot = sum(evals)
        pc1 = info[0]
        row.update({'eig1': evals[0], 'eig2': evals[1], 'eig3': evals[2], 'eig4': evals[3],
                    'PC1_var_explained_pct': 100 * evals[0] / tot, 'load_nNDVI': pc1[1], 'load_nWET': pc1[2],
                    'load_nNDSI_inv': pc1[3], 'load_nLST_inv': pc1[4]})
        print(f'{mun} {y}: PC1 {100*evals[0]/tot:.1f}% loads {pc1[1]:.3f} {pc1[2]:.3f} {pc1[3]:.3f} {pc1[4]:.3f}', flush=True)
    except Exception as e:
        print(f'{mun} {y} @ {scale} m: ERROR {str(e)[:100]}', flush=True)
        if scale < 90:
            return one(task, scale=90)
    return row


tasks = [(m, y) for m in muns for y in YEARS if (m, y) not in done]
with ThreadPoolExecutor(max_workers=1) as ex:
    for row in ex.map(one, tasks):
        rows.append(row)
        with open('out_S4_pca_loadings.csv', 'w', newline='', encoding='utf-8') as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)
print('done', flush=True)
