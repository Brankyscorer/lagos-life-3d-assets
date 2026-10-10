import json, urllib.request, os, sys
H={'User-Agent':'lagos-work-kit/1.0 (asset build script)'}
def get(u): return urllib.request.urlopen(urllib.request.Request(u,headers=H)).read()
os.chdir('/workspace/workkit/src/ph')
for t in sys.argv[1].split(','):
    f = json.loads(get(f'https://api.polyhaven.com/files/{t}'))
    info = json.loads(get(f'https://api.polyhaven.com/info/{t}'))
    os.makedirs(t, exist_ok=True)
    json.dump({'id':t,'name':info.get('name'),'authors':info.get('authors'),'dimensions':info.get('dimensions'),'url':f'https://polyhaven.com/a/{t}','license':'CC0'},open(f'{t}/info.json','w'))
    for key, name in [('Diffuse','diff'),('nor_gl','nor'),('arm','arm')]:
        if key not in f: print('missing',t,key); continue
        u = f[key]['1k']['jpg']['url']
        open(f'{t}/{name}.jpg','wb').write(get(u))
    print('ok', t, info.get('dimensions'))
