# -*- coding: utf-8 -*-
"""
build_revised_manuscript.py  (RNV, 2026)
Builds the revised manuscript (Revised: red text + RNV comments; Clean) from the
original Main_text_UEC_formatted_v3.docx, the revision texts defined below and
the numbers collected by revision_stats.py. Every edit is tagged with the
reviewer question identifiers it answers; a JSON log of edits is written for the
response letters and the Summary of Changes.
Usage: python build_revised_manuscript.py <original.docx> <out_dir> <github_url>
"""
import sys
import os
import json
import re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from docx_revision_tools import Docx, q
import revision_stats as RS

ORIG, OUT, GH = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)
S = RS.load()
C = S['city']
f1, f2 = RS.f1, RS.f2
d = Docx(ORIG)
EDITS = []   # (qids, action, anchor/prefix, note)


def rep(prefix, text, qids, nth=0, note=None, segments=None, drop_math=False):
    p = d.replace(prefix, text, nth=nth, segments=segments, note=note, drop_math=drop_math)
    for qq in qids:
        d.comment(p, qq)
    EDITS.append({'qids': qids, 'action': 'replace', 'anchor': prefix[:70], 'new_text': text, 'note': note})
    return p


def ins(anchor, text, qids, style_from=None, note=None):
    p = d.insert_after(anchor, text, style_from=style_from, note=note)
    for qq in qids:
        d.comment(p, qq)
    EDITS.append({'qids': qids, 'action': 'insert', 'anchor': anchor if isinstance(anchor, str) else '(element)',
                  'new_text': text, 'note': note})
    return p


def dele(prefix, qids, nth=0, note=None):
    d.delete(prefix, nth=nth, note=note)
    EDITS.append({'qids': qids, 'action': 'delete', 'anchor': prefix[:70], 'new_text': None, 'note': note})


def pct(city, col):
    return f1(C[city][col])


def cityuf(city):
    return f'{city}-{RS.UF[city]}'


# ------------------------------------------------------------------ numbers
t = S['t1']
nd3, nd5, nimp = S['n_deg_third'], S['n_deg_half'], S['n_imp_gt_deg']
top_deg = [cityuf(c) + f' ({pct(c, "degradation_pct")}%)' for c in S['top_deg'].municipio]
top_imp = [cityuf(c) + f' ({pct(c, "improvement_pct")}%)' for c in S['top_imp'].municipio]
reg = S['reg']
nat_w, nat_u = S['nat_w'], S['nat_u']
rho_dd, rho_dg = S['rho_deg_dens'], S['rho_deg_growth']
rho_id, rho_ig = S['rho_imp_dens'], S['rho_imp_growth']
s2n, s2neg = S.get('s2_n', 0), S.get('s2_n_neg_ndvi', 0)
s4 = S.get('s4')
have_s3 = 's3' in S
have_cs = 'cs' in S

# ================================================================== ABSTRACT
rep("Urbanization in the Global South is reshaping",
    "Brazil's 27 state capitals concentrate much of the national urban population and span five macro-regions with "
    "contrasting biomes, climates and urbanization histories, yet a nationally consistent, long-term diagnosis of their "
    "ecological condition was not available. We built annual Remote Sensing Ecological Index (RSEI) series for all 27 "
    "capitals over 1985–2025 (41 years) from Landsat Collection 2 surface-reflectance and surface-temperature composites "
    "processed in Google Earth Engine, integrating greenness (NDVI), wetness (WET), heat (LST) and dryness (NDBSI) through "
    "a Principal Component Analysis computed separately for each capital and year. Pixel-wise monotonic trends were tested "
    "with the Mann–Kendall test and quantified with Sen's slope, and the robustness of the results to serial autocorrelation "
    "and to the orientation of the first principal component was verified. Trajectories were markedly heterogeneous within "
    f"and among regions. Statistically significant degradation (p ≤ 0.05) affected more than one third of the municipal "
    f"territory in {nd3} capitals and was most extensive in {', '.join(c.split(' (')[0] for c in top_deg[:3])}, whereas "
    f"significant improvement predominated in {', '.join(c.split(' (')[0] for c in top_imp[:4])}. Northeastern capitals "
    "showed the largest regional share of significant degradation and Amazonian capitals the largest share of improvement, "
    "while the Southeast, South and Central-West displayed intermediate and spatially fragmented patterns. Across capitals, "
    "the share of degraded area increased with population density and decreased with population growth since 1991, "
    "suggesting that consolidated, dense urban fabrics rather than recent expansion per se are associated with ecological "
    "decline. The temporal standard deviation of the RSEI further separated chronically low but stable areas from actively "
    "changing transition zones. The observed spatial patterns are consistent with, although they do not directly test, a "
    "buffering role of continuous native vegetation and large conservation units. The open, reproducible workflow provides "
    "a national baseline for monitoring urban ecological quality and for prioritizing green infrastructure in tropical cities.",
    ['Reviewer 1 Q2', 'Reviewer 2 Q1', 'Reviewer 2 Q3', 'Reviewer 1 Q14', 'Editor Q2'], note='Abstract rewritten')
rep("Remote Sensing Ecological Index (RSEI); Urban ecological quality",
    "Remote Sensing Ecological Index (RSEI); Urban ecological quality; Mann–Kendall trend analysis; Google Earth Engine; "
    "Land surface temperature; Urbanization; Time-series analysis", ['Reviewer 1 Q3'])
rep("INTRODUÇÃO", "1. INTRODUCTION", ['Reviewer 1 Q1'])

# ================================================================== INTRODUCTION
rep("Among these indices, the Remote Sensing Ecological Index (RSEI), proposed by Xu in 2013",
    "Among these indices, the Remote Sensing Ecological Index (RSEI) proposed by Xu (2013) has become one of the most widely "
    "adopted tools for ecological assessment. It couples four biophysical dimensions that are directly observable from "
    "satellite data and capture the most salient surface manifestations of ecological condition: greenness, expressed by the "
    "Normalized Difference Vegetation Index (NDVI); wetness, derived from the Tasseled Cap transformation (WET); dryness, "
    "represented by the Normalized Difference Built-up and Soil Index (NDBSI); and heat, expressed by land surface "
    "temperature (LST) (Xu 2013; Zhang et al. 2022a). Rather than relying on expert-assigned weights, the RSEI integrates "
    "these dimensions through Principal Component Analysis (PCA), deriving the contribution of each indicator from the "
    "covariance structure of the data; after rescaling to the 0–1 range, values near unity denote good ecological status and "
    "values near zero denote degraded conditions (Xu 2013; Wang 2022). Compared with single-indicator approaches or with "
    "composite indices that require ancillary socioeconomic or field data, the RSEI is fully remote-sensing based, objective "
    "and reproducible, explicitly resolves the competing influences of vegetation cooling and built-up warming, and can be "
    "computed identically for any city and date from the Landsat archive, which makes it particularly suitable for "
    "multi-city, multi-decadal comparisons (Xu 2013; Song et al. 2023; Zhang and Kuang 2025).",
    ['Reviewer 1 Q6', 'Reviewer 1 Q7'])
dele("The four constituent indicators are well established in the literature.", ['Reviewer 1 Q6', 'Reviewer 1 Q7'])
rep("The 27 Brazilian state capitals concentrate a large share of the national urban population",
    "The 27 Brazilian state capitals concentrate a large share of the national urban population and the country's principal "
    "administrative and economic functions, yet they span an exceptional diversity of climatic, biogeographical and "
    "socioeconomic conditions, from cities of a few hundred thousand inhabitants to metropolises exceeding eleven million "
    "(IBGE 2024). This heterogeneity makes them a natural laboratory for comparative analysis. However, Brazilian assessments "
    "of urban ecological quality remain largely restricted to single-city case studies or to individual components such as "
    "surface temperature or vegetation (Monteiro et al. 2021; Patriota et al. 2024), and no study has yet provided a "
    "nationally consistent, pixel-based and statistically tested diagnosis of the trajectory of urban ecological quality for "
    "all state capitals. To our knowledge, this is the first application of annual RSEI time series covering four decades "
    "(1985–2025) to the complete set of Brazilian state capitals. The contribution of the study therefore lies not in the "
    "index itself, which is well established, but in (i) a standardized and fully reproducible national framework; (ii) the "
    "use of complete annual series rather than a few snapshot years, which allows the direction, magnitude and statistical "
    "significance of change to be assessed at the pixel scale; and (iii) the explicit evaluation of the methodological "
    "choices that condition comparability among cities and years, namely the per-capital PCA, the orientation of the first "
    "component and the treatment of serial autocorrelation.",
    ['Reviewer 1 Q5', 'Reviewer 2 Q2'])
rep("Satellite-derived ecological series pose specific statistical challenges.",
    "Satellite-derived ecological series are typically non-linear, non-normally distributed, serially dependent and affected "
    "by anomalous years (droughts, intense fire seasons or residual atmospheric contamination), which violates the "
    "assumptions of parametric trend tests. Non-parametric, rank-based methods circumvent these limitations, and the pairing "
    "of the Mann–Kendall test with the Sen (Theil–Sen) slope estimator has become the methodological standard for trend "
    "detection in environmental and remote-sensing time series (Gilbert 1987; Song et al. 2023; Patriota et al. 2024). Their "
    "formulation, and the treatment of serial correlation, are presented in Section 2.6.",
    ['Reviewer 1 Q4', 'Reviewer 1 Q7'])
dele("The Mann–Kendall (MK) test is a rank-based, distribution-free procedure", ['Reviewer 1 Q4'])
dele("Whereas the MK test establishes the direction and statistical significance of a trend", ['Reviewer 1 Q4'])
dele("Applied to the present study, this framework is computed independently", ['Reviewer 1 Q4'])
rep("Accordingly, the present study aims to analyse the trend of urban ecological quality",
    "Accordingly, this study analyses the trajectory of urban ecological quality across the Brazilian state capitals from "
    "annual RSEI series derived from Landsat imagery. The specific objectives are: (i) to compute the RSEI in a standardized "
    "manner for all 27 state capitals for every year between 1985 and 2025; (ii) to apply the Mann–Kendall test and Sen's "
    "slope estimator pixel by pixel to identify the direction, significance and magnitude of change; (iii) to compare the "
    "results among capitals and macro-regions; and (iv) to evaluate the robustness of the trends to serial autocorrelation "
    "and to the construction of the index.", ['Reviewer 1 Q5', 'Reviewer 2 Q2'])

# ================================================================== METHODS
rep("The analytical framework was designed to ensure full reproducibility",
    "The analytical framework was designed to ensure reproducibility and cross-city comparability over four decades "
    "(Figure 1). The workflow comprised six stages: (i) acquisition of the Landsat Collection 2 Level-2 32-day composites and "
    "generation of annual median composites; (ii) annual computation of the four ecological components (greenness, wetness, "
    "heat and dryness); (iii) normalization and integration of the components into the RSEI through a PCA computed "
    "separately for each capital and year; (iv) export of the 1,107 annual RSEI images (27 capitals × 41 years) as Earth "
    "Engine assets, with an audit of missing years; (v) pixel-wise trend analysis with the Mann–Kendall test and Sen's slope "
    "estimator, together with the temporal mean, median and standard deviation of the index; and (vi) clipping of the "
    "products to the official municipal boundaries, area accounting by trend class, cartographic synthesis and sensitivity "
    "analyses.", ['Editor Q1', 'Reviewer 1 Q8'])
rep("The first four stages were implemented entirely within the Google Earth Engine",
    "Stages (i) to (v) were implemented in the Google Earth Engine (GEE) cloud platform (Gorelick et al. 2017) through "
    "Python scripts executed in Google Colab, and stage (vi) in QGIS and Python; the complete code is openly available "
    "(Section 2.7). Demographic indicators from the official censuses were used only in an exploratory, non-causal "
    "association analysis with the resulting trend classes (Sections 2.3.2 and 2.6.3).",
    ['Reviewer 3 Q1', 'Reviewer 1 Q11', 'Reviewer 3 Q3'])
rep("Annual time series were derived from the Landsat 5 Thematic Mapper (TM)",
    "Annual series were derived from the Landsat 5 Thematic Mapper (TM), Landsat 7 Enhanced Thematic Mapper Plus (ETM+) and "
    "Landsat 8–9 Operational Land Imager/Thermal Infrared Sensor (OLI/TIRS) sensors through the USGS Collection 2 Level-2 "
    "32-day composites available in GEE (LANDSAT/COMPOSITES/C02/T1_L2_32DAY). These composites are built from the "
    "Collection 2 surface-reflectance and surface-temperature products, which are radiometrically and atmospherically "
    "corrected and provide a harmonized set of bands across sensors (blue, green, red, near-infrared, two short-wave infrared "
    "bands and a thermal band expressed as surface temperature in kelvin); cloud, cloud-shadow and saturated pixels are "
    "excluded during the generation of the composites on the basis of the quality-assessment (QA) bands (Malakar et al. 2018; "
    "USGS 2024). For each capital and calendar year, the 32-day composites were aggregated into a single annual median "
    "composite, so that each pixel represents the median of all valid observations of that year. Because the composites "
    "integrate observations from the whole year, the annual values represent year-round conditions rather than a fixed "
    "season; the implications of this choice for capitals with strongly seasonal climates are discussed in Section 4.8.",
    ['Editor Q1', 'Reviewer 3 Q2'])
rep("Socioeconomic variables total population, demographic density",
    "The resident population of each capital in the 1991, 2000 and 2022 Demographic Censuses and the municipal territorial "
    "area were obtained from the Brazilian Institute of Geography and Statistics through the SIDRA database (IBGE 2023). "
    "These variables were used to derive population density in 2022 and relative population growth between 1991 and 2022, "
    "which were related to the trend classes through rank correlations (Section 2.6.3). This analysis is exploratory and "
    "does not test causal relationships.", ['Reviewer 1 Q11', 'Reviewer 3 Q3'])
ins("where , and  are the surface reflectance values in the blue, green, red",
    "In the processing scripts, the TM coefficients (Crist 1985) were applied to all composites up to 2012 (TM and ETM+) "
    "and the OLI coefficients (Baig et al. 2014) to composites from 2013 onwards; because the composites provide a "
    "harmonized band set, no additional cross-sensor adjustment was applied.", ['Editor Q1'],
    style_from="The wetness component was obtained from the Tasseled Cap transformation")
rep("Land Surface Temperature was retrieved from the thermal band following the standard radiative-transfer procedure",
    "Land surface temperature was taken directly from the surface-temperature band of the Collection 2 Level-2 products, "
    "which is generated by the USGS with a single-channel algorithm that uses atmospheric profiles and an emissivity derived "
    "from the ASTER Global Emissivity Dataset and the NDVI (Malakar et al. 2018). Values in kelvin were converted to degrees "
    "Celsius. Residual gaps in the thermal band of the annual composite were filled with the mean of 3 × 3, 5 × 5 and 9 × 9 "
    "pixel neighbourhoods and, where still missing, with the mean of the processing polygon of the capital.",
    ['Editor Q1'], note='LST description corrected to match the processing scripts')
for pre in ["where  is the spectral radiance,", "where  and  are the band-specific thermal conversion constants",
            "Finally, the emissivity-corrected LST was computed as", "where  is the central wavelength of the emitted radiance"]:
    dele(pre, ['Editor Q1'], note='radiative-transfer equations removed (procedure not used)')
# equation-only paragraphs between 2.4.3 heading and 2.4.4 heading
h43 = d.find("2.4.3. Heat Land Surface Temperature")
h44 = d.find("2.4.4. Dryness NDBSI")
node = h43.getnext()
removed = 0
while node is not None and node is not h44:
    nxt = node.getnext()
    if node.tag == q('p') and not Docx.ptext(node).strip():
        node.getparent().remove(node)
        removed += 1
    node = nxt
EDITS.append({'qids': ['Editor Q1'], 'action': 'delete', 'anchor': '2.4.3 equation paragraphs', 'new_text': None,
              'note': f'{removed} equation-only paragraphs removed from 2.4.3'})
ins("where  is the normalized value of indicator  at pixel",
    "The minimum and maximum of each indicator were taken within the processing polygon of each capital and for each year "
    "separately, so that the normalization, like the PCA, is specific to each capital-year. For heat (LST) and dryness "
    "(NDBSI), whose increase denotes ecological deterioration, the complement of the rescaled value was used, so that all "
    "four normalized components increase with ecological quality before entering the PCA.",
    ['Reviewer 1 Q8', 'Editor Q1'], style_from="Because the four components are expressed in different units")
pca_var = (f"{f1(S['s4_var_min'])}–{f1(S['s4_var_max'])}% (median {f1(S['s4_var_med'])}%) of the total variance in the "
           f"{S['s4_n']} capital-year combinations examined (Table S4)") if s4 is not None else "most of the total variance (Table S4)"
orient = (f"Of the 1,107 capital-year images, {s2neg} showed a negative correlation between the exported index and NDVI "
          f"(Table S3), revealing a sign inversion of PC1 in those years; these images were re-oriented (RSEI′ = 1 − RSEI, an "
          "exact complement given the min–max rescaling) before the trend analysis, so that in all images higher values "
          "consistently denote better ecological conditions.") if s2n >= 1100 else \
    "The orientation of every capital-year image was verified a posteriori against NDVI and LST (Table S3)."
rep("The four normalized components were integrated through Principal Component Analysis (PCA), a multivariate technique",
    "The four normalized components were integrated through PCA on their covariance matrix (Jolliffe and Cadima 2016). The "
    "PCA was computed independently for each capital and each year over the processing polygon, so that the weights reflect "
    "the covariance structure of that city in that year; the first principal component (PC1), which concentrated "
    f"{pca_var}, was adopted as the basis of the index. Because the sign of an eigenvector is arbitrary, the orientation "
    f"of PC1 was verified a posteriori. {orient} The initial index was obtained as:",
    ['Reviewer 1 Q8', 'Editor Q1'])
rep("The resulting annual indicators (PC1_mean and PC1_median) represent",
    "The resulting annual RSEI image of each capital ranges from 0 (worst) to 1 (best) relative to the conditions observed "
    "in that capital and year. Pixels still masked after compositing (mainly persistent cloud cover and Landsat 7 scan-line "
    "gaps) were filled with the mean of progressively larger neighbourhoods (3 to 65 pixels) and, as a last resort, with the "
    "mean of the processing polygon; the number of pixels filled in each image was recorded (Table S1). Because the index is "
    "rescaled within each capital-year, the RSEI is a relative measure of ecological condition: temporal trends describe "
    "changes in the position of each pixel relative to the whole processing polygon rather than absolute changes in the "
    "biophysical variables, a point taken up in Section 4.8.", ['Reviewer 1 Q8', 'Editor Q3'])
rep("Time-series processing was performed entirely within GEE, a cloud-computing environment",
    "Processing was performed for each capital within a processing polygon that encompasses the municipality and its "
    "immediate surroundings (feature collection CAP_JOIN2 in the code repository), and all products were subsequently "
    "clipped to the official municipal boundaries of the 2022 IBGE municipal mesh. No urban mask was applied, so the results "
    "refer to the entire municipal territory, including peri-urban, rural, forested and water-covered areas within the "
    "municipal limits. The annual RSEI images were exported as Earth Engine assets, one per capital and year; an audit "
    "script identified the years missing after the first processing run, which were reprocessed, yielding the complete set "
    "of 1,107 images (27 capitals × 41 years) used in the trend analysis (Table S1).",
    ['Editor Q1', 'Reviewer 1 Q14'], drop_math=True)
rep("As a complementary step, an interactive environment was developed within GEE",
    "As a complementary step, an interactive GEE interface allowed the dynamic selection of capitals and the visualization "
    "of the derived products (annual RSEI, temporal statistics and the Mann–Kendall metrics). This qualitative assessment "
    "supported the inspection of the spatial coherence of the patterns and the identification of processing artefacts; it "
    "does not constitute an independent validation of the index.", ['Reviewer 1 Q10'])
rep("To enable quantitative and spatial analyses in external environments, such as QGIS, R and Python",
    "A dedicated script exported, for each capital, GeoTIFF rasters (30 m, standardized NoData value and nomenclature) of "
    "Kendall's tau (RSEI_tau), the p-value of the Mann–Kendall test (RSEI_p_value), Sen's slope and the temporal mean, "
    "median and standard deviation of the RSEI, together with annual RSEI images for selected years; these files were used "
    "for the cartographic and area analyses. Full details of the export routine are given in the code repository.",
    ['Reviewer 1 Q12'])
rep("To assess the spatio-temporal evolution of urban ecological quality, a statistical trend analysis",
    "Trends in urban ecological quality were assessed pixel by pixel on the annual RSEI series of each capital (n = 41 "
    "years for every capital). Annual series were preferred over monthly series because the study focuses on long-term "
    "change and because aggregation to the annual scale harmonizes the series across years with different availability of "
    "cloud-free observations. Two non-parametric methods were applied: the Mann–Kendall test (Mann 1945; Kendall 1975; "
    "Gilbert 1987), which detects the presence of a monotonic trend, and Sen's slope estimator (Sen 1968), which quantifies "
    "its magnitude. Both were implemented directly in GEE with the formulations below, and a 5% significance level "
    "(p ≤ 0.05, two-tailed) was adopted. Pixels without a statistically significant trend are reported as “no significant "
    "trend”; this class is not interpreted as ecological stability, because it also includes areas with real but weak, "
    "non-monotonic or noisy changes.", ['Reviewer 1 Q4', 'Reviewer 1 Q9', 'Editor Q1'])
ties = f"fewer than {f1(S['tau_zero_max'])}% of the pixels of any capital had τ = 0"
auto = ("The variance of S was computed without the correction for tied values, because ties are negligible in continuous, "
        f"floating-point RSEI series ({ties}). The standard Mann–Kendall test assumes serial independence, and positive "
        "autocorrelation inflates the probability of detecting a spurious trend (Hamed and Rao 1998). The effect of "
        "autocorrelation was therefore assessed a posteriori on a random sample of 1,000 pixels per capital (27,000 series) "
        "and on the municipal mean series, by comparing the original test with the tie-corrected test and with the "
        "variance-corrected test of Hamed and Rao (1998), as implemented in the pymannkendall package (Hussain and Mahmud "
        "2019); the lag-1 autocorrelation of the Sen-detrended residuals was also computed (Section 3.8; Table S5).")
ins("which ranges between  and : values close to  indicate a strong upward trend", auto, ['Reviewer 1 Q9'],
    style_from="The Mann–Kendall test is a rank-based non-parametric method that evaluates")
p_sen = d.find("where  is the Sen slope, and  and  are the RSEI values")
h263 = ins(p_sen, "2.6.3. Area accounting and association with demographic indicators", ['Reviewer 1 Q11', 'Reviewer 3 Q3'],
           style_from="2.6.2. Sen’s slope estimator")
ins(h263, "For each capital, the trend products were clipped to the municipal boundary and the percentage of the municipal "
    "area in three classes was computed from the pixel area at 30 m: significant degradation (τ < 0 and p ≤ 0.05), "
    "significant improvement (τ > 0 and p ≤ 0.05) and no significant trend (p > 0.05). The shares of negative and positive "
    "τ irrespective of significance, which correspond to the trend maps, were also computed (Table S2). Spearman rank "
    "correlations were then calculated between the share of significant degradation (or improvement) and population "
    "density in 2022, relative population growth between 1991 and 2022 and total population in 2022 (n = 27). Given the "
    "sample size and the observational design, these correlations are reported as exploratory associations only.",
    ['Reviewer 1 Q11', 'Reviewer 3 Q3'], style_from="Although the Mann–Kendall test identifies the existence and direction")
rep("The modular structure of the GEE scripts and the standardization of the processing steps",
    f"All processing, analysis and figure-generation code is openly available in the authors' GitHub repository ({GH}), "
    "including the GEE/Colab scripts used to compute the annual RSEI, to audit missing years and to compute the pixel-wise "
    "trends, the Python scripts used for the municipal area accounting, the sensitivity analyses and the figures, and "
    "documentation of the software dependencies and of the authentication required to run GEE with the user's own "
    "credentials. The workflow can be replicated for other municipalities, periods or territorial units.",
    ['Reviewer 3 Q1'])
rep("The processed images were organized and analysed in QGIS (version 3.28.0)",
    "The exported rasters were clipped to the municipal boundaries and mapped in QGIS (version 3.28) and Python (rasterio, "
    "matplotlib). For each capital, five panels were produced: the trend map (sign of Kendall's τ), the statistically "
    "significant trend map (p ≤ 0.05) and the temporal mean, median and standard deviation of the RSEI (Figures 3–6); the "
    "complete set of annual RSEI maps is provided in Figure S1.", ['Reviewer 1 Q16', 'Reviewer 1 Q17'])
rep("Standardized criteria were defined for the classification of the cartographic products",
    "Standardized criteria were adopted for all cartographic products. Trend maps were classified according to the sign of "
    "Kendall's τ into negative (decreasing RSEI), null and positive (increasing RSEI) values. Significant trend maps retained "
    "only pixels with p ≤ 0.05, classified as significant degradation (τ < 0) or significant improvement (τ > 0), with the "
    "remaining pixels shown in grey. Mean and median maps were displayed on a continuous 0–1 scale, and the "
    "standard-deviation maps in three fixed intervals: 0–0.05 (low temporal variability), 0.05–0.10 (moderate) and above "
    "0.10 (high). Figures 3–6 were rendered at 30 m for municipalities up to about 4,000 km² and at 40–150 m for the larger "
    "municipalities, as indicated in the captions; all area statistics were computed at 30 m.",
    ['Reviewer 1 Q16', 'Editor Q1'], drop_math=True)

# ================================================================== RESULTS
rep("3.1. Overview of Spatio-Temporal RSEI Patterns Across Brazilian State Capitals",
    "3.1. Overview of spatio-temporal RSEI patterns across the 27 state capitals", ['Reviewer 1 Q14'])
rep("The analysis of the Remote Sensing Ecological Index (RSEI) across all 26 Brazilian state capitals",
    "The RSEI products for the 27 state capitals (Figures 3–6; annual maps in Figure S1) revealed pronounced spatial "
    "heterogeneity of urban ecological quality at both the intra-urban and the inter-regional scales. In every capital the "
    "temporal mean and median maps were closely similar, indicating that the dominant spatial pattern of the index was "
    "persistent over the 41 years rather than driven by a few anomalous years, whereas the standard-deviation maps exposed "
    "substantial intra-municipal variability in most cities.", ['Reviewer 1 Q14', 'Reviewer 1 Q13', 'Reviewer 1 Q17'])
ne = t[t.region == 'Northeast']
rep("At the national scale, 17 of the 26 capitals had more than one-third of their urban area",
    f"Table 1 summarizes the area shares of the three trend classes within the municipal boundaries. Statistically "
    f"significant degradation (τ < 0, p ≤ 0.05) covered more than one third of the municipal territory in {nd3} of the 27 "
    f"capitals and more than half in {nd5} ({', '.join(top_deg[:nd5])}); the other capitals with the largest degraded "
    f"shares were {', '.join(top_deg[nd5:5])}. Significant improvement (τ > 0, p ≤ 0.05) was most extensive in "
    f"{', '.join(top_imp[:5])}, and exceeded the degraded share in {nimp} capitals. The class without a significant trend "
    f"occupied between {f1(t.no_significant_trend_pct.min())}% ({cityuf(t.loc[t.no_significant_trend_pct.idxmin(), 'municipio'])}) and "
    f"{f1(t.no_significant_trend_pct.max())}% ({cityuf(t.loc[t.no_significant_trend_pct.idxmax(), 'municipio'])}) of the municipal "
    f"area. Averaged by macro-region, the share of significant degradation was highest in the Northeast "
    f"({f1(reg.loc['Northeast', 'degradation_pct'])}%) and lowest in the North ({f1(reg.loc['North', 'degradation_pct'])}%), "
    f"while significant improvement was highest in the North ({f1(reg.loc['North', 'improvement_pct'])}%) and lowest in the "
    f"Northeast ({f1(reg.loc['Northeast', 'improvement_pct'])}%); the Central-West ({f1(reg.loc['Central-West', 'degradation_pct'])}% "
    f"degradation, {f1(reg.loc['Central-West', 'improvement_pct'])}% improvement), Southeast ({f1(reg.loc['Southeast', 'degradation_pct'])}% "
    f"and {f1(reg.loc['Southeast', 'improvement_pct'])}%) and South ({f1(reg.loc['South', 'degradation_pct'])}% and "
    f"{f1(reg.loc['South', 'improvement_pct'])}%) occupied intermediate positions. Weighted by municipal area, "
    f"{f1(nat_w['degradation_pct'])}% of the combined territory of the 27 capitals showed significant degradation, "
    f"{f1(nat_w['improvement_pct'])}% significant improvement and {f1(nat_w['no_significant_trend_pct'])}% no significant trend, "
    f"a balance dominated by the very large Amazonian municipalities; the unweighted means were {f1(nat_u['degradation_pct'])}%, "
    f"{f1(nat_u['improvement_pct'])}% and {f1(nat_u['no_significant_trend_pct'])}%, respectively.",
    ['Reviewer 1 Q14', 'Reviewer 1 Q13', 'Reviewer 1 Q15', 'Editor Q1'])
rep("Table 1. Classification of RSEI trends (1985–2025) by Brazilian state capital.",
    "Table 1. Percentage of the municipal area of each Brazilian state capital with statistically significant degradation "
    "(τ < 0, p ≤ 0.05), no significant trend (p > 0.05) and statistically significant improvement (τ > 0, p ≤ 0.05) of the "
    "RSEI over 1985–2025, computed at 30 m within the official municipal boundaries (n = 41 annual observations for every "
    "capital). The shares of negative and positive τ irrespective of significance are given in Table S2.",
    ['Reviewer 1 Q14', 'Editor Q1'])

# ---- Table 1 cells ----
tbl = d.body.find(q('tbl'))
rows = tbl.findall(q('tr'))
hdr_cells = rows[0].findall(q('tc'))
heads = ['Capital', 'Significant degradation (%)', 'No significant trend (%)', 'Significant improvement (%)']
for cell, txt in zip(hdr_cells, heads):
    p = cell.find(q('p'))
    d._fill(p, txt, d._base_rpr(p), True)
by_upper = {k.upper(): v for k, v in C.items()}
for r in rows[1:]:
    cells = r.findall(q('tc'))
    name = Docx.ptext(cells[0]).strip()
    key = name.split('-')[0].strip().upper()
    rec = by_upper[key]
    vals = [f2(rec['degradation_pct']), f2(rec['no_significant_trend_pct']), f2(rec['improvement_pct'])]
    for cell, v in zip(cells[1:], vals):
        p = cell.find(q('p'))
        d._fill(p, v, d._base_rpr(p), True)
d.comment(hdr_cells[1].find(q('p')), 'Reviewer 1 Q14')
d.comment(hdr_cells[1].find(q('p')), 'Editor Q1')
EDITS.append({'qids': ['Reviewer 1 Q14', 'Editor Q1'], 'action': 'replace', 'anchor': 'Table 1 (all cells)',
              'new_text': 'Table 1 recomputed from the consolidated trend products', 'note': 'Table 1'})


def region_text(region, cities_order):
    parts = []
    for c in cities_order:
        r = C[c]
        parts.append(f"{cityuf(c)} ({pct(c, 'degradation_pct')}% significant degradation, {pct(c, 'improvement_pct')}% "
                     f"significant improvement, {pct(c, 'no_significant_trend_pct')}% without significant trend)")
    return parts


# ---- 3.2 North ----
rep("3.2. Amazon Legal Region: Ecological Stability and Sustained Improvement Trends", "3.2. North region (Legal Amazon)",
    ['Reviewer 1 Q13'])
north = ['Manaus', 'Boa Vista', 'Macapá', 'Porto Velho', 'Rio Branco', 'Palmas', 'Belém']
rep("The Amazonian capitals consistently exhibited the most favourable ecological conditions",
    "The northern capitals displayed the highest temporal mean RSEI values of the sample and, with the exception of Belém, "
    f"the largest shares of significant improvement (Table 1; Figures 3–5). In {cityuf('Manaus')}, "
    f"{pct('Manaus', 'improvement_pct')}% of the municipal area showed significant improvement and only "
    f"{pct('Manaus', 'degradation_pct')}% significant degradation, the latter forming a compact cluster over the "
    f"consolidated urban core in the west of the municipality (Figure 4). {cityuf('Boa Vista')} "
    f"({pct('Boa Vista', 'improvement_pct')}% improvement, {pct('Boa Vista', 'degradation_pct')}% degradation), "
    f"{cityuf('Macapá')} ({pct('Macapá', 'improvement_pct')}% and {pct('Macapá', 'degradation_pct')}%) and "
    f"{cityuf('Porto Velho')} ({pct('Porto Velho', 'improvement_pct')}% and {pct('Porto Velho', 'degradation_pct')}%) "
    "followed the same pattern, with significant degradation restricted to the built-up areas and to their margins and "
    f"improvement spread over the vegetated matrix. In {cityuf('Rio Branco')} ({pct('Rio Branco', 'improvement_pct')}% and "
    f"{pct('Rio Branco', 'degradation_pct')}%) and {cityuf('Palmas')} ({pct('Palmas', 'improvement_pct')}% and "
    f"{pct('Palmas', 'degradation_pct')}%) the class without significant trend predominated "
    f"({pct('Rio Branco', 'no_significant_trend_pct')}% and {pct('Palmas', 'no_significant_trend_pct')}%).",
    ['Reviewer 1 Q13', 'Reviewer 1 Q15', 'Reviewer 1 Q16'])
rep("Manaus-AM displayed the highest proportion of ecological improvement among all capitals",
    f"{cityuf('Belém')} departed from the regional pattern: {pct('Belém', 'degradation_pct')}% of its municipal area "
    f"showed significant degradation, the largest share of the whole sample, and only {pct('Belém', 'improvement_pct')}% "
    "significant improvement (Figure 3). The trend maps are spatially bifurcated between the continental sector, almost "
    "entirely covered by negative and significant τ values, and the fluvial islands, where positive values predominate; "
    "the standard-deviation map shows the highest temporal variability along the transition between these two sectors.",
    ['Reviewer 1 Q13', 'Reviewer 1 Q16'])
for pre in ["Boa Vista-RR registered the lowest degradation percentage", "Macapá-AP presented 62.82% improvement",
            "Porto Velho-RO recorded 59.45% improvement", "Rio Branco-AC showed 55.28% improvement",
            "Belém-PA presents a markedly different profile"]:
    dele(pre, ['Reviewer 1 Q16', 'Reviewer 2 Q4'])
# figure captions
scales = {}
try:
    import pandas as pd
    sc = pd.read_csv(os.path.join(RS.NFR, 'scale_used.csv'))
    scales = {r.municipio: int(r.scale_m) for r in sc.itertuples()}
except Exception:
    pass


def cap(num, cities):
    sc_txt = '; '.join(f'{c} {scales[c]} m' for c in cities if scales.get(c, 30) != 30)
    sc_txt = f' Panels were rendered at 30 m except {sc_txt}.' if sc_txt else ' Panels were rendered at 30 m.'
    return (f"Figure {num}. Spatiotemporal patterns of the Remote Sensing Ecological Index (RSEI) over 1985–2025 for "
            f"{len(cities)} Brazilian state capitals: {', '.join(cityuf(c) for c in cities)}. For each capital, the five "
            "panels show, from left to right: the RSEI trend (sign of Kendall's τ), the statistically significant trend "
            "(Mann–Kendall, p ≤ 0.05; non-significant pixels in grey) and the temporal mean, median and standard deviation of "
            "the RSEI within the official municipal boundary." + sc_txt)


rep("Figure 3. Spatiotemporal patterns of the Remote Sensing Ecological Index",
    cap(3, ['Aracaju', 'Belém', 'Belo Horizonte', 'Boa Vista', 'Brasília', 'Campo Grande', 'Cuiabá', 'Curitiba']), ['Editor Q1'])
rep("Figure 4. Spatiotemporal patterns of the Remote Sensing Ecological Index",
    cap(4, ['Florianópolis', 'Fortaleza', 'Goiânia', 'João Pessoa', 'Macapá', 'Maceió', 'Manaus', 'Natal']), ['Editor Q1'])
rep("Figure 5. Spatiotemporal patterns of the Remote Sensing Ecological Index",
    cap(5, ['Palmas', 'Porto Alegre', 'Porto Velho', 'Recife', 'Rio Branco', 'Rio de Janeiro', 'Salvador', 'São Luís']), ['Editor Q1'])
rep("Figure 6. Spatiotemporal patterns of the Remote Sensing Ecological Index",
    cap(6, ['São Paulo', 'Teresina', 'Vitória']), ['Editor Q1'])

# ---- 3.3 Northeast ----
rep("3.3. Northeast Region: Pervasive Ecological Degradation in Rapidly Urbanizing Coastal Metropolises",
    "3.3. Northeast region", ['Reviewer 1 Q13'])
ne_sorted = ne.sort_values('degradation_pct', ascending=False)
ne_list = [f"{cityuf(c)} ({pct(c, 'degradation_pct')}%)" for c in ne_sorted.municipio]
rep("The Northeast region exhibited the most widespread and spatially consistent pattern of ecological degradation",
    f"The nine northeastern capitals showed the largest regional share of significant degradation "
    f"({f1(reg.loc['Northeast', 'degradation_pct'])}% on average) and the smallest share of significant improvement "
    f"({f1(reg.loc['Northeast', 'improvement_pct'])}%). Significant degradation covered "
    f"{', '.join(ne_list[:4])} and {', '.join(ne_list[4:])} of the municipal area (Table 1; Figures 3–6). In Salvador, "
    "Aracaju, Fortaleza, Natal and Recife the negative and significant τ values form large contiguous areas over the "
    "consolidated urban fabric, whereas positive values are restricted to peripheral vegetated fragments, mangroves and "
    f"dune fields; the temporal mean and median maps of these capitals are dominated by low to intermediate values. "
    f"{cityuf('São Luís')} was the only northeastern capital in which significant improvement "
    f"({pct('São Luís', 'improvement_pct')}%) exceeded significant degradation ({pct('São Luís', 'degradation_pct')}%), with "
    f"improvement concentrated in the northern and coastal sectors. In {cityuf('Maceió')} and {cityuf('Teresina')} the "
    f"class without significant trend covered {pct('Maceió', 'no_significant_trend_pct')}% and "
    f"{pct('Teresina', 'no_significant_trend_pct')}% of the territory, and both capitals, together with Salvador and "
    "Fortaleza, showed the highest temporal standard deviations of the sample (Section 3.7).",
    ['Reviewer 1 Q13', 'Reviewer 1 Q15', 'Reviewer 1 Q16'])
for pre in ["Salvador-BA recorded the highest degradation percentage", "Fortaleza-CE presented 56.40% degradation",
            "Natal-RN showed 54.58% degradation", "Aracaju-SE registered 60.36% degradation", "Recife-PE showed 50.23% degradation",
            "João Pessoa-PB exhibited 46.93% degradation", "Maceió-AL recorded 43.83% degradation",
            "Teresina-PI showed 51.64% degradation", "São Luís-MA presented 35.74% degradation"]:
    dele(pre, ['Reviewer 1 Q16', 'Reviewer 2 Q4'])

# ---- 3.4 Southeast ----
rep("3.4. Southeast Region: Pronounced Intra-Urban Heterogeneity and the Ecological Role of Forest Remnants",
    "3.4. Southeast region", ['Reviewer 1 Q13'])
rep("The Southeast region exhibited the greatest intra-urban ecological heterogeneity among all Brazilian regions",
    f"The four southeastern capitals combined intermediate regional shares of significant degradation "
    f"({f1(reg.loc['Southeast', 'degradation_pct'])}%) and improvement ({f1(reg.loc['Southeast', 'improvement_pct'])}%) with the "
    f"sharpest intra-municipal contrasts of the sample (Figures 3, 5 and 6). In {cityuf('São Paulo')} "
    f"({pct('São Paulo', 'improvement_pct')}% improvement, {pct('São Paulo', 'degradation_pct')}% degradation) and "
    f"{cityuf('Rio de Janeiro')} ({pct('Rio de Janeiro', 'improvement_pct')}% and {pct('Rio de Janeiro', 'degradation_pct')}%), "
    "significant degradation clusters in the densely built-up districts, whereas significant improvement and the highest "
    "mean and median values coincide with the forested southern districts of São Paulo and with the forested massifs of "
    f"Rio de Janeiro. {cityuf('Belo Horizonte')} ({pct('Belo Horizonte', 'degradation_pct')}% degradation, "
    f"{pct('Belo Horizonte', 'improvement_pct')}% improvement) and {cityuf('Vitória')} "
    f"({pct('Vitória', 'degradation_pct')}% and {pct('Vitória', 'improvement_pct')}%) showed negative balances, with "
    "degradation concentrated in the central districts of Belo Horizonte and in the island sector of Vitória and improvement "
    "restricted to the periphery and to the continental sector, respectively. The standard-deviation maps of São Paulo and "
    "Vitória show low temporal variability in the consolidated cores and higher variability in the peri-urban and "
    "transitional areas.", ['Reviewer 1 Q13', 'Reviewer 1 Q15', 'Reviewer 1 Q16'])
for pre in ["São Paulo-SP presented a balanced overall profile", "Rio de Janeiro-RJ showed 53.91% improvement",
            "Belo Horizonte-MG recorded 53.24% degradation", "Vitória-ES presented a pronounced intra-urban spatial contrast"]:
    dele(pre, ['Reviewer 1 Q16', 'Reviewer 2 Q4'])

# ---- 3.5 South ----
rep("3.5. South Region: Spatially Fragmented Patterns Between Ecological Degradation and Improvement",
    "3.5. South region", ['Reviewer 1 Q13'])
rep("The South region exhibited the most spatially fragmented RSEI trend patterns among all Brazilian regions",
    f"The three southern capitals showed similar regional shares of significant degradation "
    f"({f1(reg.loc['South', 'degradation_pct'])}%) and improvement ({f1(reg.loc['South', 'improvement_pct'])}%), but with "
    f"contrasting balances (Figures 3–5). {cityuf('Porto Alegre')} had the most favourable balance "
    f"({pct('Porto Alegre', 'improvement_pct')}% improvement, {pct('Porto Alegre', 'degradation_pct')}% degradation), with "
    f"improvement widespread in the southern and eastern sectors along the Guaíba shoreline, whereas {cityuf('Curitiba')} "
    f"({pct('Curitiba', 'degradation_pct')}% degradation, {pct('Curitiba', 'improvement_pct')}% improvement) and "
    f"{cityuf('Florianópolis')} ({pct('Florianópolis', 'degradation_pct')}% and {pct('Florianópolis', 'improvement_pct')}%) "
    "showed negative balances. In Curitiba the two significant classes form a fine-grained mosaic that does not follow a "
    "simple core–periphery gradient, and in Florianópolis significant degradation is concentrated along the coastal "
    "sectors of Santa Catarina Island, with improvement in the interior of the island and in the continental sector.",
    ['Reviewer 1 Q13', 'Reviewer 1 Q15', 'Reviewer 1 Q16'])
for pre in ["Porto Alegre-RS registered the most favourable ecological balance", "Curitiba-PR showed 49.87% degradation",
            "Florianópolis-SC recorded 55.38% degradation"]:
    dele(pre, ['Reviewer 1 Q16', 'Reviewer 2 Q4'])

# ---- 3.6 Central-West ----
rep("3.6. Central-West Region: Intermediate Ecological Dynamics Amid Rapid Urban and Agricultural Expansion",
    "3.6. Central-West region", ['Reviewer 1 Q13'])
rep("The Central-West capitals displayed intermediate ecological patterns between the consistently positive trends",
    f"The Central-West capitals showed intermediate shares of significant degradation "
    f"({f1(reg.loc['Central-West', 'degradation_pct'])}%) and improvement ({f1(reg.loc['Central-West', 'improvement_pct'])}%), "
    f"and the largest regional share of area without significant trend ({f1(reg.loc['Central-West', 'no_significant_trend_pct'])}%) "
    f"(Figures 3 and 4). {cityuf('Brasília')} ({pct('Brasília', 'improvement_pct')}% improvement, "
    f"{pct('Brasília', 'degradation_pct')}% degradation) combined significant degradation in the planned urban sectors with "
    f"improvement over the surrounding Cerrado areas. {cityuf('Goiânia')} ({pct('Goiânia', 'degradation_pct')}% and "
    f"{pct('Goiânia', 'improvement_pct')}%) and {cityuf('Campo Grande')} ({pct('Campo Grande', 'degradation_pct')}% and "
    f"{pct('Campo Grande', 'improvement_pct')}%) showed near-balanced and spatially fragmented patterns, whereas "
    f"{cityuf('Cuiabá')} ({pct('Cuiabá', 'degradation_pct')}% and {pct('Cuiabá', 'improvement_pct')}%) showed a negative "
    "balance, with significant degradation concentrated in the consolidated urban area.",
    ['Reviewer 1 Q13', 'Reviewer 1 Q15', 'Reviewer 1 Q16'])
for pre in ["Brasília-DF showed 52.44% improvement", "Goiânia-GO recorded 40.47% degradation",
            "Campo Grande-MS showed 34.34% degradation", "Cuiabá-MT exhibited 48.33% degradation",
            "Palmas-TO Brazil's newest state capital"]:
    dele(pre, ['Reviewer 1 Q16', 'Reviewer 2 Q4'])

# ---- 3.7 SD ----
rep("3.7. Spatial Variability of RSEI: Standard Deviation as an Indicator of Intra-Urban Ecological Instability",
    "3.7. Temporal standard deviation of the RSEI", ['Reviewer 1 Q13'])
sdmax = t.sort_values('RSEI_stdDev_mean', ascending=False).head(4)
sdmin = t.sort_values('RSEI_stdDev_mean').head(4)
rep("The temporal standard deviation of the RSEI provided a complementary dimension to the trend analysis",
    "The temporal standard deviation of the RSEI complemented the trend analysis by mapping the amplitude of inter-annual "
    "variation of each pixel over 1985–2025 (Figures 3–6). The municipal mean of the standard deviation ranged from "
    f"{f2(t.RSEI_stdDev_mean.min())} ({', '.join(cityuf(c) for c in sdmin.municipio[:3])}) to {f2(t.RSEI_stdDev_mean.max())} "
    f"({', '.join(cityuf(c) for c in sdmax.municipio[:3])}). Three spatial configurations recurred across the sample. "
    "First, extensive and continuous vegetated areas, notably in Manaus, Porto Velho, Rio Branco and Macapá, showed low "
    "variability (< 0.05) with higher values confined to the urban–forest boundary. Second, several northeastern capitals "
    "(Teresina, Maceió, Fortaleza and Salvador) showed high variability (> 0.10) over most of the municipal territory. "
    "Third, in São Paulo, Vitória and Rio de Janeiro the consolidated urban cores combined low mean values with low "
    "variability, while the peri-urban and transitional zones showed moderate to high variability.",
    ['Reviewer 1 Q13', 'Reviewer 1 Q16'])
for pre in ["Cities with extensive and continuous native vegetation cover particularly the Amazonian capitals",
            "In contrast the most urbanized Northeast capitals particularly Teresina-PI",
            "São Paulo-SP presented an opposite pattern", "Cities with complex urban morphology involving mosaics",
            "Collectively the standard deviation analysis demonstrates"]:
    dele(pre, ['Reviewer 1 Q13', 'Reviewer 1 Q16', 'Reviewer 2 Q4'])

# ---- 3.8 robustness ----
rep("3.8. Synthesis of Spatio-Temporal RSEI Dynamics and Regional Ecological Differentiation",
    "3.8. Robustness of the index and of the trends", ['Reviewer 1 Q8', 'Reviewer 1 Q9', 'Reviewer 1 Q13'])
if s4 is not None:
    ab = S['s4_abs_mean']
    pca_txt = (f"The PCA computed for each capital in 1985, 2005 and 2025 (Table S4) assigned {f1(S['s4_var_min'])}–"
               f"{f1(S['s4_var_max'])}% of the total variance to PC1, and in all {S['s4_n']} capital-year combinations the four "
               f"loadings had the same sign, with mean absolute values of {f2(ab['load_nNDVI'])} (NDVI), {f2(ab['load_nWET'])} "
               f"(WET), {f2(ab['load_nNDSI_inv'])} (NDBSI) and {f2(ab['load_nLST_inv'])} (LST); PC1 therefore behaved as a "
               "general ecological-quality axis in every city and year, although the relative weight of the components varied "
               "among cities. ")
else:
    pca_txt = ""
if s2n:
    ori_txt = (f"The a posteriori orientation check (Table S3) found a negative correlation between the exported RSEI and "
               f"NDVI in {s2neg} of the {s2n} capital-year images (median correlation {f2(S['s2_ndvi_med'])}); these images "
               "were re-oriented before the trend analysis (Section 2.4.6), and after re-orientation the index was positively "
               "correlated with NDVI and negatively with LST in every image. ")
else:
    ori_txt = ""
if have_s3:
    s3_txt = (f"In the random sample of {S['s3_n_pix']:,} pixel series (Table S5), the median lag-1 autocorrelation of the "
              f"Sen-detrended residuals was {f2(S['s3_pix_lag1_med'])}, and {f1(S['s3_pix_lag1_gt03_pct'])}% of the series had "
              f"values above 0.3. The share of series with a significant trend was {f1(S['s3_sig_orig_mean'])}% with the "
              f"original test, {f1(S['s3_sig_ties_mean'])}% with the tie-corrected test and {f1(S['s3_sig_hr_mean'])}% with "
              f"the Hamed–Rao variance correction; on average {f1(S['s3_lost_mean'])}% of the series per capital (range "
              f"{f1(S['s3_lost_min'])}–{f1(S['s3_lost_max'])}%) lost significance after the correction, and the original and "
              f"corrected tests agreed on significance in {f1(S['s3_sign_agree_pct'])}% of the series. The correction reduced "
              f"the mean share of significant degradation from {f1(S['s3_deg_orig'])}% to {f1(S['s3_deg_hr'])}% and of "
              f"significant improvement from {f1(S['s3_imp_orig'])}% to {f1(S['s3_imp_hr'])}%, without changing the ranking "
              "of the capitals. ")
else:
    s3_txt = ""
if have_cs:
    cs_txt = (f"At the municipal scale, the annual mean RSEI series (Figure S2; Table S2) showed a significant monotonic "
              f"trend under the Hamed–Rao test in {S['cs_n_sig_hr']} of the 27 capitals: negative in "
              f"{', '.join(S['cs_neg_cities']) or 'none'} and positive in {', '.join(S['cs_pos_cities']) or 'none'}; Sen's "
              f"slopes ranged from {S['cs_slope_min']:+.4f} to {S['cs_slope_max']:+.4f} RSEI units per year. ")
else:
    cs_txt = ""
soc_txt = (f"Finally, the share of significant degradation was positively correlated with population density in 2022 "
           f"(Spearman ρ = {f2(rho_dd.spearman_rho)}, p = {f2(rho_dd.p_value)}, n = 27) and negatively with relative population "
           f"growth between 1991 and 2022 (ρ = {f2(rho_dg.spearman_rho)}, p = {f2(rho_dg.p_value)}), but not with total "
           f"population (ρ = {f2(S['rho_deg_pop'].spearman_rho)}, p = {f2(S['rho_deg_pop'].p_value)}); the share of significant "
           f"improvement was not significantly correlated with any of the three indicators (|ρ| ≤ "
           f"{f2(max(abs(rho_id.spearman_rho), abs(rho_ig.spearman_rho), abs(S['rho_imp_pop'].spearman_rho)))}, p ≥ "
           f"{f2(min(rho_id.p_value, rho_ig.p_value, S['rho_imp_pop'].p_value))}) (Table S6).")
rep("The integrated analysis of RSEI mean, median, standard deviation and Kendall's tau trend maps",
    pca_txt + ori_txt + s3_txt + cs_txt + soc_txt,
    ['Reviewer 1 Q8', 'Reviewer 1 Q9', 'Reviewer 1 Q11', 'Reviewer 3 Q3'])
for pre in ["The Amazon Legal Region exhibited unequivocal ecological advantages", "In the Southeast the RSEI patterns confirm that protected areas",
            "The South and Central-West regions demonstrated that planned urban green infrastructure",
            "Overall the RSEI proved highly effective in capturing the spatial and temporal complexity"]:
    dele(pre, ['Reviewer 1 Q13', 'Reviewer 2 Q4'])

# ================================================================== DISCUSSION
rep("The spatiotemporal analysis of the Remote Sensing Ecological Index (RSEI) across all 26 Brazilian state capitals",
    "The spatiotemporal analysis of the RSEI across the 27 Brazilian state capitals provided a consistent, multi-dimensional "
    "characterization of urban ecological dynamics over four decades. The index synthesized vegetation vigour (NDVI), "
    "surface moisture (WET), surface temperature (LST) and built-up and bare-soil extent (NDBSI) into a single metric, "
    "enabling spatially explicit comparisons among climatically and morphologically diverse cities, and its combination "
    "with pixel-wise Mann–Kendall testing allowed persistent change to be distinguished from inter-annual variability. The "
    "results extend to Brazil the evidence from Chinese and other urban contexts in which the RSEI tracked the ecological "
    "consequences of urbanization (Xu 2013; Hu and Xu 2018; Wang et al. 2020; Yang et al. 2022; Song et al. 2023). Two "
    "robustness checks strengthen this diagnosis: PC1 behaved as a general ecological-quality axis in all capital-year "
    "combinations examined, and the ranking of the capitals was insensitive to the correction for serial autocorrelation, "
    "although the corrected test reduced the extent of significant change (Section 3.8).",
    ['Reviewer 1 Q14', 'Reviewer 1 Q18', 'Reviewer 1 Q8', 'Reviewer 1 Q9'])
rep("Across the full national sample.17 of the 26 capitals exhibited statistically significant ecological degradation",
    f"Across the national sample, {nd3} of the 27 capitals showed statistically significant degradation over more than one "
    "third of their municipal territory, whereas significant improvement predominated in the Amazonian capitals and in some "
    "large metropolises with extensive protected areas. In contrast with degradation-dominated long-term RSEI trajectories "
    "reported elsewhere, such as the Zhoushan Archipelago, where more than 84% of the territory degraded between 1985 and "
    "2020 (Song et al. 2023), the Brazilian capitals displayed a far more heterogeneous picture, with improvement exceeding "
    f"degradation in {nimp} of them. This heterogeneity is consistent with the coexistence, within the same municipal "
    "boundaries, of consolidating urban cores and of large vegetated or peri-urban areas, and with national evidence of "
    "intensifying surface heat islands in the metropolitan cores (Monteiro et al. 2021; Patriota et al. 2024). The close "
    "correspondence between the mean and median maps indicates that the dominant conditions in each city are persistent "
    "rather than episodic, reinforcing the value of complete annual series for separating structural change from "
    "transient fluctuations. It should be stressed, however, that the RSEI is a relative index rescaled within each "
    "capital and year, so that a trend expresses the changing position of a pixel relative to its surroundings rather than "
    "an absolute change in surface conditions.", ['Reviewer 1 Q14', 'Reviewer 1 Q19', 'Reviewer 1 Q18', 'Editor Q2'])
rep("4.2. Ecological Resilience of Amazonian Capitals: The Primacy of Forest Continuity",
    "4.2. Amazonian capitals: favourable trajectories in forest-dominated municipalities", ['Reviewer 1 Q18', 'Editor Q2'])
rep("The Amazonian capitals Manaus-AM, Boa Vista-RR, Macapá-AP, Porto Velho-RO, and Rio Branco-AC consistently displayed",
    f"The Amazonian capitals Manaus, Boa Vista, Macapá and Porto Velho displayed the most favourable trajectories of the "
    f"sample, with significant improvement over {pct('Porto Velho', 'improvement_pct')}–{pct('Manaus', 'improvement_pct')}% "
    "of their municipal areas (Table 1). Because these municipalities are very large and predominantly covered by forest "
    "or savanna, the municipal balance is dominated by the non-urban matrix, which sustains high NDVI and WET values and "
    "attenuated LST, the biophysical drivers of high RSEI scores (Li et al. 2021; Zhao et al. 2021). The association between "
    "forest cover and favourable ecological indicators is well documented in tropical urban ecology (Silva Dias et al. "
    "2002; Bolund and Hunhammar 1999), but the present analysis did not quantify forest cover or its change; the "
    "interpretation that forest continuity underlies the positive trajectories is therefore inferred from the spatial "
    "coincidence between improvement and the vegetated matrix (Figures 3–5) and from the literature, not demonstrated by "
    "a formal attribution analysis.", ['Reviewer 1 Q18', 'Reviewer 1 Q15', 'Editor Q2'])
rep("The case of Manaus is particularly instructive.",
    f"Manaus is illustrative: {pct('Manaus', 'improvement_pct')}% of its municipal area showed significant improvement, "
    "while a compact cluster of significant degradation coincides with the consolidated urban core. The standard-deviation "
    "map adds a complementary reading, with low temporal variability over the forest matrix and elevated variability along "
    "the urban–forest boundary, which spatially delineates the active urbanization front. Positive RSEI trends over "
    "forested municipal territory may also reflect regrowth after earlier clearing and the long-term greening recorded by "
    "satellite indices in parts of the Amazon, and should not be read as evidence of improving conditions in the built-up "
    "areas themselves (Forman 2014; Pickett et al. 2011).", ['Reviewer 1 Q18', 'Editor Q2'])
rep("Belém-PA presents an analytically important exception within the Amazonian context.",
    f"Belém is an informative exception: it recorded the largest share of significant degradation of the sample "
    f"({pct('Belém', 'degradation_pct')}%), driven by its densely urbanized continental sector, whereas the fluvial islands "
    "that make up most of the municipal area retained higher and improving values. The contrast suggests that regional "
    "vegetation abundance does not by itself guarantee favourable conditions where urban pressure is spatially "
    "concentrated, in line with evidence that intra-urban green space conservation remains necessary even in cities "
    "embedded in forested regions (Weng 2009; Li et al. 2021). Rio Branco and Palmas, where the class without significant "
    "trend predominated, show that the Amazonian pattern is not uniform across the region.",
    ['Reviewer 1 Q18', 'Reviewer 1 Q19', 'Editor Q2'])
rep("The Northeast region exhibited the most widespread and spatially coherent pattern of ecological degradation among all Brazilian regions with five",
    f"The Northeast concentrated the most extensive significant degradation of the sample "
    f"({f1(reg.loc['Northeast', 'degradation_pct'])}% of the municipal area on average), with Salvador, Aracaju, Fortaleza, "
    "Natal and Recife showing large, contiguous areas of significant decline over the consolidated urban fabric. Several "
    "factors documented for these cities are plausible contributors, namely rapid and frequently unplanned urbanization, "
    "the suppression and fragmentation of Atlantic Forest, restinga and Caatinga remnants, intense coastal occupation and the "
    "amplifying effect of sub-humid and semi-arid climates on the thermal consequences of surface sealing (Nobre et al. "
    "2011; Oke 1982; Amorim 2017). These interpretations are consistent with the spatial coincidence between the degraded "
    "areas and the urban fabric visible in Figures 3–6, and with the positive surface heat-island trends reported for "
    "northeastern metropolitan regions by Monteiro et al. (2021) and Patriota et al. (2024), but the drivers were not "
    "quantified in the present study.", ['Reviewer 1 Q18', 'Reviewer 3 Q4', 'Reviewer 1 Q15'])
rep("Salvador-BA epitomizes the most extreme form of urban ecological deterioration observed in this study.",
    f"Salvador ({pct('Salvador', 'degradation_pct')}% significant degradation) and Aracaju "
    f"({pct('Aracaju', 'degradation_pct')}%) combined extensive decline with high temporal variability, indicating that "
    "ecological conditions along their coastal urban fabrics have not merely declined but fluctuated strongly, a pattern "
    "compatible with ongoing land conversion and with the vulnerability of littoral cities to unplanned urbanization "
    "(Mendonça 2003; Marandola Jr. and Hogan 2007). In Fortaleza, the near-homogeneous low mean and median values across "
    "the municipal territory are consistent with an advanced stage of urban consolidation, in which residual vegetation "
    "fragments retain little capacity to offset the ecological effects of impervious surfaces, a threshold behaviour "
    "described for cities with very high impervious fractions (Weng 2009; Seto et al. 2012); the smaller share of "
    f"significant degradation in Fortaleza ({pct('Fortaleza', 'degradation_pct')}%) than in Salvador may in part reflect "
    "this saturation, since further decline is limited in an already impoverished landscape.",
    ['Reviewer 1 Q18', 'Reviewer 3 Q4', 'Editor Q2'])
dele("Fortaleza-CE presents a qualitatively distinct degradation profile", ['Reviewer 1 Q18', 'Reviewer 2 Q4'])
rep("The elevated standard deviation values observed across Teresina-PI.Salvador-BA, and Maceió-AL deserve specific consideration",
    "The elevated temporal variability of Teresina, Maceió, Fortaleza and Salvador deserves attention because it indicates "
    "temporal instability rather than steady decline. In Teresina, the pronounced seasonality of the semi-arid climate "
    "produces strong intra-annual phenological cycles; because the annual composites integrate observations from the whole "
    "year, inter-annual differences in the timing and number of valid observations may contribute to the variability "
    "recorded there (Section 4.8). São Luís occupied a distinct position, with significant improvement exceeding "
    "degradation, which is spatially associated with mangrove, restinga and coastal forest sectors (MMA 2018); this "
    "suggests, without demonstrating, that the conservation status of coastal ecosystems modulates the municipal balance "
    "in coastal northeastern cities.", ['Reviewer 1 Q18', 'Reviewer 3 Q2', 'Editor Q2'])
dele("São Luís-MA occupies a distinctive intermediate position among Northeastern capitals", ['Reviewer 2 Q4'])
rep("4.4. Urban Conservation Units as Critical Ecological Anchors in Southeastern Capitals",
    "4.4. Southeastern capitals: intra-urban heterogeneity and the role of protected areas", ['Reviewer 1 Q18'])
rep("The Southeast region exhibited the greatest intra-urban RSEI heterogeneity among all Brazilian regions driven by the spatial coexistence",
    f"The Southeast displayed the sharpest intra-municipal contrasts of the sample. In São Paulo "
    f"({pct('São Paulo', 'improvement_pct')}% significant improvement, {pct('São Paulo', 'degradation_pct')}% degradation) and "
    f"Rio de Janeiro ({pct('Rio de Janeiro', 'improvement_pct')}% and {pct('Rio de Janeiro', 'degradation_pct')}%), significant "
    "degradation was concentrated in the high-density districts, while improvement and the highest mean values coincided "
    "with the Atlantic Forest remnants of southern São Paulo and with the forested massifs of Rio de Janeiro, including the "
    "Tijuca National Park. This spatial segregation is consistent with the view that large conservation units within "
    "metropolitan limits sustain ecological quality in densely built environments (Haaland and van den Bosch 2015; Forman "
    "2014; Pickett et al. 2011), although the present data document the coincidence between protected areas and favourable "
    "trends rather than a causal effect of protection.", ['Reviewer 1 Q18', 'Reviewer 1 Q15', 'Editor Q2'])
rep("São Paulo-SP exemplifies this dynamic: despite being Brazil's largest metropolis",
    f"Belo Horizonte ({pct('Belo Horizonte', 'degradation_pct')}% significant degradation) and Vitória "
    f"({pct('Vitória', 'degradation_pct')}%) showed negative balances, reflecting the predominance of high-density impervious "
    "cover and the limited extent of forest remnants within their municipal perimeters, with improvement confined to the "
    "Serra do Curral area in the south of Belo Horizonte and to the continental sector of Vitória. The elevated temporal "
    "variability across much of Belo Horizonte is compatible with evidence that rapidly expanding mid-sized metropolises "
    "in the Global South frequently outpace the capacity of planning systems to maintain green infrastructure (Angeoletto "
    "et al. 2019; Seto et al. 2012).", ['Reviewer 1 Q18', 'Editor Q2'])
for pre in ["Rio de Janeiro-RJ presents the most dramatic intra-urban RSEI contrast", "Belo Horizonte-MG.by contrast exhibited predominantly negative trends"]:
    dele(pre, ['Reviewer 2 Q4', 'Reviewer 1 Q18'])
rep("4.5. Southern and Central-West Capitals: Planned Green Infrastructure Cerrado Remnants.and Ecological Fragmentation",
    "4.5. Southern and Central-West capitals: green infrastructure, Cerrado remnants and fragmentation", ['Reviewer 1 Q18'])
rep("The South region exhibited the most spatially fragmented RSEI trend patterns among all Brazilian regions characterized by fine-grained",
    f"In the South, Porto Alegre achieved the most favourable balance ({pct('Porto Alegre', 'improvement_pct')}% significant "
    "improvement), with improvement spatially associated with the Guaíba shoreline and riparian systems, whereas Curitiba "
    f"({pct('Curitiba', 'degradation_pct')}% degradation, {pct('Curitiba', 'improvement_pct')}% improvement) and Florianópolis "
    f"({pct('Florianópolis', 'degradation_pct')}% and {pct('Florianópolis', 'improvement_pct')}%) showed negative balances. "
    "Curitiba is frequently cited internationally for its park system; the fine-grained mosaic of significant degradation "
    "and improvement observed here suggests that distributed parks generate local stability but do not offset the "
    "aggregate effect of densification at the municipal scale, in line with arguments that connectivity and the "
    "preservation of larger contiguous green areas are as important as the number of green spaces (Ahern 2013; Benedict and "
    "McMahon 2006). In Florianópolis, significant degradation concentrated along the coastal urbanization fronts of Santa "
    "Catarina Island, where tourism-driven expansion has been most intense, while improvement persisted in the interior "
    "Atlantic Forest remnants; this pattern echoes international evidence that amenity-driven coastal expansion removes "
    "highly productive coastal ecosystems (MMA 2018).", ['Reviewer 1 Q18', 'Reviewer 1 Q19', 'Editor Q2'])
rep("In the Central-West, Brasília-DF presents a spatially structured RSEI pattern directly shaped by its planned urban morphology",
    f"In the Central-West, Brasília ({pct('Brasília', 'improvement_pct')}% significant improvement) combined degradation in the "
    "planned urban sectors with improvement over the surrounding Cerrado, whereas Goiânia and Campo Grande were nearly "
    f"balanced and Cuiabá showed a negative balance ({pct('Cuiabá', 'degradation_pct')}% degradation). The Cerrado is among "
    "the most threatened tropical savannas because of agricultural conversion (Klink and Machado 2005; Sano et al. 2010; "
    "Alencar et al. 2020), and the capitals of the region add localized pressure on remnant patches; the large share of "
    "area without significant trend in these capitals may reflect the combination of such pressures with the high "
    "inter-annual variability of savanna vegetation, which reduces the power of monotonic trend tests. Palmas, founded in "
    "1989 and therefore the only capital built almost entirely within the observation window, showed the high temporal "
    "variability expected from its rapid transition from undeveloped to urban land.", ['Reviewer 1 Q18', 'Editor Q2'])
dele("Florianópolis-SC recorded the highest degradation rate among southern capitals (55.38%) concentrated", ['Reviewer 2 Q4'])
rep("The temporal standard deviation of RSEI emerged as a particularly valuable complementary metric",
    "The temporal standard deviation of the RSEI proved a useful complement to the trend maps by revealing patterns of "
    "instability that trends alone cannot capture. Three configurations recurred: continuous vegetated areas with low "
    "variability (notably the Amazonian capitals); intensely urbanized northeastern capitals with high variability over most "
    "of their territory, suggesting temporal instability associated with irregular vegetation dynamics, fluctuating thermal "
    "regimes and land-cover turnover; and consolidated metropolitan cores (São Paulo, Vitória, Rio de Janeiro) with low but "
    "stable values, surrounded by transitional zones of high variability. This structure distinguishes chronically "
    "impoverished but stable areas, actively changing areas and stable high-quality areas, each of which calls for "
    "different planning responses (Haaland and van den Bosch 2015; Dobbs et al. 2014). High variability in degraded areas "
    "may indicate susceptibility to further deterioration or, conversely, potential for recovery, and such zones are "
    "candidates for priority monitoring and restoration.", ['Reviewer 1 Q18', 'Reviewer 1 Q21'])
dele("These findings reinforce the interpretive value of combining mean/median trend statistics", ['Reviewer 2 Q4'])
rep("The inverse relationship between RSEI and urban heat island (UHI) intensity mediated through LST",
    "Because LST is one of the four components of the index, low RSEI values are by construction associated with high "
    "surface temperature; the coupling between ecological impoverishment and thermal exposure observed here is therefore "
    "expected and consistent with the extensive evidence on surface urban heat islands (Oke 1982; Amorim 2017; IPCC 2023; "
    "Patriota et al. 2024). The practical implication is that green-infrastructure measures that raise the RSEI, such as "
    "the conservation of forest remnants, the creation of parks, the maintenance of riparian corridors and the expansion "
    "of permeable surfaces, address ecological quality and thermal exposure simultaneously.", ['Reviewer 1 Q18', 'Editor Q2'])
rep("The regional differentiation identified in this study suggests that climate-ecological vulnerability",
    "The regional differentiation identified here suggests that ecological and thermal vulnerability is unevenly "
    "distributed among Brazilian capitals, with the northeastern capitals combining the most extensive significant "
    "degradation with hot climates. These cities appear to be priority targets for green-infrastructure policies, including "
    "the recovery of native remnants within urban perimeters, park networks in impervious-dominated districts and the "
    "integration of green-infrastructure standards into zoning instruments, and the apparent saturation of Fortaleza "
    "underlines the value of preventive planning in secondary cities that are still growing (Seto et al. 2012; Ahern 2013). "
    "The exploratory association between the share of degraded area and population density, together with the absence of "
    "association with total population, is consistent with this reading: degradation was more extensive in dense, "
    "consolidated capitals than in large but sparsely occupied municipalities, and less extensive where population growth "
    "since 1991 was fastest, which mostly corresponds to the northern and central-western capitals with vast non-urban "
    "territories. These correlations describe municipal-scale associations only and should not be interpreted causally.",
    ['Reviewer 1 Q18', 'Reviewer 3 Q3', 'Editor Q2'])
rep("More broadly the results confirm that the spatial organization of land use within each city",
    "More broadly, the results are compatible with the view that the spatial organization of land use within each city, "
    "in particular the extent and conservation status of large green areas, matters as much for the municipal RSEI balance "
    "as urbanization intensity per se. São Paulo, Rio de Janeiro, Brasília and Porto Alegre achieved positive balances not "
    "because urban pressure is lower but because large conserved areas within or adjacent to their urban boundaries offset "
    "the degradation of the built-up zones. This observation supports, without formally testing, the case for green "
    "infrastructure as a structural component of urban development strategies (Benedict and McMahon 2006; Ahern 2013; "
    "Haaland and van den Bosch 2015).", ['Reviewer 1 Q18', 'Editor Q2'])
rep("The analytical framework employed integrating Landsat time series processed on Google Earth Engine",
    "The framework, which integrates Landsat time series processed in GEE with a per-capital PCA-based RSEI and "
    "non-parametric trend testing, proved replicable and internally consistent: the mean, median and trend maps agreed "
    "spatially in every capital, PC1 behaved as a general ecological-quality axis in all combinations examined, and the "
    "ranking of the capitals was robust to the correction for serial autocorrelation. The complete pipeline is available "
    "in the code repository (Section 2.7).", ['Editor Q3', 'Reviewer 3 Q1'])
rep("Several limitations must be acknowledged. The 30-metre spatial resolution of Landsat imagery",
    "Several limitations must be acknowledged. (i) Seasonality: the annual composites are medians of all valid observations "
    "of the year, and the number and timing of valid observations differ among years and capitals (fewer cloud-free "
    "scenes in the wet season, Landsat 7 scan-line gaps after 2003, and a sparser archive in the 1980s and 1990s for some "
    "northern capitals). In capitals with strongly seasonal climates, such as Teresina, Cuiabá and Palmas, part of the "
    "inter-annual variability of the RSEI may therefore reflect differences in the seasonal composition of the composites "
    "rather than ecological change; the seasonal periods represented in each composite could not be controlled, and this "
    "is a source of uncertainty for the trends, particularly where the temporal standard deviation is high. (ii) Relative "
    "index: because normalization and PCA are repeated for each capital and year, the RSEI expresses the position of a "
    "pixel relative to the processing polygon in that year; the index is not directly comparable in absolute terms among "
    "cities or years, and the trends are trends in relative condition. (iii) Serial autocorrelation: the Hamed–Rao "
    "correction reduced the extent of significant change in every capital, so the shares in Table 1, which are based on "
    "the uncorrected test, should be regarded as upper bounds; the sensitivity analysis is reported in Table S5. (iv) Sign "
    "of PC1: the orientation of the first component had to be verified and corrected a posteriori in a small number of "
    "capital-year images (Table S3), a step that we recommend as standard practice in automated RSEI pipelines. (v) Spatial "
    "domain: the processing polygons encompass areas beyond the municipality, water surfaces were not masked and residual "
    "gaps were filled with neighbourhood or polygon means (Table S1), which may smooth local values; no urban mask was "
    "applied, so the municipal shares combine urban, rural, forested and water-covered land. (vi) The 30 m resolution limits "
    "the detection of fine-scale features such as street trees and small parks (Liu et al. 2022), and the index does not "
    "incorporate socioeconomic, institutional or infrastructural dimensions, so the drivers discussed above are inferred "
    "rather than tested. Future work should combine the RSEI with land-cover change data, higher-resolution imagery and "
    "explicit urban-form and governance variables to attribute the observed trajectories.",
    ['Editor Q3', 'Reviewer 3 Q2', 'Reviewer 1 Q9', 'Reviewer 1 Q8'])

# ================================================================== CONCLUSIONS
c1 = rep("This study provided a comprehensive statistically robust characterization of urban ecological dynamics across all 26",
         "This study provided the first nationally consistent characterization of the trajectory of urban ecological quality "
         "in all 27 Brazilian state capitals, based on annual RSEI series for 1985–2025 and pixel-wise Mann–Kendall testing. "
         "Urban ecological quality in Brazil is strongly differentiated by region and within municipalities. Significant "
         f"degradation covered more than one third of the municipal territory in {nd3} capitals and was most extensive in "
         "the Northeast and in Belém, whereas significant improvement predominated in the Amazonian capitals and in large "
         "metropolises with extensive protected areas; in the Southeast, South and Central-West the two classes coexisted "
         "in fragmented mosaics, and a substantial share of every municipality showed no significant monotonic trend.",
         ['Reviewer 1 Q20', 'Reviewer 1 Q21', 'Reviewer 1 Q22', 'Editor Q2'])
c2 = ins(c1, "The spatial coincidence between favourable trajectories and continuous native vegetation or large conservation "
         "units, and between degradation and consolidated urban cores, is consistent with a buffering role of green "
         "infrastructure, but these associations were inferred from spatial patterns and from the literature rather than "
         "demonstrated by attribution analyses; the exploratory correlation between degraded area and population density "
         "points in the same direction. The temporal standard deviation of the RSEI added a useful dimension by separating "
         "stable high-quality areas, chronically impoverished but stable cores and actively changing transition zones. The "
         "robustness checks showed that PC1 behaves as a general ecological-quality axis, that the orientation of the index "
         "must be verified in automated pipelines, and that serial autocorrelation reduces the extent, but not the ranking, "
         "of significant change.", ['Reviewer 1 Q20', 'Reviewer 1 Q21', 'Editor Q2'])
ins(c2, "The open workflow and the national baseline presented here can support the monitoring of urban ecological quality "
    "and the prioritization of green infrastructure and climate-adaptation measures in Brazilian cities. Future research "
    "should attribute the observed trajectories to land-cover change, urban form and governance, control the seasonal "
    "composition of the annual composites, and extend the comparison to other Latin American cities.",
    ['Reviewer 1 Q21'])
for pre in ["The principal findings can be synthesized into five overarching conclusions.", "Second native forest continuity is the primary determinant",
            "Third within-city conservation units and large urban forest remnants", "Fourth the temporal standard deviation of RSEI constitutes",
            "Fifth urban ecological quality and climate vulnerability are functionally coupled",
            "Collectively these findings underscore that the trajectory of urban ecological quality"]:
    dele(pre, ['Reviewer 1 Q20', 'Reviewer 1 Q21', 'Reviewer 2 Q4'])

# ================================================================== DECLARATIONS / SUPPLEMENT
p_av = rep("All datasets used and/or analyzed during this study are available from the data sources",
           "The Landsat Collection 2 composites are publicly available in Google Earth Engine. The annual RSEI images and the "
           "per-capital trend products (Kendall's τ, p-value, Sen's slope, temporal mean, median and standard deviation) "
           "generated in this study, clipped to the municipal boundaries, are distributed as GeoTIFF files with the code "
           f"repository ({GH}); the complete Earth Engine assets are available from the corresponding author on request. "
           "Demographic data were obtained from IBGE/SIDRA (https://sidra.ibge.gov.br).", ['Reviewer 3 Q1'])
h_code = ins(p_av, "Code Availability", ['Reviewer 3 Q1'], style_from="Availability of Data and Materials")
ins(h_code, f"The computational scripts supporting this study are publicly available in the authors' GitHub repository ({GH}). "
    "The repository includes the Google Earth Engine/Colab scripts for Landsat processing and RSEI computation, the audit "
    "of missing years, the pixel-wise Mann–Kendall and Sen's slope trend analysis, the Python scripts used for the "
    "municipal area accounting, the sensitivity analyses (orientation of PC1, PCA loadings, serial autocorrelation) and the "
    "generation of the figures and tables, together with documentation and the software dependencies required to "
    "reproduce the workflow. Authentication credentials, private configuration files and restricted-access datasets are "
    "excluded; users must authenticate to Google Earth Engine with their own credentials.", ['Reviewer 3 Q1'],
    style_from=p_av)
rep("Supplementary Material S1. Spatial distribution of the Remote Sensing Ecological Index (RSEI) across the 27 Brazilian capitals.",
    "Figure S1. Annual maps of the Remote Sensing Ecological Index (RSEI) for the 27 Brazilian state capitals (1985–2025), "
    "ordered alphabetically by capital. Figure S2. Annual municipal mean RSEI series of the 27 capitals with the Sen's slope "
    "line. Table S1. Data completeness and gap-filling diagnostics of the 1,107 annual RSEI images. Table S2. Municipal "
    "trend statistics (shares of negative and positive τ, Mann–Kendall statistics of the municipal mean series with and "
    "without the Hamed–Rao correction, Sen's slope). Table S3. Orientation check of every capital-year image (Pearson "
    "correlation of the exported RSEI with NDVI and LST). Table S4. Eigenvalues, variance explained and PC1 loadings of the "
    "per-capital PCA in 1985, 2005 and 2025. Table S5. Sensitivity of the Mann–Kendall significance to tie correction and "
    "to serial autocorrelation on 1,000 random pixels per capital. Table S6. Demographic indicators of the 27 capitals and "
    "Spearman correlations with the trend classes.", ['Reviewer 1 Q17', 'Reviewer 1 Q23', 'Reviewer 1 Q14'])

# ================================================================== REFERENCES
for pre in ["Artis DA.Carnahan WH (1982)", "Congalton RG.Green K (2019)", "Pohlert T (2023) trend:", "Sobrino JA.Jiménez-Muñoz JC.Paolini L (2004)",
            "Fearnside PM (2005)", "Monteiro CAF (1976)"]:
    dele(pre, ['Editor Q1'], note='reference no longer cited')
rep("IBGE – Instituto Brasileiro de Geografia e Estatística (2023) Pesquisa Nacional por Amostra",
    "IBGE – Instituto Brasileiro de Geografia e Estatística (2023) Censo Demográfico 2022: população e domicílios; Sistema "
    "IBGE de Recuperação Automática (SIDRA), tabelas 200, 4709 e 4714. IBGE, Rio de Janeiro. https://sidra.ibge.gov.br",
    ['Reviewer 1 Q11', 'Reviewer 3 Q3'])
ins("Hu X.Xu H (2018) A new remote sensing index",
    "Hussain M, Mahmud I (2019) pyMannKendall: a python package for non parametric Mann Kendall family of trend tests. "
    "J Open Source Softw 4:1556. https://doi.org/10.21105/joss.01556", ['Reviewer 1 Q9'])
ins("Luo X.Liu J.Ma X.Zhang L (2022) Temporal and spatial changes",
    "Malakar NK, Hulley GC, Hook SJ, Laraby K, Cook M, Schott JR (2018) An operational land surface temperature product for "
    "Landsat thermal data: methodology and validation. IEEE Trans Geosci Remote Sens 56:5717–5735. "
    "https://doi.org/10.1109/TGRS.2018.2824828", ['Editor Q1'])
ins("United Nations Department of Economic and Social Affairs Population Division (2018)",
    "USGS – U.S. Geological Survey (2024) Landsat Collection 2 Level-2 Science Products. USGS, Sioux Falls. "
    "https://www.usgs.gov/landsat-missions/landsat-collection-2-level-2-science-products", ['Editor Q1'])


# ---- Reviewer 1 Q1: uniform font in the title block (affiliations) ----
from lxml import etree as _et
for pre in ["1 Postgraduate Program in Earth Modeling", "2 Facultad de Humanidades de Albacete", "3 Department of Engenharia Florestal",
            "*Author to whom correspondence", "rnvuefsppgm@gmail.com / rnv@uefs.br"]:
    try:
        p = d.find(pre)
    except KeyError:
        continue
    for r in p.iter(q('r')):
        rpr = r.find(q('rPr'))
        if rpr is None:
            rpr = _et.SubElement(r, q('rPr'))
            r.insert(0, rpr)
        for e in rpr.findall(q('rFonts')):
            rpr.remove(e)
        rf = _et.Element(q('rFonts'))
        for a in ('ascii', 'hAnsi', 'cs', 'eastAsia'):
            rf.set(q(a), 'Times New Roman')
        rpr.insert(0, rf)
        for e in rpr.findall(q('sz')) + rpr.findall(q('szCs')):
            rpr.remove(e)
        for tag in ('sz', 'szCs'):
            s_ = _et.SubElement(rpr, q(tag))
            s_.set(q('val'), '22')
EDITS.append({'qids': ['Reviewer 1 Q1'], 'action': 'format', 'anchor': 'title block / affiliations', 'new_text': None,
              'note': 'font set to Times New Roman 11 pt (no text change)'})

# ================================================================== SAVE
d.set_metadata('RNV')
rev = os.path.join(OUT, 'Main_text_UEC_formatted_v4_Revised.docx')
cln = os.path.join(OUT, 'Main_text_UEC_formatted_v4_Clean.docx')
d.save(rev, clean=False)
d.save(cln, clean=True)
json.dump(EDITS, open(os.path.join(OUT, 'edit_log.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump(d.log, open(os.path.join(OUT, 'edit_log_raw.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
words = sum(len(Docx.ptext(p).split()) for p in d.paragraphs())
print('saved', rev, '| comments:', len(d.comments), '| edits:', len(EDITS), '| words (all paragraphs incl. refs):', words)
