# -*- coding: utf-8 -*-
"""
Orientation check of the exported annual RSEI against its components.
New for Review (2026). For every capital-year image, the annual median Landsat
composite used by the original script is rebuilt and the Pearson correlation
between the exported RSEI band and NDVI (expected positive) and LST (expected
negative) is computed over the image footprint. A negative RSEI-NDVI correlation
would reveal a PC1 sign inversion for that year. One server request per image
(resumable). Output: out_S2_orientation_check.csv
"""
import sys
import os
import csv
import ee
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
import gee_init_and_rsei_assets as C
import municipal_boundaries as MG

OUT = 'out_S2_orientation_check.csv'
SCALE = 120  # coarser than 30 m only to keep the 1,100+ correlations affordable

C.init()
col, ids = C.load_merged_collection()
IC = ee.ImageCollection(C.LANDSAT_IC)
done = set()
rows = []
if os.path.exists(OUT):
    with open(OUT, encoding='utf-8') as fh:
        for r in csv.DictReader(fh):
            rows.append(r)
            done.add(r['asset'])

GEOMS = None


def one(aid, bounds=False):
    img = ee.Image(aid)
    y = ee.Number.parse(ee.String(img.get('ANO')))
    region = img.geometry()
    if bounds:
        # Fallback for very large municipalities (e.g. Porto Velho), whose image footprint geometry exceeds
        # the request size limit: the correlation is computed within the official municipal boundary instead.
        global GEOMS
        if GEOMS is None:
            GEOMS = MG.ee_geometries()
        region = GEOMS[img.get('NM_MUN').getInfo()]
    start = ee.Date.fromYMD(y, 1, 1)
    annual = IC.filterDate(start, start.advance(1, 'year')).median().clip(region)
    ndvi = annual.normalizedDifference(['nir', 'red']).rename('NDVI')
    lst = annual.select('thermal').subtract(273.15).rename('LST')
    rsei = img.select('RSEI')
    r1 = ee.Image.cat([rsei, ndvi]).reduceRegion(ee.Reducer.pearsonsCorrelation(), region, SCALE, maxPixels=1e13, tileScale=4)
    r2 = ee.Image.cat([rsei, lst]).reduceRegion(ee.Reducer.pearsonsCorrelation(), region, SCALE, maxPixels=1e13, tileScale=4)
    try:
        d = ee.Dictionary({'NM_MUN': img.get('NM_MUN'), 'ANO': y, 'r_RSEI_NDVI': r1.get('correlation'),
                           'r_RSEI_LST': r2.get('correlation')}).getInfo()
    except Exception as e:
        if not bounds and 'too large' in str(e):
            return one(aid, bounds=True)
        print(aid, 'ERROR', str(e)[:100], flush=True)
        return None
    d['asset'] = aid
    return d


def dump():
    with open(OUT, 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=['asset', 'NM_MUN', 'ANO', 'r_RSEI_NDVI', 'r_RSEI_LST'])
        w.writeheader()
        w.writerows(rows)


todo = [a for a in sorted(ids) if a not in done]
with ThreadPoolExecutor(max_workers=1) as ex:
    for i, d in enumerate(ex.map(one, todo), 1):
        if d:
            rows.append(d)
        if i % 20 == 0:
            print(f'[{i}/{len(todo)}] done so far', flush=True)
            dump()
dump()
print('done', flush=True)
