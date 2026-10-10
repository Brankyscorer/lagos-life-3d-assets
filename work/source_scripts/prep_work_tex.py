# Work-scene textures: tiled CC0 Poly Haven sets + one 2048 sign/screen atlas drawn here (own work, CC0).
# All brands are fictional (KoboPay, PalmTrust, SwiftDrop, Kings Cut, Iya Basira, Palm Grove Estate).
import json, os, math, random, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S='/workspace/workkit/src/ph'; O='/workspace/workkit/tex'; os.makedirs(O,exist_ok=True)
G='/usr/share/fonts/truetype/sand-box/google'
def F(path,size,wght=None):
    f=ImageFont.truetype(f'{G}/{path}',size)
    if wght is not None:
        try: f.set_variation_by_axes([wght])
        except Exception: pass
    return f
MONT='Montserrat/Montserrat-VariableFont_wght.ttf'; OSW='Oswald/Oswald-VariableFont_wght.ttf'
def lum(a): return 0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
def load(t,m): return Image.open(f'{S}/{t}/{m}.jpg').convert('RGB')
def norm_bright(img,target=0.8,keep_sat=1.0,tint=None):
    a=np.asarray(img).astype(np.float32)/255; g=lum(a)[...,None]; m=np.median(g)
    a=g+(a-g)*keep_sat; a=a*(target/max(m,1e-3))
    if tint is not None: a=a*np.array(tint,np.float32)
    return Image.fromarray((np.clip(a,0,1)*255).astype(np.uint8))
meta={}
def std(name,t,res,tile,cf=None,q=84):
    c=load(t,'diff'); n=load(t,'nor'); o=load(t,'arm')
    if cf: c=cf(c)
    c.resize((res,res),Image.LANCZOS).save(f'{O}/{name}_c.jpg',quality=q,optimize=True)
    n.resize((512,512),Image.LANCZOS).save(f'{O}/{name}_n.jpg',quality=q,optimize=True)
    o.resize((512,512),Image.LANCZOS).save(f'{O}/{name}_orm.jpg',quality=q,optimize=True)
    meta[name]={'tile_m':tile,'res':res,'src':[t]}
std('tile_floor','interior_tiles',1024,1.9,lambda c:norm_bright(c,0.78,0.6))
std('terrazzo','terrazzo_tiles',1024,2.0,lambda c:norm_bright(c,0.70,0.8))
std('worn_tile','worn_tile_floor',1024,2.0,lambda c:norm_bright(c,0.62,0.7))
std('hessian','hessian_230',512,0.6,lambda c:norm_bright(c,0.55,0.9))
std('linen','rough_linen',512,0.6,lambda c:norm_bright(c,0.86,0.0))
std('wood_floor','wood_floor_worn',1024,2.0,lambda c:norm_bright(c,0.42,0.9))
json.dump(meta,open(f'{O}/tex_meta.json','w'),indent=1)

# ------------------------------------------------------------------ atlas
N=2048; A=Image.new('RGB',(N,N),(128,128,128)); D=ImageDraw.Draw(A); R={}
rnd=random.Random(11)
def region(name,x,y,w,h): R[name]=[x,y,x+w,y+h]; return (x,y,w,h)
def ctext(d,box,txt,font,fill,dy=0):
    x,y,w,h=box; b=d.textbbox((0,0),txt,font=font); tw=b[2]-b[0]; th=b[3]-b[1]
    d.text((x+(w-tw)/2-b[0],y+(h-th)/2-b[1]+dy),txt,font=font,fill=fill)
def fit(txt,path,maxw,start):
    s=start
    while s>8:
        f=F(path,s); b=f.getbbox(txt)
        if b[2]-b[0]<=maxw: return f
        s-=2
    return F(path,8)
def weather(box,amt=0.08,seed=0):
    x,y,w,h=box; tile=A.crop((x,y,x+w,y+h)); a=np.asarray(tile).astype(np.float32)/255
    rs=np.random.RandomState(seed); g=rs.rand(h//96+2,w//96+2).astype(np.float32)
    nz=np.asarray(Image.fromarray((g*255).astype(np.uint8)).resize((w,h),Image.BICUBIC)).astype(np.float32)/255
    grain=rs.rand(h,w).astype(np.float32)
    a=a*(1-amt*0.6*(nz[...,None]-0.5)*2)*(1-amt*0.25*(grain[...,None]-0.5))
    A.paste(Image.fromarray((np.clip(a,0,1)*255).astype(np.uint8)),(x,y))
def rr(d,box,r,fill,outline=None,width=1):
    x,y,w,h=box; d.rounded_rectangle([x,y,x+w-1,y+h-1],r,fill=fill,outline=outline,width=width)

BEB='Bebas Neue/BebasNeue-Regular.ttf'; POP='Poppins/Poppins-Bold.ttf'; POPS='Poppins/Poppins-SemiBold.ttf'; POPR='Poppins/Poppins-Regular.ttf'
ANT='Anton/Anton-Regular.ttf'; CAV='Caveat/Caveat-VariableFont_wght.ttf'; KAL='Kalam/Kalam-Regular.ttf'; MONO='JetBrains Mono/JetBrainsMono-VariableFont_wght.ttf'
LIL='Lilita One/LilitaOne-Regular.ttf'; ALFA='Alfa Slab One/AlfaSlabOne-Regular.ttf'; MARK='Permanent Marker/PermanentMarker-Regular.ttf'

# --- POS A-frame board (512x768)
b=region('pos_aframe',0,0,512,768); x,y,w,h=b
D.rectangle([x,y,x+w,y+h],fill=(0,92,170)); D.rectangle([x,y+170,x+w,y+h],fill=(250,250,246))
ctext(D,(x,y+6,w,120),'POS',F(ANT,128),(255,214,0)); ctext(D,(x,y+118,w,50),'KoboPay  Agent',F(POPS,34),(255,255,255))
items=['CASH WITHDRAWAL','TRANSFER','DEPOSIT','AIRTIME & DATA','BILLS · DSTV · NEPA']
for i,t in enumerate(items):
    yy=y+200+i*86; D.rectangle([x+28,yy,x+w-28,yy+70],fill=(0,92,170) if i%2==0 else (226,40,40))
    ctext(D,(x+28,yy,w-56,70),t,fit(t,POP,w-90,40),(255,255,255))
ctext(D,(x,y+640,w,60),'Fast · Safe · No wahala',F(KAL,40),(20,40,70)); ctext(D,(x,y+700,w,50),'0803 ••• 4417',F(POPS,30),(20,40,70))
weather(b,0.1,1)
# --- POS terminal screen (256x192) + keypad (192x256)
b=region('pos_screen',512,0,256,192); x,y,w,h=b
D.rectangle([x,y,x+w,y+h],fill=(236,244,250)); D.rectangle([x,y,x+w,y+34],fill=(0,92,170)); ctext(D,(x,y,w,34),'KoboPay',F(POP,22),(255,255,255))
ctext(D,(x,y+40,w,30),'WITHDRAWAL',F(POPS,20),(30,40,60)); ctext(D,(x,y+70,w,64),'₦20,000',F(MONT,40,800),(10,20,40))
rr(D,(x+30,y+144,w-60,36),8,(31,160,90)); ctext(D,(x+30,y+144,w-60,36),'APPROVED',F(POP,20),(255,255,255))
b=region('pos_keys',768,0,192,256); x,y,w,h=b
D.rectangle([x,y,x+w,y+h],fill=(26,28,32))
keys=['1','2','3','4','5','6','7','8','9','*','0','#']
for i,k in enumerate(keys):
    cx=x+12+(i%3)*58; cy=y+12+(i//3)*48; rr(D,(cx,cy,52,40),8,(210,212,216)); ctext(D,(cx,cy,52,40),k,F(POPS,24),(30,30,34))
for j,(c,t) in enumerate([((220,50,50),'X'),((240,190,40),'<'),((40,170,90),'OK')]):
    cx=x+12+j*58; cy=y+206; rr(D,(cx,cy,52,40),8,c); ctext(D,(cx,cy,52,40),t,F(POP,20),(255,255,255))
# --- cash bundle top (256x128): fictional note art
b=region('cash_note',960,0,256,128); x,y,w,h=b
D.rectangle([x,y,x+w,y+h],fill=(170,120,190)); D.rectangle([x+6,y+6,x+w-6,y+h-6],outline=(110,70,130),width=3)
D.ellipse([x+150,y+18,x+236,y+108],fill=(190,150,205),outline=(110,70,130),width=2); ctext(D,(x+12,y+10,120,60),'1000',F(ANT,46),(80,40,100)); ctext(D,(x+12,y+70,130,40),'NAIRA',F(POPS,22),(80,40,100))
weather(b,0.12,2)
b=region('cash_note_b',1216,0,256,128); x,y,w,h=b
D.rectangle([x,y,x+w,y+h],fill=(214,168,90)); D.rectangle([x+6,y+6,x+w-6,y+h-6],outline=(140,90,40),width=3)
D.ellipse([x+150,y+18,x+236,y+108],fill=(230,190,120),outline=(140,90,40),width=2); ctext(D,(x+12,y+10,120,60),'500',F(ANT,46),(110,60,20)); ctext(D,(x+12,y+70,130,40),'NAIRA',F(POPS,22),(110,60,20))
weather(b,0.12,3)
# --- buka menu board (512x640)
b=region('buka_menu',0,768,512,640); x,y,w,h=b
D.rectangle([x,y,x+w,y+h],fill=(28,52,40)); D.rectangle([x+10,y+10,x+w-10,y+h-10],outline=(196,150,80),width=6)
ctext(D,(x,y+20,w,70),'IYA BASIRA',F(ALFA,58),(250,214,120)); ctext(D,(x,y+88,w,40),'Buka & Canteen',F(KAL,36),(240,240,230))
menu=[('Jollof rice','1,500'),('White rice & stew','1,200'),('Amala & ewedu','1,000'),('Eba & egusi','1,100'),('Dodo (plantain)','300'),('Beef / Ponmo','500'),('Fried fish','700'),('Pure water','50')]
for i,(n,p) in enumerate(menu):
    yy=y+150+i*56; fm=F(CAV,44,600); D.text((x+36,yy-6),n,font=fm,fill=(245,245,235)); tb=D.textbbox((0,0),'₦'+p,font=fm); D.text((x+w-36-(tb[2]-tb[0]),yy-6),'₦'+p,font=fm,fill=(250,214,120))
ctext(D,(x,y+h-62,w,40),'Mon–Sat · 7am till food finish',F(KAL,26),(200,220,200))
weather(b,0.14,4)
# --- barber sign (1024x256) and style poster (512x640)
b=region('barber_sign',512,768,1024,256); x,y,w,h=b
D.rectangle([x,y,x+w,y+h],fill=(18,18,22)); 
for i in range(0,w,40): D.polygon([(x+i,y),(x+i+20,y),(x+i,y+20)],fill=(200,30,40)) if False else None
D.rectangle([x,y,x+w,y+14],fill=(200,30,40)); D.rectangle([x,y+h-14,x+w,y+h],fill=(30,70,180))
ctext(D,(x,y+10,w,150),'KINGS CUT',F(ANT,150),(245,245,245)); ctext(D,(x,y+168,w,64),'BARBING SALON  ·  LOW CUT · FADE · BEARD',F(POPS,34),(230,190,60))
weather(b,0.1,5)
b=region('barber_poster',1536,768,512,640); x,y,w,h=b
D.rectangle([x,y,x+w,y+h],fill=(240,236,226)); ctext(D,(x,y+12,w,60),'HAIR STYLES',F(BEB,64),(20,20,24))
styles=['LOW CUT','FADE','AFRO','WAVES','MOHAWK','BALD','TWISTS','BEARD']
for i,s in enumerate(styles):
    cx=x+24+(i%2)*244; cy=y+86+(i//2)*136
    D.rectangle([cx,cy,cx+220,cy+124],fill=(225,220,208))
    hx=cx+60; hy=cy+66
    D.ellipse([hx-34,hy-40,hx+34,hy+40],fill=(92,58,40)); D.rectangle([hx-16,hy+30,hx+16,hy+58],fill=(92,58,40))
    hair=(18,14,12)
    if s=='AFRO': D.ellipse([hx-50,hy-62,hx+50,hy+10],fill=hair)
    elif s=='MOHAWK': D.rectangle([hx-8,hy-62,hx+8,hy-20],fill=hair)
    elif s=='FADE': D.chord([hx-36,hy-46,hx+36,hy+10],180,360,fill=hair)
    elif s=='LOW CUT': D.chord([hx-35,hy-43,hx+35,hy],180,360,fill=hair)
    elif s=='WAVES':
        D.chord([hx-35,hy-43,hx+35,hy],180,360,fill=hair)
        for k in range(3): D.arc([hx-28,hy-38+k*9,hx+28,hy-18+k*9],200,340,fill=(70,60,50),width=2)
    elif s=='TWISTS':
        for k in range(-3,4): D.line([hx+k*10,hy-44,hx+k*12,hy-8],fill=hair,width=7)
    elif s=='BEARD': D.chord([hx-35,hy-43,hx+35,hy],180,360,fill=hair); D.chord([hx-34,hy-4,hx+34,hy+46],0,180,fill=hair)
    D.text((cx+112,cy+46),s,font=F(BEB,34),fill=(30,30,34))
weather(b,0.1,6)
# --- chalkboard (1024x512)
b=region('chalkboard',0,1408,1024,512); x,y,w,h=b
a=np.zeros((h,w,3),np.float32); a[...]=np.array([38,66,52])/255
rs=np.random.RandomState(7); a*= (1+0.08*(rs.rand(h,w,1)-0.5)); 
sm=np.asarray(Image.fromarray((rs.rand(h//32+2,w//32+2)*255).astype(np.uint8)).resize((w,h),Image.BICUBIC)).astype(np.float32)/255
a+= 0.06*(sm[...,None]-0.3)
A.paste(Image.fromarray((np.clip(a,0,1)*255).astype(np.uint8)),(x,y))
chalk=(232,236,228)
D.text((x+40,y+24),'Tuesday, 14th October',font=F(CAV,54),fill=chalk); D.text((x+620,y+24),'Primary 4B',font=F(CAV,54),fill=(240,220,140))
D.line([x+40,y+92,x+980,y+92],fill=(200,205,198),width=3)
D.text((x+40,y+110),'MATHEMATICS',font=F(CAV,60),fill=chalk)
for i,l in enumerate(['12 x 7 = 84','45 + 38 = 83','144 ÷ 12 = 12','₦500 − ₦275 = ₦225']): D.text((x+60,y+190+i*68),l,font=F(CAV,56),fill=chalk)
D.text((x+600,y+190),'Homework:',font=F(CAV,52),fill=(240,220,140)); D.text((x+600,y+254),'Page 36, Q1–10',font=F(CAV,50),fill=chalk); D.text((x+600,y+318),'Spelling test Fri.',font=F(CAV,50),fill=chalk)
for k in range(9):  # eraser smudges
    sx=rnd.randint(x+20,x+w-200); sy=rnd.randint(y+120,y+h-60)
    sm=Image.new('L',(220,60),0); ImageDraw.Draw(sm).ellipse([20,10,200,50],fill=14); sm=sm.filter(ImageFilter.GaussianBlur(16))
    A.paste(Image.new('RGB',(220,60),(170,190,175)),(sx,sy),sm)
D=ImageDraw.Draw(A)
# --- bank sign (1024x192), teller screen (256x160), poster (512x640)
b=region('bank_sign',1024,1408,1024,192); x,y,w,h=b
D.rectangle([x,y,x+w,y+h],fill=(250,250,248)); D.rectangle([x,y+h-20,x+w,y+h],fill=(31,107,74))
cx=x+110; cy=y+86; D.ellipse([cx-70,cy-70,cx+70,cy+70],fill=(31,107,74))
for k in range(5):
    ang=math.radians(200+k*35); D.line([cx,cy+30,cx+56*math.cos(ang),cy+20+46*math.sin(ang)],fill=(224,168,74),width=12)
D.line([cx,cy+30,cx+4,cy+62],fill=(250,250,248),width=10)
D.text((x+210,y+22),'PalmTrust',font=F(POP,96),fill=(31,107,74)); D.text((x+720,y+58),'BANK',font=F(POPS,64),fill=(224,168,74))
b=region('bank_screen',1024,1600,256,160); x,y,w,h=b
D.rectangle([x,y,x+w,y+h],fill=(236,242,240)); D.rectangle([x,y,x+w,y+26],fill=(31,107,74)); D.text((x+8,y+2),'PalmTrust Teller',font=F(POPS,16),fill=(255,255,255))
for i in range(5):
    D.rectangle([x+10,y+36+i*24,x+150,y+52+i*24],fill=(200,214,208)); D.rectangle([x+160,y+36+i*24,x+240,y+52+i*24],fill=(160,190,178) if i!=2 else (224,168,74))
b=region('bank_poster',1280,1600,384,448); x,y,w,h=b
D.rectangle([x,y,x+w,y+h],fill=(31,107,74)); ctext(D,(x,y+30,w,60),'SAVE SMALL,',F(BEB,64),(250,250,248)); ctext(D,(x,y+90,w,60),'GROW BIG.',F(BEB,64),(224,168,74))
D.ellipse([x+120,y+170,x+264,y+314],fill=(224,168,74)); ctext(D,(x+120,y+170,144,144),'₦',F(MONT,96,800),(31,107,74))
ctext(D,(x,y+330,w,40),'PalmTrust Target Savings',F(POPS,26),(250,250,248)); ctext(D,(x,y+372,w,40),'Up to 12% p.a. · T&Cs apply',F(POPR,20),(210,230,220))
# --- code screen (512x320) and helpdesk (512x320)
b=region('code_screen',1664,1600,384,256); x,y,w,h=b
D.rectangle([x,y,x+w,y+h],fill=(22,26,34)); D.rectangle([x,y,x+w,y+18],fill=(40,46,58))
code=['import { route } from "./api";','','export async function pay(n) {','  const res = await route(n);','  if (!res.ok) {','    throw new Error("timeout");','  }','  return res.json();','}','// TODO: retry on 502']
cols=[(198,120,221),(0,0,0),(97,175,239),(229,192,123),(198,120,221),(224,108,117),(171,178,191),(152,195,121),(171,178,191),(92,99,112)]
for i,l in enumerate(code): D.text((x+10,y+24+i*22),f'{i+1:>2}  {l}',font=F(MONO,15),fill=cols[i] if cols[i]!=(0,0,0) else (171,178,191))
b=region('desk_screen',1664,1856,384,192); x,y,w,h=b
D.rectangle([x,y,x+w,y+h],fill=(245,247,250)); D.rectangle([x,y,x+w,y+24],fill=(91,45,130)); D.text((x+8,y+3),'HelpDesk · Tickets',font=F(POPS,15),fill=(255,255,255))
for i,(t,c) in enumerate([('#4471 Printer offline','open'),('#4472 Wi-Fi drop, 3rd floor','urgent'),('#4473 Password reset','done'),('#4474 POS app crash','open'),('#4475 Laptop slow','open')]):
    yy=y+32+i*31; D.text((x+10,yy),t,font=F(POPR,15),fill=(40,40,50)); col={'open':(59,130,196),'urgent':(212,83,58),'done':(31,160,90)}[c]
    rr(D,(x+w-80,yy,68,22),10,col); ctext(D,(x+w-80,yy,68,22),c,F(POPS,13),(255,255,255))
# --- security + estate + park + dispatch + stage + stripes + speaker + kanban
b=region('security_sign',0,1920,512,128); x,y,w,h=b
D.rectangle([x,y,x+w,y+h],fill=(30,58,52)); ctext(D,(x,y+4,w,74),'SECURITY POST',F(ANT,64),(250,214,0)); ctext(D,(x,y+80,w,40),'All visitors report here',F(POPS,26),(240,240,235)); weather(b,0.12,8)
b=region('estate_sign',1536,0,512,256); x,y,w,h=b
D.rectangle([x,y,x+w,y+h],fill=(245,240,228)); D.rectangle([x+8,y+8,x+w-8,y+h-8],outline=(31,107,74),width=6)
ctext(D,(x,y+24,w,90),'PALM GROVE',F(ALFA,70),(31,107,74)); ctext(D,(x,y+112,w,60),'ESTATE · IKEJA',F(POPS,40),(120,90,50)); ctext(D,(x,y+176,w,50),'Slow down · Kids at play',F(KAL,34),(160,60,40)); weather(b,0.12,9)
b=region('park_sign',1024,256,1024,256); x,y,w,h=b
D.rectangle([x,y,x+w,y+h],fill=(240,196,0)); D.rectangle([x,y,x+w,y+110],fill=(20,22,26))
ctext(D,(x,y+6,w,100),'OSHODI MOTOR PARK',F(ANT,92),(240,196,0))
for i,(r,p) in enumerate([('OBALENDE','800'),('CMS','900'),('IKEJA','600'),('YABA','700')]):
    cx=x+14+i*252; D.rectangle([cx,y+124,cx+238,y+244],fill=(20,22,26)); ctext(D,(cx,y+124,238,70),r,fit(r,BEB,220,64),(255,255,255)); ctext(D,(cx,y+190,238,50),'₦'+p,F(OSW,44,700),(240,196,0))
weather(b,0.14,10)
b=region('dispatch_logo',512,192,512,256); x,y,w,h=b
D.rectangle([x,y,x+w,y+h],fill=(212,83,58)); ctext(D,(x,y+30,w,120),'SwiftDrop',F(LIL,110),(255,255,255)); ctext(D,(x,y+160,w,60),'DISPATCH · 0700 SWIFT',F(POPS,34),(255,236,200)); weather(b,0.1,11)
b=region('parcel_label',1024,128,256,128); x,y,w,h=b
D.rectangle([x,y,x+w,y+h],fill=(250,250,246)); D.text((x+10,y+8),'TO: Adaeze O.',font=F(POPS,18),fill=(20,20,20)); D.text((x+10,y+32),'14 Herbert Macaulay, Yaba',font=F(POPR,14),fill=(40,40,40))
for i in range(40): 
    if rnd.random()<0.6: D.rectangle([x+10+i*5,y+70,x+12+i*5,y+118],fill=(10,10,10))
b=region('stage_banner',0,512,1024,256); x,y,w,h=b
for i in range(h):
    t=i/h; D.line([x,y+i,x+w,y+i],fill=(int(90+60*t),int(20+10*t),int(80+30*t)))
ctext(D,(x,y+18,w,120),'LIVE BAND',F(ANT,120),(255,224,120)); ctext(D,(x,y+148,w,50),'FRIDAY NIGHT · HIGHLIFE · AFROBEAT · FUJI',F(POPS,36),(255,255,255)); ctext(D,(x,y+200,w,40),'Ikeja Groove Spot',F(KAL,34),(255,200,220)); weather(b,0.08,12)
b=region('stripes',1280,128,128,128); x,y,w,h=b
D.rectangle([x,y,x+w,y+h],fill=(245,245,240))
for k in range(-2,4): D.polygon([(x+k*48,y+h),(x+k*48+24,y+h),(x+k*48+24+h,y),(x+k*48+h,y)],fill=(210,30,30))
b=region('speaker',1408,128,128,128); x,y,w,h=b
D.rectangle([x,y,x+w,y+h],fill=(24,24,26))
for yy in range(y+2,y+h,4):
    for xx in range(x+2,x+w,4): D.point((xx,yy),fill=(44,44,48))
b=region('kanban',1024,512,512,256); x,y,w,h=b
D.rectangle([x,y,x+w,y+h],fill=(246,248,250)); 
for i,t in enumerate(['TO DO','DOING','DONE']): D.text((x+20+i*168,y+10),t,font=F(MARK,28),fill=(40,60,120))
for k in range(9):
    cx=x+18+(k%3)*168+rnd.randint(0,30); cy=y+56+(k//3)*64+rnd.randint(0,8); col=[(255,236,120),(255,170,190),(150,220,255),(180,240,170)][k%4]
    D.rectangle([cx,cy,cx+110,cy+52],fill=col); D.line([cx+10,cy+18,cx+90,cy+18],fill=(70,70,90),width=3); D.line([cx+10,cy+32,cx+70,cy+32],fill=(70,70,90),width=3)
b=region('market_sign',1536,512,512,128); x,y,w,h=b
D.rectangle([x,y,x+w,y+h],fill=(250,232,60)); ctext(D,(x,y+4,w,80),'MAMA CHIDINMA',fit('MAMA CHIDINMA',ANT,w-40,70),(160,20,20)); ctext(D,(x,y+84,w,40),'Foodstuff · Provisions · Balogun',F(POPS,24),(30,30,30)); weather(b,0.14,13)
b=region('cardboard',1536,640,256,128); x,y,w,h=b
a=np.zeros((h,w,3),np.float32); a[...]=np.array([176,134,88])/255; a*= (1+0.08*(np.random.RandomState(3).rand(h,w,1)-0.5)); A.paste(Image.fromarray((np.clip(a,0,1)*255).astype(np.uint8)),(x,y))
D.rectangle([x,y+52,x+w,y+76],fill=(200,170,120))
b=region('tv_screen',1792,640,256,128); x,y,w,h=b
for i in range(h):
    t=i/h; D.line([x,y+i,x+w,y+i],fill=(int(30+40*t),int(90+40*t),int(40+30*t)))
D.rectangle([x,y+100,x+w,y+h],fill=(10,10,30)); D.text((x+8,y+104),'LIVE · Super Eagles 1 – 0',font=F(POPS,16),fill=(255,255,255))
A.save(f'{O}/work_atlas.jpg',quality=88,optimize=True)
json.dump(R,open(f'{O}/work_rects.json','w'),indent=0)
A.resize((1024,1024)).save('/tmp/work_atlas_preview.jpg',quality=80)
print('ok',len(R),'regions')
