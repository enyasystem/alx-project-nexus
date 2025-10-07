import json
p=json.load(open('main_protection_backup.json','r',encoding='utf8'))
if 'required_pull_request_reviews' not in p:
    p['required_pull_request_reviews']={}
p['required_pull_request_reviews']['required_approving_review_count']=0
json.dump(p, open('main_protection_patch.json','w',encoding='utf8'))
print('Wrote main_protection_patch.json')
\n
