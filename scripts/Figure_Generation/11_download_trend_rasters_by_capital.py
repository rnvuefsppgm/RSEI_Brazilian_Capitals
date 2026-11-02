# -*- coding: utf-8 -*-
"""
Download of the per-capital trend products for figure generation.
New for Review (2026). Retrieves, for each capital, the bands RSEI_tau,
RSEI_p_value, RSEI_mean, RSEI_median and RSEI_stdDev from the trend assets
produced by the original trend notebook, as GeoTIFF files. The export scale is
30 m whenever the municipality fits the per-request pixel limit of the Earth
Engine download service; larger municipalities are retrieved at the coarsest
multiple of 10 m that keeps the request below 4 million pixels (the scale used
is written to scale_used.csv and reported in the figure captions).
Usage: python 11_download_trend_rasters_by_capital.py <output_folder>
"""
import sys
import os
import math
import csv
import urllib.request
import ee
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
import gee_init_and_rsei_assets as C

TREND_ROOT = os.environ.get('TREND_ROOT', 'projects/YOUR_PROJECT_2/assets/RSEI_TRENDS_2026_new_new')
BANDS = ['RSEI_tau', 'RSEI_p_value', 'RSEI_mean', 'RSEI_median', 'RSEI_stdDev']
MAX_PIX = 4e6
out = sys.argv[1] if len(sys.argv) > 1 else 'trend_rasters'
os.makedirs(out, exist_ok=True)

C.init()
ids = sorted(C.list_images(TREND_ROOT))
rows = []
for i, aid in enumerate(ids, 1):
    name = aid.split('/')[-1]
    img = ee.Image(aid)
    region = img.geometry()
    area = region.area(1).getInfo()
    scale = max(30, int(math.ceil(math.sqrt(area / MAX_PIX) / 10.0)) * 10)
    for b in BANDS:
        path = os.path.join(out, f'{name}_{b}.tif')
        if os.path.exists(path):
            continue
        url = img.select(b).toFloat().getDownloadURL({'region': region.bounds(1), 'scale': scale,
                                                      'format': 'GEO_TIFF', 'crs': 'EPSG:4326'})
        with urllib.request.urlopen(url, timeout=600) as r, open(path, 'wb') as fh:
            fh.write(r.read())
    rows.append({'asset': name, 'municipio': img.get('municipio').getInfo(), 'area_km2': area / 1e6, 'scale_m': scale})
    print(f'[{i}/{len(ids)}] {name}: area {area/1e6:.0f} km2, scale {scale} m', flush=True)
    with open(os.path.join(out, 'scale_used.csv'), 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
print('done', flush=True)
