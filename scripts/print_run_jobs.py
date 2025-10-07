import json
import sys

path = '.gh_run_jobs.json'
try:
    j = json.load(open(path))
except Exception as e:
    print('Error loading', path, e)
    sys.exit(2)

for job in j.get('jobs', []):
    name = job.get('name')
    status = job.get('status')
    conclusion = job.get('conclusion')
    started = job.get('started_at')
    completed = job.get('completed_at')
    print(f"{name}\t{status}\t{conclusion}\tstarted:{started}\tcompleted:{completed}")
\n
