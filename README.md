# Spatiotemporal dynamics of urban ecological quality (RSEI) in the Brazilian state capitals, 1985–2025

Code and derived products supporting the manuscript *Spatiotemporal dynamics of urban ecological quality based on the
Remote Sensing Ecological Index (RSEI) in the Brazilian state capitals (1985–2025)* (Urban Ecosystems, revised version).

## 1. Objectives
Build annual Remote Sensing Ecological Index (RSEI) series for the 27 Brazilian state capitals over 1985–2025 (41 years),
test pixel-wise monotonic trends with the Mann–Kendall test and Sen's slope, and compare the resulting trajectories among
capitals and macro-regions, together with sensitivity analyses on the construction of the index.

## 2. Study area and period
All 27 capitals of the Brazilian federative units (26 states and the Federal District), 1985–2025. Earth Engine processing
was run on processing polygons that encompass each municipality and its surroundings (feature collection `CAP_JOIN2`);
all statistics reported in the manuscript are computed after clipping the products to the official IBGE municipal
boundaries (`data/boundaries/Capitais.shp`, IBGE 2022 municipal mesh).

## 3. Data sources and Landsat products
* `LANDSAT/COMPOSITES/C02/T1_L2_32DAY` (Google Earth Engine): USGS Collection 2 Level-2 32-day composites of Landsat 5 TM,
  7 ETM+ and 8–9 OLI/TIRS surface reflectance and surface temperature (cloud/shadow masked, harmonized bands
  `blue, green, red, nir, swir1, swir2, thermal`). Annual median composites are built per calendar year.
* Demographic data: IBGE Censuses 1991, 2000 and 2022 and municipal area, via the SIDRA API (tables 200, 4709, 4714).

## 4. Methodology (as implemented in the code)
1. **Components** (`01_compute_annual_rsei_by_capital.py`, functions also in `common/rsei_original_functions.py`):
   NDVI; Tasseled Cap wetness (TM coefficients for years ≤ 2012, OLI coefficients for years ≥ 2013);
   LST = thermal band − 273.15; NDBSI = (IBI + SI)/2.
2. **Normalisation**: min–max scaling to 0–1 within the processing polygon of each capital-year; LST and NDBSI inverted.
3. **PCA**: covariance PCA computed separately for every capital and year (`ee.Reducer.centeredCovariance`); RSEI =
   rescaled (1 − PC1). Residual gaps are filled with focal means (radii 1–32 px) and the polygon mean. One asset per
   capital-year (1,107 images).
4. **Missing-year audit and re-processing** (`02_audit_missing_annual_rsei_images.ipynb`,
   `03_reprocess_missing_annual_rsei_images.ipynb`).
5. **Trends** (`04_pixelwise_mann_kendall_sen_trends.ipynb`): pixel-wise Mann–Kendall S, Var(S) (no tie correction),
   continuity-corrected Z, two-tailed p, Kendall's tau, Sen's slope and intercept, temporal mean/median/SD.
6. **Orientation correction and recomputed trends** (`05_check_pc1_orientation_against_ndvi_lst.py`,
   `10_recompute_trends_after_orientation_correction.py`): capital-year images whose exported RSEI correlates negatively
   with NDVI (sign inversion of PC1) are re-oriented as 1 − RSEI before the trend analysis.
7. **Area accounting, sensitivity analyses and figures** (scripts 06–19): municipal shares of significant degradation /
   no significant trend / significant improvement (Table 1); municipal annual series (Table S2, Figure S2); PCA loadings
   (Table S4); Hamed–Rao and tie corrections on 1,000 random pixels per capital (Table S5); demographic associations
   (Table S6); Figures 1, 3–6 and S1.

## 5. Script index
Scripts are numbered in execution order. The last column gives the short code used for each analysis in the response
letters to the reviewers.

| # | Script | What it does | Code in the responses |
|---|---|---|---|
| 01 | `scripts/Colab/01_compute_annual_rsei_by_capital.py` | Annual median Landsat composites, NDVI/WET/LST/NDBSI, min–max normalisation, per capital-year PCA, RSEI export (one asset per capital-year) | original pipeline |
| 02 | `scripts/Colab/02_audit_missing_annual_rsei_images.ipynb` | Lists the RSEI assets and reports missing capital-years | original pipeline |
| 03 | `scripts/Colab/03_reprocess_missing_annual_rsei_images.ipynb` | Re-runs script 01 only for the missing capital-years | original pipeline |
| 04 | `scripts/Colab/04_pixelwise_mann_kendall_sen_trends.ipynb` | Pixel-wise Mann–Kendall, Kendall's tau, Sen's slope and temporal mean/median/SD per capital | original pipeline |
| 05 | `scripts/RSEI/05_check_pc1_orientation_against_ndvi_lst.py` | Pearson correlation of every exported RSEI image with NDVI and LST; flags sign-inverted PC1 (Table S3) | S2 |
| 06 | `scripts/RSEI/06_pca_eigenvalues_loadings_1985_2005_2025.py` | Recomputes eigenvalues, explained variance and PC1 loadings for 1985, 2005 and 2025 (Table S4) | S4 |
| 07 | `scripts/Trend_Analysis/07_data_completeness_and_municipal_rsei_series.py` | Checks completeness of the 27 × 41 series and extracts the municipal mean/median RSEI per year (Tables S1–S2, Figure S2) | S1 |
| 08 | `scripts/Trend_Analysis/08_sample_random_pixel_rsei_series.py` | Draws 1,000 random pixels per capital and extracts their annual RSEI series | S3 |
| 09 | `scripts/Trend_Analysis/09_trend_sensitivity_hamed_rao_autocorrelation.py` | Replicates the Earth Engine Mann–Kendall on the sampled pixels and compares it with the Hamed–Rao variance correction and lag-1 autocorrelation (Table S5) | S3b |
| 10 | `scripts/Trend_Analysis/10_recompute_trends_after_orientation_correction.py` | Re-orients the flagged images (1 − RSEI) and recomputes the pixel-wise trends with the original code of script 04 | A1 |
| 11 | `scripts/Figure_Generation/11_download_trend_rasters_by_capital.py` | Downloads tau, p-value, mean, median and SD rasters per capital (scale per municipality in `scale_used.csv`) | S7 |
| 12 | `scripts/Trend_Analysis/12_table1_trend_class_shares_by_capital.py` | Shares of significant degradation, no significant trend and significant improvement within each municipality (Table 1) | S5 |
| 13 | `scripts/Trend_Analysis/13_spearman_trends_vs_demographic_indicators.py` | Downloads IBGE/SIDRA demographic indicators and computes Spearman correlations with the trend shares (Table S6) | S6 |
| 14 | `scripts/Validation/14_check_exported_rasters_epoch_consistency.py` | Consistency check of locally exported rasters across epochs | L1 |
| 15 | `scripts/Figure_Generation/15_figure1_workflow_diagram.py` | Figure 1 (methodological workflow) | F0 |
| 16 | `scripts/Figure_Generation/16_figures3_to_6_trend_maps.py` | Figures 3–6 (tau, mean, median and SD maps of the 27 capitals) | F1 |
| 17 | `scripts/Figure_Generation/17_export_figures_png600_svg.py` | Exports the figures as 600 dpi PNG and editable SVG | F2 |
| 18 | `scripts/Figure_Generation/18_supplementary_tables_s1_s6_and_figure_s2.py` | Tables S1–S6 (xlsx/docx) and Figure S2 from the CSV outputs | FS |
| 19 | `scripts/Figure_Generation/19_figure_s1_annual_rsei_maps.py` | Figure S1: annual RSEI maps of every capital (re-oriented images) | FS1 |

Shared modules in `scripts/common/`: `gee_init_and_rsei_assets.py` (Earth Engine initialisation and loading of the annual
RSEI collection), `municipal_boundaries.py` (IBGE boundaries as Earth Engine geometries), `rsei_original_functions.py`
(helper functions copied verbatim from script 01) and `wait_for_earth_engine_tasks.py` (waits for the export tasks of
script 10). `scripts/Python/sanitize_colab_notebooks.py` removes outputs, metadata and private identifiers from notebooks.

The notebooks in `scripts/Colab/archive_superseded_2025_workflow/` (prefixes `2025_01`–`2025_13` in chronological order,
and `2026_01`) document the earlier scene-based workflow and a first trend run on incomplete series. They were not used
for the published results.

## 6. Repository structure
```
scripts/Colab/              original Google Colab / Earth Engine Python pipeline (01–04, sanitized)
scripts/Colab/archive_superseded_2025_workflow/   earlier versions, not used for the published results
scripts/common/             shared modules imported by scripts 05–19
scripts/RSEI/               PC1 orientation check and PCA loadings (05–06)
scripts/Trend_Analysis/     completeness, trend sensitivity, corrected trends, Table 1, demographic association (07–10, 12–13)
scripts/Validation/         local consistency checks on exported rasters (14)
scripts/Figure_Generation/  raster download, Figures 1, 3–6, S1, S2 and supplementary tables (11, 15–19)
scripts/Python/             notebook sanitisation utility
scripts/GEE/                note on the Earth Engine implementation (Python API, no JavaScript scripts)
scripts/R/                  note (no R code was used for the published results)
data/boundaries/            IBGE municipal boundaries of the 27 capitals
data/results_tables/        CSV outputs of every analysis (inputs of the manuscript tables)
data/trend_products_clipped/ per-capital GeoTIFFs of tau, p-value, mean, median, SD (clipped to the municipality)
```

## 7. Dependencies
Python ≥ 3.10 and the packages in `requirements.txt` (earthengine-api, geemap, numpy, pandas, scipy, pymannkendall,
rasterio, geopandas, matplotlib, python-docx, lxml, openpyxl). QGIS 3.28 was used for the original cartography.

## 8. Running the code
1. Authenticate to Google Earth Engine once: `earthengine authenticate`.
2. Copy `config.example` to `.env` (or export the variables) and set `EE_PROJECT` to **your own** Google Cloud project.
   No project identifiers, user names or credentials of the authors are stored in this repository: every asset path is
   written as `projects/YOUR_PROJECT/assets/...` (the annual images were exported in two batches, written as
   `YOUR_PROJECT` and `YOUR_PROJECT_2`; if you export everything to one folder, keep a single entry).
3. Annual RSEI: run `01_compute_annual_rsei_by_capital.py` in Colab or locally (edit `MUNS_TO_RUN` and the output asset
   root `OUT_ASSET_ROOT`; `CAP_JOIN2` must be replaced by your own processing polygons or by the IBGE boundaries in
   `data/boundaries`).
4. Audit and re-process missing years with notebooks 02 and 03; then run notebook 04 (set `ASSET_IDS_LEITURA` and
   `OUTPUT_ASSET_FOLDER` to your assets).
5. Review analyses: set `RSEI_ASSET_ROOTS` (comma-separated folders with the annual images) and run scripts 05–09 from
   their folder; then `10_recompute_trends_after_orientation_correction.py out_S2_orientation_check.csv`, wait for the
   exports (`common/wait_for_earth_engine_tasks.py`), set `TREND_ROOT=projects/<EE_PROJECT>/assets/RSEI_TRENDS_2026_oriented`
   and run scripts 11–13 and 15–19. The Earth Engine scripts respect the concurrency limits of a non-commercial project;
   expect several hours for the full set.

## 9. Outputs and their relation to the manuscript
| Product (`data/results_tables/`) | Script | Manuscript item |
|---|---|---|
| `out_S5_table1_recomputed.csv` | 12 | Table 1, Sections 3.1–3.6 |
| `out_S1_city_annual_series.csv` | 07 | Tables S1–S2, Figure S2 |
| `out_S2_orientation_check.csv` | 05 | Table S3, Sections 2.4.6 and 3.8 |
| `out_S4_pca_loadings.csv` | 06 | Table S4 |
| `out_S3b_*.csv` | 08–09 | Table S5, Section 3.8 |
| `out_S6_*.csv` | 13 | Table S6, Sections 3.8 and 4.7 |
| `Figure_1.png/svg` | 15 | Figure 1 |
| `Figure_3..6.png/svg` | 16 (+11) | Figures 3–6 |
| `Figure_S1`, `Figure_S2`, `Tables_S1_S6` | 19, 18 | Supplementary material |

The CSV file names keep the analysis codes of the response letters (S1–S6). Asset identifiers inside the tables are
written with the `YOUR_PROJECT` placeholder.

## 10. Limitations of reproduction
* The Earth Engine assets with the 1,107 annual RSEI images and the trend products are stored in the authors' projects;
  reproducing them from scratch requires running the processing scripts (several hours of batch exports) with your own
  assets. The clipped trend products are distributed in `data/trend_products_clipped/`.
* `LANDSAT/COMPOSITES/C02/T1_L2_32DAY` is maintained by Google/USGS; reprocessing of the composites may change values slightly.
* Figures 3–6 are rendered at 30 m for municipalities up to ~4,000 km² and at 40–150 m for larger municipalities
  (`data/results_tables/scale_used.csv`); all area statistics were computed at 30 m.

## 11. Licence and citation
* **Code** (scripts, notebooks, modules): MIT licence (see `LICENSE`).
* **Data and derived products** (`data/results_tables/`, `data/trend_products_clipped/`, tables and figures):
  Creative Commons Attribution 4.0 International, CC BY 4.0 (see `LICENSE-DATA`). They are free to use, share and
  adapt for any purpose, provided that the source is cited.
* **Third-party inputs** keep their own terms: Landsat Collection 2 composites (USGS, public domain) and the municipal
  boundaries (IBGE, open data with attribution).

Please cite the manuscript when using this code or the derived products (citation metadata in `CITATION.cff`;
GitHub shows it under "Cite this repository"):

> Lima LB, Vasconcelos RN, Cebrian F, Santana MMM, Franca Rocha WJSA (2026) Spatiotemporal dynamics of urban
> ecological quality based on the Remote Sensing Ecological Index (RSEI) in the Brazilian state capitals (1985–2025).
> Urban Ecosystems (under review). Code and data: https://github.com/rnvuefsppgm/RSEI_Brazilian_Capitals

A versioned archive of the repository with a DOI will be deposited in Zenodo upon acceptance.
