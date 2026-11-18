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
# Part A: download (6 parallel requests). The municipal geometry is limited to the extent of the
# clipped trend products (TREND_DIR), which removes the oceanic islands of Vitória.
import json
import time
import rasterio
from shapely.geometry import box
from concurrent.futures import ThreadPoolExecutor
TREND_DIR = os.environ.get('TREND_DIR', '')


def mapped_geom(mun):
    geom = gdf[gdf.NM_MUN == mun].geometry.iloc[0]
    tif = os.path.join(TREND_DIR, f'{slug(mun)}_RSEI_tau.tif')
    if TREND_DIR and os.path.exists(tif):
        with rasterio.open(tif) as src:
            geom = geom.intersection(box(*src.bounds))
    gj = json.loads(gpd.GeoSeries([geom]).to_json())['features'][0]['geometry']
    return ee.Geometry(gj, 'EPSG:4326', False)


import geopandas as gpd
GM = {m: mapped_geom(m) for m in gdf.NM_MUN}
info = ee.FeatureCollection(col.map(lambda im: ee.Feature(None, {'id': im.get('system:id'), 'mun': im.get('NM_MUN'), 'ano': im.get('ANO')}))).getInfo()['features']


def fetch(p):
    aid, mun, ano = p['id'], p['mun'], int(p['ano'])
    path = os.path.join(RDIR, f'{slug(mun)}_{ano}.tif')
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return 0
    geom = GM[mun]
    scale = max(30, int(math.ceil(math.sqrt(areas[mun] / MAX_PIX) / 10.0)) * 10)
    img = ee.Image(aid).select('RSEI')
    if aid in flagged:
        img = ee.Image.constant(1).subtract(img).rename('RSEI')
    img = img.clip(geom).toFloat()
    for attempt in range(5):
        try:
            url = img.getDownloadURL({'region': geom.bounds(1), 'scale': scale, 'format': 'GEO_TIFF', 'crs': 'EPSG:4326'})
            with urllib.request.urlopen(url, timeout=600) as r:
                data = r.read()
            open(path, 'wb').write(data)
            return 1
        except Exception as e:
            err = str(e)
            time.sleep(20 * (attempt + 1))
    print('FAILED', mun, ano, err[:120], flush=True)
    return 0


n_done = 0
with ThreadPoolExecutor(6) as ex:
    for k in ex.map(fetch, [f['properties'] for f in info]):
        n_done += k
        if k and n_done % 100 == 0:
            print(n_done, 'downloaded', flush=True)
print('download complete', n_done, flush=True)

# Part B: compose
import rasterio
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import docx
from docx.shared import Cm

from figure_style import CM, WIDTH_CM, FS, FS_SMALL, set_geo_aspect, add_scale_bar
flag_years = {}
for f in info:
    if f['properties']['id'] in flagged:
        flag_years.setdefault(f['properties']['mun'], set()).add(int(f['properties']['ano']))
pages = []
for _, row in gdf.sort_values('NM_MUN').iterrows():
    mun, uf = row.NM_MUN, row.SIGLA_UF
    fl = flag_years.get(mun, set())
    H = 21.0
    fig = plt.figure(figsize=(WIDTH_CM * CM, H * CM))
    cols, rows, gap, top, bottom = 7, 6, 0.1, 1.0, 0.3
    pw = (WIDTH_CM - 0.2 - (cols - 1) * gap) / cols
    ph = (H - top - bottom - (rows - 1) * 0.8) / rows
    ext0 = None
    for k, ano in enumerate(range(1985, 2026)):
        r_, c_ = divmod(k, cols)
        ax = fig.add_axes([(0.1 + c_ * (pw + gap)) / WIDTH_CM, (H - top - (r_ + 1) * ph - r_ * 0.8) / H,
                           pw / WIDTH_CM, ph / H])
        path = os.path.join(RDIR, f'{slug(mun)}_{ano}.tif')
        if os.path.exists(path):
            with rasterio.open(path) as src:
                a = src.read(1).astype('float32')
                if src.nodata is not None:
                    a[a == src.nodata] = np.nan
                a[~np.isfinite(a)] = np.nan
                b = src.bounds
            ext = [b.left, b.right, b.bottom, b.top]
            ax.imshow(a, extent=ext, cmap='RdYlGn', vmin=0, vmax=1, interpolation='nearest')
            set_geo_aspect(ax, ext)
            if ext0 is None:
                ext0 = ext
                add_scale_bar(ax, ext, fontsize=6)
        else:
            ax.text(0.5, 0.5, 'no image', ha='center', va='center', fontsize=FS_SMALL, transform=ax.transAxes)
        ax.set_title(f'{ano}*' if ano in fl else str(ano), fontsize=FS_SMALL, pad=2)
        ax.set_xticks([]); ax.set_yticks([])
        for s_ in ax.spines.values():
            s_.set_visible(False)
    r_, c_ = divmod(41, cols)
    cax = fig.add_axes([(0.1 + c_ * (pw + gap) + 0.15 * pw) / WIDTH_CM, (H - top - (r_ + 1) * ph - r_ * 0.8 + 0.4 * ph) / H,
                        0.7 * pw / WIDTH_CM, 0.12 * ph / H])
    sm = plt.cm.ScalarMappable(cmap='RdYlGn', norm=plt.Normalize(0, 1))
    cb = fig.colorbar(sm, cax=cax, orientation='horizontal', ticks=[0, 0.5, 1])
    cb.set_label('RSEI', fontsize=FS_SMALL); cb.ax.tick_params(labelsize=6, width=0.4, length=2)
    cb.outline.set_linewidth(0.4)
    fig.text(0.1 / WIDTH_CM, (H - 0.25) / H, f'Figure S1 ({mun}, {uf}). Annual RSEI, 1985–2025', fontsize=FS + 1,
             fontweight='bold', va='top')
    png = os.path.join(OUT, f'Figure_S1_{slug(mun)}.png')
    fig.savefig(png, dpi=300)
    plt.close(fig)
    pages.append((mun, uf, png))
    print('page', mun, flush=True)

D = docx.Document()
D.core_properties.author = 'RNV'
D.core_properties.last_modified_by = 'RNV'
sec = D.sections[0]
sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
sec.left_margin = sec.right_margin = Cm(1.6)
sec.top_margin = sec.bottom_margin = Cm(1.8)
D.add_heading('Supplementary Material S1', 1)
D.add_paragraph('Figure S1. Annual maps of the Remote Sensing Ecological Index (RSEI) for the 27 Brazilian state capitals, '
                '1985–2025, within the official municipal boundaries (IBGE). Values range from 0 (lowest ecological quality '
                'in the capital-year) to 1 (highest). Capital-year images in which the first principal component was inverted '
                'were re-oriented before mapping and are marked with an asterisk (Table S3). Maps are ordered alphabetically by '
                'capital; the oceanic islands of Trindade and Martim Vaz (Vitória) are not shown. The rendering scale is '
                '30 m for small municipalities and up to 100 m or coarser for the largest ones.')
for mun, uf, png in pages:
    D.add_page_break()
    D.add_picture(png, width=Cm(17.4))
D.save(os.path.join(OUT, 'Supplementary_Material_S1.docx'))
print('done')
