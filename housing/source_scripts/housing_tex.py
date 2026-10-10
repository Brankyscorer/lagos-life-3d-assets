# Lagos Life housing kit textures (Step 07): tiled CC0 Poly Haven sets resized + colour-normalised.
import json, os, numpy as np
from PIL import Image
S='/workspace/workkit/src/ph'; O='/workspace/workkit/tex'
def lum(a): return 0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
def norm(img,target,sat=1.0,tint=None):
    a=np.asarray(img).astype(np.float32)/255; g=lum(a)[...,None]; m=np.median(g)
    a=g+(a-g)*sat; a=a*(target/max(m,1e-3))
    if tint is not None: a=a*np.array(tint,np.float32)
    return Image.fromarray((np.clip(a,0,1)*255).astype(np.uint8))
meta=json.load(open(f'{O}/tex_meta.json'))
def std(name,t,res,tile,cf=None,diff='diff',rough=None):
    c=Image.open(f'{S}/{t}/{diff}.jpg').convert('RGB'); n=Image.open(f'{S}/{t}/nor.jpg').convert('RGB'); o=Image.open(f'{S}/{t}/arm.jpg').convert('RGB')
    if cf: c=cf(c)
    if rough is not None:
        a=np.asarray(o).astype(np.float32); a[...,1]=a[...,1]*rough; o=Image.fromarray(a.clip(0,255).astype(np.uint8))
    c.resize((res,res),Image.LANCZOS).save(f'{O}/{name}_c.jpg',quality=84,optimize=True)
    n.resize((512,512),Image.LANCZOS).save(f'{O}/{name}_n.jpg',quality=84,optimize=True)
    o.resize((512,512),Image.LANCZOS).save(f'{O}/{name}_orm.jpg',quality=84,optimize=True)
    meta[name]={'tile_m':tile,'res':res,'src':[t]}
std('hk_marble','marble_01',1024,2.4,lambda c:norm(c,0.82,0.55,(1.0,0.99,0.97)),rough=0.35)
std('hk_porcelain','granite_tile_03',1024,1.8,lambda c:norm(c,0.68,0.15,(0.98,0.99,1.0)),rough=0.55)
std('hk_laminate','laminate_floor_02',1024,1.7,lambda c:norm(c,0.55,0.95))
std('hk_bathtile','long_white_tiles',1024,1.27,lambda c:norm(c,0.86,0.5))
std('hk_leather','brown_leather',512,0.6,lambda c:norm(c,0.22,0.9))
std('hk_check','fabric_pattern_07',512,0.5,diff='col_02')
json.dump(meta,open(f'{O}/tex_meta.json','w'),indent=1)
print('ok',[k for k in meta if k.startswith('hk_')])
# own-work art textures (CC0): Aso-oke stripe rug and an Adire (indigo resist) canvas, plus a small print
from PIL import ImageDraw, ImageFilter
import random
rnd=random.Random(7)
W=512; im=Image.new('RGB',(W,W),(120,30,40)); d=ImageDraw.Draw(im)
cols=[(150,32,38),(214,160,60),(28,60,40),(235,220,190),(40,32,30)]
y=0
while y<W:
    h=rnd.choice([6,10,16,28]); d.rectangle([0,y,W,y+h],fill=rnd.choice(cols)); y+=h
for x in range(0,W,64):
    for yy in range(0,W,32):
        if (x//64+yy//32)%2==0: d.rectangle([x+20,yy+8,x+44,yy+24],fill=(214,160,60))
a=np.asarray(im).astype(np.float32); n=np.random.default_rng(3).normal(0,9,(W,W,1)); a=np.clip(a+n,0,255)
for i in range(0,W,2): a[:,i]*=0.93
Image.fromarray(a.astype(np.uint8)).save(f'{O}/hk_rug_c.jpg',quality=86)
meta['hk_rug']={'tile_m':1.0,'res':512,'src':['own work']}
im=Image.new('RGB',(W,W),(28,40,92)); d=ImageDraw.Draw(im)
for gx in range(4):
    for gy in range(4):
        cx=gx*128+64; cy=gy*128+64
        for r in range(54,4,-12): d.ellipse([cx-r,cy-r,cx+r,cy+r],outline=(205,215,232),width=3)
        d.line([gx*128,cy,gx*128+128,cy],fill=(170,185,215),width=2); d.line([cx,gy*128,cx,gy*128+128],fill=(170,185,215),width=2)
im=im.filter(ImageFilter.GaussianBlur(0.8)); a=np.asarray(im).astype(np.float32)*(0.92+0.08*np.random.default_rng(5).random((W,W,1)))
Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save(f'{O}/hk_adire_c.jpg',quality=86)
meta['hk_adire']={'tile_m':1.0,'res':512,'src':['own work']}
im=Image.new('RGB',(256,256),(232,224,205)); d=ImageDraw.Draw(im)
d.rectangle([0,150,256,256],fill=(40,110,120)); d.ellipse([150,40,210,100],fill=(230,150,60))
for i in range(5): d.polygon([(20+i*45,150),(45+i*45,95-i*6),(70+i*45,150)],fill=(30,70,50))
im.save(f'{O}/hk_print_c.jpg',quality=86); meta['hk_print']={'tile_m':1.0,'res':256,'src':['own work']}
json.dump(meta,open(f'{O}/tex_meta.json','w'),indent=1)
print('art ok')
