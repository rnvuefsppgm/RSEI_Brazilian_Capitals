# -*- coding: utf-8 -*-
"""
gee_init_and_rsei_assets.py  (New for Review, 2026 revision)
Shared helpers to load the annual RSEI asset collections produced by the original
processing script (01_compute_annual_rsei_by_capital.py) from the two Earth Engine asset roots
used in the study, exactly as merged by the original trend notebook
(04_pixelwise_mann_kendall_sen_trends.ipynb).

Authentication: run `earthengine authenticate` once, then set the environment
variable EE_PROJECT to your own Cloud project (no credentials are stored here).
"""
import os
import ee

# Asset folders holding the annual RSEI images (comma-separated environment variable).
ASSET_ROOTS = [r for r in os.environ.get(
    'RSEI_ASSET_ROOTS',
    'projects/YOUR_PROJECT/assets/RSEI_Bands_2026_new_new,'
    'projects/YOUR_PROJECT_2/assets/RSEI_Bands_2026_new_new').split(',') if r]
YEAR_START, YEAR_END = 1985, 2025
LANDSAT_IC = "LANDSAT/COMPOSITES/C02/T1_L2_32DAY"


def init():
    project = os.environ.get('EE_PROJECT')
    try:
        ee.Initialize(project=project)
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=project)


def list_images(root):
    """List all IMAGE assets below an asset folder (paginated)."""
    ids, tok = [], None
    while True:
        q = {'parent': root}
        if tok:
            q['pageToken'] = tok
        r = ee.data.listAssets(q)
        ids += [a['id'] for a in r.get('assets', []) if a.get('type') == 'IMAGE']
        tok = r.get('nextPageToken')
        if not tok:
            break
    return ids


def load_merged_collection():
    """Merge the annual RSEI images from both roots and standardise ANO/NM_MUN."""
    ids = []
    for root in ASSET_ROOTS:
        ids += list_images(root)

    def std(img):
        img = ee.Image(img)
        ano = ee.Number.parse(ee.String(img.get('ANO')))
        return img.set('ANO', ano).set('NM_MUN', ee.String(img.get('NM_MUN')))

    col = ee.ImageCollection.fromImages([ee.Image(i) for i in ids]).map(std)
    col = col.filter(ee.Filter.gte('ANO', YEAR_START)).filter(ee.Filter.lte('ANO', YEAR_END))
    return col, ids


def municipalities(col):
    m = col.aggregate_array('NM_MUN').distinct().sort().getInfo()
    return [x for x in m if x]
