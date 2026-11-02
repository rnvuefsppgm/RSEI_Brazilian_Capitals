# -*- coding: utf-8 -*-
"""
Figure S1: annual RSEI maps (1985-2025) for the 27 capitals, regenerated from the
annual assets after the orientation correction. New for Review (2026).
Part A downloads every annual RSEI image clipped to the municipal boundary at a
display scale (default 100 m; 30 m for small municipalities), re-orienting the
images flagged by 05_check_pc1_orientation_against_ndvi_lst. Part B composes one page per capital (41 panels) and
writes a Word document (Supplementary Material S1) with all pages.
Usage: python 19_figure_s1_annual_rsei_maps.py <out_S2_orientation_check.csv> <raster_dir> <out_dir>
"""
import sys
import os
import math
import csv
import urllib.request
import unicodedata
import numpy as np
import ee
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
import gee_init_and_rsei_assets as C
import municipal_boundaries as MG

S2, RDIR, OUT = sys.argv[1:4]
os.makedirs(RDIR, exist_ok=True)
os.makedirs(OUT, exist_ok=True)
MAX_PIX = 1.5e6


def slug(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    return ''.join(c if c.isalnum() else '_' for c in s).strip('_')


flagged = set()
with open(S2, encoding='utf-8') as fh:
    for r in csv.DictReader(fh):
        if r['r_RSEI_NDVI'] and float(r['r_RSEI_NDVI']) < 0:
            flagged.add(r['asset'])

C.init()
col, ids = C.load_merged_collection()
G = MG.ee_geometries()
gdf = MG.load_gdf()
areas = {r.NM_MUN: gdf.to_crs(5880).area.iloc[i] for i, r in gdf.iterrows()}
meta = {}
for aid in sorted(ids):
    img = ee.Image(aid)
    mun = aid.split('/')[-1]
    meta[aid] = img
# Part A: download (sequential)
info = ee.FeatureCollection(col.map(lambda im: ee.Feature(None, {'id': im.get('system:id'), 'mun': im.get('NM_MUN'), 'ano': im.get('ANO')}))).getInfo()['features']
n_done = 0
for f in info:
    p = f['properties']
    aid, mun, ano = p['id'], p['mun'], int(p['ano'])
    path = os.path.join(RDIR, f'{slug(mun)}_{ano}.tif')
    if os.path.exists(path):
        continue
    geom = G[mun]
    scale = max(30, int(math.ceil(math.sqrt(areas[mun] / MAX_PIX) / 10.0)) * 10)
    img = ee.Image(aid).select('RSEI')
    if aid in flagged:
        img = ee.Image.constant(1).subtract(img).rename('RSEI')
    img = img.clip(geom).toFloat()
    url = img.getDownloadURL({'region': geom.bounds(1), 'scale': scale, 'format': 'GEO_TIFF', 'crs': 'EPSG:4326'})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(url, timeout=600) as r, open(path, 'wb') as fh:
                fh.write(r.read())
            break
        except Exception as e:
            import time
            time.sleep(30 * (attempt + 1))
    n_done += 1
    if n_done % 50 == 0:
        print(n_done, 'downloaded', flush=True)
print('download complete', flush=True)

# Part B: compose
import rasterio
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import docx
from docx.shared import Cm

pages = []
for _, row in gdf.sort_values('NM_MUN').iterrows():
    mun, uf = row.NM_MUN, row.SIGLA_UF
    fig, axes = plt.subplots(6, 7, figsize=(14, 12.5), dpi=100)
    axes = axes.ravel()
    for k, ano in enumerate(range(1985, 2026)):
        ax = axes[k]
        path = os.path.join(RDIR, f'{slug(mun)}_{ano}.tif')
        if os.path.exists(path):
            with rasterio.open(path) as src:
                a = src.read(1).astype('float32')
                a[~np.isfinite(a)] = np.nan
                b = src.bounds
            ax.imshow(a, extent=[b.left, b.right, b.bottom, b.top], cmap='RdYlGn', vmin=0, vmax=1, interpolation='nearest')
        ax.set_title(str(ano), fontsize=8)
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_linewidth(0.3)
    axes[41].axis('off')
    sm = plt.cm.ScalarMappable(cmap='RdYlGn', norm=plt.Normalize(0, 1))
    cb = fig.colorbar(sm, ax=axes[41], fraction=0.9, aspect=12)
    cb.set_label('RSEI', fontsize=8); cb.ax.tick_params(labelsize=7)
    fig.suptitle(f'{mun}-{uf}: annual RSEI, 1985–2025', fontsize=12)
    plt.tight_layout(rect=(0, 0, 1, 0.97))
    png = os.path.join(OUT, f'Figure_S1_{slug(mun)}.png')
    fig.savefig(png, dpi=300)
    plt.close(fig)
    pages.append((mun, uf, png))
    print('page', mun, flush=True)

D = docx.Document()
D.core_properties.author = 'RNV'
D.core_properties.last_modified_by = 'RNV'
D.add_heading('Supplementary Material S1', 1)
D.add_paragraph('Figure S1. Annual maps of the Remote Sensing Ecological Index (RSEI) for the 27 Brazilian state capitals, '
                '1985–2025, within the official municipal boundaries (IBGE). Values range from 0 (lowest ecological quality '
                'in the capital-year) to 1 (highest). Capital-year images in which the first principal component was inverted '
                'were re-oriented before mapping (Table S3). Maps are ordered alphabetically by capital; the rendering scale is '
                '30 m for small municipalities and up to 100 m or coarser for the largest ones.')
for mun, uf, png in pages:
    D.add_paragraph(f'Figure S1 ({mun}-{uf}).')
    D.add_picture(png, width=Cm(16))
D.save(os.path.join(OUT, 'Supplementary_Material_S1_Figure_S1.docx'))
print('done')
