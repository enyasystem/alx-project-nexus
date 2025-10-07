import sys
from pathlib import Path
import yaml

wf_dir = Path('.github/workflows')
if not wf_dir.exists():
    print('No workflows directory found')
    sys.exit(1)

errors = []
for p in sorted(wf_dir.glob('*.yml')):
    try:
        text = p.read_text(encoding='utf-8')
        # remove common accidental backtick markers
        cleaned = text
        # Try to load the YAML; allow multiple docs
        docs = list(yaml.safe_load_all(cleaned))
        print(f'OK: {p} -> {len(docs)} doc(s)')
    except Exception as e:
        errors.append((str(p), str(e)))

if errors:
    print('\nErrors:')
    for f, err in errors:
        print(f'{f}: {err}')
    sys.exit(2)
else:
    print('\nAll workflow files parsed successfully')
    sys.exit(0)
\n