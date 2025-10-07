import sys, yaml

p = '.github/workflows/ci.yml'
with open(p,'r',encoding='utf-8') as f:
    try:
        yaml.safe_load(f)
        print('YAML parsed OK')
    except Exception as e:
        print('YAML parse error:',e)
        sys.exit(1)
\n
