# -*- coding: utf-8 -*-
"""
sanitize_notebooks.py  (RNV, 2026)
Prepares the original Google Colab notebooks and scripts for public release:
  * removes all cell outputs and execution counts;
  * removes notebook/cell metadata that identifies accounts or sessions
    (Colab 'authorship_tag', user ids, display names, provenance, executionInfo);
  * replaces hard-coded Earth Engine project ids in ee.Initialize(...) by an
    environment-variable lookup (EE_PROJECT) so that users authenticate with
    their own credentials;
  * removes personal Google Drive paths and Colab URLs from docstrings;
  * flags, without altering the scientific logic, any remaining string that
    looks like a secret (token, key, password) so the file is NOT published.
Usage: python sanitize_notebooks.py <src_dir> <dst_dir>
"""
import sys
import os
import re
import json

SRC, DST = sys.argv[1], sys.argv[2]
os.makedirs(DST, exist_ok=True)
SECRET = re.compile(r'(AIza[0-9A-Za-z\-_]{20,}|ya29\.[0-9A-Za-z\-_]+|ghp_[0-9A-Za-z]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY|"private_key"|token\s*=\s*["\'][^"\']{12,}|password\s*=\s*["\']|api[_-]?key\s*=\s*["\'][^"\']{8,})', re.I)
EE_INIT = re.compile(r"ee\.Initialize\(\s*project\s*=\s*['\"][^'\"]+['\"]\s*\)")
EE_INIT_PLAIN = re.compile(r"ee\.Initialize\(\s*\)")
DRIVE_PATH = re.compile(r"/content/drive/MyDrive/[^\s'\"]*")
COLAB_URL = re.compile(r"https://colab\.research\.google\.com/drive/[0-9A-Za-z\-_]+")
HEADER = ("# Authentication: run `earthengine authenticate` once and set the environment\n"
          "# variable EE_PROJECT to your own Google Cloud project before executing.\n"
          "import os\n")


def clean_source(src):
    src = EE_INIT.sub("ee.Initialize(project=os.environ.get('EE_PROJECT'))", src)
    src = EE_INIT_PLAIN.sub("ee.Initialize(project=os.environ.get('EE_PROJECT'))", src)
    src = DRIVE_PATH.sub("<YOUR_DRIVE_PATH>", src)
    src = COLAB_URL.sub("<colab-notebook-url-removed>", src)
    if 'ee.Initialize' in src and 'import os' not in src:
        src = HEADER + src
    return src


report = []
for name in sorted(os.listdir(SRC)):
    p = os.path.join(SRC, name)
    if name.endswith('.ipynb'):
        nb = json.load(open(p, encoding='utf-8'))
        nb['metadata'] = {k: v for k, v in nb.get('metadata', {}).items() if k in ('kernelspec', 'language_info')}
        nb['metadata'].setdefault('kernelspec', {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'})
        nb['metadata'].setdefault('language_info', {'name': 'python'})
        for c in nb.get('cells', []):
            c['metadata'] = {}
            if c.get('cell_type') == 'code':
                c['outputs'] = []
                c['execution_count'] = None
                c['source'] = clean_source(''.join(c.get('source', []))).splitlines(keepends=True)
        text = json.dumps(nb, ensure_ascii=False, indent=1)
    elif name.endswith('.py'):
        text = clean_source(open(p, encoding='utf-8').read())
    else:
        continue
    hits = SECRET.findall(text)
    if hits:
        report.append((name, 'BLOCKED: possible secret', hits[:3]))
        continue
    open(os.path.join(DST, name), 'w', encoding='utf-8').write(text)
    report.append((name, 'sanitized', []))
for r in report:
    print(r)
