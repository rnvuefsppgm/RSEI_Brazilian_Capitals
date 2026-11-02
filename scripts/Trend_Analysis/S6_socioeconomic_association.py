# -*- coding: utf-8 -*-
"""
S6 - Exploratory association between RSEI trend classes and demographic indicators.
New for Review (2026). Downloads official population counts of the 27 state
capitals from IBGE/SIDRA (Censuses 1991, 2000, 2010 and 2022; table 200, 1378 and 4709)
and the municipal territorial area (table 4714), and computes Spearman rank
correlations between the share of the municipal area with significant RSEI
degradation/improvement (Table 1) and (i) population density in 2022,
(ii) absolute and relative population growth 1991-2022.
Inputs: table1_recomputed or table1 CSV (column names: municipio, degradation_pct, improvement_pct).
Outputs: out_S6_socioeconomic.csv, out_S6_spearman.csv
"""
import sys
import csv
import json
import urllib.request
import numpy as np
from scipy.stats import spearmanr

CODES = {'Rio Branco': 1200401, 'Maceió': 2704302, 'Macapá': 1600303, 'Manaus': 1302603, 'Salvador': 2927408,
         'Fortaleza': 2304400, 'Brasília': 5300108, 'Vitória': 3205309, 'Goiânia': 5208707, 'São Luís': 2111300,
         'Cuiabá': 5103403, 'Campo Grande': 5002704, 'Belo Horizonte': 3106200, 'Belém': 1501402,
         'João Pessoa': 2507507, 'Curitiba': 4106902, 'Recife': 2611606, 'Teresina': 2211001,
         'Rio de Janeiro': 3304557, 'Natal': 2408102, 'Porto Alegre': 4314902, 'Porto Velho': 1100205,
         'Boa Vista': 1400100, 'Florianópolis': 4205407, 'São Paulo': 3550308, 'Aracaju': 2800308, 'Palmas': 1721000}
ids = ",".join(map(str, CODES.values()))


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    return json.load(urllib.request.urlopen(req, timeout=90))


def sidra(table, extra=''):
    out = {}
    for r in get(f"https://apisidra.ibge.gov.br/values/t/{table}/n6/{ids}/v/93/p/all{extra}")[1:]:
        try:
            out[(int(r['D1C']), int(r['D3N']))] = float(r['V'])
        except (ValueError, KeyError):
            pass
    return out


pop = {}
pop.update(sidra(200, '/c2/0/c1/0/c58/0'))   # 1991, 2000 censuses
try:
    pop.update(sidra(1378, '/c2/0/c1/0/c58/0'))  # 2010 census
except Exception as e:
    print('2010 (t1378) unavailable:', str(e)[:80])
pop.update(sidra(4709))                      # 2022 census
area = {}
for r in get(f"https://apisidra.ibge.gov.br/values/t/4714/n6/{ids}/v/6318/p/all")[1:]:
    area[int(r['D1C'])] = float(r['V'])

table1 = sys.argv[1] if len(sys.argv) > 1 else 'out_S5_table1_recomputed.csv'
t1 = {}
with open(table1, encoding='utf-8') as fh:
    for r in csv.DictReader(fh):
        t1[r['municipio'].strip()] = r

rows = []
for city, code in CODES.items():
    p91, p00, p10, p22 = pop.get((code, 1991)), pop.get((code, 2000)), pop.get((code, 2010)), pop.get((code, 2022))
    a = area.get(code)
    r = t1.get(city, {})
    rows.append({'municipio': city, 'ibge_code': code, 'area_km2_ibge': a, 'pop_1991': p91, 'pop_2000': p00,
                 'pop_2010': p10, 'pop_2022': p22,
                 'density_2022_hab_km2': (p22 / a) if (p22 and a) else None,
                 'growth_1991_2022_pct': (100 * (p22 - p91) / p91) if (p22 and p91) else None,
                 'degradation_pct': float(r['degradation_pct']) if r else None,
                 'improvement_pct': float(r['improvement_pct']) if r else None})
with open('out_S6_socioeconomic.csv', 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

res = []
for y in ['degradation_pct', 'improvement_pct']:
    for x in ['density_2022_hab_km2', 'growth_1991_2022_pct', 'pop_2022']:
        xs = np.array([r[x] for r in rows if r[x] is not None and r[y] is not None], float)
        ys = np.array([r[y] for r in rows if r[x] is not None and r[y] is not None], float)
        rho, p = spearmanr(xs, ys)
        res.append({'response': y, 'predictor': x, 'n': len(xs), 'spearman_rho': rho, 'p_value': p})
        print(f"{y} ~ {x}: n={len(xs)} rho={rho:.3f} p={p:.3f}")
with open('out_S6_spearman.csv', 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=list(res[0].keys())); w.writeheader(); w.writerows(res)
print('done')
