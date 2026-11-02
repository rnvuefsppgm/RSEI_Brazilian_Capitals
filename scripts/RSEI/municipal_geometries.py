# -*- coding: utf-8 -*-
"""
municipal_geometries.py  (New for Review, 2026)
Official municipal boundaries of the 27 Brazilian state capitals (IBGE municipal
mesh, shapefile 'Capitais.shp' used in the original QGIS cartography) exposed as
Earth Engine geometries and as a GeoDataFrame. The Earth Engine processing
polygons (asset CAP_JOIN2) are considerably larger than the municipalities; all
municipal statistics reported in the revised manuscript are computed after
clipping the products to these official boundaries.
Set the environment variable CAPITAIS_SHP to the shapefile path if it is not in
the default location (data/Capitais.shp relative to this file).
"""
import os
import json
import geopandas as gpd
import ee

DEFAULT = os.environ.get('CAPITAIS_SHP', os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                      '..', 'data', 'Capitais.shp'))


def load_gdf(path=DEFAULT):
    g = gpd.read_file(path)
    return g.to_crs(4326)


def ee_geometries(path=DEFAULT):
    """dict NM_MUN -> ee.Geometry (WGS84, geodesic=False)."""
    g = load_gdf(path)
    out = {}
    for _, r in g.iterrows():
        gj = json.loads(gpd.GeoSeries([r.geometry]).to_json())['features'][0]['geometry']
        out[r['NM_MUN']] = ee.Geometry(gj, 'EPSG:4326', False)
    return out
