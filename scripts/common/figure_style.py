# -*- coding: utf-8 -*-
"""
Shared figure style for the revised manuscript (Springer Nature artwork guidelines):
maximum width 17.4 cm (double column), maximum height 23.4 cm, Arial lettering of
7-9 pt at final print size, 600 dpi raster output and SVG with editable text.
New for Review (2026).
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
import matplotlib.patheffects as pe

CM = 1 / 2.54
WIDTH_CM = 17.4
MAX_HEIGHT_CM = 23.4
FS = 8          # base font size (pt) at print size
FS_SMALL = 7    # scale bars, legends, tick labels

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
    'font.size': FS,
    'axes.titlesize': FS,
    'axes.labelsize': FS,
    'legend.fontsize': FS_SMALL,
    'xtick.labelsize': FS_SMALL,
    'ytick.labelsize': FS_SMALL,
    'axes.linewidth': 0.5,
    'svg.fonttype': 'none',
    'pdf.fonttype': 42,
    'savefig.dpi': 600,
})

# Landscape artwork for the capital maps (rotated on the page): 23.4 x 16.0 cm, three capitals per figure
LANDSCAPE_W_CM, LANDSCAPE_H_CM = 23.4, 16.0

# Capitals per figure (alphabetical; nine landscape figures of three rows)
_CAPS = ['Aracaju', 'Belém', 'Belo Horizonte', 'Boa Vista', 'Brasília', 'Campo Grande', 'Cuiabá', 'Curitiba',
         'Florianópolis', 'Fortaleza', 'Goiânia', 'João Pessoa', 'Macapá', 'Maceió', 'Manaus', 'Natal', 'Palmas',
         'Porto Alegre', 'Porto Velho', 'Recife', 'Rio Branco', 'Rio de Janeiro', 'Salvador', 'São Luís', 'São Paulo',
         'Teresina', 'Vitória']
FIG_GROUPS = {3 + k: _CAPS[3 * k:3 * k + 3] for k in range(9)}
CITY_FIGURE = {c: f for f, cs in FIG_GROUPS.items() for c in cs}

# Trend classes (diverging red-green), not significant in neutral grey, continuous RSEI
# (RdYlGn) and standard-deviation classes in a separate sequential purple ramp
C_NEG, C_NULL, C_POS, C_NS = '#c51b29', '#f2f2f2', '#1a9641', '#d9d9d9'
SD_COLORS = ['#efedf5', '#9e9ac8', '#54278f']
CMAP_TREND = ListedColormap([C_NEG, C_NULL, C_POS])
NORM_TREND = BoundaryNorm([-.5, .5, 1.5, 2.5], 3)
CMAP_SIG = ListedColormap([C_NEG, C_NS, C_POS])
NORM_SIG = NORM_TREND
CMAP_SD = ListedColormap(SD_COLORS)
NORM_SD = NORM_TREND
CMAP_RSEI = 'RdYlGn'


def nice_bar_km(span_km):
    for v in (50, 20, 10, 5, 2, 1, 0.5):
        if v <= span_km * 0.3:
            return v
    return 0.5


def add_scale_bar(ax, ext, fontsize=FS_SMALL, below=True):
    """Scale bar for a geographic (EPSG:4326) panel. With below=True it is drawn under the panel, outside
    the map, so that it never covers mapped pixels (call after the axis limits and aspect are final)."""
    ax.apply_aspect()
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    lat = (ext[2] + ext[3]) / 2
    km_deg = 111.32 * np.cos(np.radians(lat))
    bar = nice_bar_km((ext[1] - ext[0]) * km_deg)
    frac = bar / km_deg / (x1 - x0)
    # anchored to the lower-left corner of the mapped extent (ext), just below it
    xl = max(0.0, (ext[0] - x0) / (x1 - x0)) + 0.02
    yb = max(0.0, (ext[2] - y0) / (y1 - y0))
    y = yb - 0.05 if below else yb + 0.04
    ax.plot([xl, xl + frac], [y, y], color='black', lw=1.4, solid_capstyle='butt', transform=ax.transAxes,
            clip_on=False)
    for xx in (xl, xl + frac):
        ax.plot([xx, xx], [y - 0.02, y + 0.02], color='black', lw=0.6, transform=ax.transAxes, clip_on=False)
    ax.text(xl + 0.03 + frac, y, f'{bar:g} km', fontsize=fontsize, va='center', ha='left', transform=ax.transAxes,
            clip_on=False)


def set_geo_aspect(ax, ext):
    lat = (ext[2] + ext[3]) / 2
    ax.set_aspect(1 / np.cos(np.radians(lat)), adjustable='datalim')
