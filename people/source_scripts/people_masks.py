# Lagos Life people kit: per-part recolour masks (R = skin, G = fabric) at 256 px PNG, and the base skin
# statistics the runtime shader needs to retone skin while keeping the painted detail (pores, shading, lips).
import json, glob, sys
from PIL import Image, ImageFilter
import numpy as np
AV=dict(m12='Male_Adult_12',m04='Male_Adult_04',mbm05='Business_Male_05',m17='Male_Adult_17',m19='Male_Adult_19',m08='Male_Adult_08',
        m14='Male_Adult_14',msp03='Sports_Male_03',fp02='Female_Party_02',fbf01='Business_Female_01',f11='Female_Adult_11',f03='Female_Adult_03',
        f08='Female_Adult_08',f12='Female_Adult_12',f15='Female_Adult_15',fmed01='Medical_Female_01')
OUT=sys.argv[1]
lumw=np.array([0.299,0.587,0.114])
def sat(a): mx=a.max(-1); mn=a.min(-1); return (mx-mn)/(mx+1e-6)
def skin(a):
    r,g,b=a[...,0],a[...,1],a[...,2]; mx=a.max(-1); s=sat(a); gr=g/(r+1e-6)
    return np.clip((s-0.07)/0.08,0,1)*np.clip((mx-0.3)/0.15,0,1)*(r>=g)*np.clip((gr-0.32)/0.1,0,1)*(g>=b*0.8)
def soft(x,a,b): return np.clip((x-a)/(b-a),0,1)
# fabric predicates per body (garment that takes prints / colourways)
def fab(pid,a):
    r,g,b=a[...,0],a[...,1],a[...,2]; L=a@lumw; s=sat(a)
    if pid in ('m19','fmed01'): return soft(L,0.42,0.55)*(1-soft(s,0.12,0.2))
    if pid=='m08': return soft(b-r,0.06,0.12)*soft(L,0.36,0.46)
    if pid=='f15': return soft(b-r,0.05,0.1)*soft(L,0.16,0.24)
    if pid=='m17': return soft(b-r,0.12,0.2)
    if pid=='f08':
        # the tee is the grey centre column of the atlas (top 75%); denim legs sit either side and the watch below/right
        m=soft(L,0.15,0.25)*(1-soft(s,0.2,0.3)); x=np.arange(256)/256; y=x[:,None]
        return m*(soft(x,0.33,0.345)*(1-soft(x,0.645,0.66)))[None,:]*(1-soft(y,0.745,0.76))
    if pid=='f03': return soft(np.minimum(r-g,b-g),0.12,0.2)
    if pid=='f11': return (1-soft(L,0.22,0.3))*soft(r-b,0.03,0.06)
    return None
def png(m,path):
    Image.fromarray(np.clip(m*255+0.5,0,255).astype(np.uint8),'RGB').save(path,optimize=True)
man={}
for pid,av in AV.items():
    ent={}
    for part in ('head','body'):
        f=glob.glob(f'/workspace/rb/tex/{av}/512/*_{part}_color.jpg')[0]
        a=np.asarray(Image.open(f).convert('RGB').resize((256,256),Image.LANCZOS)).astype(np.float32)/255
        sk=skin(a); fb=fab(pid,a) if part=='body' else None
        if part=='head': sk[int(256*0.78):,:int(256*0.32)]=0   # eyeballs, teeth, tongue live in this corner of the head atlas
        if fb is None: fb=np.zeros_like(sk)
        fb=fb*(1-sk)
        blur=lambda m: np.asarray(Image.fromarray((m*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0))).astype(np.float32)/255
        sk=blur(sk); fb=blur(np.asarray(Image.fromarray((fb*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))).astype(np.float32)/255)
        m=np.stack([sk,fb,np.zeros_like(sk)],-1)
        png(m,f'{OUT}/masks/{pid}_{part}.png')
        sel=a[sk>0.9] if (sk>0.9).sum()>50 else a[sk>0.5]
        Cm=sel.mean(0); Lm=float(Cm@lumw)
        e={'skin':[round(float(x),4) for x in Cm],'skinL':round(Lm,4),'skinFrac':round(float((sk>0.5).mean()),3)}
        if fb.max()>0.5:
            fsel=a[fb>0.8]; e['fabL']=round(float((fsel@lumw).mean()),4); e['fabFrac']=round(float((fb>0.5).mean()),3)
        ent[part]=e
    man[pid]=ent
    print(pid, ent)
json.dump(man,open(f'{OUT}/masks/stats.json','w'),indent=1)
