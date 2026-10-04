"""Actual sysconfig console Unicode valid/error JSON; preserve before failures."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

p = argparse.ArgumentParser()
p.add_argument('--out', type=Path, required=True)
p.add_argument('--assert-success', action='store_true')
a = p.parse_args()
out = a.out.resolve()
out.mkdir(parents=True, exist_ok=False)
console = Path(json.loads(subprocess.check_output([sys.executable, '-I', '-c', "import sysconfig,json; print(json.dumps(sysconfig.get_path('scripts'),ensure_ascii=True))"]))) / ('splitleak.exe' if os.name == 'nt' else 'splitleak')
records = []
for mode in ('native', 'utf8-off', 'utf8-on', 'cp936', 'cp1252'):
    env = os.environ.copy()
    for key in ('PYTHONUTF8', 'PYTHONIOENCODING'):
        env.pop(key, None)
    if mode.startswith('utf8-'):
        env['PYTHONUTF8'] = '1' if mode == 'utf8-on' else '0'
    elif mode.startswith('cp'):
        env['PYTHONIOENCODING'] = mode
    encoding = json.loads(subprocess.check_output([sys.executable, '-c', "import sys,json; print(json.dumps(sys.stdout.encoding))"], env=env))
    for case in ('valid', 'invalid'):
        document = {'samples': [{'id': 'A\U0001f642', 'split': 'train', 'content': '\u4e2d\u6587 Stra\u00dfe'}]}
        if case == 'invalid':
            document['samples'][0]['start'] = 1
        source = out / (mode + '-' + case + '.json')
        source.write_text(json.dumps(document, ensure_ascii=False), encoding='utf-8')
        before = hashlib.sha256(source.read_bytes()).hexdigest()
        r = subprocess.run([str(console), 'audit', str(source)], capture_output=True, env=env)
        (out / (mode + '-' + case + '-private.stdout')).write_bytes(r.stdout)
        (out / (mode + '-' + case + '-private.stderr')).write_bytes(r.stderr)
        try:
            value = json.loads((r.stdout if case == 'valid' else r.stderr).decode('utf-8'))
            json_ok = 'sample_count' in value if case == 'valid' else 'error' in value
        except (UnicodeError, ValueError):
            json_ok = False
        record = {'mode': mode, 'native_encoding': encoding, 'case': case, 'exit': r.returncode,
                  'expected_exit': 0 if case == 'valid' else 2, 'utf8_json': json_ok,
                  'source_unchanged': before == hashlib.sha256(source.read_bytes()).hexdigest()}
        records.append(record)
(out / 'result.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
print(json.dumps(records))
if a.assert_success:
    assert all(r['exit'] == r['expected_exit'] and r['utf8_json'] and r['source_unchanged'] for r in records)
