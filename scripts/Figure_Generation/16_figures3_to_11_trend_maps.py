# -*- coding: utf-8 -*-
"""
Figures 3-11: five-panel RSEI composites per capital (trend sign, significant
trend, temporal mean, median and standard deviation, 1985-2025), regenerated from the
orientation-corrected trend products. New for Review (2026).
Layout : landscape artwork of 23.4 x 16.0 cm (printed rotated), three capitals (rows) per
         figure, Arial 7-8 pt at print size, maps zoomed to the municipal extent, scale bars
         outside the maps and legends in a column at the right (figure_style.py).
Inputs : GeoTIFFs <slug>_RSEI_{tau,p_value,mean,median,stdDev}.tif (clipped trend
         products; the prefix trend_ is also accepted) and Capitais.shp.
Note   : the municipality of Vitória includes the oceanic islands of Trindade and
         Martim Vaz (about 1,150 km offshore); the panels are limited to the extent of
         the trend products, i.e. the continental and island sector of the city.
Usage  : python 16_figures3_to_11_trend_maps.py <raster_folder> <boundaries.shp> <output_folder>
"""
import sys
import os
import unicodedata
import numpy as np
import rasterio
import geopandas as gpd
from shapely.geometry import box
from matplotlib.patches import Patch
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
from figure_style import (plt, CM, LANDSCAPE_W_CM as WIDTH_CM, LANDSCAPE_H_CM as MAX_HEIGHT_CM, FS, FS_SMALL, FIG_GROUPS, CMAP_TREND, NORM_TREND,
                       CMAP_SIG, NORM_SIG, CMAP_SD, NORM_SD, CMAP_RSEI, C_NEG, C_NULL, C_POS, C_NS,
                       SD_COLORS, add_scale_bar, set_geo_aspect)

RAST, SHP, OUT = sys.argv[1:4]
os.makedirs(OUT, exist_ok=True)
gdf = gpd.read_file(SHP).to_crs(4326)


def slug(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    return ''.join(c if c.isalnum() else '_' for c in s).strip('_')


def read(city, band):
    for pre in ('', 'trend_'):
        p = os.path.join(RAST, f'{pre}{slug(city)}_RSEI_{band}.tif')
        if os.path.exists(p):
            with rasterio.open(p) as src:
                a = src.read(1).astype('float32')
                if src.nodata is not None:
                    a[a == src.nodata] = np.nan
                b = src.bounds
            a[~np.isfinite(a)] = np.nan
            return a, [b.left, b.right, b.bottom, b.top]
    raise FileNotFoundError(f'{city} {band}')


def valid_extent(a, ext, pad=0.03):
    rows = np.where(np.isfinite(a).any(1))[0]
    cols = np.where(np.isfinite(a).any(0))[0]
    h, w = a.shape
    dx = (ext[1] - ext[0]) / w
    dy = (ext[3] - ext[2]) / h
    x0, x1 = ext[0] + cols[0] * dx, ext[0] + (cols[-1] + 1) * dx
    y1, y0 = ext[3] - rows[0] * dy, ext[3] - (rows[-1] + 1) * dy
    px, py = (x1 - x0) * pad, (y1 - y0) * pad
    return [x0 - px, x1 + px, y0 - py, y1 + py]


TITLES = ["Kendall's τ sign", 'Significant trend\n(p ≤ 0.05)', 'Mean RSEI', 'Median RSEI',
          'Standard deviation\nof RSEI']
LEFT, LABEL_W, GAP, LEGCOL = 0.05, 0.5, 0.1, 3.3   # cm; legends in a column at the right
HEAD, LEG, ROWGAP = 0.75, 0.45, 0.5                 # LEG: room for the scale bar of the last row
PANEL = (WIDTH_CM - LEFT - LABEL_W - 4 * GAP - LEGCOL) / 5
PANEL_H = (MAX_HEIGHT_CM - HEAD - LEG - 2 * ROWGAP) / 3

for fig_no, cities in FIG_GROUPS.items():
    n = len(cities)
    H = HEAD + n * PANEL_H + (n - 1) * ROWGAP + LEG
    assert H <= MAX_HEIGHT_CM + 1e-6, (fig_no, H)
    fig = plt.figure(figsize=(WIDTH_CM * CM, H * CM))
    fx = lambda cm: cm / WIDTH_CM
    fy = lambda cm: cm / H
    for i, city in enumerate(cities):
        row = gdf[gdf['NM_MUN'] == city].iloc[0]
        tau, ext = read(city, 'tau')
        p, _ = read(city, 'p_value')
        mean, _ = read(city, 'mean')
        med, _ = read(city, 'median')
        sd, _ = read(city, 'stdDev')
        vext = valid_extent(tau, ext, pad=0.01)
        # boundary restricted to the mapped extent (drops the oceanic islands of Vitória)
        bnd = gpd.GeoSeries([row.geometry]).intersection(box(vext[0], vext[2], vext[1], vext[3]))
        cls = np.where(np.isnan(tau), np.nan, np.where(tau < 0, 0, np.where(tau > 0, 2, 1)))
        sig = np.where(np.isnan(tau), np.nan,
                       np.where((p <= 0.05) & (tau < 0), 0, np.where((p <= 0.05) & (tau > 0), 2, 1)))
        sdc = np.where(np.isnan(sd), np.nan, np.where(sd < 0.05, 0, np.where(sd <= 0.10, 1, 2)))
        panels = [(cls, CMAP_TREND, NORM_TREND), (sig, CMAP_SIG, NORM_SIG), (mean, CMAP_RSEI, None),
                  (med, CMAP_RSEI, None), (sdc, CMAP_SD, NORM_SD)]
        y = H - HEAD - (i + 1) * PANEL_H - i * ROWGAP
        for j, (arr, cmap, nrm) in enumerate(panels):
            x = LEFT + LABEL_W + j * (PANEL + GAP)
            ax = fig.add_axes([fx(x), fy(y), fx(PANEL), fy(PANEL_H)])
            kw = dict(norm=nrm) if nrm is not None else dict(vmin=0, vmax=1)
            ax.imshow(arr, extent=ext, cmap=cmap, interpolation='nearest', **kw)
            bnd.boundary.plot(ax=ax, color='#333333', linewidth=0.35)
            ax.set_xlim(vext[0], vext[1])
            ax.set_ylim(vext[2], vext[3])
            set_geo_aspect(ax, vext)
            ax.set_xticks([])
            ax.set_yticks([])
            for s in ax.spines.values():
                s.set_visible(False)
            if i == 0:
                fig.text(fx(x + PANEL / 2), fy(H - 0.12), TITLES[j], ha='center', va='top',
                         fontsize=FS, fontweight='bold')
            if j == 0:
                add_scale_bar(ax, vext)
        fig.text(fx(LEFT + 0.2), fy(y + PANEL_H / 2), f"{city} ({row['SIGLA_UF']})", rotation=90,
                 ha='center', va='center', fontsize=FS, fontweight='bold')

    # legends: stacked in the right-hand column, clear of the maps and of the scale bars
    lx = LEFT + LABEL_W + 5 * PANEL + 4 * GAP + 0.35
    lw = LEGCOL - 0.4

    def legend_at(top, handles, title):
        lax = fig.add_axes([fx(lx), fy(H - top - 2.0), fx(lw), fy(2.0)])
        lax.axis('off')
        lax.legend(handles=handles, title=title, loc='upper left', frameon=False, fontsize=FS_SMALL,
                   title_fontsize=FS_SMALL, handlelength=1.1, handleheight=0.9, borderaxespad=0,
                   labelspacing=0.3, alignment='left')

    edge = dict(edgecolor='#666666', linewidth=0.3)
    legend_at(HEAD + 0.1, [Patch(facecolor=C_NEG, label='Negative', **edge), Patch(facecolor=C_NULL, label='Null', **edge),
                           Patch(facecolor=C_POS, label='Positive', **edge)], "Trend direction (τ)")
    legend_at(HEAD + 2.1, [Patch(facecolor=C_NEG, label='Degradation', **edge),
                           Patch(facecolor=C_NS, label='Not significant', **edge),
                           Patch(facecolor=C_POS, label='Improvement', **edge)], 'Mann–Kendall (p ≤ 0.05)')
    fig.text(fx(lx), fy(H - HEAD - 4.25), 'Mean and median RSEI', ha='left', va='top', fontsize=FS_SMALL)
    cax = fig.add_axes([fx(lx), fy(H - HEAD - 4.95), fx(lw - 0.2), fy(0.25)])
    sm = plt.cm.ScalarMappable(cmap=CMAP_RSEI, norm=plt.Normalize(0, 1))
    cb = fig.colorbar(sm, cax=cax, orientation='horizontal', ticks=[0, 0.5, 1.0])
    cb.outline.set_linewidth(0.4)
    cb.ax.tick_params(labelsize=FS_SMALL, width=0.4, length=2)
    fig.text(fx(lx), fy(H - HEAD - 5.55), '0 = low, 1 = high\necological quality', ha='left', va='top',
             fontsize=FS_SMALL, linespacing=1.2)
    legend_at(HEAD + 6.5, [Patch(facecolor=SD_COLORS[0], label='< 0.05 (low)', **edge),
                           Patch(facecolor=SD_COLORS[1], label='0.05–0.10 (moderate)', **edge),
                           Patch(facecolor=SD_COLORS[2], label='> 0.10 (high)', **edge)], 'Standard deviation')
    fig.savefig(os.path.join(OUT, f'Figure_{fig_no}.png'), dpi=600)
    fig.savefig(os.path.join(OUT, f'Figure_{fig_no}.svg'))
    plt.close(fig)
    print(f'Figure {fig_no}: {n} capitals, {WIDTH_CM} x {H:.1f} cm', flush=True)
print('done')
