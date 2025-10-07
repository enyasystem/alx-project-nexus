import json
import sys

path = '.gh_workflow_runs.json'
try:
    j = json.load(open(path))
except Exception as e:
    print('Error loading', path, e)
    sys.exit(2)

runs = j.get('workflow_runs', [])
if not runs:
    print('No runs found in', path)
    sys.exit(0)

for r in runs[:10]:
    print(f"id={r.get('id')}	run_number={r.get('run_number')}	head_sha={r.get('head_sha')}	status={r.get('status')}	conclusion={r.get('conclusion')}	event={r.get('event')}	created_at={r.get('created_at')}")
\n
