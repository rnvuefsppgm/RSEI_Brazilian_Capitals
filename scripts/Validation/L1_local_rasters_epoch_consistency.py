# -*- coding: utf-8 -*-
"""
L1 - Temporal consistency of the exported five-yearly RSEI GeoTIFFs (local check).
New for Review (2026). For every capital, reads the RSEI rasters exported for
1985, 1990, ..., 2025 (files/rsei - 5 anos/*_RSEI_only.tif), computes the
municipal mean/median and the pixel-wise Pearson correlation between
consecutive epochs. A strongly negative correlation would indicate a sign
inversion of the index between years. Output: out_L1_epoch_stats.csv
Usage: python L1_local_rasters_epoch_consistency.py <folder_with_tifs>
"""
import sys
import os
import re
import glob
import csv
import numpy as np
import rasterio

folder = sys.argv[1] if len(sys.argv) > 1 else os.path.join('..', '..', '..', '..', 'files', 'rsei - 5 anos')
files = sorted(glob.glob(os.path.join(folder, '*_RSEI_only.tif')))
by_city = {}
for f in files:
    m = re.match(r'(.+)_RSEI_(\d{4})_RSEI_only\.tif$', os.path.basename(f))
    if m:
        by_city.setdefault(m.group(1), {})[int(m.group(2))] = f

rows = []
for city, d in sorted(by_city.items()):
    prev = None
    for y in sorted(d):
        with rasterio.open(d[y]) as src:
            a = src.read(1).astype('float64')
            nod = src.nodata
        a[(a == nod) | ~np.isfinite(a)] = np.nan if nod is not None else a[~np.isfinite(a)]
        valid = np.isfinite(a)
        row = {'city': city, 'year': y, 'n_valid': int(valid.sum()),
               'mean': float(np.nanmean(a)), 'median': float(np.nanmedian(a)),
               'sd': float(np.nanstd(a)), 'min': float(np.nanmin(a)), 'max': float(np.nanmax(a)),
               'r_with_previous_epoch': None, 'previous_year': None}
        if prev is not None and prev[1].shape == a.shape:
            both = valid & np.isfinite(prev[1])
            if both.sum() > 100:
                row['r_with_previous_epoch'] = float(np.corrcoef(a[both], prev[1][both])[0, 1])
                row['previous_year'] = prev[0]
        rows.append(row)
        prev = (y, a)
    print(city, [(r['year'], round(r['mean'], 3), None if r['r_with_previous_epoch'] is None else round(r['r_with_previous_epoch'], 2)) for r in rows if r['city'] == city], flush=True)

with open('out_L1_epoch_stats.csv', 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print('done')
