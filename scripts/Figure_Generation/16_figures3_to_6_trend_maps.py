# -*- coding: utf-8 -*-
"""
Regeneration of Figures 3-6 (five-panel RSEI composites per capital) from
the consolidated trend products. New for Review (2026).
Inputs : GeoTIFFs downloaded by 11_download_trend_rasters_by_capital (trend_<city>_RSEI_{tau,p_value,mean,median,stdDev}.tif),
         official municipal boundaries (data/Capitais.shp) used to clip the panels.
Panels : (1) RSEI trend: sign of Kendall's tau (negative / null / positive);
         (2) statistically significant trend (Mann-Kendall, p <= 0.05): negative / positive;
         (3) temporal mean, (4) temporal median (continuous 0-1, RdYlGn);
         (5) temporal standard deviation in the three fixed classes of the manuscript
             (< 0.05 low; 0.05-0.10 moderate; > 0.10 high).
Outputs: PNG at 600 dpi and SVG (editable text) in the output folder.
Usage  : python 16_figures3_to_6_trend_maps.py <raster_folder> <output_folder>
"""
import sys
import os
import numpy as np
import rasterio
from rasterio.mask import mask as rio_mask
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch

RAST = sys.argv[1] if len(sys.argv) > 1 else 'trend_rasters'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'figures_out'
os.makedirs(OUT, exist_ok=True)
SHP = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'Capitais.shp')
gdf = gpd.read_file(SHP).to_crs(4326)

FIGS = {  # same grouping as the submitted version
    3: ['Aracaju', 'Belém', 'Belo Horizonte', 'Boa Vista', 'Brasília', 'Campo Grande', 'Cuiabá', 'Curitiba'],
    4: ['Florianópolis', 'Fortaleza', 'Goiânia', 'João Pessoa', 'Macapá', 'Maceió', 'Manaus', 'Natal'],
    5: ['Palmas', 'Porto Alegre', 'Porto Velho', 'Recife', 'Rio Branco', 'Rio de Janeiro', 'Salvador', 'São Luís'],
    6: ['São Paulo', 'Teresina', 'Vitória'],
}
import unicodedata


def slug(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    return ''.join(c if c.isalnum() else '_' for c in s).strip('_')


def read_clipped(path, geom):
    with rasterio.open(path) as src:
        arr, tr = rio_mask(src, [geom], crop=True, nodata=np.nan, filled=True)
    a = arr[0].astype('float32')
    a[~np.isfinite(a)] = np.nan
    return a, tr


cm_trend = ListedColormap(['#d7191c', '#ffffbf', '#1a9641'])
cm_sig = ListedColormap(['#d7191c', '#1a9641'])
cm_sd = ListedColormap(['#2c7bb6', '#ffffbf', '#d7191c'])
titles = ["RSEI trend (Kendall's tau)", 'Significant trend (p ≤ 0.05)', 'Mean', 'Median', 'Standard deviation']

for fig_no, cities in FIGS.items():
    n = len(cities)
    fig, axes = plt.subplots(n, 5, figsize=(12.5, 2.35 * n), dpi=100)
    axes = np.atleast_2d(axes)
    for i, city in enumerate(cities):
        row = gdf[gdf['NM_MUN'] == city].iloc[0]
        geom = row.geometry
        uf = row['SIGLA_UF']
        base = os.path.join(RAST, f'trend_{slug(city)}_RSEI_')
        tau, tr = read_clipped(base + 'tau.tif', geom)
        p, _ = read_clipped(base + 'p_value.tif', geom)
        mean, _ = read_clipped(base + 'mean.tif', geom)
        med, _ = read_clipped(base + 'median.tif', geom)
        sd, _ = read_clipped(base + 'stdDev.tif', geom)
        h, w = tau.shape
        ext = [tr.c, tr.c + tr.a * w, tr.f + tr.e * h, tr.f]
        tr_cls = np.where(np.isnan(tau), np.nan, np.where(tau < 0, 0, np.where(tau > 0, 2, 1)))
        sig = np.where(np.isnan(tau) | (p > 0.05) | (tau == 0), np.nan, np.where(tau < 0, 0, 1))
        sd_cls = np.where(np.isnan(sd), np.nan, np.where(sd < 0.05, 0, np.where(sd <= 0.10, 1, 2)))
        panels = [(tr_cls, cm_trend, BoundaryNorm([-.5, .5, 1.5, 2.5], 3)), (sig, cm_sig, BoundaryNorm([-.5, .5, 1.5], 2)),
                  (mean, 'RdYlGn', None), (med, 'RdYlGn', None), (sd_cls, cm_sd, BoundaryNorm([-.5, .5, 1.5, 2.5], 3))]
        for j, (arr, cmap, nrm) in enumerate(panels):
            ax = axes[i, j]
            if j == 1:  # grey background of the municipality for non-significant pixels
                ax.imshow(np.where(np.isnan(tau), np.nan, 0.5), extent=ext, cmap='Greys', vmin=0, vmax=1, alpha=0.25, interpolation='nearest')
            if nrm is None:
                ax.imshow(arr, extent=ext, cmap=cmap, vmin=0, vmax=1, interpolation='nearest')
            else:
                ax.imshow(arr, extent=ext, cmap=cmap, norm=nrm, interpolation='nearest')
            gpd.GeoSeries([geom]).boundary.plot(ax=ax, color='black', linewidth=0.3)
            ax.set_xticks([]); ax.set_yticks([])
            for s in ax.spines.values():
                s.set_linewidth(0.4)
            if i == 0:
                ax.set_title(titles[j], fontsize=8)
            if j == 0:
                ax.set_ylabel(f'{city}-{uf}', fontsize=8, fontweight='bold')
        # scale bar (km) on first panel
        ax = axes[i, 0]
        lat = (ext[2] + ext[3]) / 2
        km_per_deg = 111.32 * np.cos(np.radians(lat))
        span_km = (ext[1] - ext[0]) * km_per_deg
        bar_km = 10 if span_km > 40 else (5 if span_km > 15 else 2)
        x0 = ext[0] + 0.05 * (ext[1] - ext[0]); y0 = ext[2] + 0.06 * (ext[3] - ext[2])
        ax.plot([x0, x0 + bar_km / km_per_deg], [y0, y0], color='black', linewidth=1.2)
        ax.text(x0, y0 + 0.02 * (ext[3] - ext[2]), f'{bar_km} km', fontsize=5.5)
    handles = [Patch(color='#d7191c', label='Negative tau (degradation)'), Patch(color='#ffffbf', label='Null tau'),
               Patch(color='#1a9641', label='Positive tau (improvement)'),
               Patch(color='#2c7bb6', label='SD < 0.05 (low)'), Patch(color='#ffffbf', label='SD 0.05-0.10 (moderate)'),
               Patch(color='#d7191c', label='SD > 0.10 (high)')]
    fig.legend(handles=handles, loc='lower center', ncol=6, fontsize=6.5, frameon=False, bbox_to_anchor=(0.5, -0.005))
    sm = plt.cm.ScalarMappable(cmap='RdYlGn', norm=plt.Normalize(0, 1))
    cax = fig.add_axes([0.92, 0.3, 0.012, 0.4])
    cb = fig.colorbar(sm, cax=cax); cb.set_label('RSEI (mean / median)', fontsize=7); cb.ax.tick_params(labelsize=6)
    plt.subplots_adjust(left=0.04, right=0.90, top=0.95, bottom=0.05, wspace=0.05, hspace=0.12)
    plt.rcParams['svg.fonttype'] = 'none'
    fig.savefig(os.path.join(OUT, f'Figure_{fig_no}.png'), dpi=600)
    fig.savefig(os.path.join(OUT, f'Figure_{fig_no}.svg'))
    plt.close(fig)
    print('Figure', fig_no, 'written', flush=True)
print('done')
