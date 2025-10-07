import subprocess, base64
p = subprocess.run(['gh','api','repos/enyasystem/alx-project-nexus/contents/.github/workflows/integration.yml','--jq','.content'], capture_output=True, text=True)
content = p.stdout.strip().strip('"')
decoded = base64.b64decode(content.encode('utf-8')).decode('utf-8')
print(decoded)
\n
