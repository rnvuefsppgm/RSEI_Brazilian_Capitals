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
1. **Components** (`scripts/Colab/NEW_RSEI_2026_Luana_v3.py`, functions also in `scripts/RSEI/rsei_core.py`): NDVI;
   Tasseled Cap wetness (TM coefficients for years ≤ 2012, OLI coefficients for years ≥ 2013); LST = thermal band − 273.15;
   NDBSI = (IBI + SI)/2.
2. **Normalisation**: min–max scaling to 0–1 within the processing polygon of each capital-year; LST and NDBSI inverted.
3. **PCA**: covariance PCA computed separately for every capital and year (`ee.Reducer.centeredCovariance`); RSEI =
   rescaled (1 − PC1). Residual gaps are filled with focal means (radii 1–32 px) and the polygon mean. One asset per
   capital-year (1,107 images).
4. **Missing-year audit** (`quantifica_faltantes_rsei_multiplos_assets.ipynb`) and re-processing
   (`V2_Roda_RSEI_FALTANTE_NEW_RSEI_2026_Luana_v3.ipynb`).
5. **Trends** (`NEW_Trends_RSEI_2026_Luana_V3_multiplos_assets__b.ipynb`): pixel-wise Mann–Kendall S, Var(S) (no tie
   correction), continuity-corrected Z, two-tailed p, Kendall's tau, Sen's slope and intercept, temporal mean/median/SD.
6. **Orientation correction and recomputed trends** (`scripts/RSEI/S2_orientation_check_rsei_vs_components.py`,
   `scripts/Trend_Analysis/A1_recompute_trends_orientation_corrected.py`): capital-year images whose exported RSEI
   correlates negatively with NDVI (sign inversion of PC1) are re-oriented as 1 − RSEI before the trend analysis.
7. **Area accounting, sensitivity analyses and figures** (`scripts/Trend_Analysis`, `scripts/Validation`,
   `scripts/Figure_Generation`): municipal shares of significant degradation / no significant trend / significant
   improvement (Table 1); municipal annual series (Table S2, Figure S2); PCA loadings (Table S4); Hamed–Rao and tie
   corrections on 1,000 random pixels per capital (Table S5); demographic associations (Table S6); Figures 1 and 3–6.

## 5. Repository structure
```
scripts/Colab/              original Google Colab / Earth Engine Python scripts (sanitized; final pipeline)
scripts/Colab/archive_superseded_2025_workflow/   earlier scene-based versions, not used for the published results
scripts/GEE/                note on the Earth Engine implementation (Python API, no JavaScript scripts)
scripts/RSEI/               RSEI core functions, shared loaders, PCA loadings and orientation check
scripts/Trend_Analysis/     trend recomputation, Table 1 recomputation, autocorrelation sensitivity, demographic association
scripts/Validation/         local consistency checks on exported rasters
scripts/Figure_Generation/  Figures 1, 3–6, supplementary figures/tables, raster download
scripts/Python/             manuscript-revision tooling (docx editing, notebook sanitisation, repository assembly)
scripts/R/                  note (no R code was used for the published results)
data/boundaries/            IBGE municipal boundaries of the 27 capitals
data/results_tables/        CSV outputs of every analysis (inputs of the manuscript tables)
data/trend_products_clipped/ per-capital GeoTIFFs of tau, p-value, Sen's slope, mean, median, SD (clipped to the municipality)
documentation/              additional documentation
```

## 6. Dependencies
Python ≥ 3.10 and the packages in `requirements.txt` (earthengine-api, geemap, numpy, pandas, scipy, pymannkendall,
rasterio, geopandas, matplotlib, python-docx, lxml, openpyxl). QGIS 3.28 was used for the original cartography.

## 7. Running the code
1. Authenticate to Google Earth Engine once: `earthengine authenticate`.
2. Copy `config.example` to `.env` (or export the variables) and set `EE_PROJECT` to **your own** Google Cloud project.
   All scripts read the project id from the environment; no credentials are stored in this repository.
3. Annual RSEI: run `scripts/Colab/NEW_RSEI_2026_Luana_v3.py` in Colab or locally (edit `MUNS_TO_RUN` and the output
   asset root `OUT_ASSET_ROOT` to an asset folder you own; `CAP_JOIN2` must be replaced by your own processing polygons
   or by the IBGE boundaries in `data/boundaries`).
4. Audit and re-process missing years with the two notebooks listed above; then run the trend notebook (set
   `ASSET_IDS_LEITURA` and `OUTPUT_ASSET_FOLDER` to your assets).
5. Orientation check and corrected trends: `S2_orientation_check_rsei_vs_components.py`, then
   `A1_recompute_trends_orientation_corrected.py out_S2_orientation_check.csv`.
6. Tables and figures: `S5_table1_validation_from_trend_assets.py`, `S1_data_completeness_and_city_series.py`,
   `S3_pixel_sample_trend_sensitivity.py` + `S3b_local_trend_statistics.py`, `S4_pca_loadings_subset.py`,
   `S6_socioeconomic_association.py`, `S7_download_trend_products.py`, `F0_...`, `F1_...`, `FS_...`.
   The Earth Engine scripts respect the concurrency limits of a non-commercial project; expect several hours for the
   full set.

## 8. Outputs and their relation to the manuscript
| Product | Script | Manuscript item |
|---|---|---|
| `out_S5_table1_recomputed.csv` | S5 | Table 1, Section 3.1–3.6 |
| `out_S1_city_annual_series.csv` | S1 | Table S1, Table S2, Figure S2 |
| `out_S2_orientation_check.csv` | S2 | Table S3, Section 2.4.6 / 3.8 |
| `out_S4_pca_loadings.csv` | S4 | Table S4 |
| `out_S3b_*.csv` | S3/S3b | Table S5, Section 3.8 |
| `out_S6_*.csv` | S6 | Table S6, Section 3.8 / 4.7 |
| `Figure_1.png/svg` | F0 | Figure 1 |
| `Figure_3..6.png/svg` | F1 (+S7) | Figures 3–6 |
| `Figure_S2`, `Tables_S1_S6` | FS | Supplementary material |

## 9. Limitations of reproduction
* The Earth Engine assets with the 1,107 annual RSEI images and the trend products are stored in the authors' projects;
  reproducing them from scratch requires running the processing scripts (several hours of batch exports) with your own
  assets. The clipped trend products are distributed in `data/trend_products_clipped/`.
* `LANDSAT/COMPOSITES/C02/T1_L2_32DAY` is maintained by Google/USGS; reprocessing of the composites may change values slightly.
* Figures 3–6 are rendered at 30 m for municipalities up to ~4,000 km² and at 40–150 m for larger municipalities
  (`data/results_tables/scale_used.csv`); all area statistics were computed at 30 m.

## 10. Licence and citation
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
