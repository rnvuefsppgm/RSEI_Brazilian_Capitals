# -*- coding: utf-8 -*-
"""
revision_stats.py  (New for Review, 2026)
Collects, from the CSV outputs of the New_for_Review analyses, every number quoted
in the revised manuscript, so that text, tables and supplementary material are
generated from the same data. Returns a dictionary used by build_revised_manuscript.py.
"""
import os
import pandas as pd
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
NFR = os.path.join(HERE, '..', 'New_for_Review')

REGIONS = {'North': ['Belém', 'Boa Vista', 'Macapá', 'Manaus', 'Palmas', 'Porto Velho', 'Rio Branco'],
           'Northeast': ['Aracaju', 'Fortaleza', 'João Pessoa', 'Maceió', 'Natal', 'Recife', 'Salvador', 'São Luís', 'Teresina'],
           'Central-West': ['Brasília', 'Campo Grande', 'Cuiabá', 'Goiânia'],
           'Southeast': ['Belo Horizonte', 'Rio de Janeiro', 'São Paulo', 'Vitória'],
           'South': ['Curitiba', 'Florianópolis', 'Porto Alegre']}
UF = {'Aracaju': 'SE', 'Belém': 'PA', 'Belo Horizonte': 'MG', 'Boa Vista': 'RR', 'Brasília': 'DF', 'Campo Grande': 'MS',
      'Cuiabá': 'MT', 'Curitiba': 'PR', 'Florianópolis': 'SC', 'Fortaleza': 'CE', 'Goiânia': 'GO', 'João Pessoa': 'PB',
      'Macapá': 'AP', 'Maceió': 'AL', 'Manaus': 'AM', 'Natal': 'RN', 'Palmas': 'TO', 'Porto Alegre': 'RS',
      'Porto Velho': 'RO', 'Recife': 'PE', 'Rio Branco': 'AC', 'Rio de Janeiro': 'RJ', 'Salvador': 'BA',
      'São Luís': 'MA', 'São Paulo': 'SP', 'Teresina': 'PI', 'Vitória': 'ES'}


def f1(x):
    return f'{x:.1f}'


def f2(x):
    return f'{x:.2f}'


def load():
    S = {}
    t = pd.read_csv(os.path.join(NFR, 'out_S5_table1_recomputed.csv'))
    t['region'] = t['municipio'].map({c: r for r, cs in REGIONS.items() for c in cs})
    t = t.sort_values('municipio').reset_index(drop=True)
    S['t1'] = t
    S['city'] = {r['municipio']: r for _, r in t.iterrows()}
    S['n_deg_third'] = int((t.degradation_pct > 100 / 3).sum())
    S['n_deg_half'] = int((t.degradation_pct > 50).sum())
    S['n_imp_gt_deg'] = int((t.improvement_pct > t.degradation_pct).sum())
    S['n_nsig_half'] = int((t.no_significant_trend_pct > 50).sum())
    S['reg'] = t.groupby('region')[['degradation_pct', 'no_significant_trend_pct', 'improvement_pct']].mean()
    w = t.area_km2_valid
    S['nat_w'] = (t[['degradation_pct', 'no_significant_trend_pct', 'improvement_pct']].multiply(w, axis=0).sum() / w.sum())
    S['nat_u'] = t[['degradation_pct', 'no_significant_trend_pct', 'improvement_pct']].mean()
    S['top_deg'] = t.sort_values('degradation_pct', ascending=False).head(5)
    S['top_imp'] = t.sort_values('improvement_pct', ascending=False).head(5)
    S['tau_zero_max'] = t.tau_zero_pct.max()
    # S1 municipal series
    p = os.path.join(NFR, 'out_S1_city_annual_series.csv')
    if os.path.exists(p):
        s1 = pd.read_csv(p)
        S['s1'] = s1
        g = s1.groupby('NM_MUN')
        S['s1_n_images'] = len(s1)
        S['s1_years_per_city'] = g['ANO'].count()
        S['gap_share_pct'] = None
    # S2 orientation
    p = os.path.join(NFR, 'out_S2_orientation_check.csv')
    if os.path.exists(p):
        s2 = pd.read_csv(p)
        S['s2'] = s2
        S['s2_n'] = len(s2)
        S['s2_n_neg_ndvi'] = int((s2.r_RSEI_NDVI < 0).sum())
        S['s2_n_pos_lst'] = int((s2.r_RSEI_LST > 0).sum())
        S['s2_ndvi_min'] = s2.r_RSEI_NDVI.min()
        S['s2_ndvi_med'] = s2.r_RSEI_NDVI.median()
        S['s2_lst_med'] = s2.r_RSEI_LST.median()
        S['s2_lst_max'] = s2.r_RSEI_LST.max()
    # S4 PCA
    p = os.path.join(NFR, 'out_S4_pca_loadings.csv')
    if os.path.exists(p):
        s4 = pd.read_csv(p).dropna(subset=['eig1'])
        S['s4'] = s4
        S['s4_n'] = len(s4)
        S['s4_var_min'] = s4.PC1_var_explained_pct.min()
        S['s4_var_max'] = s4.PC1_var_explained_pct.max()
        S['s4_var_med'] = s4.PC1_var_explained_pct.median()
        same = ((np.sign(s4.load_nNDVI) == np.sign(s4.load_nWET)) & (np.sign(s4.load_nNDVI) == np.sign(s4.load_nNDSI_inv)) & (np.sign(s4.load_nNDVI) == np.sign(s4.load_nLST_inv)))
        S['s4_same_sign_n'] = int(same.sum())
        ab = s4[['load_nNDVI', 'load_nWET', 'load_nNDSI_inv', 'load_nLST_inv']].abs()
        S['s4_abs_mean'] = ab.mean()
        S['s4_abs_min'] = ab.min()
        S['s4_abs_max'] = ab.max()
    # S3b pixel sensitivity
    p = os.path.join(NFR, 'out_S3b_pixel_summary_by_city.csv')
    if os.path.exists(p):
        s3 = pd.read_csv(p)
        S['s3'] = s3
        S['s3_n_pix'] = int(s3.n_pixels.sum())
        S['s3_sig_orig_mean'] = s3.sig_pct_original.mean()
        S['s3_sig_ties_mean'] = s3.sig_pct_tie_corrected.mean()
        S['s3_sig_hr_mean'] = s3.sig_pct_hamed_rao.mean()
        S['s3_lost_mean'] = s3.pct_lost_after_hamed_rao.mean()
        S['s3_lost_min'] = s3.pct_lost_after_hamed_rao.min()
        S['s3_lost_max'] = s3.pct_lost_after_hamed_rao.max()
        S['s3_lag1_med'] = s3.median_lag1_residuals.median()
        S['s3_lag1_gt03'] = s3['pct_lag1_resid_gt_0.3'].mean()
        pr = pd.read_csv(os.path.join(NFR, 'out_S3b_pixel_results.csv'))
        S['s3_pix_lag1_med'] = pr.lag1_residuals.median()
        S['s3_pix_lag1_gt03_pct'] = 100 * (pr.lag1_residuals > 0.3).mean()
        S['s3_sign_agree_pct'] = 100 * ((pr.p_gee <= 0.05) == (pr.p_hamed_rao <= 0.05)).mean()
        S['s3_deg_orig'] = s3.sig_deg_pct_original.mean()
        S['s3_deg_hr'] = s3.sig_deg_pct_hamed_rao.mean()
        S['s3_imp_orig'] = s3.sig_imp_pct_original.mean()
        S['s3_imp_hr'] = s3.sig_imp_pct_hamed_rao.mean()
    p = os.path.join(NFR, 'out_S3b_city_series_results.csv')
    if os.path.exists(p):
        c = pd.read_csv(p)
        S['cs'] = c
        S['cs_n_sig'] = int((c.p_gee <= 0.05).sum())
        S['cs_n_sig_hr'] = int((c.p_hamed_rao <= 0.05).sum())
        S['cs_n_neg_sig_hr'] = int(((c.p_hamed_rao <= 0.05) & (c.tau_gee < 0)).sum())
        S['cs_n_pos_sig_hr'] = int(((c.p_hamed_rao <= 0.05) & (c.tau_gee > 0)).sum())
        S['cs_neg_cities'] = sorted(c[(c.p_hamed_rao <= 0.05) & (c.tau_gee < 0)].NM_MUN.tolist())
        S['cs_pos_cities'] = sorted(c[(c.p_hamed_rao <= 0.05) & (c.tau_gee > 0)].NM_MUN.tolist())
        S['cs_lag1_med'] = c.lag1_residuals.median()
        S['cs_slope_min'] = c.sen_slope.min()
        S['cs_slope_max'] = c.sen_slope.max()
    # S6 socioeconomic
    p = os.path.join(NFR, 'out_S6_spearman.csv')
    if os.path.exists(p):
        sp = pd.read_csv(p)
        S['sp'] = sp
        d = {(r.response, r.predictor): r for r in sp.itertuples()}
        S['rho_deg_dens'] = d[('degradation_pct', 'density_2022_hab_km2')]
        S['rho_deg_growth'] = d[('degradation_pct', 'growth_1991_2022_pct')]
        S['rho_deg_pop'] = d[('degradation_pct', 'pop_2022')]
        S['rho_imp_dens'] = d[('improvement_pct', 'density_2022_hab_km2')]
        S['rho_imp_growth'] = d[('improvement_pct', 'growth_1991_2022_pct')]
        S['rho_imp_pop'] = d[('improvement_pct', 'pop_2022')]
        S['s6'] = pd.read_csv(os.path.join(NFR, 'out_S6_socioeconomic.csv'))
    # L1 local epochs
    p = os.path.join(NFR, 'out_L1_epoch_stats.csv')
    if os.path.exists(p):
        l1 = pd.read_csv(p)
        S['l1'] = l1
        S['l1_r_min'] = l1.r_with_previous_epoch.min()
        S['l1_r_mean'] = l1.r_with_previous_epoch.mean()
    # figure rendering scales
    p = os.path.join(NFR, 'scale_used.csv')
    return S


if __name__ == '__main__':
    S = load()
    for k, v in S.items():
        if not isinstance(v, (pd.DataFrame, pd.Series, dict)):
            print(k, v)
