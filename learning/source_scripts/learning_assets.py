# Lagos Life learning kit (Step 08): Akoka Learning Centre lecture hall + the sketchbook easel.
# Procedural Blender builders (envlib MB) and decimated Poly Haven CC0 models (SchoolChair_01, classic_laptop,
# office_notepads, stationery_supplies, wall_clock, mounted_fluorescent_lights). Blender Z up; fronts face -Y.
# Metres; origin at floor centre of the footprint.
import math, json
from mathutils import Vector as V, Matrix
import bpy
from envlib import *
import envlib
from phlib import ph_load, ph_place, join
envlib.META.update(json.load(open('/workspace/workkit/tex/tex_meta.json')))
envlib.MAT_FLAT.update({'lk_board':((0.97,0.97,0.96),0.25,0.0),'lk_slide':((1,1,1),0.3,0.0),'lk_paper':((0.96,0.95,0.92),0.9,0.0),
  'glass_clear':((0.8,0.9,0.92),0.05,0.0),'screen_off':((0.02,0.02,0.025),0.15,0.0)})
import work_assets
FULL=('uvs',[(0,0),(1,0),(1,1),(0,1)])

def finish(mb,name,objs=(),seed=0,grime=0.5,damp_h=0.0,ground=True,smooth=35,ao=True):
    ob=build_object(mb,name,mat_lib,merge=True)
    ob=join([ob,*objs],name) if objs else ob
    shade(ob,smooth)
    if ao: bake_ao_grime(ob,grime_amt=grime,damp_h=damp_h,seed=seed,ground=ground)
    return ob
def ph(pid,tris,loc=(0,0,0),rotz=0.0,scale=1.0,tint=None):
    return ph_place(ph_load(pid,target_tris=tris),loc,rotz,scale,tint=tint)
def meta(cat,notes,**k): return dict(category=cat,notes=notes,**k)
WOOD=(0.62,0.45,0.32)

# ------------------------------------------------------------------ hall shell + tiers
def hall_room():
    ob,m=work_assets.room('lk_hall_room',10.0,9.0,3.8,'terrazzo',(0.95,0.92,0.84),band_tint=(0.2,0.36,0.46),band_h=1.0,lights=4)
    m['notes']='Lecture hall shell 10 x 9 x 3.8 m, open toward -Y (camera side), terrazzo floor, cream walls with a blue gloss dado, door back-right, louvre window left, four fluorescent fittings.'
    return ob,m
def tiers():
    # stage at the back wall (+Y) and three seating tiers stepping up toward -Y (the camera side)
    mb=MB()
    mb.box((-5,2.8,0),(5,4.5,0.2),'wood_floor',tint=(0.9,0.85,0.8))
    mb.box((-5,2.78,0),(5,2.8,0.2),'metal_paint',tint=(0.25,0.22,0.2))
    for k in range(1,4):
        zd=-1.6+1.1*k          # three.js z of row k desk; blender y = -z
        y_front=-(zd-0.35)     # tier front edge (toward the stage)
        mb.box((-5,-4.5,0.2*(k-1)),(5,y_front,0.2*k),'wood_floor',tint=(0.86,0.8,0.74))
        mb.box((-5,y_front,0.2*(k-1)),(5,y_front+0.012,0.2*k),'metal_paint',tint=(0.25,0.22,0.2))
        mb.box((-5,y_front-0.04,0.2*k),(5,y_front+0.012,0.2*k+0.01),'alu')  # nosing
    return finish(mb,'lk_tiers',seed=81,grime=0.6),meta('learning','Stage (1.7 m deep, 0.2 m) against the back wall and three 0.2 m seating tiers stepping up toward the camera; row k desk at three z = -1.6 + 1.1k, floor 0.2k.')
# ------------------------------------------------------------------ bench row (desk + 4 chairs)
def bench():
    mb=MB(); L=3.0
    mb.box((-L/2,-0.62,0.72),(L/2,-0.2,0.75),'hk_laminate',tint=(1,0.95,0.88))          # writing top
    mb.box((-L/2,-0.64,0.05),(L/2,-0.6,0.72),'hk_laminate',tint=(0.85,0.78,0.7))         # modesty panel (faces the stage)
    mb.box((-L/2,-0.6,0.52),(L/2,-0.25,0.54),'metal_paint',tint=(0.2,0.2,0.21))           # book shelf
    for x in (-L/2,-0.02,L/2-0.04):
        mb.box((x,-0.6,0),(x+0.04,-0.24,0.72),'metal_paint',tint=(0.2,0.2,0.21))
    objs=[]
    seats=[]
    for i in range(4):
        x=-L/2+L*(i+0.5)/4
        objs.append(ph('SchoolChair_01',1400,(x,0.12,0),rotz=math.pi))
        seats.append([round(x,3),0.12,0.45])
    # notebooks + pens on some places
    objs.append(ph('office_notepads',300,(-1.12,-0.42,0.75),rotz=0.15,scale=0.45))
    objs.append(ph('office_notepads',300,(0.4,-0.4,0.75),rotz=-0.2,scale=0.45))
    objs.append(ph('stationery_supplies',300,(1.2,-0.5,0.75),scale=0.7))
    return finish(mb,'lk_bench',objs,seed=82,grime=0.5),meta('learning','Lecture bench 3.0 m: laminate writing desk + 4 school chairs; students sit at seats (x, y, seat z) facing -Y.',seats=seats)
# ------------------------------------------------------------------ front of house
def lectern():
    mb=MB(); T=WOOD
    mb.box((-0.33,-0.22,0),(0.33,0.22,0.06),'wood',tint=tuple(c*0.8 for c in T))
    mb.box((-0.26,-0.18,0.06),(0.26,0.18,1.0),'wood',tint=T)
    n0=len(mb.faces); mb.box((-0.34,-0.3,0),(0.34,0.3,0.035),'wood',tint=tuple(c*0.9 for c in T)); mb.transform(Matrix.Translation(V((0,0,1.04)))@Matrix.Rotation(-0.3,4,'X'),n0)
    mb.box((-0.2,-0.185,0.55),(0.2,-0.18,0.8),'metal_paint',tint=(0.85,0.7,0.25))       # brass plaque
    mb.cyl((0.22,0.1,1.08),0.006,0.32,'metal_dark',seg=6); mb.cyl((0.22,0.1,1.40),0.018,0.05,'rubber',seg=10)  # gooseneck mic
    return finish(mb,'lk_lectern',[ph('office_notepads',300,(-0.08,0.0,1.09),rotz=0.1,scale=0.42)],seed=83),meta('learning','Hardwood lectern with brass plaque and gooseneck mic; front faces -Y, lecturer stands at +Y.')
def whiteboard():
    mb=MB(); W=3.2; H=1.3
    mb.box((-W/2-0.03,0,0),(W/2+0.03,0.03,H+0.06),'alu')
    mb.quad(V((-W/2,-0.002,0.03)),V((W/2,-0.002,0.03)),V((W/2,-0.002,H+0.03)),V((-W/2,-0.002,H+0.03)),'lk_board',uv=FULL,grime=0)
    mb.box((-W/2,-0.09,-0.01),(W/2,0.03,0.025),'alu')
    for i,(x,c) in enumerate(((-1.0,(0.1,0.2,0.7)),(-0.9,(0.75,0.1,0.1)),(-0.8,(0.05,0.05,0.05)))): mb.cyl((x,-0.05,0.04),0.009,0.12,'plastic',seg=8,axis='X',tint=c)
    mb.box((1.0,-0.08,0.025),(1.14,-0.03,0.06),'fabric',tint=(0.2,0.2,0.22))
    return finish(mb,'lk_whiteboard',seed=84,ground=False),meta('learning','Wall whiteboard 3.2 x 1.3 m (material lk_board takes a runtime canvas: lesson notes); mount base at ~0.9 m. Back at y=+0.03.')
def screen():
    mb=MB(); W=2.4; H=1.5
    mb.cyl((-W/2-0.1,0.0,H+0.25),0.05,W+0.2,'plastic',seg=12,axis='X',tint=(0.92,0.92,0.92))
    mb.quad(V((-W/2-0.06,-0.003,0.0)),V((W/2+0.06,-0.003,0.0)),V((W/2+0.06,-0.003,H+0.2)),V((-W/2-0.06,-0.003,H+0.2)),'fabric',tint=(0.05,0.05,0.05),grime=0)
    mb.quad(V((-W/2,-0.006,0.08)),V((W/2,-0.006,0.08)),V((W/2,-0.006,H+0.08)),V((-W/2,-0.006,H+0.08)),'lk_slide',uv=FULL,grime=0)
    mb.box((-W/2-0.06,-0.02,-0.03),(W/2+0.06,0.01,0.0),'alu')
    return finish(mb,'lk_screen',seed=85,ground=False,ao=False),meta('learning','Pull-down projector screen 2.4 x 1.5 m picture (material lk_slide takes the runtime slide canvas); hang base at ~1.3 m.')
def projector_trolley():
    mb=MB()
    mb.box((-0.3,-0.25,0.7),(0.3,0.25,0.73),'metal_paint',tint=(0.2,0.2,0.22)); mb.box((-0.3,-0.25,0.2),(0.3,0.25,0.22),'metal_paint',tint=(0.2,0.2,0.22))
    for x in (-0.28,0.26):
        for y in (-0.23,0.21): mb.box((x,y,0.05),(x+0.02,y+0.02,0.7),'alu'); mb.cyl((x+0.01,y+0.01,0.0),0.03,0.05,'rubber',seg=10)
    mb.box((-0.15,-0.11,0.73),(0.15,0.11,0.83),'plastic',tint=(0.92,0.92,0.9))   # projector body
    mb.cyl((0.08,-0.11,0.78),0.032,0.03,'glass',seg=14,axis='Y'); mb.cyl((0.08,-0.115,0.78),0.04,0.01,'metal_dark',seg=14,axis='Y')
    mb.box((-0.12,-0.112,0.8),(-0.02,-0.11,0.81),'emit_cool')
    mb.box((-0.1,0.11,0.74),(-0.02,0.4,0.75),'cable')
    return finish(mb,'lk_projector_trolley',[ph('classic_laptop',1200,(0.0,0.0,0.22),rotz=0.0,scale=1.0)],seed=86),meta('learning','AV trolley with a projector (lens faces -Y) and a laptop on the lower shelf.')
def noticeboard():
    mb=MB(); W=1.2; H=0.9
    mb.box((-W/2-0.04,0,0),(W/2+0.04,0.03,H+0.08),'wood',tint=WOOD)
    mb.quad(V((-W/2,-0.002,0.04)),V((W/2,-0.002,0.04)),V((W/2,-0.002,H+0.04)),V((-W/2,-0.002,H+0.04)),'hessian',tint=(0.75,0.55,0.35),grime=0.2)
    import random; r=random.Random(8)
    cols=[(0.98,0.97,0.94),(0.98,0.93,0.55),(0.7,0.88,0.98),(0.98,0.97,0.94),(0.98,0.75,0.8),(0.98,0.97,0.94)]
    for i,c in enumerate(cols):
        x=-0.48+(i%3)*0.36+r.uniform(-0.03,0.03); z=0.15+(i//3)*0.4+r.uniform(-0.03,0.03); w=0.24 if i%2 else 0.2; h=0.3 if i%2 else 0.22
        n0=len(mb.faces); mb.quad(V((-w/2,0,-h/2)),V((w/2,0,-h/2)),V((w/2,0,h/2)),V((-w/2,0,h/2)),'lk_paper',tint=c,uv=FULL,grime=0.1)
        mb.transform(Matrix.Translation(V((x,-0.006-i*0.0005,z+h/2)))@Matrix.Rotation(r.uniform(-0.08,0.08),4,'Y'),n0)
        mb.cyl((x,-0.012,z+h-0.02),0.008,0.008,'plastic',seg=6,axis='Y',tint=(0.85,0.1,0.1))
    return finish(mb,'lk_noticeboard',seed=87,ground=False),meta('learning','Cork noticeboard 1.2 x 0.9 m with pinned notices; mount base at ~1.1 m.')
def easel():
    # Sketchbook practice spot (Creativity): pine A-frame easel with an open sketch pad, stool, pencil cup.
    mb=MB(); T=(0.85,0.7,0.5)
    for s in (-1,1):
        n0=len(mb.faces); mb.box((-0.02,-0.015,0),(0.02,0.015,1.55),'wood',tint=T); mb.transform(Matrix.Translation(V((s*0.28,-0.05,0)))@Matrix.Rotation(-s*0.14,4,'Y')@Matrix.Rotation(-0.12,4,'X'),n0)
    n0=len(mb.faces); mb.box((-0.02,-0.015,0),(0.02,0.015,1.45),'wood',tint=T); mb.transform(Matrix.Translation(V((0,0.6,0)))@Matrix.Rotation(0.32,4,'X'),n0)
    mb.box((-0.32,-0.09,0.62),(0.32,0.02,0.65),'wood',tint=T)   # ledge
    # sketch pad: card back + paper with a few charcoal strokes
    n0=len(mb.faces)
    mb.box((-0.24,0,0),(0.24,0.012,0.64),'paint_wood',tint=(0.55,0.42,0.3))
    mb.quad(V((-0.22,-0.002,0.02)),V((0.22,-0.002,0.02)),V((0.22,-0.002,0.62)),V((-0.22,-0.002,0.62)),'lk_paper',uv=FULL,grime=0.05)
    for (x0,z0,x1,z1) in ((-0.15,0.18,0.12,0.22),(-0.1,0.3,0.14,0.42),(-0.16,0.46,0.02,0.5),(0.03,0.12,0.06,0.45)):
        L=math.hypot(x1-x0,z1-z0); a=math.atan2(z1-z0,x1-x0); m0=len(mb.faces)
        mb.quad(V((0,-0.004,-0.003)),V((L,-0.004,-0.003)),V((L,-0.004,0.003)),V((0,-0.004,0.003)),'charcoal',grime=0)
        mb.transform(Matrix.Translation(V((x0,0,z0)))@Matrix.Rotation(-a,4,'Y'),m0)
    mb.transform(Matrix.Translation(V((0,-0.045,0.65)))@Matrix.Rotation(-0.12,4,'X'),n0)
    # stool in front
    mb.cyl((0,-0.55,0.44),0.16,0.03,'wood',seg=16,tint=T)
    for k in range(3):
        a=k*2.094; mb.box((0.11*math.cos(a)-0.015,-0.55+0.11*math.sin(a)-0.015,0),(0.11*math.cos(a)+0.015,-0.55+0.11*math.sin(a)+0.015,0.44),'wood',tint=T)
    mb.cyl((0.25,-0.05,0.65),0.025,0.08,'ceramic',seg=10,tint=(0.3,0.45,0.6))
    for k in range(3): mb.cyl((0.24+0.01*k,-0.05,0.7),0.003,0.08,'paint_wood',seg=5,tint=(0.9,0.75,0.2))
    return finish(mb,'lk_easel',seed=88),meta('furniture','Sketchbook easel 0.7 x 0.9 m: pine A-frame, open sketch pad with charcoal strokes, stool in front (artist sits at -Y facing +Y), pencil cup.')
def wall_clock():
    o=ph('wall_clock',900,(0,0,0),rotz=0.0,scale=1.0)
    mb=MB(); mb.box((-0.001,-0.001,0),(0.001,0.001,0.001),'metal_dark')
    return finish(mb,'lk_wall_clock',[o],seed=89,ao=False),meta('learning','Wall clock (Poly Haven wall_clock, CC0).')

BUILDERS={'lk_hall_room':hall_room,'lk_tiers':tiers,'lk_bench':bench,'lk_lectern':lectern,'lk_whiteboard':whiteboard,'lk_screen':screen,
 'lk_projector_trolley':projector_trolley,'lk_noticeboard':noticeboard,'lk_easel':easel,'lk_wall_clock':wall_clock}
