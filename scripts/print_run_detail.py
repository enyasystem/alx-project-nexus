import json
import sys

path = '.gh_run_detail.json'
try:
    r = json.load(open(path))
except Exception as e:
    print('Error loading', path, e)
    sys.exit(2)

keys = ['id','run_number','status','conclusion','html_url','jobs_url','check_suite_url','logs_url','head_sha','path','created_at']
for k in keys:
    print(f"{k}: {r.get(k)}")

owner = r.get('actor') or r.get('triggering_actor')
if owner:
    print('actor_login:', owner.get('login'))
\n