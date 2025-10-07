import os
root='.'
missing=[]
for dirpath,dirnames,filenames in os.walk(root):
    if any(p in dirpath for p in ['.git','venv','\.pre-commit-cache','.cache','node_modules']):
        continue
    for f in filenames:
        if f.endswith(('.py','.md','.yml','.yaml','.txt','.rst','.ini','.cfg')):
            p=os.path.join(dirpath,f)
            try:
                with open(p,'rb') as fh:
                    data=fh.read()
                if len(data)>0 and not data.endswith(b'\n'):
                    missing.append(p)
            except Exception:
                pass
print('\n'.join(missing))
\n