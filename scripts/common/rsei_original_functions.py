# -*- coding: utf-8 -*-
"""
rsei_original_functions.py  (Adapted, 2026 revision)
Helper functions copied VERBATIM from the original processing script
01_compute_annual_rsei_by_capital.py (Google Colab / Earth Engine): pixel-count diagnostics,
thermal gap filling, RSEI component indices (NDVI, WET, IBI, SI, NDBSI stored as NDSI, LST),
min-max normalisation (with inversion for heat and dryness) and per-region PCA.
Only change: packaged as an importable module (no exports are triggered on import).
"""
import math
import re
import ee

# ============================================================
# HELPERS: contagem de pixels mascarados
# ============================================================
def count_masked_pixels(img, band_name, region, scale, tile_scale=4):
    band = img.select(band_name)

    valid_count = ee.Number(
        band.mask().reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=region,
            scale=scale,
            maxPixels=1e13,
            bestEffort=True,
            tileScale=tile_scale
        ).get(band_name)
    )

    total_count = ee.Number(
        ee.Image.constant(1).clip(region).reduceRegion(
            reducer=ee.Reducer.count(),
            geometry=region,
            scale=scale,
            maxPixels=1e13,
            bestEffort=True,
            tileScale=tile_scale
        ).get('constant')
    )

    valid_count = ee.Number(ee.Algorithms.If(valid_count, valid_count, 0))
    total_count = ee.Number(ee.Algorithms.If(total_count, total_count, 0))

    return total_count.subtract(valid_count).max(0)

# ============================================================
# HELPERS: preenchimento leve da banda termal
# ============================================================
def fill_thermal_gaps(img, region, scale, tile_scale=4):
    thermal = img.select('thermal')

    fill_1 = thermal.focalMean(radius=1, kernelType='square', units='pixels')
    fill_2 = thermal.focalMean(radius=2, kernelType='square', units='pixels')
    fill_4 = thermal.focalMean(radius=4, kernelType='square', units='pixels')

    mean_dict = thermal.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=scale,
        maxPixels=1e13,
        bestEffort=True,
        tileScale=tile_scale
    )

    mean_val = ee.Number(
        ee.Algorithms.If(mean_dict.get('thermal'), mean_dict.get('thermal'), 0)
    )
    mean_img = ee.Image.constant(mean_val).rename('thermal')

    thermal_filled = (
        thermal
        .unmask(fill_1)
        .unmask(fill_2)
        .unmask(fill_4)
        .unmask(mean_img)
        .rename('thermal')
        .clip(region)
    )

    return img.addBands(thermal_filled, overwrite=True)

# ============================================================
# HELPERS: preenchimento completo e leve do RSEI
# ============================================================
def fill_rsei_gaps_complete(rsei_img, region, scale, tile_scale=4):
    """
    Preenche todos os buracos da banda RSEI:
    - contexto local escalonado: 1, 2, 4, 8, 16, 32 pixels
    - fallback final com a média do município
    """
    missing_before = count_masked_pixels(rsei_img, 'RSEI', region, scale, tile_scale)

    radii = [1, 2, 4, 8, 16, 32]
    filled = rsei_img

    for rad in radii:
        neigh = filled.focalMean(radius=rad, kernelType='square', units='pixels')
        filled = filled.unmask(neigh).rename('RSEI')

    mean_dict = filled.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=scale,
        maxPixels=1e13,
        bestEffort=True,
        tileScale=tile_scale
    )

    mean_val = ee.Number(
        ee.Algorithms.If(mean_dict.get('RSEI'), mean_dict.get('RSEI'), 0)
    )

    mean_img = ee.Image.constant(mean_val).rename('RSEI')

    # garante preenchimento total do que restar
    filled = filled.unmask(mean_img).rename('RSEI').clip(region)

    missing_after = count_masked_pixels(filled, 'RSEI', region, scale, tile_scale)

    return filled, missing_before, missing_after

# ============================================================
# HELPERS: índices
# ============================================================
def add_indices(img, year):
    blue  = img.select('blue')
    green = img.select('green')
    red   = img.select('red')
    nir   = img.select('nir')
    swir1 = img.select('swir1')
    swir2 = img.select('swir2')
    thermalK = img.select('thermal')  # Kelvin

    ndvi = nir.subtract(red).divide(nir.add(red)).rename('NDVI')

    year = ee.Number(year)

    wetTM = (
        blue.multiply(0.0315)
        .add(green.multiply(0.2021))
        .add(red.multiply(0.3102))
        .add(nir.multiply(0.1594))
        .add(swir1.multiply(-0.6806))
        .add(swir2.multiply(-0.6109))
        .rename('WET')
    )

    wetOLI = (
        blue.multiply(0.1511)
        .add(green.multiply(0.1972))
        .add(red.multiply(0.3283))
        .add(nir.multiply(0.3407))
        .add(swir1.multiply(-0.7117))
        .add(swir2.multiply(-0.4559))
        .rename('WET')
    )

    wet = ee.Image(ee.Algorithms.If(year.lte(2012), wetTM, wetOLI)).rename('WET')

    term1 = swir1.multiply(2).divide(swir1.add(nir))
    term2 = nir.divide(nir.add(red)).add(green.divide(green.add(swir1)))
    ibi = term1.subtract(term2).divide(term1.add(term2)).rename('IBI')

    si = (
        swir1.add(red)
        .subtract(nir.add(blue))
        .divide((swir1.add(red)).add(nir.add(blue)))
        .rename('SI')
    )

    ndsi = ibi.add(si).divide(2).rename('NDSI')

    lst = thermalK.subtract(273.15).rename('LST')

    return img.addBands([ndvi, wet, ibi, si, ndsi, lst])

# ============================================================
# HELPERS: normalização min-max
# ============================================================
def min_max_norm(img, band_name, region, scale, invert=False, tile_scale=4):
    band = img.select(band_name)

    stats = band.reduceRegion(
        reducer=ee.Reducer.minMax(),
        geometry=region,
        scale=scale,
        maxPixels=1e13,
        bestEffort=True,
        tileScale=tile_scale
    )

    mn = ee.Number(stats.get(ee.String(band_name).cat('_min')))
    mx = ee.Number(stats.get(ee.String(band_name).cat('_max')))
    eps = ee.Number(1e-6)

    if invert:
        normalized = (
            ee.Image.constant(mx)
            .subtract(band)
            .divide(ee.Image.constant(mx).subtract(mn).add(eps))
        )
    else:
        normalized = band.subtract(mn).divide(mx.subtract(mn).add(eps))

    return normalized.rename('n_' + band_name)

# ============================================================
# HELPERS: PCA por região
# ============================================================
def run_pca(norm_stack, region, scale, tile_scale=4):
    band_names = norm_stack.bandNames()
    n_bands = band_names.length()

    array_image_1d = norm_stack.toArray()

    covar = array_image_1d.reduceRegion(
        reducer=ee.Reducer.centeredCovariance(),
        geometry=region,
        scale=scale,
        maxPixels=1e13,
        bestEffort=True,
        tileScale=tile_scale
    )
    covar_array = ee.Array(covar.get('array'))

    eigens = covar_array.eigen()
    eigen_vectors = eigens.slice(1, 1)

    mean_dict = norm_stack.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=scale,
        maxPixels=1e13,
        bestEffort=True,
        tileScale=tile_scale
    )

    means = ee.Image.constant(
        band_names.map(lambda b: ee.Number(mean_dict.get(ee.String(b))))
    ).toArray().toArray(1)

    centered = array_image_1d.toArray(1).subtract(means)

    pcs = (
        ee.Image(eigen_vectors)
        .matrixMultiply(centered)
        .arrayProject([0])
    )

    pc_names = ee.List.sequence(1, n_bands).map(
        lambda i: ee.String('PC').cat(ee.Number(i).int().format())
    )

    pcs = pcs.arrayFlatten([pc_names])
    return pcs

