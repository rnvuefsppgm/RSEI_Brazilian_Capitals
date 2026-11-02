# -*- coding: utf-8 -*-
"""
Supplementary figures and tables. New for Review (2026).
Builds Figure S2 (municipal annual mean RSEI series with Sen's slope line; PNG 600 dpi
and SVG) and Tables S1-S6 (Excel workbook with one sheet per table, plus a Word
document with the same tables and captions) from the CSV outputs of the review analyses (scripts 05-13).
Usage: python 18_supplementary_tables_s1_s6_and_figure_s2.py <nfr_dir> <out_dir>
"""
import sys
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import docx
from docx.shared import Pt

NFR, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
plt.rcParams['svg.fonttype'] = 'none'
R = lambda n: pd.read_csv(os.path.join(NFR, n))

# ---------------- Figure S2 ----------------
s1 = R('out_S1_city_annual_series.csv').sort_values(['NM_MUN', 'ANO'])
cs = R('out_S3b_city_series_results.csv').set_index('NM_MUN') if os.path.exists(os.path.join(NFR, 'out_S3b_city_series_results.csv')) else None
muns = sorted(s1.NM_MUN.unique())
fig, axes = plt.subplots(7, 4, figsize=(13, 16), dpi=100, sharex=True)
axes = axes.ravel()
for ax, m in zip(axes, muns):
    g = s1[s1.NM_MUN == m]
    ax.plot(g.ANO, g.RSEI_mean, '-o', ms=2.2, lw=0.9, color='#1f77b4')
    if cs is not None and m in cs.index:
        sl = cs.loc[m, 'sen_slope']
        y0 = np.median(g.RSEI_mean.values - sl * (g.ANO.values - g.ANO.values[0]))
        ax.plot(g.ANO, y0 + sl * (g.ANO - g.ANO.values[0]), '--', color='#d62728', lw=0.9)
        p = cs.loc[m, 'p_hamed_rao']
        ax.set_title(f"{m}  (Sen = {sl:+.4f}/yr, p(HR) = {p:.3f})", fontsize=8)
    else:
        ax.set_title(m, fontsize=8)
    ax.set_ylim(0.3, 0.9)
    ax.tick_params(labelsize=7)
    ax.grid(alpha=0.3, lw=0.4)
for ax in axes[len(muns):]:
    ax.axis('off')
fig.supylabel('Municipal mean RSEI', fontsize=10)
fig.supxlabel('Year', fontsize=10)
plt.tight_layout()
fig.savefig(os.path.join(OUT, 'Figure_S2.png'), dpi=600)
fig.savefig(os.path.join(OUT, 'Figure_S2.svg'))
plt.close(fig)

# ---------------- Tables ----------------
tabs = {}
caps = {}
# S1 completeness
g = s1.groupby('NM_MUN')
t1 = pd.DataFrame({'Years available (1985-2025)': g['ANO'].count(),
                   'Images with residual gaps after filling': g['missing_after_fill'].apply(lambda x: int((x > 0).sum())),
                   'Mean pixels filled per image (before fill)': g['missing_before_fill'].mean().round(0),
                   'Max pixels filled in one image': g['missing_before_fill'].max(),
                   'Mean municipal RSEI 1985-2025': g['RSEI_mean'].mean().round(3)}).reset_index().rename(columns={'NM_MUN': 'Capital'})
tabs['Table S1'] = t1
caps['Table S1'] = ("Table S1. Data completeness and gap-filling diagnostics of the 1,107 annual RSEI images (27 capitals × 41 years). "
                    "'Pixels filled' is the number of pixels of the processing polygon that were masked after compositing and were "
                    "filled by the focal-mean / polygon-mean procedure, as recorded by the processing script.")
# S2 municipal trend stats
t5 = R('out_S5_table1_recomputed.csv')
cols = ['municipio', 'tau_negative_pct', 'tau_zero_pct', 'tau_positive_pct', 'degradation_pct', 'no_significant_trend_pct',
        'improvement_pct', 'sen_slope_mean', 'RSEI_mean_of_means', 'RSEI_stdDev_mean', 'area_km2_valid']
t2 = t5[cols].rename(columns={'municipio': 'Capital', 'tau_negative_pct': 'τ < 0 (%)', 'tau_zero_pct': 'τ = 0 (%)',
                              'tau_positive_pct': 'τ > 0 (%)', 'degradation_pct': 'Significant degradation (%)',
                              'no_significant_trend_pct': 'No significant trend (%)', 'improvement_pct': 'Significant improvement (%)',
                              'sen_slope_mean': "Mean Sen's slope (yr⁻¹)", 'RSEI_mean_of_means': 'Mean of temporal mean RSEI',
                              'RSEI_stdDev_mean': 'Mean of temporal SD', 'area_km2_valid': 'Municipal area (km²)'})
if cs is not None:
    c2 = cs.reset_index()[['NM_MUN', 'tau_gee', 'p_gee', 'p_hamed_rao', 'sen_slope', 'lag1_residuals']].rename(columns={
        'NM_MUN': 'Capital', 'tau_gee': 'τ (municipal mean series)', 'p_gee': 'p (original MK)', 'p_hamed_rao': 'p (Hamed–Rao)',
        'sen_slope': "Sen's slope of municipal series (yr⁻¹)", 'lag1_residuals': 'Lag-1 autocorrelation of residuals'})
    t2 = t2.merge(c2, on='Capital', how='left')
tabs['Table S2'] = t2.round(4)
caps['Table S2'] = ("Table S2. Municipal trend statistics: shares of the municipal area with negative, null and positive Kendall's τ "
                    "irrespective of significance (the classes of the trend maps), the three significance classes of Table 1, mean Sen's "
                    "slope, mean of the temporal mean and standard deviation of the RSEI, and the Mann–Kendall statistics of the "
                    "municipal annual mean series (original test and Hamed–Rao variance-corrected test).")
# S3 orientation
s2 = R('out_S2_orientation_check.csv')
t3 = s2[['NM_MUN', 'ANO', 'r_RSEI_NDVI', 'r_RSEI_LST']].rename(columns={'NM_MUN': 'Capital', 'ANO': 'Year', 'r_RSEI_NDVI': 'r(RSEI, NDVI)', 'r_RSEI_LST': 'r(RSEI, LST)'})
t3['Re-oriented'] = np.where(t3['r(RSEI, NDVI)'] < 0, 'yes', 'no')
tabs['Table S3'] = t3.sort_values(['Capital', 'Year']).round(3)
caps['Table S3'] = ("Table S3. Orientation check of every capital-year RSEI image: Pearson correlation (120 m) between the exported RSEI "
                    "and the NDVI and LST of the annual median composite. Images with r(RSEI, NDVI) < 0 were re-oriented (RSEI′ = 1 − RSEI) "
                    "before the trend analysis.")
# S4 PCA
s4 = R('out_S4_pca_loadings.csv').dropna(subset=['eig1'])
t4 = s4.rename(columns={'NM_MUN': 'Capital', 'ANO': 'Year', 'scale_m': 'Scale (m)', 'eig1': 'λ1', 'eig2': 'λ2', 'eig3': 'λ3', 'eig4': 'λ4',
                        'PC1_var_explained_pct': 'PC1 variance (%)', 'load_nNDVI': 'Loading NDVI', 'load_nWET': 'Loading WET',
                        'load_nNDSI_inv': 'Loading NDBSI (inverted)', 'load_nLST_inv': 'Loading LST (inverted)'})
tabs['Table S4'] = t4.round(4)
caps['Table S4'] = ("Table S4. Eigenvalues (λ), variance explained by PC1 and PC1 loadings of the per-capital PCA of the four normalized "
                    "components in 1985, 2005 and 2025, recomputed with the functions of the original processing script. Equal signs of "
                    "the four loadings indicate that PC1 is a general ecological-quality axis (the sign itself is arbitrary).")
# S5 sensitivity
if os.path.exists(os.path.join(NFR, 'out_S3b_pixel_summary_by_city.csv')):
    s3 = R('out_S3b_pixel_summary_by_city.csv')
    tabs['Table S5'] = s3.round(3).rename(columns={'NM_MUN': 'Capital'})
    caps['Table S5'] = ("Table S5. Sensitivity of the Mann–Kendall significance (p ≤ 0.05) to the tie correction and to the Hamed–Rao "
                        "variance correction for serial autocorrelation, on 1,000 random pixels per capital (series of 41 years): share of "
                        "series with a significant trend under each test, shares of significant degradation and improvement, share of "
                        "series losing significance after the correction, median lag-1 autocorrelation of the series and of the "
                        "Sen-detrended residuals, and median Sen's slope.")
# S6 socioeconomic
s6 = R('out_S6_socioeconomic.csv')
sp = R('out_S6_spearman.csv')
tabs['Table S6a'] = s6.round(2).rename(columns={'municipio': 'Capital'})
tabs['Table S6b'] = sp.round(4)
caps['Table S6a'] = ("Table S6. (a) Resident population (IBGE Censuses 1991, 2000, 2022), municipal area, population density in 2022 and "
                     "relative growth 1991–2022 of the 27 capitals, with the shares of significant degradation and improvement (Table 1); "
                     "(b) Spearman rank correlations between the trend classes and the demographic indicators (n = 27).")
caps['Table S6b'] = ""

with pd.ExcelWriter(os.path.join(OUT, 'Tables_S1_S6.xlsx')) as xw:
    for k, v in tabs.items():
        v.to_excel(xw, sheet_name=k.replace(' ', '_'), index=False)
D = docx.Document()
st = D.styles['Normal']
st.font.name = 'Times New Roman'
st.font.size = Pt(9)
D.add_heading('Supplementary Tables S1–S6', 1)
D.add_paragraph('Spatiotemporal dynamics of urban ecological quality based on the Remote Sensing Ecological Index (RSEI) in '
                'the Brazilian state capitals (1985–2025). Figure S1 (annual RSEI maps) is provided as a separate file; Figure S2 '
                '(municipal annual mean RSEI series) accompanies this document.')
for k, v in tabs.items():
    if caps.get(k):
        D.add_paragraph(caps[k])
    if len(v) > 300:
        D.add_paragraph(f'({len(v)} rows; the complete table is provided in the Excel file Tables_S1_S6.xlsx, sheet {k}. '
                        f'Only the rows flagged as re-oriented are listed below.)')
        v = v[v['Re-oriented'] == 'yes'] if 'Re-oriented' in v.columns else v.head(50)
    tb = D.add_table(rows=1, cols=len(v.columns))
    tb.style = 'Table Grid'
    for i, c in enumerate(v.columns):
        tb.rows[0].cells[i].text = str(c)
    for _, row in v.iterrows():
        cells = tb.add_row().cells
        for i, c in enumerate(v.columns):
            x = row[c]
            cells[i].text = '' if pd.isna(x) else (f'{x:.4g}' if isinstance(x, float) else str(x))
    D.add_paragraph('')
D.add_paragraph('Figure S2. Annual municipal mean RSEI (1985–2025) of the 27 Brazilian state capitals, computed within the official '
                'municipal boundaries, with the Sen\'s slope line (dashed) and the p-value of the Hamed–Rao variance-corrected '
                'Mann–Kendall test of the municipal series.')
D.add_picture(os.path.join(OUT, 'Figure_S2.png'), width=docx.shared.Cm(16))
cp = D.core_properties
cp.author = 'RNV'
cp.last_modified_by = 'RNV'
D.save(os.path.join(OUT, 'Supplementary_Tables_S1_S6_and_Figure_S2.docx'))
print('supplementary written:', list(tabs))
