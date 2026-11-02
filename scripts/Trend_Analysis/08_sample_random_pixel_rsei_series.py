# -*- coding: utf-8 -*-
"""
Pixel-level sensitivity of Mann-Kendall significance to tie correction and
serial autocorrelation (Hamed & Rao 1998), on a random sample of pixels per capital.
New for Review (2026). Part A (this file) draws N_PIX random points inside the
official IBGE municipal polygon of each capital (Capitais.shp) and extracts the annual RSEI series at those points; Part B
(09_trend_sensitivity_hamed_rao_autocorrelation.py) runs the statistics locally with pymannkendall.
Output: out_S3_pixel_samples.csv
"""
import sys
import os
import csv
import ee
import time
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
import gee_init_and_rsei_assets as C
import municipal_boundaries as MG

N_PIX = 1000
SEED = 42
OUT = 'out_S3_pixel_samples.csv'

C.init()
col, ids = C.load_merged_collection()
muns = C.municipalities(col)
GEOMS = MG.ee_geometries()

rows = []
for i, mun in enumerate(muns, 1):
    geom = GEOMS[mun]
    pts = ee.FeatureCollection.randomPoints(geom, N_PIX, SEED)
    ic = col.filter(ee.Filter.eq('NM_MUN', mun)).sort('ANO')
    years = ic.aggregate_array('ANO').getInfo()
    def one(y):
        img = ee.Image(ic.filter(ee.Filter.eq('ANO', y)).first()).select('RSEI')
        for attempt in range(6):
            try:
                return y, img.reduceRegions(pts, ee.Reducer.first(), 30, tileScale=4).aggregate_array('first').getInfo()
            except Exception as e:
                time.sleep(20 * (attempt + 1))
        raise RuntimeError(f'failed {mun} {y}')
    n_ok = 0
    with ThreadPoolExecutor(max_workers=1) as ex:
        for y, vals in ex.map(one, years):
            for k, v in enumerate(vals):
                rows.append({'NM_MUN': mun, 'pixel': k, 'ANO': int(y), 'RSEI': v})
            n_ok += 1
    print(f'[{i}/{len(muns)}] {mun}: {n_ok} years x {N_PIX} points', flush=True)
    with open(OUT, 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=['NM_MUN', 'pixel', 'ANO', 'RSEI'])
        w.writeheader()
        w.writerows(rows)
print('done', flush=True)
