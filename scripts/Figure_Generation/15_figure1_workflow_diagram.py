# -*- coding: utf-8 -*-
"""
Figure 1: detailed methodological workflow (inputs, annual RSEI in Google Earth Engine,
pixel-wise trend analysis, municipal synthesis and results), with the quality-control and
sensitivity analyses of the revision and the tables/figures in which each step is reported.
Every element follows the processing actually implemented in the recovered scripts.
New for Review (2026).
Output: Figure_1.png (600 dpi) and Figure_1.svg (editable text), 17.4 x 21.6 cm.
Usage: python 15_figure1_workflow_diagram.py <output_folder>
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
from figure_style import plt, CM, WIDTH_CM, FS, FS_SMALL
from matplotlib.patches import FancyBboxPatch

OUT = sys.argv[1] if len(sys.argv) > 1 else 'figures_out'
os.makedirs(OUT, exist_ok=True)

W, H = WIDTH_CM, 21.6
fig = plt.figure(figsize=(W * CM, H * CM))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(H, 0)            # y measured from the top, in cm
ax.axis('off')

C_IN, C_GEE, C_TR, C_SY, C_RES, C_QC = '#eef1f5', '#e3eef9', '#fdf0de', '#e7f4e4', '#efe9f6', '#fffbe6'
E_IN, E_GEE, E_TR, E_SY, E_RES, E_QC = '#6b7a8f', '#2f6aa3', '#c77a12', '#3d8b37', '#6b4c9a', '#b8962e'
MX0, MX1 = 0.25, 11.75        # main column
QX0, QX1 = 12.05, 17.15       # quality-control lane


def box(x0, y0, x1, y1, title, body, fc, ec, dashed=False, tsize=FS_SMALL + 0.5, bsize=FS_SMALL, tag=None):
    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle='round,pad=0,rounding_size=0.12',
                                fc=fc, ec=ec, lw=0.8, ls=(0, (3, 2)) if dashed else '-'))
    ty = y0 + 0.14
    if title:
        ax.text(x0 + 0.14, ty, title, fontsize=tsize, fontweight='bold', va='top', ha='left', color='#111111')
        ty += 0.36 * (title.count('\n') + 1) + 0.04
    if body:
        ax.text(x0 + 0.14, ty, body, fontsize=bsize, va='top', ha='left', linespacing=1.25, color='#222222')
    if tag:
        ax.text(x1 - 0.1, y1 - 0.08, tag, fontsize=FS_SMALL - 0.5, va='bottom', ha='right', color=ec,
                fontweight='bold')


def band(y0, y1, label, ec):
    ax.add_patch(FancyBboxPatch((0.08, y0), W - 0.16, y1 - y0, boxstyle='round,pad=0,rounding_size=0.15',
                                fc='none', ec=ec, lw=0.6, alpha=0.9))
    ax.text(0.22, y0 + 0.1, label, fontsize=FS, fontweight='bold', va='top', ha='left', color=ec)


def arrow(x0, y0, x1, y1, color='#333333', dashed=False, lw=0.9):
    ax.annotate('', xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle='-|>', color=color, lw=lw, mutation_scale=7,
                                linestyle=(0, (3, 2)) if dashed else '-', shrinkA=0, shrinkB=0))


# ---------------------------------------------------------------- A. inputs
band(0.1, 2.75, 'A  Input data', E_IN)
box(0.25, 0.55, 7.0, 2.6, 'Landsat Collection 2 Level-2',
    'USGS 32-day composites (LANDSAT/COMPOSITES/\nC02/T1_L2_32DAY); TM, ETM+, OLI/TIRS;\n'
    'surface reflectance and surface temperature;\nclouds, shadows and saturation masked (QA)', C_IN, E_IN)
box(7.25, 0.55, 12.0, 2.6, 'Spatial units',
    '27 state capitals; processing polygons\n(municipality + surroundings, CAP_JOIN2);\n'
    'official municipal boundaries\n(IBGE municipal mesh 2022)', C_IN, E_IN)
box(12.25, 0.55, 17.15, 2.6, 'Demographic data',
    'IBGE Demographic Censuses\n1991, 2000 and 2022 (SIDRA);\nmunicipal area → density 2022\nand growth 1991–2022', C_IN, E_IN)

# ---------------------------------------------------------------- B. annual RSEI
band(2.95, 13.0, 'B  Annual RSEI (GEE), per capital-year', E_GEE)
ax.text((QX0 + QX1) / 2, 3.42, 'Quality control and sensitivity', fontsize=FS, fontweight='bold', ha='center',
        va='top', color=E_QC)
arrow(6.85, 2.6, 6.85, 3.5)
box(MX0, 3.5, MX1, 4.45, 'B1  Annual median composite',
    'Median of all valid 32-day composites of the calendar year (year-round conditions; 30 m)', C_GEE, E_GEE)
comp = [('Greenness', 'NDVI =\n(NIR − Red) /\n(NIR + Red)'),
        ('Wetness', 'Tasseled Cap WET;\nTM coefficients ≤ 2012,\nOLI coefficients ≥ 2013'),
        ('Heat', 'LST = ST band,\nK → °C; gaps filled\n(3×3, 5×5, 9×9 means)'),
        ('Dryness', 'NDBSI =\n(IBI + SI) / 2')]
cw = (MX1 - MX0 - 3 * 0.15) / 4
for k, (t, b) in enumerate(comp):
    x0 = MX0 + k * (cw + 0.15)
    arrow(x0 + cw / 2, 4.45, x0 + cw / 2, 4.85)
    box(x0, 4.85, x0 + cw, 6.55, t, b, C_GEE, E_GEE)
    arrow(x0 + cw / 2, 6.55, x0 + cw / 2, 6.95)
ax.text(MX0 + 0.05, 4.68, 'B2', fontsize=FS_SMALL + 0.5, fontweight='bold', va='center', color=E_GEE)
box(MX0, 6.95, MX1, 7.95, 'B3  Min–max normalization (per capital-year)',
    'Each component rescaled to 0–1 within the processing polygon; LST and NDBSI complemented', C_GEE, E_GEE)
arrow(6.0, 7.95, 6.0, 8.3)
box(MX0, 8.3, MX1, 9.55, 'B4  Principal component analysis (per capital-year)',
    'Covariance matrix of the four normalized components → PC1 (most of the variance; Table S4)\n'
    'RSEI = rescaled (1 − PC1), 0 = lowest and 1 = highest ecological quality in the capital-year', C_GEE, E_GEE)
arrow(6.0, 9.55, 6.0, 9.9)
box(MX0, 9.9, MX1, 11.2, 'B5  Spatial gap filling',
    'Residual masked pixels (persistent clouds, Landsat 7 scan-line gaps) filled with neighbourhood\n'
    'means (3 to 65 pixels) and, as a last resort, the polygon mean; pixels filled recorded', C_GEE, E_GEE)
arrow(6.0, 11.2, 6.0, 11.5)
box(MX0, 11.5, MX1, 12.8, 'B6  Export of annual RSEI assets',
    '27 capitals × 41 years = 1,107 images\nAudit of missing years → reprocessing until the series is complete',
    C_GEE, E_GEE)
# reprocessing loop
ax.annotate('', xy=(MX1 - 0.15, 3.97), xytext=(MX1 - 0.15, 12.0),
            arrowprops=dict(arrowstyle='-|>', color=E_GEE, lw=0.7, mutation_scale=6, linestyle=(0, (3, 2)),
                            connectionstyle='arc3,rad=0', shrinkA=0, shrinkB=0))
ax.text(MX1 - 0.25, 12.15, 'reprocess\nmissing years', fontsize=FS_SMALL - 0.5, ha='right', va='top', color=E_GEE)

# quality-control lane for B
box(QX0, 3.75, QX1, 6.25, 'QC1  PC1 orientation',
    'Pearson r between RSEI and NDVI\nand LST (120 m) in all 1,107 images;\n'
    '37 images with r(RSEI, NDVI) < 0\nre-oriented: RSEI′ = 1 − RSEI', C_QC, E_QC, dashed=True, tag='Table S3')
box(QX0, 6.55, QX1, 8.65, 'QC2  PCA structure',
    'Eigenvalues, variance explained\nand PC1 loadings of the four\ncomponents in 1985, 2005, 2025', C_QC, E_QC,
    dashed=True, tag='Table S4')
box(QX0, 8.95, QX1, 12.8, 'QC3  Completeness and gap filling',
    'Number of valid 32-day composites\nand of filled pixels per image;\n'
    'complete series of 41 years for\nall 27 capitals', C_QC, E_QC, dashed=True, tag='Table S1')
for (ya, yb) in ((8.9, 5.0), (8.9, 7.6), (10.55, 10.55), (12.15, 11.9)):
    arrow(MX1, ya, QX0, yb, color=E_QC, dashed=True, lw=0.6)

# ---------------------------------------------------------------- C. trend analysis
band(13.2, 15.55, 'C  Pixel-wise trends (GEE)', E_TR)
arrow(7.0, 12.8, 7.0, 13.65)
box(MX0, 13.65, MX1, 15.4, 'C1  Mann–Kendall test and Sen\'s slope (41 annual values per pixel)',
    'S, Var(S), Z and two-tailed p (α = 0.05); Kendall\'s τ; Sen\'s slope and intercept\n'
    'Temporal mean, median and standard deviation of the RSEI', C_TR, E_TR)
box(QX0, 13.65, QX1, 15.4, 'QC4  Serial autocorrelation',
    '1,000 random pixels per capital\n(27,000 series) and municipal series:\noriginal, tie-corrected, Hamed–Rao',
    C_QC, E_QC, dashed=True, tag='Table S5, Fig. S2')
arrow(MX1, 14.5, QX0, 14.5, color=E_QC, dashed=True, lw=0.6)

# ---------------------------------------------------------------- D. municipal synthesis
band(15.75, 18.55, 'D  Municipal synthesis', E_SY)
arrow(7.0, 15.4, 7.0, 16.2)
box(MX0, 16.2, 4.05, 18.4, 'D1  Clipping (Python/QGIS)',
    'Products clipped to the\nIBGE municipal\nboundaries (whole\nterritory, no urban mask)', C_SY, E_SY)
box(4.25, 16.2, 7.9, 18.4, 'D2  Trend classes',
    'Sign of τ: negative,\nnull, positive\np ≤ 0.05: significant\ndegradation/improvement', C_SY, E_SY)
box(8.1, 16.2, MX1, 18.4, 'D3  Variability classes',
    'Temporal SD: < 0.05 low,\n0.05–0.10 moderate,\n> 0.10 high', C_SY, E_SY)
arrow(4.05, 17.3, 4.25, 17.3)
arrow(7.9, 17.3, 8.1, 17.3)
box(QX0, 16.2, QX1, 18.4, 'D4  Area accounting',
    'Share of the municipal area in\neach class, by capital and region\n(area statistics at 30 m)', C_SY, E_SY,
    tag='Table 1, Table S2')
arrow(MX1, 17.3, QX0, 17.3, color=E_SY)

# ---------------------------------------------------------------- E. results
band(18.75, 21.45, 'E  Results', E_RES)
arrow(7.0, 18.4, 7.0, 19.2)
box(MX0, 19.2, 5.9, 21.3, 'Trend and variability maps',
    'Five panels per capital\n(Figures 3–11);\nannual RSEI maps (Figure S1)', C_RES, E_RES)
box(6.1, 19.2, MX1, 21.3, 'Regional comparison',
    'Capitals and the five\nmacro-regions (Sections 3–4);\nmunicipal series (Figure S2)', C_RES, E_RES)
box(QX0, 19.2, QX1, 21.3, 'Exploratory association',
    'Spearman ρ between trend-class\nshares and density / growth\n(n = 27; non-causal)', C_RES, E_RES,
    tag='Table S6')
arrow(QX0 + 2.5, 18.4, QX0 + 2.5, 19.2, color=E_SY)
# demographic data feed the association analysis (route along the right margin)
ax.plot([17.27, 17.27], [1.6, 20.25], color=E_IN, lw=0.6, ls=(0, (3, 2)))
ax.plot([17.15, 17.27], [1.6, 1.6], color=E_IN, lw=0.6, ls=(0, (3, 2)))
arrow(17.27, 20.25, QX1, 20.25, color=E_IN, dashed=True, lw=0.6)

fig.savefig(os.path.join(OUT, 'Figure_1.png'), dpi=600)
fig.savefig(os.path.join(OUT, 'Figure_1.svg'))
plt.close(fig)
print('Figure 1 written')
