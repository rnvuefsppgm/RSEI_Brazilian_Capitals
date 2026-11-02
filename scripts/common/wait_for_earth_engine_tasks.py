# -*- coding: utf-8 -*-
"""Wait until no Earth Engine export task whose description starts with 'trend_' is READY/RUNNING."""
import time, ee, os
ee.Initialize(project=os.environ.get('EE_PROJECT'))
while True:
    ts = [t for t in ee.batch.Task.list() if t.config.get('description', '').startswith('trend_')]
    active = [t for t in ts if t.state in ('READY', 'RUNNING')]
    done = [t for t in ts if t.state == 'COMPLETED']
    failed = [t for t in ts if t.state in ('FAILED', 'CANCELLED')]
    print(time.strftime('%H:%M'), 'active', len(active), 'completed', len(done), 'failed', len(failed), flush=True)
    if not active:
        for t in failed[:30]:
            print('FAILED', t.config.get('description'), t.status().get('error_message', '')[:200], flush=True)
        break
    time.sleep(120)
