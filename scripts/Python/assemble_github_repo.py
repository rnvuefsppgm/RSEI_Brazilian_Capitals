# -*- coding: utf-8 -*-
"""
assemble_github_repo.py  (RNV, 2026)
Builds the public repository tree from the sanitized scripts and the New_for_Review /
Adapted scripts, writes README.md, LICENSE, .gitignore, requirements.txt and
config.example, and clips the per-capital trend products to the municipal
boundaries for distribution. Internal provenance reports (Drive ids) are NOT copied.
Usage: python assemble_github_repo.py <scripts_root> <trend_raster_dir> <repo_dir> <repo_url>
"""
import sys
import os
import shutil
import glob
import json
import numpy as np

SRC, RAST, REPO, URL = sys.argv[1:5]
FINAL = ['NEW_RSEI_2026_Luana_v3.py', 'quantifica_faltantes_rsei_multiplos_assets.ipynb',
         'V2_Roda_RSEI_FALTANTE_NEW_RSEI_2026_Luana_v3.ipynb', 'NEW_Trends_RSEI_2026_Luana_V3_multiplos_assets__b.ipynb']
SUPERSEDED = ['BANDS_RSEI_PCA.ipynb', 'BANDS_RSEI_PCA_v2.ipynb', 'Export_data_Bandas_RSEI_cidades_Preenche_hole_V3.ipynb',
              'Export_data_Bandas_RSEI_cidades_V2.ipynb', 'export_data_temperatura_cidades.ipynb', 'Trend_RSEI.ipynb',
              'Trend_RSEI_GAP_FILL.ipynb', 'Trend_RSEI_GAP_FILL_v2.ipynb', 'Trend_RSEI_GAP_FILL_fixed.ipynb',
              'Trend_RSEI_GAP_FILL_kendall_band.ipynb', 'Trend_RSEI_GAP_FILL_export_fix.ipynb',
              'Trend_RSEI_GAP_FILL_Media_Mediana_desvpad.ipynb', 'Trend_RSEI_GAP_FILL_Final.ipynb',
              'NEW_Trends_RSEI_2026_Luana_V3_multiplos_assets__a.ipynb']


def mk(*p):
    d = os.path.join(REPO, *p)
    os.makedirs(d, exist_ok=True)
    return d


if os.path.exists(REPO):
    for n in os.listdir(REPO):
        if n != '.git':
            p = os.path.join(REPO, n)
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
mk()
# --- original (sanitized) Colab / GEE scripts ---
for n in FINAL:
    shutil.copy(os.path.join(SRC, 'Colab', n), mk('scripts', 'Colab'))
for n in SUPERSEDED:
    shutil.copy(os.path.join(SRC, 'Colab', n), mk('scripts', 'Colab', 'archive_superseded_2025_workflow'))
# the GEE processing is Python API code; keep a pointer folder for clarity
open(os.path.join(mk('scripts', 'GEE'), 'README.md'), 'w', encoding='utf-8').write(
    "# Google Earth Engine processing\n\nAll Earth Engine processing in this study was written with the Earth Engine "
    "Python API and executed in Google Colab. The scripts are in `../Colab` (annual RSEI computation, missing-year audit "
    "and re-processing, pixel-wise Mann-Kendall / Sen's slope trends) and `../RSEI`, `../Trend_Analysis`. No JavaScript "
    "Code Editor scripts were used.\n")
# --- RSEI core, trends, validation, figures ---
for n in ['rsei_core.py', 'ee_common.py', 'municipal_geometries.py', 'S4_pca_loadings_subset.py',
          'S2_orientation_check_rsei_vs_components.py']:
    shutil.copy(os.path.join(SRC, 'New_for_Review', n), mk('scripts', 'RSEI'))
for n in ['S1_data_completeness_and_city_series.py', 'S3_pixel_sample_trend_sensitivity.py', 'S3b_local_trend_statistics.py',
          'S5_table1_validation_from_trend_assets.py', 'S6_socioeconomic_association.py']:
    shutil.copy(os.path.join(SRC, 'New_for_Review', n), mk('scripts', 'Trend_Analysis'))
shutil.copy(os.path.join(SRC, 'Adapted', 'A1_recompute_trends_orientation_corrected.py'), mk('scripts', 'Trend_Analysis'))
for n in ['L1_local_rasters_epoch_consistency.py']:
    shutil.copy(os.path.join(SRC, 'New_for_Review', n), mk('scripts', 'Validation'))
for n in ['F0_make_figure_1_workflow.py', 'F1_make_figures_3_to_6.py', 'F2_export_figures_png600_svg.py',
          'S7_download_trend_products.py', 'FS_make_supplementary_figures_tables.py']:
    p = os.path.join(SRC, 'New_for_Review', n)
    if os.path.exists(p):
        shutil.copy(p, mk('scripts', 'Figure_Generation'))
for n in ['build_revised_manuscript.py', 'docx_revision_tools.py', 'revision_stats.py', 'sanitize_notebooks.py',
          'assemble_github_repo.py', 'word_locate_and_export.py']:
    shutil.copy(os.path.join(SRC, 'Python', n), mk('scripts', 'Python'))
mk('scripts', 'R')
open(os.path.join(REPO, 'scripts', 'R', 'README.md'), 'w', encoding='utf-8').write(
    "# R\n\nNo R code was used to produce the published results. The original submission mentioned the R package "
    "`trend`; the pixel-wise Mann-Kendall / Sen's slope analysis was in fact implemented in Earth Engine "
    "(`../Colab/NEW_Trends_RSEI_2026_Luana_V3_multiplos_assets__b.ipynb`), and the sensitivity analyses in Python "
    "(`pymannkendall`). Two small R helper scripts used only to organise exported files locally are not part of the "
    "scientific workflow and were not published.\n")
# --- data: boundaries + results tables + clipped trend products ---
for ext in ('shp', 'shx', 'dbf', 'prj', 'cpg'):
    shutil.copy(os.path.join(SRC, 'data', 'Capitais.' + ext), mk('data', 'boundaries'))
for n in glob.glob(os.path.join(SRC, 'New_for_Review', 'out_*.csv')) + [os.path.join(SRC, 'New_for_Review', 'scale_used.csv')]:
    if os.path.exists(n) and 'pixel_samples' not in n and 'CAPJOIN2' not in n:
        shutil.copy(n, mk('data', 'results_tables'))
# clipped trend products
try:
    import rasterio
    from rasterio.mask import mask as rio_mask
    import geopandas as gpd
    gdf = gpd.read_file(os.path.join(SRC, 'data', 'Capitais.shp')).to_crs(4326)
    import unicodedata

    def slug(s):
        s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
        return ''.join(c if c.isalnum() else '_' for c in s).strip('_')
    out = mk('data', 'trend_products_clipped')
    for _, r in gdf.iterrows():
        for b in ['tau', 'p_value', 'sen_slope', 'mean', 'median', 'stdDev']:
            p = os.path.join(RAST, f'trend_{slug(r.NM_MUN)}_RSEI_{b}.tif')
            if not os.path.exists(p):
                continue
            with rasterio.open(p) as src:
                arr, tr = rio_mask(src, [r.geometry], crop=True, nodata=-9999, filled=True)
                prof = src.profile
            prof.update(height=arr.shape[1], width=arr.shape[2], transform=tr, nodata=-9999, compress='lzw', dtype='float32')
            with rasterio.open(os.path.join(out, f'{slug(r.NM_MUN)}_RSEI_{b}.tif'), 'w', **prof) as dst:
                dst.write(arr.astype('float32'))
    print('trend products clipped')
except Exception as e:
    print('clipping skipped:', e)

open(os.path.join(REPO, '.gitignore'), 'w').write(
    "# credentials and private configuration\n*.json\n!data/**/*.json\ncredentials*\n.config/\n*.pem\n*.key\nconfig.py\n"
    ".env\n# python\n__pycache__/\n*.pyc\n.ipynb_checkpoints/\n# large intermediate files\n*_pixel_samples.csv\n"
    "trend_rasters/\n*.ovr\n*.aux.xml\n")
open(os.path.join(REPO, 'config.example'), 'w').write(
    "# Copy to .env or export in your shell before running the Earth Engine scripts\n"
    "EE_PROJECT=your-google-cloud-project-id\n"
    "# Optional: path to the IBGE capital boundaries shapefile (default: data/boundaries/Capitais.shp)\n"
    "CAPITAIS_SHP=data/boundaries/Capitais.shp\n")
open(os.path.join(REPO, 'requirements.txt'), 'w').write(
    "earthengine-api>=1.0\ngeemap\nnumpy\npandas\nscipy\npymannkendall\nrasterio\ngeopandas\nmatplotlib\npython-docx\nlxml\nopenpyxl\n")
open(os.path.join(REPO, 'LICENSE'), 'w').write(
    "MIT License\n\nCopyright (c) 2026 The authors of \"Spatiotemporal dynamics of urban ecological quality based on the "
    "Remote Sensing Ecological Index (RSEI) in the Brazilian state capitals (1985-2025)\"\n\nPermission is hereby granted, "
    "free of charge, to any person obtaining a copy of this software and associated documentation files (the \"Software\"), "
    "to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, "
    "publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is "
    "furnished to do so, subject to the following conditions:\n\nThe above copyright notice and this permission notice shall "
    "be included in all copies or substantial portions of the Software.\n\nTHE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT "
    "WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A "
    "PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, "
    "DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION "
    "WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.\n")
shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'README_repo.md'), os.path.join(REPO, 'README.md'))
mk('documentation')
print('repo assembled at', REPO)
