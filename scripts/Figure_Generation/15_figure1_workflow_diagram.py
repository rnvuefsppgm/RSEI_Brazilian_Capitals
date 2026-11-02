# -*- coding: utf-8 -*-
"""
Figure 1 (methodological workflow) redrawn to match the processing actually
implemented in the recovered scripts. New for Review (2026).
Output: Figure_1.png (600 dpi) and Figure_1.svg (editable text).
Usage: python 15_figure1_workflow_diagram.py <output_folder>
"""
import sys
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = sys.argv[1] if len(sys.argv) > 1 else 'figures_out'
os.makedirs(OUT, exist_ok=True)
plt.rcParams['svg.fonttype'] = 'none'
plt.rcParams['font.family'] = 'DejaVu Sans'

boxes = [
    ('1. Data acquisition (GEE)', 'Landsat Collection 2 Level-2 32-day composites\n(TM, ETM+, OLI/TIRS; USGS cloud-masked)\nAnnual median composite, 1985-2025 (41 years)', '#e8f1fa'),
    ('2. RSEI components', 'NDVI (greenness) | WET (Tasseled Cap wetness,\nTM coefficients <= 2012, OLI coefficients >= 2013)\nLST (surface temperature, K to °C) | NDBSI = (IBI + SI)/2', '#e8f1fa'),
    ('3. Normalisation and PCA (per capital, per year)', 'Min-max scaling to 0-1 (LST and NDBSI inverted)\nCovariance PCA over the processing polygon\nRSEI = rescaled (1 - PC1); spatial gap filling', '#e8f1fa'),
    ('4. Annual RSEI assets', '27 capitals x 41 years = 1,107 images (30 m)\nMissing years re-processed; completeness audit', '#fdf2e0'),
    ('5. Pixel-wise trend analysis (GEE)', "Mann-Kendall S, Var(S), Z, p (two-tailed), Kendall's tau\nSen's slope and intercept; temporal mean, median, SD", '#fdf2e0'),
    ('6. Municipal clipping and cartography (QGIS / Python)', 'Clip to IBGE municipal boundaries\nTrend classes (sign of tau; p <= 0.05) and area shares (Table 1)\nMaps (Figures 3-6); supplementary sensitivity analyses', '#eaf5e6'),
]
fig, ax = plt.subplots(figsize=(7.2, 8.6), dpi=100)
ax.set_xlim(0, 10); ax.set_ylim(0, 10.2); ax.axis('off')
y = 9.6
h = 1.32
for i, (title, body, col) in enumerate(boxes):
    b = FancyBboxPatch((0.6, y - h), 8.8, h, boxstyle='round,pad=0.02,rounding_size=0.15', fc=col, ec='#444444', lw=0.8)
    ax.add_patch(b)
    ax.text(0.85, y - 0.28, title, fontsize=9.5, fontweight='bold', va='top')
    ax.text(0.85, y - 0.62, body, fontsize=7.8, va='top', linespacing=1.35)
    if i < len(boxes) - 1:
        ax.add_patch(FancyArrowPatch((5.0, y - h - 0.02), (5.0, y - h - 0.26), arrowstyle='-|>', mutation_scale=12, color='#444444', lw=0.9))
    y -= h + 0.3
fig.savefig(os.path.join(OUT, 'Figure_1.png'), dpi=600, bbox_inches='tight')
fig.savefig(os.path.join(OUT, 'Figure_1.svg'), bbox_inches='tight')
print('Figure 1 written')
