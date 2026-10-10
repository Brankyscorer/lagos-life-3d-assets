# Lagos Life housing kit (Step 07): furniture + building pieces. Procedural Blender builders (envlib MB) and
# decimated Poly Haven CC0 models. Blender Z up; fronts face -Y (= +Z in three.js). Metres; origin at floor centre
# of the footprint (wall items: origin at the wall plane, bottom of the item at mountY handled at runtime).
import math, random, json
from mathutils import Vector as V, Matrix
import bpy
from envlib import *
import envlib
from phlib import ph_load, ph_place, join
envlib.META.update(json.load(open('/workspace/workkit/tex/tex_meta.json')))
envlib.MAT_FLAT.update({'mirror':((0.92,0.93,0.94),0.04,1.0),'glass_clear':((0.8,0.9,0.92),0.05,0.0),'net':((1,1,1),0.9,0.0),
  'screen_off':((0.02,0.02,0.025),0.15,0.0),'emit_led':((0.9,0.95,1),0.3,0.0)})
FULL=('uvs',[(0,0),(1,0),(1,1),(0,1)])

def finish(mb,name,objs=(),seed=0,grime=0.5,damp_h=0.0,ground=True,smooth=35,ao=True):
    ob=build_object(mb,name,mat_lib,merge=True)
    ob=join([ob,*objs],name) if objs else ob
    shade(ob,smooth)
    if ao: bake_ao_grime(ob,grime_amt=grime,damp_h=damp_h,seed=seed,ground=ground)
    return ob
def empty_mb():
    mb=MB(); mb.box((0,0,0),(0.001,0.001,0.001),'metal_dark'); return mb
def bbox(ob):
    pts=[ob.matrix_world@V(c) for c in ob.bound_box]
    return [min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]
def phfit(pid,tris,size=None,height=None,rotz=0.0,loc=(0,0,0),uniform=True,tint=None):
    """Load a PH model, rotate, then scale to fit size (w,d,h) or height, centre on XY, ground at z=0, offset by loc."""
    ob=ph_place(ph_load(pid,target_tris=tris),(0,0,0),rotz,1.0,tint=tint)
    mn,mx=bbox(ob); dims=[mx[i]-mn[i] for i in range(3)]
    if size:
        s=[size[i]/max(dims[i],1e-4) for i in range(3)]
        if uniform: s=[min(s)]*3
    else:
        s=[height/dims[2]]*3
    M=Matrix.Translation(V(loc))@Matrix.Diagonal((*s,1))@Matrix.Translation(V((-(mn[0]+mx[0])/2,-(mn[1]+mx[1])/2,-mn[2])))
    ob.data.transform(M)
    return ob
def meta(cat,notes,**k): return dict(category=cat,notes=notes,**k)

# ------------------------------------------------------------------ sleep
def mattress_block(mb,x0,y0,x1,y1,z0,z1,tint=(0.93,0.91,0.86)):
    b=0.04
    mb.box((x0+b,y0+b,z0),(x1-b,y1-b,z1),'linen',tint=tint)
    mb.box((x0,y0+b,z0+b),(x1,y1-b,z1-b),'linen',tint=tint)
    mb.box((x0+b,y0,z0+b),(x1-b,y1,z1-b),'linen',tint=tint)
def bedding(mb,x0,y0,x1,y1,z,seed=1):
    # pillows at the head (+Y), a wrapper/sheet folded over the foot half
    W=x1-x0
    for i in range(2 if W>1.0 else 1):
        cx=x0+W*(i+0.5)/(2 if W>1.0 else 1)
        mb.box((cx-0.3,y1-0.5,z),(cx+0.3,y1-0.12,z+0.12),'linen',tint=(0.97,0.97,0.95))
    mb.box((x0-0.01,y0-0.01,z-0.04),(x1+0.01,y0+(y1-y0)*0.55,z+0.025),'hk_check',tint=(1,1,1))
def foam_mattress():
    mb=MB(); mattress_block(mb,-0.72,-0.97,0.72,0.97,0,0.18,(0.75,0.82,0.92)); bedding(mb,-0.7,-0.95,0.7,0.95,0.18)
    return finish(mb,'hk_foam_mattress',seed=1),meta('sleep','6-inch foam on the floor, blue cover, check sheet, pillows. 1.5 x 2.0 m.')
def spring_bed():
    mb=MB(); T=(0.62,0.5,0.42)
    mb.box((-0.76,-1.0,0.1),(0.76,1.0,0.32),'hk_laminate',tint=T)          # frame rails
    for x in (-0.74,0.7):
        for y in (-0.98,0.94): mb.box((x,y,0),(x+0.04,y+0.04,0.1),'hk_laminate',tint=T)
    mb.box((-0.78,0.94,0),(0.78,1.0,1.05),'hk_laminate',tint=T)             # headboard
    mb.box((-0.7,0.93,0.55),(0.7,0.94,0.95),'hk_leather',tint=(1,1,1))
    mattress_block(mb,-0.72,-0.96,0.72,0.92,0.32,0.55); bedding(mb,-0.7,-0.94,0.7,0.9,0.55)
    return finish(mb,'hk_spring_bed',seed=2),meta('sleep','Wood frame double with leather headboard panel, spring mattress, pillows, check sheet. 1.5 x 2.0 m.')
def mosquito_net():
    mb=MB(); H=1.9; x0,x1,y0,y1=-0.75,0.75,-1.0,1.0
    for (a,b) in (((x0,y0),(x1,y0)),((x1,y0),(x1,y1)),((x1,y1),(x0,y1)),((x0,y1),(x0,y0))):
        mb.quad(V((a[0],a[1],0.25)),V((b[0],b[1],0.25)),V((b[0],b[1],H)),V((a[0],a[1],H)),'net',uv=FULL,grime=0)
    mb.quad(V((x0,y0,H)),V((x1,y0,H)),V((x1,y1,H)),V((x0,y1,H)),'net',uv=FULL,grime=0)
    for x,y in ((x0,y0),(x1,y0),(x1,y1),(x0,y1)): mb.cyl((x,y,0.25),0.006,H-0.25,'plastic',seg=6,tint=(0.95,0.95,0.95))
    return finish(mb,'hk_mosquito_net',seed=3,ao=False),meta('sleep','Box mosquito net over a 1.5 x 2.0 m bed, 1.9 m high (alpha "net").')
def wardrobe():
    mb=MB(); T=(1.0,0.95,0.9)
    mb.box((-0.74,-0.28,0.05),(0.74,0.28,2.0),'hk_laminate',tint=T)
    mb.box((-0.72,-0.27,0),(0.72,0.25,0.05),'metal_dark')
    mb.box((-0.005,-0.285,0.08),(0.005,-0.28,1.97),'metal_dark')
    for x in (-0.06,0.04): mb.box((x,-0.31,0.95),(x+0.02,-0.285,1.25),'alu')
    mb.box((-0.76,-0.3,1.98),(0.76,0.3,2.02),'hk_laminate',tint=(0.7,0.6,0.5))
    return finish(mb,'hk_wardrobe',seed=4),meta('sleep','Two-door wardrobe 1.5 x 0.56 x 2.0 m.')
# ------------------------------------------------------------------ kitchen
def kerosene_stove():
    mb=MB(); mb.cyl((0,0,0),0.17,0.16,'metal_paint',seg=16,tint=(0.15,0.35,0.6))
    mb.cyl((0,0,0.16),0.12,0.08,'steel_galv',seg=16,cap_top=False); mb.cyl((0,0,0.22),0.16,0.01,'metal_dark',seg=16)
    for a in range(3):
        t=a*2*math.pi/3; mb.box((0.11*math.cos(t)-0.015,0.11*math.sin(t)-0.015,0.23),(0.11*math.cos(t)+0.015,0.11*math.sin(t)+0.015,0.29),'metal_dark')
    mb.cyl((0,0,0.29),0.14,0.14,'steel_galv',seg=16,r2=0.15); mb.cyl((0,0,0.43),0.15,0.01,'steel_galv',seg=16)
    mb.cyl((0.16,-0.0,0.06),0.015,0.06,'metal_dark',seg=8,axis='X')
    return finish(mb,'hk_kerosene_stove',seed=5),meta('kitchen','Wick kerosene stove with a pot on it, 0.35 m.')
def gas_cooker():
    ob=phfit('electric_stove',5000,size=(0.95,0.85,0.92),rotz=0.0)
    return finish(empty_mb(),'hk_gas_cooker',[ob],seed=6),meta('kitchen','4-burner cooker with oven (Poly Haven electric_stove, CC0).')
def fridge_box(name,w,d,h,chest=False):
    mb=MB(); x0,x1,y0,y1=-w/2,w/2,-d/2,d/2
    mb.box((x0+0.02,y0+0.02,0.04),(x1-0.02,y1,h),'plastic',tint=(0.93,0.93,0.92))
    mb.box((x0,y0,0.06),(x1,y0+0.06,h-0.02),'plastic',tint=(0.96,0.96,0.95)) if not chest else mb.box((x0,y0,h-0.08),(x1,y1,h),'plastic',tint=(0.96,0.96,0.95))
    mb.box((x0+0.03,y0+0.03,0),(x1-0.03,y1-0.03,0.04),'metal_dark')
    if chest: mb.box((-0.2,y0-0.03,h-0.1),(0.2,y0,h-0.06),'plastic',tint=(0.2,0.2,0.2))
    else:
        mb.box((x0,y0-0.002,h*0.62),(x1,y0,h*0.625),'metal_dark')
        mb.box((x1-0.08,y0-0.04,h*0.66),(x1-0.06,y0,h*0.86),'alu'); mb.box((x1-0.08,y0-0.04,h*0.35),(x1-0.06,y0,h*0.55),'alu')
    return finish(mb,name,seed=7)
def small_fridge(): return fridge_box('hk_small_fridge',0.6,0.62,1.3),meta('kitchen','Small double-door fridge 0.6 x 0.62 x 1.3 m.')
def freezer(): return fridge_box('hk_freezer',1.2,0.68,0.88,chest=True),meta('kitchen','Chest freezer 1.2 x 0.68 x 0.88 m.')
def dining_set():
    t=phfit('dining_table',1200,size=(1.2,0.85,0.76),uniform=False)
    c1=phfit('dining_chair_02',3000,height=0.95,loc=(0,-0.55,0),rotz=0)
    c2=phfit('dining_chair_02',3000,height=0.95,loc=(0,0.55,0),rotz=math.pi)
    return finish(empty_mb(),'hk_dining_set',[t,c1,c2],seed=8),meta('kitchen','Dining table 1.2 m + 2 chairs (Poly Haven dining_table, dining_chair_02, CC0).')
# ------------------------------------------------------------------ bath
def wc_shower():
    mb=MB()
    mb.box((-0.75,0.0,0),(0.0,0.75,0.08),'ceramic',tint=(0.95,0.95,0.94))                 # shower tray (back-left)
    mb.box((-0.72,0.03,0.08),(-0.03,0.72,0.081),'metal_dark')
    mb.quad(V((0,0,0.08)),V((0,0.75,0.08)),V((0,0.75,2.0)),V((0,0,2.0)),'glass_clear',uv=FULL,grime=0)
    mb.box((-0.01,0,0.08),(0.01,0.75,0.11),'alu'); mb.box((-0.01,0,1.98),(0.01,0.75,2.0),'alu')
    mb.cyl((-0.38,0.73,1.0),0.012,1.05,'chrome',seg=8); mb.cyl((-0.38,0.6,2.05),0.08,0.02,'chrome',seg=14)
    mb.box((-0.39,0.6,2.04),(-0.37,0.74,2.06),'chrome')
    # WC (front-right)
    mb.box((0.25,0.55,0.38),(0.65,0.73,0.75),'ceramic',tint=(0.97,0.97,0.96))
    mb.cyl((0.45,0.28,0),0.13,0.38,'ceramic',seg=16,r2=0.2,tint=(0.97,0.97,0.96))
    mb.cyl((0.45,0.28,0.38),0.2,0.03,'ceramic',seg=16,tint=(0.97,0.97,0.96))
    mb.box((0.27,0.3,0.38),(0.63,0.56,0.42),'ceramic',tint=(0.97,0.97,0.96))
    mb.box((0.52,0.6,0.75),(0.58,0.66,0.77),'chrome')
    return finish(mb,'hk_wc_shower',seed=9),meta('bath','Corner shower tray with glass screen and chrome head + WC. 1.5 x 1.5 m.')
def bucket_bowl():
    mb=MB(); mb.cyl((0,0,0),0.14,0.32,'plastic',seg=16,r2=0.17,cap_top=False,cap_bot=True,tint=(0.1,0.35,0.75))
    mb.cyl((0,0,0.28),0.16,0.005,'water',seg=16); mb.cyl((0.0,0,0.3),0.17,0.02,'plastic',seg=16,tint=(0.08,0.3,0.65))
    mb.cyl((0.16,0.12,0),0.06,0.08,'plastic',seg=12,r2=0.1,tint=(0.85,0.15,0.15))
    return finish(mb,'hk_bucket_bowl',seed=10),meta('bath','Blue bucket of water + red bowl.')
# ------------------------------------------------------------------ comfort
def plastic_chair():
    ob=phfit('plastic_monobloc_chair_01',2400,height=0.86)
    return finish(empty_mb(),'hk_plastic_chair',[ob],seed=11),meta('comfort','Monobloc chair (Poly Haven, CC0).')
def sofa():
    ob=phfit('sofa_02',3000,size=(2.0,0.95,0.9))
    return finish(empty_mb(),'hk_sofa',[ob],seed=12),meta('comfort','Three-seater fabric sofa (Poly Haven sofa_02, CC0).')
def armchair():
    ob=phfit('ArmChair_01',3000,size=(0.9,0.9,1.0))
    return finish(empty_mb(),'hk_armchair',[ob],seed=13),meta('comfort','Armchair (Poly Haven ArmChair_01, CC0).')
def fan_blades(name,r,n,blade_w,mat='plastic',tint=(0.85,0.88,0.92)):
    mb=MB()
    for i in range(n):
        a=i*2*math.pi/n; ca,sa=math.cos(a),math.sin(a)
        pts=[(0.03,-blade_w/2),(r,-blade_w*0.8),(r,blade_w*0.8),(0.03,blade_w/2)]
        q=[V((p[0]*ca-p[1]*sa,p[0]*sa+p[1]*ca,0)) for p in pts]
        mb.face(q,mat,tint=tint,grime=0); mb.face(list(reversed(q)),mat,tint=tint,grime=0)
    mb.cyl((0,0,-0.02),0.035,0.04,'plastic',seg=12,tint=tint,cap_bot=True)
    return mb
def standing_fan():
    mb=MB(); T=(0.92,0.93,0.95)
    mb.cyl((0,0,0),0.2,0.04,'plastic',seg=20,tint=T); mb.cyl((0,0,0.04),0.018,1.0,'chrome',seg=8)
    mb.box((-0.07,0.0,1.0),(0.07,0.16,1.14),'plastic',tint=T)
    # cage: two rings + spokes, facing -Y, centre (0,-0.04,1.12)
    c=V((0,-0.03,1.12)); R=0.24
    for yy in (0.02,-0.1):
        pts=[V((R*math.cos(t),0,R*math.sin(t)))+c+V((0,yy,0)) for t in [i*2*math.pi/24 for i in range(25)]]
        for a,b in zip(pts,pts[1:]): mb.box((min(a.x,b.x)-0.004,a.y-0.004,min(a.z,b.z)-0.004),(max(a.x,b.x)+0.004,a.y+0.004,max(a.z,b.z)+0.004),'chrome')
    blades=fan_blades('b',0.21,3,0.12); blades.transform(Matrix.Translation(c+V((0,-0.04,0)))@Matrix.Rotation(math.pi/2,4,'X'))
    return finish(mb,'hk_standing_fan',seed=14),meta('comfort','Standing fan, white; blades are hk_fan_blades (spin about local Y at hub).',hub=[0,-0.07,1.12])
def fan_blades_std():
    mb=fan_blades('hk_fan_blades',0.21,3,0.12); mb.transform(Matrix.Rotation(math.pi/2,4,'X'))
    return finish(mb,'hk_fan_blades',ao=False),meta('part','Standing-fan blades; spin about Y (three: Z) at origin.')
def ceiling_fan():
    mb=MB(); T=(0.95,0.95,0.95)
    mb.cyl((0,0,-0.06),0.07,0.06,'plastic',seg=16,tint=T); mb.cyl((0,0,-0.3),0.012,0.24,'chrome',seg=8)
    mb.cyl((0,0,-0.42),0.1,0.12,'plastic',seg=18,tint=T,cap_bot=True)
    return finish(mb,'hk_ceiling_fan',seed=15,ground=False),meta('comfort','Ceiling fan body; hangs down from origin (ceiling); blades hk_ceiling_fan_blades at z=-0.44.',hub=[0,0,-0.44])
def ceiling_fan_blades():
    mb=fan_blades('x',0.68,3,0.14,'hk_laminate',tint=(0.9,0.8,0.7))
    return finish(mb,'hk_ceiling_fan_blades',ao=False),meta('part','Ceiling fan blades, spin about Z (three: Y).')
def split_ac():
    mb=MB(); T=(0.96,0.96,0.95)
    mb.box((-0.45,0,0),(0.45,0.22,0.3),'plastic',tint=T)
    for i in range(6): mb.box((-0.4,-0.004,0.03+i*0.012),(0.4,0.0,0.036+i*0.012),'plastic',tint=(0.8,0.8,0.8))
    mb.box((0.3,-0.004,0.2),(0.38,0,0.22),'emit_led')
    return finish(mb,'hk_split_ac',seed=16,ground=False),meta('comfort','Split AC indoor unit 0.9 x 0.22 x 0.3 m; back on the wall plane (y=+0.22 back), origin bottom.')
# ------------------------------------------------------------------ fun
def flat_tv(mb,cx,cy,z,w=0.73,h=0.43):
    mb.box((cx-w/2,cy-0.03,z+0.02),(cx+w/2,cy+0.02,z+h),'plastic',tint=(0.05,0.05,0.05))
    mb.quad(V((cx-w/2+0.015,cy-0.031,z+0.035)),V((cx+w/2-0.015,cy-0.031,z+0.035)),V((cx+w/2-0.015,cy-0.031,z+h-0.015)),V((cx-w/2+0.015,cy-0.031,z+h-0.015)),'screen_off',uv=FULL,grime=0)
    mb.box((cx-0.12,cy-0.06,z),(cx+0.12,cy+0.06,z+0.02),'plastic',tint=(0.08,0.08,0.08))
def tv_stand(name,console=False):
    cab=phfit('modern_wooden_cabinet',4000,size=(1.4,0.45,0.55),uniform=False)
    mb=MB(); flat_tv(mb,0,0.05,0.55)
    objs=[cab]
    if console: objs.append(phfit('gaming_console',2500,size=(0.3,0.3,0.09),loc=(0.42,0.0,0.55)))
    return finish(mb,name,objs,seed=17),meta('fun',f'Low TV cabinet 1.4 m (Poly Haven modern_wooden_cabinet, CC0) with a 32-inch flat TV{" and a console" if console else ""}.')
def speaker():
    ob=phfit('boombox',2500,size=(0.42,0.12,0.3))
    return finish(empty_mb(),'hk_speaker',[ob],seed=18),meta('fun','Portable speaker (Poly Haven boombox, CC0).')
# ------------------------------------------------------------------ skills
def mirror():
    mb=MB(); T=(0.3,0.2,0.12)
    mb.box((-0.27,0.0,0.0),(0.27,0.05,1.6),'hk_laminate',tint=(0.55,0.42,0.32))
    mb.quad(V((-0.22,-0.001,0.06)),V((0.22,-0.001,0.06)),V((0.22,-0.001,1.54)),V((-0.22,-0.001,1.54)),'mirror',uv=FULL,grime=0)
    return finish(mb,'hk_mirror',seed=19),meta('skills','Full-length wall mirror 0.54 x 1.6 m; back on the wall plane.')
def laptop_desk():
    d=phfit('small_wooden_table_01',2000,size=(1.0,0.55,0.75),uniform=False)
    l=phfit('classic_laptop',3000,size=(0.34,0.26,0.24),loc=(0.0,0.02,0.75))
    c=phfit('plastic_monobloc_chair_01',1500,height=0.86,loc=(0,-0.5,0),rotz=math.pi)
    return finish(empty_mb(),'hk_laptop_desk',[d,l,c],seed=20),meta('skills','Desk with laptop and chair (Poly Haven small_wooden_table_01, classic_laptop, monobloc, CC0).')
def guitar():
    mb=MB(); T=(0.62,0.38,0.18)
    # stand
    for s in (-1,1): mb.box((s*0.12-0.01,-0.08,0),(s*0.12+0.01,0.12,0.02),'metal_dark')
    mb.box((-0.01,0.1,0),(0.01,0.12,0.5),'metal_dark')
    def blob(cz,r,dz):
        mb.cyl((0,0.04,cz),r,0.09,'wood',seg=20,axis='Y',tint=T,cap_bot=True)
    blob(0.25,0.17,0); blob(0.47,0.13,0)
    mb.cyl((0,-0.051,0.35),0.045,0.002,'metal_dark',seg=16,axis='Y')
    mb.box((-0.025,-0.04,0.55),(0.025,0.0,1.0),'wood',tint=(0.25,0.15,0.08))
    mb.box((-0.035,-0.035,0.95),(0.035,-0.005,1.05),'wood',tint=(0.2,0.12,0.06))
    return finish(mb,'hk_guitar',seed=21),meta('skills','Acoustic guitar on a stand, ~1.05 m.')
def dumbbells():
    mb=MB(); mb.box((-0.45,-0.25,0),(0.45,0.25,0.012),'rubber')
    for x in (-0.2,0.2):
        mb.cyl((x-0.13,0.0,0.07),0.06,0.05,'metal_dark',seg=14,axis='X',cap_top=True,cap_bot=True)
        mb.cyl((x+0.08,0.0,0.07),0.06,0.05,'metal_dark',seg=14,axis='X',cap_top=True,cap_bot=True)
        mb.cyl((x-0.08,0.0,0.07),0.015,0.16,'chrome',seg=8,axis='X')
    return finish(mb,'hk_dumbbells',seed=22),meta('skills','Exercise mat + two dumbbells.')
def bookshelf():
    s=phfit('wooden_bookshelf_worn',3000,size=(1.0,0.4,1.8),uniform=False)
    mb=MB(); rnd=random.Random(3)
    cols=[(0.55,0.12,0.1),(0.1,0.3,0.5),(0.15,0.4,0.2),(0.8,0.65,0.3),(0.2,0.2,0.22),(0.85,0.85,0.8)]
    for z in (0.44,0.86,1.28):
        x=-0.44
        while x<0.4:
            w=rnd.uniform(0.025,0.05); h=rnd.uniform(0.2,0.3)
            if rnd.random()<0.85: mb.box((x,-0.12,z),(x+w,0.12,z+h),'plastic',tint=rnd.choice(cols))
            x+=w+0.003
    return finish(mb,'hk_bookshelf',[s],seed=23),meta('skills','Bookshelf with books (Poly Haven wooden_bookshelf_worn, CC0, + own books).')
# ------------------------------------------------------------------ light
def rechargeable_lamp():
    mb=MB(); mb.box((-0.09,-0.05,0),(0.09,0.05,0.06),'plastic',tint=(0.9,0.9,0.88))
    mb.cyl((0,0,0.06),0.045,0.22,'glass_clear',seg=14); mb.cyl((0,0,0.08),0.015,0.18,'emit_cool',seg=8)
    mb.cyl((0,0,0.28),0.06,0.03,'plastic',seg=14,tint=(0.9,0.9,0.88)); mb.box((-0.005,-0.04,0.31),(0.005,0.04,0.36),'plastic',tint=(0.2,0.2,0.2))
    return finish(mb,'hk_rechargeable_lamp',seed=24),meta('light','Rechargeable lantern; light at z 0.18.',light=[0,0,0.18])
def floor_lamp():
    mb=MB(); mb.cyl((0,0,0),0.15,0.03,'metal_dark',seg=18); mb.cyl((0,0,0.03),0.012,1.3,'alu',seg=8)
    mb.cyl((0,0,1.3),0.2,0.28,'fabric',seg=20,r2=0.13,cap_top=False,tint=(0.95,0.9,0.8)); mb.cyl((0,0,1.33),0.04,0.08,'emit_warm',seg=10)
    return finish(mb,'hk_floor_lamp',seed=25),meta('light','Floor lamp 1.6 m, fabric shade; light at z 1.4.',light=[0,0,1.4])
# ------------------------------------------------------------------ power
def petrol_gen():
    ob=phfit('portable_generator',4000,size=(0.85,0.6,0.6))
    return finish(empty_mb(),'hk_petrol_gen',[ob],seed=26),meta('power','"I better pass my neighbour" petrol generator (Poly Haven portable_generator, CC0). Exhaust at the -X end.',exhaust=[-0.42,0,0.3])
def diesel_gen():
    mb=MB(); G=(0.18,0.32,0.22)
    mb.box((-0.95,-0.45,0.1),(0.95,0.45,1.15),'metal_paint',tint=G); mb.box((-1.0,-0.5,0),(1.0,0.5,0.1),'metal_dark')
    for i in range(10): mb.box((-0.8+i*0.12,-0.452,0.3),(-0.74+i*0.12,-0.45,0.9),'metal_dark')
    mb.box((0.55,-0.455,0.45),(0.85,-0.45,0.85),'plastic',tint=(0.1,0.1,0.1)); mb.box((0.6,-0.457,0.65),(0.8,-0.455,0.8),'emit_led')
    mb.cyl((-0.7,0.2,1.15),0.05,0.25,'metal_dark',seg=10)
    return finish(mb,'hk_diesel_gen',seed=27),meta('power','Soundproof diesel generator canopy 2.0 x 1.0 x 1.2 m. Exhaust stack top-left.',exhaust=[-0.7,0.2,1.4])
def inverter():
    mb=MB()
    mb.box((-0.45,-0.2,0),(0.45,0.2,0.04),'metal_dark')
    for x in (-0.42,0.02): mb.box((x,-0.17,0.04),(x+0.4,0.17,0.3),'plastic',tint=(0.08,0.08,0.09)); mb.box((x+0.05,-0.08,0.3),(x+0.1,-0.03,0.33),'metal_dark')
    mb.box((-0.25,-0.12,0.42),(0.25,0.12,0.88),'metal_paint',tint=(0.92,0.92,0.9)); mb.box((-0.5,-0.2,0.38),(0.5,0.2,0.42),'metal_dark')
    mb.box((-0.12,-0.122,0.7),(0.12,-0.12,0.82),'screen_off'); mb.box((-0.08,-0.123,0.6),(-0.05,-0.12,0.63),'emit_led')
    return finish(mb,'hk_inverter',seed=28),meta('power','Inverter on a rack over two deep-cycle batteries.')
def solar_kit():
    mb=MB()
    mb.box((-0.3,-0.2,0),(0.3,0.2,0.9),'metal_paint',tint=(0.9,0.9,0.88)); mb.box((-0.2,-0.202,0.6),(0.2,-0.2,0.8),'screen_off')
    mb.box((-0.15,-0.203,0.65),(-0.1,-0.2,0.7),'emit_led')
    # one display panel leaning on the cabinet side (the rest are on the roof)
    p0=V((0.32,-0.25,0)); 
    for i in range(1):
        mb.quad(V((0.33,-0.45,0.02)),V((0.33,0.45,0.02)),V((0.48,0.45,1.0)),V((0.33+0.15,-0.45,1.0)),'glass',tint=(0.1,0.15,0.35),uv=FULL)
    return finish(mb,'hk_solar_kit',seed=29),meta('power','Solar battery cabinet + charge controller, one panel leaning (rest on the roof).')
def jerrycan():
    ob=phfit('metal_jerrycan',2500,height=0.46)
    return finish(empty_mb(),'hk_jerrycan',[ob],seed=30),meta('power','Fuel jerrycan (Poly Haven metal_jerrycan, CC0).')
# ------------------------------------------------------------------ decor
def rug():
    mb=MB(); mb.quad(V((-1.0,-0.75,0.006)),V((1.0,-0.75,0.006)),V((1.0,0.75,0.006)),V((-1.0,0.75,0.006)),'hk_rug',uv=FULL,grime=0)
    return finish(mb,'hk_rug',ao=False),meta('decor','Aso-oke stripe rug 2.0 x 1.5 m (own texture).')
def framed(name,w,h,tex,frame=(0.2,0.14,0.08)):
    mb=MB(); mb.box((-w/2,0.0,0),(w/2,0.03,h),'hk_laminate',tint=frame)
    mb.quad(V((-w/2+0.04,-0.001,0.04)),V((w/2-0.04,-0.001,0.04)),V((w/2-0.04,-0.001,h-0.04)),V((-w/2+0.04,-0.001,h-0.04)),tex,uv=FULL,grime=0)
    return mb
def art_small():
    return finish(framed('hk_art_small',0.4,0.5,'hk_print',(0.35,0.28,0.22)),'hk_art_small',ao=False),meta('decor','Framed print 0.4 x 0.5 m (own art); back on the wall plane.')
def art_big():
    return finish(framed('hk_art_big',0.95,0.8,'hk_adire',(0.25,0.2,0.16)),'hk_art_big',ao=False),meta('decor','Adire canvas 0.95 x 0.8 m (own art); back on the wall plane.')
def curtains():
    mb=MB(); W=1.5; H=2.3
    mb.cyl((-W/2,-0.08,H),0.012,W,'alu',seg=8,axis='X')
    for side in (-1,1):
        x0=side*W/2; x1=side*0.25; n=10
        for i in range(n):
            a=x0+(x1-x0)*i/n; b=x0+(x1-x0)*(i+1)/n; ya=-0.08+0.035*math.sin(i*math.pi/2); yb=-0.08+0.035*math.sin((i+1)*math.pi/2)
            mb.quad(V((a,ya,0.05)),V((b,yb,0.05)),V((b,yb,H)),V((a,ya,H)),'linen',tint=(0.62,0.26,0.2),grime=0.2)
            mb.quad(V((b,yb,0.05)),V((a,ya,0.05)),V((a,ya,H)),V((b,yb,H)),'linen',tint=(0.62,0.26,0.2),grime=0.2)
    return finish(mb,'hk_curtains',seed=31,ao=False),meta('decor','Pair of curtains on a rod, 1.5 x 2.3 m; back on the wall plane.')
def plant():
    ob=phfit('potted_plant_02',4000,height=1.05)
    return finish(empty_mb(),'hk_plant',[ob],seed=32),meta('decor','Potted plant (Poly Haven potted_plant_02, CC0).')
# ------------------------------------------------------------------ building pieces (sit in a wall opening; origin at the bottom centre of the opening, wall plane y=0, inside = -Y)
def window_burglar():
    mb=MB(); W=1.2; H=1.2; T=0.2
    mb.box((-W/2,-0.02,0),(W/2,0.02,0.05),'alu'); mb.box((-W/2,-0.02,H-0.05),(W/2,0.02,H),'alu')
    mb.box((-W/2,-0.02,0),(-W/2+0.05,0.02,H),'alu'); mb.box((W/2-0.05,-0.02,0),(W/2,0.02,H),'alu'); mb.box((-0.02,-0.02,0),(0.02,0.02,H),'alu')
    for half in (-1,1):
        for i in range(9):
            z=0.08+i*0.118; x0=half*0.03 if half>0 else -W/2+0.05; x1=W/2-0.05 if half>0 else -0.03
            mb.quad(V((x0,0.0,z)),V((x1,0.0,z)),V((x1,0.03,z+0.1)),V((x0,0.03,z+0.1)),'glass_louvre',grime=0)
            mb.quad(V((x1,0.0,z)),V((x0,0.0,z)),V((x0,0.03,z+0.1)),V((x1,0.03,z+0.1)),'glass_louvre',grime=0)
    # burglar-proof bars on the outside (+Y) + net
    for i in range(1,8): x=-W/2+i*W/8; mb.box((x-0.009,0.07,0.02),(x+0.009,0.088,H-0.02),'metal_paint',tint=(0.15,0.15,0.15))
    for z in (0.35,0.85): mb.box((-W/2,0.07,z),(W/2,0.088,z+0.02),'metal_paint',tint=(0.15,0.15,0.15))
    # sill + reveal
    mb.box((-W/2-0.05,-0.13,-0.03),(W/2+0.05,0.1,0.0),'concrete',tint=(0.85,0.85,0.83))
    return finish(mb,'kit_window_burglar',seed=40,ground=False),meta('kit','Louvre window 1.2 x 1.2 m, aluminium frame, glass blades, burglar-proof bars outside. Opening sill at z=0 (place at 0.95 m).',opening=[W,H])
def window_glass():
    mb=MB(); W=2.0; H=2.2
    for (a,b) in (((-W/2,0),(W/2,0.06)),((-W/2,H-0.06),(W/2,H))): mb.box((a[0],-0.03,a[1]),(b[0],0.03,b[1]),'metal_dark')
    for x in (-W/2,-0.03,W/2-0.06): mb.box((x,-0.03,0),(x+0.06,0.03,H),'metal_dark')
    for x0,x1 in ((-W/2+0.06,-0.03),(0.03,W/2-0.06)):
        mb.quad(V((x0,0,0.06)),V((x1,0,0.06)),V((x1,0,H-0.06)),V((x0,0,H-0.06)),'glass_clear',uv=FULL,grime=0)
    return finish(mb,'kit_window_glass',seed=41,ground=False,ao=False),meta('kit','Floor-to-ceiling aluminium + glass 2.0 x 2.2 m (place at 0.1 m).',opening=[W,H])
def door_panel():
    mb=MB(); W=0.9; H=2.1; T=(0.75,0.55,0.42)
    mb.box((-W/2-0.06,-0.1,0),(-W/2,0.1,H+0.06),'hk_laminate',tint=(0.55,0.42,0.32)); mb.box((W/2,-0.1,0),(W/2+0.06,0.1,H+0.06),'hk_laminate',tint=(0.55,0.42,0.32))
    mb.box((-W/2,-0.1,H),(W/2,0.1,H+0.06),'hk_laminate',tint=(0.55,0.42,0.32))
    mb.box((-W/2,-0.02,0.01),(W/2,0.02,H),'hk_laminate',tint=T)
    for z0,z1 in ((0.15,0.95),(1.1,1.95)):
        for x0,x1 in ((-0.36,-0.04),(0.04,0.36)): mb.box((x0,-0.03,z0),(x1,-0.02,z1),'hk_laminate',tint=(0.62,0.45,0.33))
    mb.box((0.32,-0.07,1.0),(0.38,-0.02,1.03),'alu'); mb.cyl((0.35,-0.06,1.12),0.012,0.04,'alu',seg=8,axis='Y')
    return finish(mb,'kit_door_panel',seed=42),meta('kit','Panelled hardwood door 0.9 x 2.1 m with frame (closed).',opening=[W+0.12,H+0.06])
def door_flush():
    mb=MB(); W=1.0; H=2.3
    mb.box((-W/2-0.04,-0.1,0),(-W/2,0.1,H+0.04),'metal_dark'); mb.box((W/2,-0.1,0),(W/2+0.04,0.1,H+0.04),'metal_dark'); mb.box((-W/2,-0.1,H),(W/2,0.1,H+0.04),'metal_dark')
    mb.box((-W/2,-0.025,0.01),(W/2,0.025,H),'hk_laminate',tint=(0.85,0.78,0.7))
    mb.box((0.36,-0.06,0.6),(0.38,-0.025,1.6),'chrome')
    return finish(mb,'kit_door_flush',seed=43),meta('kit','Modern flush door 1.0 x 2.3 m, wood-look veneer, long chrome pull.',opening=[W+0.08,H+0.04])
def ceiling_light():
    mb=MB(); mb.cyl((0,0,-0.05),0.16,0.05,'plastic',seg=20,tint=(0.97,0.97,0.96)); mb.cyl((0,0,-0.051),0.13,0.002,'emit_warm',seg=20)
    return finish(mb,'kit_ceiling_light',ground=False,ao=False),meta('kit','Round ceiling light (emit_warm), hangs below origin.')
def downlight():
    mb=MB(); mb.cyl((0,0,-0.01),0.07,0.01,'alu',seg=16); mb.cyl((0,0,-0.011),0.05,0.001,'emit_warm',seg=16)
    return finish(mb,'kit_downlight',ground=False,ao=False),meta('kit','POP-ceiling downlight.')
def pop_cornice():
    mb=MB(); L=1.0
    mb.quad(V((0,0,0)),V((L,0,0)),V((L,-0.12,-0.0)),V((0,-0.12,0)),'plaster_paint',tint=(0.97,0.97,0.96),grime=0)
    mb.quad(V((0,-0.12,0)),V((L,-0.12,0)),V((L,-0.12,-0.06)),V((0,-0.12,-0.06)),'plaster_paint',tint=(0.97,0.97,0.96),grime=0)
    mb.quad(V((0,-0.12,-0.06)),V((L,-0.12,-0.06)),V((L,0,-0.14)),V((0,0,-0.14)),'plaster_paint',tint=(0.97,0.97,0.96),grime=0)
    return finish(mb,'kit_pop_cornice',ground=False,ao=False),meta('kit','1 m POP cornice strip; wall plane y=0, ceiling z=0; scale X to length.')
def stairs():
    mb=MB(); n=14; W=1.0; R=0.2; G=0.27
    for i in range(n):
        mb.box((-W/2,i*G,0),(W/2,(i+1)*G,(i+1)*R),'hk_porcelain',tint=(1,1,1))
    for i in range(n):
        x=W/2; mb.cyl((x-0.03,i*G+G/2,(i+1)*R),0.012,0.9,'chrome',seg=6)
    mb.box((W/2-0.05,0,0.9+R),(W/2-0.01,n*G,0.94+R),'chrome') if False else None
    return finish(mb,'kit_stairs',seed=44),meta('kit','Straight stair 1.0 m wide, 14 risers to 2.8 m, going +Y, porcelain treads, chrome balusters.')
def gatehouse():
    mb=MB()
    mb.box((-0.9,-0.9,0),(0.9,0.9,2.6),'plaster_paint',tint=(0.92,0.92,0.9)); mb.box((-1.05,-1.05,2.6),(1.05,1.05,2.8),'plaster_paint',tint=(0.55,0.56,0.58))
    mb.quad(V((-0.6,-0.901,1.0)),V((0.6,-0.901,1.0)),V((0.6,-0.901,1.9)),V((-0.6,-0.901,1.9)),'glass',uv=FULL)
    return finish(mb,'kit_gatehouse',seed=45),meta('kit','Security post 1.8 x 1.8 x 2.8 m.')
def gate():
    mb=MB(); W=4.0; H=2.2
    for x in (-W/2-0.3,W/2): mb.box((x,-0.15,0),(x+0.3,0.15,H+0.3),'plaster_paint',tint=(0.55,0.56,0.58))
    mb.box((-W/2,-0.04,0.05),(W/2,0.04,H),'metal_paint',tint=(0.12,0.12,0.13))
    for i in range(1,20): x=-W/2+i*W/20; mb.box((x-0.01,-0.05,0.1),(x+0.01,-0.04,H-0.05),'metal_paint',tint=(0.2,0.2,0.21))
    return finish(mb,'kit_gate',seed=46),meta('kit','Sliding steel compound gate 4 m with rendered pillars.')

BUILDERS={
 'hk_foam_mattress':foam_mattress,'hk_spring_bed':spring_bed,'hk_mosquito_net':mosquito_net,'hk_wardrobe':wardrobe,
 'hk_kerosene_stove':kerosene_stove,'hk_gas_cooker':gas_cooker,'hk_small_fridge':small_fridge,'hk_freezer':freezer,'hk_dining_set':dining_set,
 'hk_wc_shower':wc_shower,'hk_bucket_bowl':bucket_bowl,
 'hk_plastic_chair':plastic_chair,'hk_sofa':sofa,'hk_armchair':armchair,'hk_standing_fan':standing_fan,'hk_fan_blades':fan_blades_std,
 'hk_ceiling_fan':ceiling_fan,'hk_ceiling_fan_blades':ceiling_fan_blades,'hk_split_ac':split_ac,
 'hk_tv_stand':lambda:tv_stand('hk_tv_stand'),'hk_console_tv':lambda:tv_stand('hk_console_tv',True),'hk_speaker':speaker,
 'hk_mirror':mirror,'hk_laptop_desk':laptop_desk,'hk_guitar':guitar,'hk_dumbbells':dumbbells,'hk_bookshelf':bookshelf,
 'hk_rechargeable_lamp':rechargeable_lamp,'hk_floor_lamp':floor_lamp,
 'hk_petrol_gen':petrol_gen,'hk_diesel_gen':diesel_gen,'hk_inverter':inverter,'hk_solar_kit':solar_kit,'hk_jerrycan':jerrycan,
 'hk_rug':rug,'hk_art_small':art_small,'hk_art_big':art_big,'hk_curtains':curtains,'hk_plant':plant,
 'kit_window_burglar':window_burglar,'kit_window_glass':window_glass,'kit_door_panel':door_panel,'kit_door_flush':door_flush,
 'kit_ceiling_light':ceiling_light,'kit_downlight':downlight,'kit_pop_cornice':pop_cornice,'kit_stairs':stairs,'kit_gatehouse':gatehouse,'kit_gate':gate,
}
