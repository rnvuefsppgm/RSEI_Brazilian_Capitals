# -*- coding: utf-8 -*-
"""
A1 - Pixel-wise Mann-Kendall / Sen's slope trends recomputed after correcting the
orientation of sign-inverted annual RSEI images.  (Adapted, 2026 revision)

Provenance: the trend computation (function mk_sen_for_collection and the export
routine) is copied VERBATIM from the original notebook
NEW_Trends_RSEI_2026_Luana_V3_multiplos_assets.ipynb (Google Colab / Earth Engine).
Only changes:
  1. the merged annual collection is loaded through ee_common (both asset roots);
  2. capital-year images flagged by S2_orientation_check (Pearson r between the
     exported RSEI and NDVI < 0) are re-oriented as RSEI' = 1 - RSEI before the
     trend analysis (the min-max rescaling of the original script makes the two
     orientations exact complements);
  3. the output folder is a new asset folder, leaving the original products intact.
Usage: python A1_recompute_trends_orientation_corrected.py <out_S2_orientation_check.csv> [municipality ...]
Requires: earthengine authenticate; EE_PROJECT environment variable.
"""
import sys
import os
import math
import re
import unicodedata
import csv
import ee
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'New_for_Review'))
import ee_common as C

OUTPUT_ASSET_FOLDER = f"projects/{os.environ.get('EE_PROJECT', 'rnvuefsppgm')}/assets/RSEI_TRENDS_2026_oriented"
MUNIC_FIELD = "NM_MUN"
YEAR_FIELD = "ANO"
BANDS_TO_ANALYZE = ["RSEI"]
MAX_PIXELS = 1e13

C.init()
col, ids = C.load_merged_collection()

# ---- flagged images (orientation check) ----
flagged = set()
with open(sys.argv[1], encoding='utf-8') as fh:
    for r in csv.DictReader(fh):
        if r['r_RSEI_NDVI'] and float(r['r_RSEI_NDVI']) < 0:
            flagged.add(r['asset'])
print(len(flagged), 'sign-inverted images will be re-oriented', flush=True)
flag_list = ee.List(sorted(flagged))


def reorient(img):
    img = ee.Image(img)
    inv = flag_list.contains(img.get('system:id'))
    rsei = img.select('RSEI')
    fixed = ee.Image(ee.Algorithms.If(inv, ee.Image.constant(1).subtract(rsei).rename('RSEI'), rsei))
    return img.addBands(fixed, overwrite=True).set('reoriented', inv)


col = col.map(reorient)


# ======== verbatim from the original notebook (helper functions) ========
def sanitize_name(text):
    text = str(text).strip()
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9]+', '_', text)
    text = re.sub(r'_+', '_', text).strip('_')
    return text


def ensure_asset_folder(asset_path):
    try:
        ee.data.getAsset(asset_path)
        print(f"Pasta de saída já existe: {asset_path}")
    except Exception:
        print(f"Criando pasta de saída: {asset_path}")
        ee.data.createAsset({'type': 'FOLDER'}, asset_path)


def normal_cdf_from_z(z_img):
    return z_img.divide(math.sqrt(2)).erf().add(1).multiply(0.5)


def rename_metric_bands(bands, metric):
    return [f"{b}_{metric}" for b in bands]


def add_numeric_year_property(img):
    year_num = ee.Number.parse(ee.String(img.get(YEAR_FIELD)))
    return img.set('year_num', year_num)


def mk_sen_for_collection(ic, bands):
    ic = ic.map(add_numeric_year_property).sort('year_num')
    n = ic.size()
    mean_img = ic.select(bands).mean().rename(rename_metric_bands(bands, "mean"))
    median_img = ic.select(bands).median().rename(rename_metric_bands(bands, "median"))
    std_img = ic.select(bands).reduce(ee.Reducer.stdDev()).rename(rename_metric_bands(bands, "stdDev"))
    n_info = n.getInfo()
    img_list = ic.toList(n)
    sign_images = []
    slope_images = []
    for i in range(n_info - 1):
        img_i = ee.Image(img_list.get(i)).select(bands)
        year_i = ee.Number(ee.Image(img_list.get(i)).get('year_num'))
        for j in range(i + 1, n_info):
            img_j = ee.Image(img_list.get(j)).select(bands)
            year_j = ee.Number(ee.Image(img_list.get(j)).get('year_num'))
            dy = img_j.subtract(img_i)
            dt = year_j.subtract(year_i)
            sign_ij = dy.gt(0).subtract(dy.lt(0)).toFloat()
            slope_ij = dy.divide(dt).toFloat()
            sign_images.append(sign_ij)
            slope_images.append(slope_ij)
    S_raw = ee.ImageCollection.fromImages(sign_images).sum()
    S_img = S_raw.rename(rename_metric_bands(bands, "S"))
    n_num = ee.Number(n)
    varS_scalar = n_num.multiply(n_num.subtract(1)).multiply(n_num.multiply(2).add(5)).divide(18)
    varS_raw = ee.Image.constant(varS_scalar).toFloat().rename(bands)
    varS_img = varS_raw.rename(rename_metric_bands(bands, "varS"))
    sqrt_varS = varS_raw.sqrt()
    z_pos = S_raw.subtract(1).divide(sqrt_varS)
    z_neg = S_raw.add(1).divide(sqrt_varS)
    z_zero = ee.Image.constant(0).rename(bands).toFloat()
    Z_raw = ee.Image(ee.Algorithms.If(True, z_zero.where(S_raw.gt(0), z_pos).where(S_raw.lt(0), z_neg), z_zero)).toFloat()
    Z_img = Z_raw.rename(rename_metric_bands(bands, "Z"))
    n_pairs = n_num.multiply(n_num.subtract(1)).divide(2)
    tau_raw = S_raw.divide(n_pairs).toFloat()
    tau_img = tau_raw.rename(rename_metric_bands(bands, "tau"))
    absZ = Z_raw.abs()
    p_raw = ee.Image.constant(1).subtract(normal_cdf_from_z(absZ)).multiply(2).toFloat()
    p_img = p_raw.rename(rename_metric_bands(bands, "p_value"))
    slope_raw = ee.ImageCollection.fromImages(slope_images).median().toFloat()
    slope_img = slope_raw.rename(rename_metric_bands(bands, "sen_slope"))
    intercept_ic = ic.map(lambda im: ee.Image(im).select(bands).subtract(slope_raw.multiply(ee.Number(im.get('year_num')))))
    intercept_raw = intercept_ic.median().toFloat()
    intercept_img = intercept_raw.rename(rename_metric_bands(bands, "sen_intercept"))
    return ee.Image.cat([S_img, varS_img, Z_img, tau_img, p_img, slope_img, intercept_img, mean_img, median_img, std_img])


def export_municipality_trend_image(ic_mun, mun_name, bands):
    ic_mun = ic_mun.map(add_numeric_year_property).sort('year_num')
    count_imgs = ic_mun.size().getInfo()
    if count_imgs == 0:
        return None
    trend_img = mk_sen_for_collection(ic_mun, bands)
    years = ic_mun.aggregate_array(YEAR_FIELD).getInfo()
    years_sorted = sorted([int(y) for y in years])
    n_reor = ic_mun.filter(ee.Filter.eq('reoriented', True)).size().getInfo()
    safe_name = sanitize_name(mun_name)
    asset_name = f"trend_{safe_name}"
    asset_id = f"{OUTPUT_ASSET_FOLDER}/{asset_name}"
    trend_img = trend_img.set({'municipio': mun_name, 'municipio_sanitizado': safe_name, 'n_images': count_imgs,
                               'years': years_sorted, 'n_reoriented': n_reor,
                               'source_asset': ' | '.join(C.ASSET_ROOTS), 'orientation_corrected': True})
    first_img = ee.Image(ic_mun.first()).select(bands[0])
    proj = first_img.projection()
    scale = proj.nominalScale().getInfo()
    crs = proj.crs().getInfo()
    region = ic_mun.geometry()
    print(f"  Exportando para: {asset_id} | anos: {len(years_sorted)} | reorientados: {n_reor}", flush=True)
    task = ee.batch.Export.image.toAsset(image=trend_img, description=asset_name[:100], assetId=asset_id,
                                         region=region, scale=scale, crs=crs, maxPixels=MAX_PIXELS)
    task.start()
    return task


# ======== execution ========
ensure_asset_folder(OUTPUT_ASSET_FOLDER)
municipios = col.aggregate_array(MUNIC_FIELD).distinct().sort().getInfo()
if len(sys.argv) > 2:
    municipios = [m for m in municipios if m in sys.argv[2:]]
tasks = []
for idx, mun in enumerate(municipios, start=1):
    print(f"[{idx}/{len(municipios)}] {mun}", flush=True)
    ic_mun = col.filter(ee.Filter.eq(MUNIC_FIELD, mun)).sort(YEAR_FIELD)
    try:
        task = export_municipality_trend_image(ic_mun, mun, BANDS_TO_ANALYZE)
        if task is not None:
            tasks.append((mun, task))
    except Exception as e:
        print(f"  Erro ao processar {mun}: {e}", flush=True)
print("Total de tasks iniciadas:", len(tasks), flush=True)
