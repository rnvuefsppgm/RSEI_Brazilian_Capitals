# -*- coding: utf-8 -*-
"""
F2 - Figure packaging. New for Review (2026).
(a) For figures that could not be regenerated from code (Figure 2, study area,
    produced in QGIS), writes a PNG with 600 dpi metadata (pixel content unchanged)
    and an SVG wrapper embedding the raster (vector container; the raster content
    itself is not editable).
(b) Copies the regenerated figures (Figures 1 and 3-6) into the PNG_600dpi and
    SVG_Editable folders.
Usage: python F2_export_figures_png600_svg.py <original_dir> <work_dir> <png_dir> <svg_dir>
"""
import sys
import os
import base64
import shutil
from PIL import Image

orig, work, png_dir, svg_dir = sys.argv[1:5]
os.makedirs(png_dir, exist_ok=True)
os.makedirs(svg_dir, exist_ok=True)
Image.MAX_IMAGE_PIXELS = None

for name in ['Figure_2']:
    src = os.path.join(orig, name + '.png')
    im = Image.open(src)
    w, h = im.size
    im.save(os.path.join(png_dir, name + '.png'), dpi=(600, 600))
    b64 = base64.b64encode(open(src, 'rb').read()).decode()
    svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" '
           f'xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" viewBox="0 0 {w} {h}">\n'
           f'<title>{name}</title>\n<image width="{w}" height="{h}" xlink:href="data:image/png;base64,{b64}"/>\n</svg>\n')
    open(os.path.join(svg_dir, name + '.svg'), 'w', encoding='utf-8').write(svg)
    print(name, 'wrapped', w, h)

for name in ['Figure_1', 'Figure_3', 'Figure_4', 'Figure_5', 'Figure_6']:
    for ext, dst in (('.png', png_dir), ('.svg', svg_dir)):
        p = os.path.join(work, name + ext)
        if os.path.exists(p):
            shutil.copy(p, os.path.join(dst, name + ext))
            print(name + ext, 'copied')
print('done')
