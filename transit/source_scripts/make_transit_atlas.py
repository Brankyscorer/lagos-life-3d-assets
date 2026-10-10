# Lagos Life transit/venue sign atlas (2048x2048). All brands are invented for the game.
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import json, random, math
G='/usr/share/fonts/truetype/sand-box/google/'
def F(name,size): return ImageFont.truetype(G+name,size)
ANTON='Anton/Anton-Regular.ttf'; POP='Poppins/Poppins-Black.ttf'; POPB='Poppins/Poppins-Bold.ttf'; BEB='Bebas Neue/BebasNeue-Regular.ttf'
import os
if not os.path.exists(G+BEB): BEB=ANTON
W=2048; im=Image.new('RGB',(W,W),(40,40,40)); R={}
def grad(box,c0,c1,vertical=True):
    x0,y0,x1,y1=box; d=ImageDraw.Draw(im); n=(y1-y0) if vertical else (x1-x0)
    for i in range(n):
        t=i/max(1,n-1); c=tuple(int(c0[k]+(c1[k]-c0[k])*t) for k in range(3))
        if vertical: d.line([(x0,y0+i),(x1-1,y0+i)],fill=c)
        else: d.line([(x0+i,y0),(x0+i,y1-1)],fill=c)
NAIRA='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def text(xy,s,font,fill,anchor='la',shadow=None,stroke=0,stroke_fill=None):
    if '₦' in s and font.getbbox('₦')[2]-font.getbbox('₦')[0]>0 and not font.path.endswith(('Anton-Regular.ttf','DejaVuSans-Bold.ttf')):
        # Poppins/Bebas have no naira glyph: draw it with DejaVu, the rest with the main font
        nf=ImageFont.truetype(NAIRA,int(font.size*0.92)); parts=s.split('₦'); widths=[font.getlength(x) for x in parts]; nw=nf.getlength('₦')
        total=sum(widths)+nw*(len(parts)-1); x,y=xy
        if anchor[0]=='m': x-=total/2
        elif anchor[0]=='r': x-=total
        a='l'+anchor[1]
        for i,part in enumerate(parts):
            if part: text((x,y),part,font,fill,a,shadow,stroke,stroke_fill); x+=widths[i]
            if i<len(parts)-1: text((x,y),'₦',nf,fill,a,shadow); x+=nw
        return
    d=ImageDraw.Draw(im)
    if shadow: d.text((xy[0]+shadow[0],xy[1]+shadow[1]),s,font=font,fill=shadow[2],anchor=anchor)
    d.text(xy,s,font=font,fill=fill,anchor=anchor,stroke_width=stroke,stroke_fill=stroke_fill)
def fit(s,name,maxw,size):
    while size>8:
        f=F(name,size)
        if f.getlength(s)<=maxw: return f
        size-=2
    return F(name,size)
def reg(n,box): R[n]=list(box)
def weather(box,amt=18,seed=0):
    rnd=random.Random(seed); x0,y0,x1,y1=box; d=ImageDraw.Draw(im,'RGBA')
    for _ in range(int((x1-x0)*(y1-y0)/9000)):
        x=rnd.randint(x0,x1); y=rnd.randint(y0,y1); r=rnd.randint(4,40)
        d.ellipse([x-r,y-r,x+r,y+r],fill=(0,0,0,rnd.randint(1,max(2,amt//3))))
    for _ in range(12):   # rain streaks from the top
        x=rnd.randint(x0,x1); L=rnd.randint(20,(y1-y0)//2); d.line([(x,y0),(x,y0+L)],fill=(30,20,10,rnd.randint(8,26)),width=rnd.randint(2,6))
# ---------------------------------------------------------------- billboards 1024x512
def ad_malt(b):
    x0,y0,x1,y1=b; grad(b,(120,20,10),(40,6,4)); d=ImageDraw.Draw(im)
    for i in range(14): d.line([(x0+620+i*30,y0),(x0+520+i*30,y1)],fill=(150,40,15),width=6)
    # bottle
    bx=x0+800; d.rounded_rectangle([bx-70,y0+150,bx+70,y1-40],30,fill=(45,20,8)); d.rectangle([bx-28,y0+60,bx+28,y0+160],fill=(45,20,8))
    d.rectangle([bx-32,y0+46,bx+32,y0+70],fill=(220,180,60)); d.rounded_rectangle([bx-66,y0+250,bx+66,y0+380],10,fill=(230,190,60))
    text((bx,y0+315),'GOLDEN',F(ANTON,34),(120,20,10),'mm'); text((bx,y0+350),'MALT',F(POPB,22),(120,20,10),'mm')
    for k in range(18): d.ellipse([bx-50+k*6%100,y0+400+k*5%60,bx-44+k*6%100,y0+406+k*5%60],outline=(255,240,200))
    text((x0+50,y0+60),'CHOP LIFE',F(ANTON,120),(255,214,90),shadow=(6,6,(30,5,0)))
    text((x0+54,y0+200),'GOLDEN MALT',F(ANTON,70),(255,255,255),shadow=(4,4,(30,5,0)))
    text((x0+56,y0+300),'Cold one for the hustle.',F(POPB,34),(255,230,200))
    d.rounded_rectangle([x0+56,y0+380,x0+420,y0+450],14,fill=(255,214,90)); text((x0+238,y0+415),'₦350 ONLY',F(POP,36),(110,15,5),'mm')
def ad_net(b):
    x0,y0,x1,y1=b; grad(b,(10,30,90),(10,140,170),False); d=ImageDraw.Draw(im,'RGBA')
    for r in range(60,420,60): d.arc([x0+780-r,y0+256-r,x0+780+r,y0+256+r],200,340,fill=(255,255,255,120),width=10)
    d.ellipse([x0+760,y0+236,x0+800,y0+276],fill=(255,255,255))
    # phone
    d.rounded_rectangle([x0+690,y0+260,x0+870,y0+520],26,fill=(20,20,30)); d.rounded_rectangle([x0+702,y0+275,x0+858,y0+520],18,fill=(60,200,220))
    text((x0+50,y0+70),'ZAPNET',F(ANTON,130),(255,255,255),shadow=(5,5,(0,0,40,160)))
    text((x0+60,y0+215),'5G now on your street',F(POPB,44),(220,250,255))
    text((x0+60,y0+290),'10GB · ₦2,000',F(POP,62),(255,220,0),shadow=(3,3,(0,0,40,180)))
    text((x0+60,y0+400),'Dial *555# · zapnet.ng',F(POPB,30),(255,255,255))
def ad_seasoning(b):
    x0,y0,x1,y1=b; grad(b,(250,200,40),(240,120,20)); d=ImageDraw.Draw(im,'RGBA')
    d.ellipse([x0+600,y0+60,x0+1000,y0+460],fill=(255,255,255,70))
    # pot of stew
    d.ellipse([x0+640,y0+230,x0+960,y0+300],fill=(60,60,60)); d.rounded_rectangle([x0+650,y0+260,x0+950,y0+440],40,fill=(80,80,82))
    d.ellipse([x0+660,y0+232,x0+940,y0+292],fill=(190,40,20))
    for k in range(9): d.ellipse([x0+690+k*27,y0+245+(k%3)*10,x0+712+k*27,y0+262+(k%3)*10],fill=(230,90,30))
    # cube box
    d.polygon([(x0+520,y0+300),(x0+640,y0+270),(x0+640,y0+440),(x0+520,y0+470)],fill=(200,20,30)); text((x0+580,y0+370),'MAMA',F(ANTON,30),(255,230,0),'mm')
    text((x0+50,y0+50),"MAMA SISI",F(ANTON,110),(140,10,10),shadow=(4,4,(255,255,255,140)))
    text((x0+56,y0+180),'Seasoning cubes',F(POP,48),(80,10,5))
    text((x0+56,y0+260),'Sweet soup,',F(POPB,40),(255,255,255)); text((x0+56,y0+310),'every time.',F(POPB,40),(255,255,255))
    d.rounded_rectangle([x0+56,y0+390,x0+380,y0+455],12,fill=(140,10,10)); text((x0+218,y0+422),'₦50 / cube',F(POP,32),(255,230,0),'mm')
def ad_bank(b):
    x0,y0,x1,y1=b; grad(b,(240,244,248),(200,214,228)); d=ImageDraw.Draw(im,'RGBA')
    d.polygon([(x0+560,y0),(x1,y0),(x1,y1),(x0+700,y1)],fill=(0,110,70))
    d.polygon([(x0+600,y0),(x0+640,y0),(x0+780,y1),(x0+740,y1)],fill=(250,190,0))
    # person silhouette with phone
    d.ellipse([x0+800,y0+110,x0+880,y0+190],fill=(70,40,25)); d.rounded_rectangle([x0+770,y0+195,x0+910,y1],40,fill=(250,250,250))
    d.rounded_rectangle([x0+860,y0+240,x0+900,y0+310],8,fill=(20,20,20))
    text((x0+50,y0+60),'EKOPAY',F(ANTON,120),(0,90,60))
    text((x0+56,y0+200),'Send money in',F(POPB,46),(30,40,50)); text((x0+56,y0+256),'3 seconds.',F(POP,60),(0,110,70))
    text((x0+56,y0+360),'No queue. No wahala.',F(POPB,32),(30,40,50))
    text((x0+56,y0+420),'Licensed by the CBN (fictional)',F(POPB,18),(90,100,110))
for i,(fn,b) in enumerate([(ad_malt,(0,0,1024,512)),(ad_net,(1024,0,2048,512)),(ad_seasoning,(0,512,1024,1024)),(ad_bank,(1024,512,2048,1024))]):
    fn(b); weather(b,14,i); reg(f'ad_{i+1}',b)
# ---------------------------------------------------------------- wide signs 1024x192
def wide(b,bg0,bg1,title,sub,fc,font=ANTON,subc=None,deco=None,seed=0):
    x0,y0,x1,y1=b; grad(b,bg0,bg1); d=ImageDraw.Draw(im)
    if deco: deco(d,b)
    h=y1-y0; f=fit(title,font,(x1-x0)-80,int(h*0.62) if sub else int(h*0.8))
    text(((x0+x1)//2,y0+(h*0.42 if sub else h*0.52)),title,f,fc,'mm',shadow=(3,3,tuple(int(c*0.4) for c in bg1)))
    if sub: text(((x0+x1)//2,y0+h*0.82),sub,F(POPB,int(h*0.15)),subc or fc,'mm')
    d.rectangle([x0,y0,x1-1,y1-1],outline=tuple(int(c*0.5) for c in bg1),width=6); weather(b,10,seed)
def stars(d,b):
    x0,y0,x1,y1=b
    for k in range(10): d.ellipse([x0+40+k*100,y1-18,x0+52+k*100,y1-6],fill=(255,230,150))
wide((0,1024,1024,1216),(25,25,35),(10,10,15),'OPEBI GALLERIA','SHOPS · FOOD COURT · CINEMA',(255,255,255),POP,(240,190,60),stars,1); reg('mall_sign',(0,1024,1024,1216))
wide((1024,1024,2048,1216),(250,240,220),(235,215,170),"IYA BASIRA'S BUKA",'AMALA · EWEDU · JOLLOF · PEPPER SOUP',(150,25,15),ANTON,(40,80,30),None,2); reg('buka_sign',(1024,1024,2048,1216))
wide((0,1216,1024,1344),(20,90,50),(10,60,30),'OLUWOLE LANE MARKET',None,(255,240,180),ANTON,None,None,3); reg('market_sign',(0,1216,1024,1344))
# BRT livery band: white stripe with blue text, red underline
b=(1024,1216,2048,1344); x0,y0,x1,y1=b; grad(b,(245,245,245),(225,228,232)); d=ImageDraw.Draw(im)
d.rectangle([x0,y1-26,x1,y1],fill=(200,30,40)); text((x0+40,y0+50),'BRT',F(ANTON,80),(10,60,150),'lm'); text((x0+200,y0+50),'LAGOS LIFE TRANSIT · Ikorodu Rd – CMS',F(POPB,38),(10,60,150),'lm'); reg('brt_livery',b)
# ---------------------------------------------------------------- 512 x 256 panels
b=(0,1344,512,1600); x0,y0,x1,y1=b; grad(b,(10,70,160),(5,45,120)); d=ImageDraw.Draw(im)
d.rounded_rectangle([x0+24,y0+40,x0+150,y0+216],18,fill=(255,255,255)); 
d.rounded_rectangle([x0+44,y0+80,x0+130,y0+150],10,fill=(10,70,160)); d.ellipse([x0+52,y0+156,x0+74,y0+178],fill=(10,70,160)); d.ellipse([x0+100,y0+156,x0+122,y0+178],fill=(10,70,160))
text((x0+175,y0+95),'BUS STOP',F(ANTON,88),(255,255,255),'lm'); text((x0+178,y0+175),'Danfo · Keke · BRT',F(POPB,30),(255,215,60),'lm'); reg('stop_sign',b)
b=(512,1344,1024,1600); x0,y0,x1,y1=b; im.paste((235,238,240),b); d=ImageDraw.Draw(im)
text((x0+20,y0+28),'ROUTE MAP',F(ANTON,34),(10,60,150),'lm')
pts=[(x0+60,y0+200),(x0+170,y0+150),(x0+250,y0+180),(x0+330,y0+110),(x0+450,y0+90)]
d.line(pts,fill=(10,70,160),width=10); d.line([(x0+170,y0+150),(x0+200,y0+80),(x0+260,y0+60)],fill=(200,30,40),width=8)
for p,n in zip(pts,['Mushin','Surulere','Yaba','Island','CMS']):
    d.ellipse([p[0]-12,p[1]-12,p[0]+12,p[1]+12],fill=(255,255,255),outline=(10,70,160),width=5); text((p[0],p[1]+(30 if n!='Island' else -30)),n,F(POPB,20),(30,30,30),'mm')
d.rectangle([x0,y0,x1-1,y1-1],outline=(150,155,160),width=4); reg('stop_map',b)
b=(1024,1344,1536,1600); x0,y0,x1,y1=b; grad(b,(30,20,15),(15,10,8)); d=ImageDraw.Draw(im)
text((x0+256,y0+40),'SHAWARMA & SUYA',F(ANTON,46),(255,190,40),'mm')
for k,(n,p) in enumerate([('Chicken shawarma','₦3,500'),('Beef shawarma','₦3,800'),('Suya wrap','₦2,500'),('Chapman','₦1,500')]):
    y=y0+100+k*38; text((x0+40,y),n,F(POPB,26),(250,240,220),'lm'); text((x1-40,y),p,F(POP,26),(255,190,40),'rm')
reg('foodcourt_menu',b)
b=(1536,1344,1792,1472); x0,y0,x1,y1=b; im.paste((250,250,250),b); d=ImageDraw.Draw(im)
d.rounded_rectangle([x0+12,y0+24,x0+92,y0+104],18,fill=(20,150,90)); text((x0+52,y0+64),'G',F(POP,58),(255,255,255),'mm')
text((x0+104,y0+48),'Gidi',F(POP,40),(20,20,20),'lm'); text((x0+104,y0+92),'Ride',F(POP,40),(20,150,90),'lm'); reg('cab_logo',b)
b=(1792,1344,2048,1472); x0,y0,x1,y1=b; im.paste((12,12,12),b); d=ImageDraw.Draw(im)
text((x0+128,y0+64),'CMS – IKD',F(ANTON,60),(255,150,20),'mm'); reg('brt_dest',b)
b=(1536,1472,2048,1600); x0,y0,x1,y1=b; grad(b,(35,35,40),(15,15,18)); d=ImageDraw.Draw(im)
text((x0+256,y0+64),'HERBERT HUB',F(ANTON,72),(120,230,160),'mm'); weather(b,8,7); reg('hub_sign',b)
# ---------------------------------------------------------------- posters 256x384, fabrics 256x256
def poster(b,bg0,bg1,title,tag,seed):
    x0,y0,x1,y1=b; grad(b,bg0,bg1); d=ImageDraw.Draw(im,'RGBA'); rnd=random.Random(seed)
    for _ in range(5):
        cx=rnd.randint(x0+30,x1-30); cy=rnd.randint(y0+60,y0+250); r=rnd.randint(20,70); d.ellipse([cx-r,cy-r,cx+r,cy+r],fill=(255,255,255,40))
    d.ellipse([x0+88,y0+120,x0+168,y0+200],fill=(30,20,15)); d.rounded_rectangle([x0+60,y0+200,x0+196,y0+300],30,fill=(30,20,15))
    f=fit(title,ANTON,220,64); text(((x0+x1)//2,y0+50),title,f,(255,255,255),'mm',shadow=(2,2,(0,0,0,200)))
    text(((x0+x1)//2,y1-50),tag,F(POPB,18),(255,230,150),'mm'); text(((x0+x1)//2,y1-22),'IN CINEMAS NOW',F(POPB,14),(255,255,255),'mm')
poster((0,1600,256,1984),(160,30,20),(20,5,5),'OWAMBE','The party of the year',11); reg('poster_1',(0,1600,256,1984))
poster((256,1600,512,1984),(20,60,120),(5,10,30),'THIRD MAINLAND','Some bridges you cross once',12); reg('poster_2',(256,1600,512,1984))
def ankara(b,c0,c1,c2,seed):
    x0,y0,x1,y1=b; im.paste(c0,b); d=ImageDraw.Draw(im); rnd=random.Random(seed)
    for gy in range(4):
        for gx in range(4):
            cx=x0+32+gx*64; cy=y0+32+gy*64
            d.ellipse([cx-26,cy-26,cx+26,cy+26],fill=c1); d.ellipse([cx-14,cy-14,cx+14,cy+14],fill=c2)
            if seed%2: d.polygon([(cx,cy-30),(cx+8,cy),(cx,cy+30),(cx-8,cy)],fill=c0)
            d.ellipse([cx+26,cy+26,cx+38,cy+38],fill=c2)
for k,(c0,c1,c2) in enumerate([((20,60,140),(240,170,20),(200,30,40)),((150,20,60),(30,150,90),(250,220,60)),((240,120,20),(30,30,30),(250,250,240)),((20,110,90),(240,80,40),(250,210,90))]):
    b=(512+k*256,1600,768+k*256,1856); ankara(b,c0,c1,c2,k); reg(f'fabric_{k+1}',b)
b=(1536,1856,2048,1984); x0,y0,x1,y1=b; grad(b,(90,10,30),(40,5,15)); d=ImageDraw.Draw(im)
for k in range(16): d.ellipse([x0+16+k*31,y0+8,x0+26+k*31,y0+18],fill=(255,220,120)); d.ellipse([x0+16+k*31,y1-18,x0+26+k*31,y1-8],fill=(255,220,120))
text((x0+256,y0+66),'GALLERIA CINEMAS',F(ANTON,58),(255,235,180),'mm'); reg('cinema_sign',b)
b=(512,1856,1024,1984); x0,y0,x1,y1=b; im.paste((250,250,250),b); d=ImageDraw.Draw(im)
text((x0+256,y0+64),'TICKETS · ₦4,000',F(ANTON,62),(150,20,40),'mm'); reg('ticket_sign',b)
b=(1024,1856,1536,1984); x0,y0,x1,y1=b; grad(b,(250,210,60),(230,170,30)); d=ImageDraw.Draw(im)
text((x0+256,y0+64),'KEEP CALM · NO STRESS',F(ANTON,50),(30,30,30),'mm'); reg('danfo_sticker',b)
# headlight disc (radial)
b=(0,1984,64,2048); x0,y0,x1,y1=b; d=ImageDraw.Draw(im)
for r in range(32,0,-1): c=int(140+115*(1-r/32)); d.ellipse([x0+32-r,y0+32-r,x0+32+r,y0+32+r],fill=(c,c,min(255,c+10)))
reg('headlight',b)
b=(64,1984,128,2048); x0,y0,x1,y1=b; grad(b,(200,20,15),(120,5,5)); reg('taillight',b)
b=(128,1984,256,2048); x0,y0,x1,y1=b; im.paste((235,235,225),b); d=ImageDraw.Draw(im); text((x0+64,y0+32),'LAG 247 KJA',F(POPB,14),(10,40,120),'mm'); reg('plate',b)
b=(256,1984,512,2048); x0,y0,x1,y1=b; grad(b,(20,20,22),(60,60,64),False); reg('grille',b)
im.save('/workspace/env/tex/transit_atlas.jpg',quality=90)
json.dump(R,open('/workspace/env/tex/transit_rects.json','w'),indent=0)
print(len(R),'regions')
