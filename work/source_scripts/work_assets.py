# Lagos Life work-scene kit: procedural Blender builders + decimated Poly Haven CC0 props.
# Blender coords: Z up, asset fronts face -Y (= +Z in three.js after the glTF Y-up export). Metres. Origin on the ground.
import math, random, json
from mathutils import Vector as V, Matrix
from envlib import *
import envlib
from phlib import ph_load, ph_place, join

# work textures (tile sizes) and the 2048 sign atlas
envlib.META.update(json.load(open('/workspace/workkit/tex/tex_meta.json')))
_WR=json.load(open('/workspace/workkit/tex/work_rects.json'))
def wr(name,flip=False,sub=None):
    u0,v0,u1,v1=[c/2048 for c in _WR[name]]
    if sub:
        sx0,sy0,sx1,sy1=sub; du=u1-u0; dv=v1-v0; u0,u1=u0+du*sx0,u0+du*sx1; v0,v1=v0+dv*sy0,v0+dv*sy1
    bl=(u0,1-v1); br=(u1,1-v1); tr=(u1,1-v0); tl=(u0,1-v0)
    if flip: bl,br,tr,tl=br,bl,tl,tr
    return ('uvs',[bl,br,tr,tl])
envlib.MAT_FLAT.update({'mirror':((0.92,0.93,0.94),0.04,1.0),'glass_clear':((0.8,0.9,0.92),0.05,0.0),'screen':((1,1,1),0.3,0.0),'atlas_work':((1,1,1),0.7,0.0)})

def finish(mb,name,objs=(),seed=0,grime=1.0,damp_h=0.6,ground=True,smooth=35,merge=True,ao=True):
    ob=build_object(mb,name,mat_lib,merge=merge)
    ob=join([ob,*objs],name)
    shade(ob,smooth)
    if ao: bake_ao_grime(ob,grime_amt=grime,damp_h=damp_h,seed=seed,ground=ground)
    return ob
def flip(mb,n0):
    for f in mb.faces[n0:]:
        f['p']=list(reversed(f['p']))
        if f['uv'] and f['uv'][0]=='uvs': f['uv']=('uvs',list(reversed(f['uv'][1])))
def tube(mb,pts,r,mat,sides=6,tint=WHITE,cap=False,**k):
    pts=[V(p) for p in pts]; rings=[]
    for i,p in enumerate(pts):
        d=(pts[min(i+1,len(pts)-1)]-pts[max(i-1,0)]).normalized()
        a=d.orthogonal().normalized(); b=d.cross(a)
        rings.append([p+(a*math.cos(2*math.pi*j/sides)+b*math.sin(2*math.pi*j/sides))*r for j in range(sides)])
    for i in range(len(rings)-1):
        for j in range(sides):
            jj=(j+1)%sides; mb.quad(rings[i][j],rings[i][jj],rings[i+1][jj],rings[i+1][j],mat,tint=tint,grime=0,**k)
    if cap: mb.face(list(reversed(rings[0])),mat,tint=tint); mb.face(rings[-1],mat,tint=tint)
def catenary(p0,p1,sag,n=16):
    p0=V(p0); p1=V(p1); out=[]
    for i in range(n+1):
        t=i/n; p=p0.lerp(p1,t); p.z-=sag*4*t*(1-t); out.append(p)
    return out
def panel(mb,x0,x1,y,z0,z1,region,mat='atlas_work',facing=-1,**k):
    """sign quad in the XZ plane at depth y; facing -1 => normal -Y (front)."""
    a=V((x0,y,z0)); b=V((x1,y,z0)); c=V((x1,y,z1)); d=V((x0,y,z1))
    if facing<0: mb.quad(a,b,c,d,mat,uv=wr(region),grime=0.2,**k)
    else: mb.quad(b,a,d,c,mat,uv=wr(region),grime=0.2,**k)
def panel_x(mb,x,y0,y1,z0,z1,region,mat='atlas_work',facing=1,**k):
    """sign quad in the YZ plane at x; facing +1 => normal +X."""
    if facing>0: mb.quad(V((x,y0,z0)),V((x,y1,z0)),V((x,y1,z1)),V((x,y0,z1)),mat,uv=wr(region),grime=0.2,**k)
    else: mb.quad(V((x,y1,z0)),V((x,y0,z0)),V((x,y0,z1)),V((x,y1,z1)),mat,uv=wr(region),grime=0.2,**k)
def top_panel(mb,x0,x1,y0,y1,z,region,mat='atlas_work',rot=0,**k):
    pts=[V((x0,y0,z)),V((x1,y0,z)),V((x1,y1,z)),V((x0,y1,z))]
    uv=wr(region); uvs=uv[1][rot:]+uv[1][:rot]
    mb.quad(*pts,mat,uv=('uvs',uvs),grime=0.1,**k)
def ph(pid,tris,loc=(0,0,0),rotz=0.0,scale=1.0,tint=None,rotx=0.0,pick=None):
    return ph_place(ph_load(pid,target_tris=tris,pick=pick),loc,rotz,scale,tint=tint,rotx=rotx)
def legs4(mb,x0,x1,y0,y1,z1,s,mat,tint):
    for x in (x0,x1-s):
        for y in (y0,y1-s): mb.box((x,y,0),(x+s,y+s,z1),mat,tint=tint)

# ===================================================== rooms (3 walls + floor + ceiling, open toward -Y)
def room(name,W,D,H,floor,wall_tint,band_tint=None,band_h=1.1,window=True,ceiling_tint=(0.93,0.92,0.88),lights=2,door=True):
    mb=MB(); T=0.15
    # floor slab and skirting
    grid_quad(mb,V((-W/2,-D/2,0)),V((1,0,0)),V((0,1,0)),W,D,floor,cu=1.0,cv=1.0,tint=WHITE)
    # back wall (y=+D/2) inner face, normal -Y
    def wall_face(o,u,L,n_tint,cut=None):
        ops=[]
        if cut: ops=[cut]
        wall(mb,o,u,V((0,0,0)),L,H,'plaster_paint',tint=n_tint,openings=ops,reveal=0.15,extra_z=(0.12,band_h))
    back_ops=None
    wall(mb,V((-W/2,D/2,0)),V((1,0,0)),V((0,-1,0)),W,H,'plaster_paint',tint=wall_tint,extra_z=(0.12,band_h),
         openings=[dict(x0=W-1.6,x1=W-0.7,z0=0,z1=2.1,kind='door',reveal=0.15)] if door else [])
    # left wall x=-W/2 running from front(-D/2) to back(+D/2), inner normal +X
    lops=[dict(x0=D/2-1.0-1.2,x1=D/2-1.0,z0=1.0,z1=2.1,kind='window',reveal=0.15,fill=None)] if window else []
    wall(mb,V((-W/2,-D/2,0)),V((0,1,0)),V((1,0,0)),D,H,'plaster_paint',tint=wall_tint,extra_z=(0.12,band_h),openings=lops)
    # right wall x=+W/2 from back to front, inner normal -X
    wall(mb,V((W/2,D/2,0)),V((0,-1,0)),V((-1,0,0)),D,H,'plaster_paint',tint=wall_tint,extra_z=(0.12,band_h))
    # wall faces were emitted with outward normal convention n; make them face into the room
    # (wall() builds quads a,b,c,d along ud/up: normal = ud x up). Fix orientation per wall:
    # back wall ud=+X up=+Z -> normal -Y (into room) OK; left wall ud=+Y -> normal +X OK; right wall ud=-Y -> normal -X OK.
    if band_tint:
        for (o,u,L) in ((V((-W/2,D/2-0.005,0)),V((1,0,0)),W),(V((-W/2+0.005,-D/2,0)),V((0,1,0)),D),(V((W/2-0.005,D/2,0)),V((0,-1,0)),L if False else D)):
            pass
    # oil-paint dado band (lower wall) drawn as a thin overlay with gloss paint
    if band_tint:
        def band(o,u,L,skip=None):
            xs=[0,L]
            if skip: xs=[0,skip[0],skip[1],L]
            for i in range(0,len(xs),2):
                a=o+u*xs[i]; b=o+u*xs[i+1]
                mb.quad(a,b,b+V((0,0,band_h)),a+V((0,0,band_h)),'metal_paint',tint=band_tint,grime=0.7)
        band(V((-W/2,D/2-0.01,0)),V((1,0,0)),W,skip=(W-1.6,W-0.7) if door else None)
        band(V((-W/2+0.01,-D/2,0)),V((0,1,0)),D)
        band(V((W/2-0.01,D/2,0)),V((0,-1,0)),D)
    # skirting
    for (a,b) in (((-W/2,D/2-0.02),(W/2,D/2-0.02)),):
        pass
    # window: frame + louvre blades + burglar bars, seen from inside
    if window:
        y0=D/2-2.2; y1=D/2-1.0; x=-W/2
        for i in range(9):
            z=1.06+i*0.115; mb.quad(V((x-0.07,y0,z)),V((x-0.07,y1,z)),V((x-0.03,y1,z+0.09)),V((x-0.03,y0,z+0.09)),'glass_louvre',grime=0)
        for yy in [y0+0.2*i for i in range(1,6)]: mb.box((x-0.02,yy-0.008,1.0),(x+0.0,yy+0.008,2.1),'metal_dark')
        # bright exterior behind the window
        mb.quad(V((x-0.3,y1,0.9)),V((x-0.3,y0,0.9)),V((x-0.3,y0,2.2)),V((x-0.3,y1,2.2)),'emit_cool',grime=0,ao=0)
    # door leaf (closed, wood) in the back-wall opening
    if door:
        dx0=-W/2+W-1.6; dx1=-W/2+W-0.7
        mb.quad(V((dx0,D/2+0.0,0)),V((dx1,D/2+0.0,0)),V((dx1,D/2+0.0,2.1)),V((dx0,D/2+0.0,2.1)),'paint_wood',tint=(0.42,0.3,0.22))
        mb.box((dx1-0.12,D/2-0.04,1.0),(dx1-0.06,D/2,1.03),'alu')
    # ceiling (normal down)
    grid_quad(mb,V((-W/2,D/2,H)),V((1,0,0)),V((0,-1,0)),W,D,'plaster_paint',cu=1.5,cv=1.5,tint=ceiling_tint)
    # fluorescent fittings
    for i in range(lights):
        cx=-W/2+W*(i+0.5)/lights; cy=0.2
        mb.box((cx-0.62,cy-0.07,H-0.06),(cx+0.62,cy+0.07,H),'metal_paint',tint=(0.92,0.92,0.9))
        mb.cyl((cx-0.6,cy,H-0.075),0.016,1.2,'emit_cool',seg=8,axis='X',cap_top=True,cap_bot=True)
    # skirting boards
    for (o,u,L) in ((V((-W/2,D/2-0.015,0)),V((1,0,0)),W),(V((-W/2+0.015,-D/2,0)),V((0,1,0)),D),(V((W/2-0.015,D/2,0)),V((0,-1,0)),D)):
        a=o; b=o+u*L; mb.quad(a,b,b+V((0,0,0.1)),a+V((0,0,0.1)),'metal_paint',tint=(0.25,0.22,0.2),grime=0.5)
    # electrical: switch + socket on the back wall
    mb.box((-W/2+0.5,D/2-0.02,1.3),(-W/2+0.58,D/2,1.4),'plastic',tint=(0.95,0.95,0.92))
    mb.box((-W/2+0.5,D/2-0.02,0.3),(-W/2+0.58,D/2,0.38),'plastic',tint=(0.95,0.95,0.92))
    obj=finish(mb,name,[],seed=hash(name)%97,grime=0.8,damp_h=0.5)
    return obj,dict(category='room',notes=f'Open-front room shell {W} x {D} x {H} m (no -Y wall). Floor {floor}. Origin at floor centre. Door on the back wall right, louvre window on the left wall, two fluorescent fittings.',size=[W,D,H])

# ===================================================== POS
def pos_terminal(mb,cx,cy,cz,rot=0.15):
    n0=len(mb.faces)
    mb.box((-0.04,-0.09,0),(0.04,0.09,0.025),'plastic',tint=(0.08,0.08,0.09))
    mb.box((-0.035,0.0,0.025),(0.035,0.085,0.032),'plastic',tint=(0.1,0.1,0.11))
    top_panel(mb,-0.033,0.033,0.008,0.082,0.0325,'pos_screen','screen',rot=0)
    top_panel(mb,-0.034,0.034,-0.085,-0.005,0.0255,'pos_keys','atlas_work')
    mb.box((-0.03,0.085,0.005),(0.03,0.1,0.02),'plastic',tint=(0.85,0.85,0.82))  # receipt roll slot
    mb.transform(Matrix.Translation(V((cx,cy,cz)))@Matrix.Rotation(rot,4,'Z'),n0)
def cash_stack(mb,x,y,z,region,n=6,rot=0.0):
    n0=len(mb.faces)
    h=0.002*n
    mb.box((-0.075,-0.035,0),(0.075,0.035,h),'paint_wood',tint=(0.72,0.6,0.75) if region=='cash_note' else (0.85,0.72,0.5))
    top_panel(mb,-0.075,0.075,-0.035,0.035,h+0.0005,region)
    mb.box((-0.012,-0.036,-0.0005),(0.012,0.036,h+0.001),'paint_wood',tint=(0.9,0.88,0.8))  # band
    mb.transform(Matrix.Translation(V((x,y,z)))@Matrix.Rotation(rot,4,'Z'),n0)
def pos_stand():
    mb=MB(); W=0.9; Dd=0.55; Hh=0.74
    # folding table: blue laminate top on steel legs
    mb.box((-W/2,-Dd/2,Hh-0.025),(W/2,Dd/2,Hh),'plastic',tint=(0.08,0.32,0.62))
    mb.box((-W/2+0.02,-Dd/2+0.02,Hh-0.07),(W/2-0.02,-Dd/2+0.04,Hh-0.025),'steel_galv')
    mb.box((-W/2+0.02,Dd/2-0.04,Hh-0.07),(W/2-0.02,Dd/2-0.02,Hh-0.025),'steel_galv')
    for sx in (-1,1):
        tube(mb,[(sx*(W/2-0.06),-Dd/2+0.05,0),(sx*(W/2-0.06),-Dd/2+0.05,Hh-0.03)],0.014,'steel_galv',sides=6)
        tube(mb,[(sx*(W/2-0.06),Dd/2-0.05,0),(sx*(W/2-0.06),Dd/2-0.05,Hh-0.03)],0.014,'steel_galv',sides=6)
        tube(mb,[(sx*(W/2-0.06),-Dd/2+0.05,0.18),(sx*(W/2-0.06),Dd/2-0.05,0.18)],0.01,'steel_galv',sides=5)
    # branded front skirt (vinyl banner)
    panel(mb,-W/2,W/2,-Dd/2-0.005,Hh-0.42,Hh-0.03,'pos_aframe',sub=None) if False else None
    mb.quad(V((-W/2,-Dd/2-0.004,Hh-0.42)),V((W/2,-Dd/2-0.004,Hh-0.42)),V((W/2,-Dd/2-0.004,Hh-0.03)),V((-W/2,-Dd/2-0.004,Hh-0.03)),'atlas_work',uv=wr('pos_aframe',sub=(0,0,1,0.22)),grime=0.3)
    pos_terminal(mb,0.12,-0.05,Hh,rot=0.2)
    pos_terminal(mb,0.3,0.12,Hh,rot=-0.3)
    cash_stack(mb,-0.25,-0.08,Hh,'cash_note',8,0.1); cash_stack(mb,-0.25,0.06,Hh,'cash_note_b',5,-0.12); cash_stack(mb,-0.06,0.13,Hh,'cash_note',3,0.6)
    # exercise book ledger (open) + biro
    mb.box((-0.38,0.1,Hh),(-0.18,0.24,Hh+0.006),'paint_wood',tint=(0.95,0.95,0.92))
    mb.quad(V((-0.38,0.1,Hh+0.0065)),V((-0.18,0.1,Hh+0.0065)),V((-0.18,0.24,Hh+0.0065)),V((-0.38,0.24,Hh+0.0065)),'atlas_work',uv=wr('parcel_label'),grime=0)
    tube(mb,[(-0.2,0.12,Hh+0.012),(-0.33,0.2,Hh+0.012)],0.004,'plastic',sides=5,tint=(0.1,0.2,0.7))
    # smartphone face-down + calculator
    mb.box((0.0,-0.2,Hh),(0.075,-0.05,Hh+0.009),'plastic',tint=(0.05,0.05,0.06))
    stat=ph('stationery_supplies',600,(-0.02,0.2,Hh+0.07),rotz=0.3,scale=0.8)
    obj=finish(mb,'work_pos_stand',[stat],seed=3,grime=0.9,damp_h=0.25)
    return obj,dict(category='work',notes='POS agent table 0.9 x 0.55 m, top 0.74 m: two card terminals, cash bundles, ledger, phone. Agent stands/sits on the +Y side; customers on -Y (front).',stand=[0,0.55])
def pos_aframe():
    mb=MB(); W=0.6; H=0.95; t=0.6
    for s in (-1,1):
        n0=len(mb.faces)
        # board leaning: front face at -Y tilted
        mb.box((-W/2,-0.012,0),(W/2,0.012,H),'paint_wood',tint=(0.85,0.85,0.82))
        mb.transform(Matrix.Translation(V((0,-s*0.18,0)))@Matrix.Rotation(s*0.2,4,'X'),n0)
    # printed faces (front and back)
    for s in (-1,1):
        n0=len(mb.faces)
        panel(mb,-W/2+0.02,W/2-0.02,-0.0135,0.04,H-0.03,'pos_aframe',facing=-1)
        if s>0: mb.transform(Matrix.Rotation(math.pi,4,'Z'),n0)
        mb.transform(Matrix.Translation(V((0,-s*0.18,0)))@Matrix.Rotation(s*0.2,4,'X'),n0)
    obj=finish(mb,'work_pos_aframe',[],seed=4,grime=1.0,damp_h=0.3)
    return obj,dict(category='work',notes='KoboPay POS A-frame sidewalk board, 0.6 m wide, 0.93 m tall, printed both sides.')

# ===================================================== market
def produce_pile(mb_objs,kind,cx,cy,cz,n,rad,seed,tris):
    rnd=random.Random(seed)
    lib={'onion':'yellow_onion','yam':'sweet_potato','lime':'food_lime_01'}[kind]
    out=[]
    for i in range(n):
        a=rnd.uniform(0,6.283); r=rad*math.sqrt(rnd.random()); layer=0 if i<n*0.65 else 1
        z=cz+layer*0.055; rr=r*(1-0.5*layer)
        out.append(ph(lib,tris,(cx+rr*math.cos(a),cy+rr*math.sin(a),z),rotz=rnd.uniform(0,6.28),rotx=rnd.uniform(-0.4,0.4) if kind!='yam' else 1.5708,scale=rnd.uniform(0.9,1.15)*(1.4 if kind=='yam' else 1)))
    return out
def tomatoes(mb,cx,cy,cz,n,rad,seed,col=(0.78,0.08,0.05)):
    rnd=random.Random(seed)
    for i in range(n):
        a=rnd.uniform(0,6.283); r=rad*math.sqrt(rnd.random()); layer=0 if i<n*0.6 else 1
        s=rnd.uniform(0.028,0.036); z=cz+s+layer*0.045
        mb.cyl((cx+r*(1-0.5*layer)*math.cos(a),cy+r*(1-0.5*layer)*math.sin(a),z-s*0.9),s,s*1.7,'plastic',seg=8,r2=s*0.85,cap_top=True,cap_bot=False,tint=tuple(c*rnd.uniform(0.85,1.05) for c in col))
def tray(mb,cx,cy,cz,w,d,tint=(0.62,0.6,0.58)):
    mb.box((cx-w/2,cy-d/2,cz),(cx+w/2,cy+d/2,cz+0.012),'alu',tint=tint)
    for (a,b) in (((cx-w/2,cy-d/2),(cx+w/2,cy-d/2+0.01)),((cx-w/2,cy+d/2-0.01),(cx+w/2,cy+d/2)),((cx-w/2,cy-d/2),(cx-w/2+0.01,cy+d/2)),((cx+w/2-0.01,cy-d/2),(cx+w/2,cy+d/2))):
        mb.box((a[0],a[1],cz),(b[0],b[1],cz+0.035),'alu',tint=tint)
def market_stall():
    mb=MB(); W=2.2; Dd=1.0; Hh=0.82; wood=(0.62,0.5,0.38)
    # plank table top + frame
    for i in range(6):
        y0=-Dd/2+i*Dd/6; mb.box((-W/2,y0+0.004,Hh-0.03),(W/2,y0+Dd/6-0.004,Hh),'wood',tint=tuple(c*random.Random(i).uniform(0.85,1.05) for c in wood))
    mb.box((-W/2,-Dd/2,Hh-0.12),(W/2,-Dd/2+0.04,Hh-0.03),'wood',tint=wood)
    legs4(mb,-W/2+0.03,W/2-0.03,-Dd/2+0.03,Dd/2-0.03,Hh-0.03,0.07,'wood',wood)
    mb.box((-W/2+0.05,-Dd/2+0.05,0.25),(W/2-0.05,Dd/2-0.05,0.27),'wood',tint=tuple(c*0.85 for c in wood))  # lower shelf
    # canopy posts + blue tarp sloping to the front
    PH=2.25; FH=1.95
    for x in (-W/2-0.05,W/2+0.05):
        tube(mb,[(x,Dd/2+0.15,0),(x,Dd/2+0.15,PH)],0.025,'wood',sides=6,tint=(0.5,0.4,0.3))
        tube(mb,[(x,-Dd/2-0.35,0),(x,-Dd/2-0.35,FH)],0.025,'wood',sides=6,tint=(0.5,0.4,0.3))
    tarp=(0.1,0.3,0.62)
    def P(s,t):
        x=-W/2-0.25+(W+0.5)*s; y=Dd/2+0.25-(Dd+0.85)*t; z=PH+0.04-(PH-FH)*t-0.08*math.sin(math.pi*t)*0.4-0.05*math.sin(math.pi*s)*math.sin(math.pi*t)
        return V((x,y,z))
    for i in range(10):
        for j in range(6):
            s0,s1=i/10,(i+1)/10; t0,t1=j/6,(j+1)/6
            mb.quad(P(s0,t1),P(s1,t1),P(s1,t0),P(s0,t0),'fabric',tint=tarp,grime=0.5)
            mb.quad(P(s0,t0),P(s1,t0),P(s1,t1),P(s0,t1),'fabric',tint=tuple(c*0.7 for c in tarp),grime=0.2)
    # stall sign hanging off the front edge
    panel(mb,-0.75,0.75,-Dd/2-0.36,FH-0.42,FH-0.04,'market_sign')
    tube(mb,[(-0.6,-Dd/2-0.36,FH-0.04),(-0.6,-Dd/2-0.36,FH+0.03)],0.006,'cable',sides=4); tube(mb,[(0.6,-Dd/2-0.36,FH-0.04),(0.6,-Dd/2-0.36,FH+0.03)],0.006,'cable',sides=4)
    # produce on enamel trays: tomatoes, pepper heaps; onions/yams/limes from Poly Haven scans
    tray(mb,-0.75,-0.18,Hh,0.5,0.4); tomatoes(mb,-0.75,-0.18,Hh+0.012,26,0.16,1)
    tray(mb,-0.2,-0.22,Hh,0.42,0.34,(0.75,0.75,0.72)); tomatoes(mb,-0.2,-0.22,Hh+0.012,40,0.13,2,(0.85,0.12,0.04))  # pepper (tatashe)
    objs=[]
    objs+=produce_pile(objs,'onion',0.35,-0.2,Hh,18,0.16,3,140)
    objs+=produce_pile(objs,'lime',0.82,-0.25,Hh,16,0.11,4,120)
    objs+=produce_pile(objs,'yam',-0.55,0.25,Hh,8,0.2,5,160)
    objs.append(ph('wicker_basket_02',1600,(0.55,0.22,Hh),rotz=0.4,pick=lambda o:'lid' not in o.name))
    objs+=produce_pile(objs,'onion',0.55,0.22,Hh+0.12,8,0.08,6,140)
    objs.append(ph('plastic_crate_01',1200,(-0.55,-0.05,0.27),rotz=1.57))
    objs.append(ph('plastic_crate_01',1200,(0.5,0.0,0.0),rotz=1.4))
    obj=finish(mb,'work_market_stall',objs,seed=6,grime=1.0,damp_h=0.4)
    return obj,dict(category='work',notes='Balogun foodstuff stall 2.2 x 1.0 m (top 0.82 m) under a blue tarp on 4 poles (2.25/1.95 m), produce on trays, sign "Mama Chidinma". Trader stands on +Y.',stand=[0,0.85])

# ===================================================== buka kitchen
def big_pot(mb,cx,cy,cz,r,h,tint=(0.82,0.82,0.8),stew=None):
    mb.cyl((cx,cy,cz),r,h,'alu',seg=18,cap_top=False,cap_bot=True,tint=tint)
    n0=len(mb.faces); mb.cyl((cx,cy,cz+0.01),r-0.006,h-0.01,'alu',seg=18,cap_top=False,tint=tuple(c*0.7 for c in tint)); flip(mb,n0)
    mb.cyl((cx,cy,cz+h-0.01),r+0.006,0.012,'alu',seg=18,cap_top=False,tint=tint)
    if stew: mb.face([V((cx+(r-0.01)*math.cos(2*math.pi*i/18),cy+(r-0.01)*math.sin(2*math.pi*i/18),cz+h*0.75)) for i in range(18)],'plastic',tint=stew,grime=0,ao=0.6)
    for s in (-1,1): tube(mb,[(cx+s*r,cy-0.03,cz+h-0.04),(cx+s*(r+0.04),cy-0.025,cz+h-0.04),(cx+s*(r+0.04),cy+0.025,cz+h-0.04),(cx+s*r,cy+0.03,cz+h-0.04)],0.007,'alu',sides=5,tint=tint)
def burner(mb,cx,cy,cz):
    mb.box((cx-0.32,cy-0.2,cz),(cx+0.32,cy+0.2,cz+0.09),'metal_paint',tint=(0.12,0.12,0.13))
    mb.box((cx-0.31,cy-0.19,cz+0.09),(cx+0.31,cy+0.19,cz+0.095),'steel_galv')
    for dx in (-0.16,0.16):
        mb.cyl((cx+dx,cy,cz+0.095),0.06,0.02,'metal_dark',seg=12)
        for k in range(4):
            a=k*math.pi/2+0.4; mb.obox((cx+dx+0.09*math.cos(a),cy+0.09*math.sin(a),cz+0.125),(0.07,0.015,0.015),a,'metal_dark')
        mb.cyl((cx+dx,cy-0.2,cz+0.045),0.018,0.025,'plastic',seg=8,axis='Y',tint=(0.1,0.1,0.1))
def plates(mb,cx,cy,cz,n,col=(0.92,0.92,0.88)):
    for i in range(n): mb.cyl((cx,cy,cz+i*0.012),0.115,0.012,'plastic',seg=16,r2=0.125,tint=col)
def buka_kitchen():
    mb=MB(); W=2.6; Dd=0.75; Hh=0.9; conc=(0.78,0.76,0.72)
    # rendered block counter with tiled top and an open shelf
    mb.box((-W/2,-Dd/2,0),(W/2,Dd/2,Hh-0.03),'plaster_old',tint=conc,skip=('+z',))
    grid_quad(mb,V((-W/2-0.02,-Dd/2-0.02,Hh-0.03)),V((1,0,0)),V((0,1,0)),W+0.04,Dd+0.04,'worn_tile',cu=0.6,cv=0.4)
    mb.box((-W/2-0.02,-Dd/2-0.03,Hh-0.06),(W/2+0.02,-Dd/2-0.02,Hh-0.03),'worn_tile')
    burner(mb,-0.7,0.05,Hh-0.03)
    big_pot(mb,-0.86,0.05,Hh+0.1,0.15,0.22,stew=(0.62,0.16,0.05))        # stew
    big_pot(mb,-0.54,0.05,Hh+0.1,0.14,0.26,stew=(0.86,0.4,0.12))          # jollof
    # serving trays with rice and dodo
    tray(mb,0.05,-0.08,Hh-0.03,0.5,0.34,(0.8,0.8,0.78))
    tomatoes(mb,0.05,-0.08,Hh-0.018,22,0.14,9,(0.95,0.62,0.18))            # fried plantain
    tray(mb,0.6,-0.08,Hh-0.03,0.42,0.34,(0.8,0.8,0.78))
    mb.box((0.42,-0.22,Hh-0.018),(0.78,0.06,Hh+0.02),'plastic',tint=(0.95,0.94,0.9),grime=0)  # white rice
    plates(mb,1.05,0.05,Hh-0.03,7); plates(mb,1.05,-0.2,Hh-0.03,4,(0.18,0.45,0.8))
    objs=[ph('small_lpg_tank',1500,(-1.0,0.6,0),rotz=0.4),ph('pot_enamel_01',1500,(0.2,0.18,Hh-0.03),rotz=0.6),ph('wooden_cutting_board',600,(0.55,0.2,Hh-0.03),rotz=0.1),
          ph('plastic_container',1200,(1.85,0.0,0),rotz=1.57,tint=(0.15,0.4,0.75)),ph('plastic_thermos',800,(-0.2,0.2,Hh-0.03))]
    # gas hose
    tube(mb,[(-0.95,0.55,0.55),(-0.9,0.4,0.6),(-0.85,0.25,Hh+0.02),(-0.75,0.2,Hh+0.03)],0.01,'rubber',sides=5)
    # zinc shade overhead on 4 poles
    PH=2.4
    for x in (-W/2-0.1,W/2+0.1):
        for y in (-Dd/2-0.9,Dd/2+0.5): tube(mb,[(x,y,0),(x,y,PH-0.05)],0.03,'metal_paint',sides=6,tint=(0.3,0.28,0.26))
    zr,fas=hip_roof(mb,-W/2-0.1,-Dd/2-0.9,W/2+0.1,Dd/2+0.5,PH,pitch_deg=8,overhang=0.3,gable=True)
    fascia(mb,fas)
    obj=finish(mb,'work_buka_kitchen',objs,seed=7,grime=1.2,damp_h=0.5)
    return obj,dict(category='work',notes='Surulere buka cook station: tiled block counter 2.6 x 0.75 m (top 0.9), 2-ring gas burner with stew and jollof pots, plantain and rice trays, plates, LPG tank, cooler, under a zinc shade (eave 2.4 m). Cook stands on +Y.',stand=[-0.7,0.75])
def buka_menu():
    mb=MB(); W=0.9; H=1.12
    for x in (-W/2+0.04,W/2-0.04): mb.box((x-0.025,-0.02,0),(x+0.025,0.02,1.75),'wood',tint=(0.45,0.34,0.24))
    mb.box((-W/2,-0.015,0.62),(W/2,0.015,0.62+H),'wood',tint=(0.4,0.3,0.2))
    panel(mb,-W/2+0.02,W/2-0.02,-0.016,0.64,0.6+H,'buka_menu')
    obj=finish(mb,'work_buka_menu',[],seed=8,grime=1.0,damp_h=0.3)
    return obj,dict(category='work',notes='Standing chalk-style menu board for Iya Basira buka, 0.9 m wide, 1.77 m tall, prices in naira.')
def bench_table():
    mb=MB(); L=1.6; wood=(0.6,0.48,0.36)
    mb.box((-L/2,-0.3,0.72),(L/2,0.3,0.76),'wood',tint=wood); legs4(mb,-L/2+0.05,L/2-0.05,-0.25,0.25,0.72,0.06,'wood',wood)
    # oilcloth on top
    grid_quad(mb,V((-L/2-0.01,-0.31,0.761)),V((1,0,0)),V((0,1,0)),L+0.02,0.62,'linen',cu=0.6,cv=0.6,tint=(0.95,0.85,0.7))
    for y in (-0.62,0.62):
        mb.box((-L/2,y-0.13,0.43),(L/2,y+0.13,0.46),'wood',tint=wood); legs4(mb,-L/2+0.08,L/2-0.08,y-0.1,y+0.1,0.43,0.05,'wood',wood)
    plates(mb,-0.4,-0.1,0.765,1); plates(mb,0.35,0.12,0.765,1,(0.18,0.45,0.8))
    obj=finish(mb,'work_bench_table',[],seed=9,grime=1.0,damp_h=0.3)
    return obj,dict(category='work',notes='Buka eating table 1.6 x 0.6 m with oilcloth and two benches.')

# ===================================================== barber
def barber_station():
    mb=MB(); W=1.8; Dd=0.42; Hh=0.86
    mb.box((-W/2,0,0),(W/2,Dd,Hh),'paint_wood',tint=(0.9,0.9,0.88))
    mb.box((-W/2-0.02,-0.02,Hh),(W/2+0.02,Dd,Hh+0.03),'plastic',tint=(0.12,0.12,0.13))
    for i in range(3): mb.quad(V((-W/2+0.05+i*0.6,-0.001,0.1)),V((-W/2+0.55+i*0.6,-0.001,0.1)),V((-W/2+0.55+i*0.6,-0.001,Hh-0.06)),V((-W/2+0.05+i*0.6,-0.001,Hh-0.06)),'paint_wood',tint=(0.78,0.78,0.76))
    # mirror with frame + LED strip
    mb.box((-W/2,Dd-0.03,Hh+0.18),(W/2,Dd,Hh+1.28),'metal_paint',tint=(0.1,0.1,0.11))
    mb.quad(V((-W/2+0.04,Dd-0.031,Hh+0.22)),V((W/2-0.04,Dd-0.031,Hh+0.22)),V((W/2-0.04,Dd-0.031,Hh+1.24)),V((-W/2+0.04,Dd-0.031,Hh+1.24)),'mirror',grime=0,ao=0)
    mb.box((-W/2,Dd-0.06,Hh+1.28),(W/2,Dd,Hh+1.31),'emit_cool')
    # tools: clippers, spray bottles, powder, combs
    rnd=random.Random(3)
    for i,(x,col) in enumerate([(-0.7,(0.1,0.1,0.1)),(-0.55,(0.75,0.6,0.1)),(-0.4,(0.1,0.1,0.1))]):
        mb.obox((x,0.15,Hh+0.045),(0.05,0.15,0.03),0.3*(i-1),'plastic',tint=col)
        tube(mb,[(x+0.02,0.25,Hh+0.04),(x+0.15,0.33,Hh+0.035),(x+0.3,0.36,Hh+0.032)],0.004,'cable',sides=4)
    for i,x in enumerate([0.15,0.28,0.42,0.6]):
        col=[(0.1,0.35,0.75),(0.9,0.9,0.88),(0.2,0.6,0.3),(0.85,0.2,0.2)][i]; h=[0.22,0.16,0.2,0.12][i]; r=[0.035,0.045,0.03,0.05][i]
        mb.cyl((x,0.2,Hh+0.03),r,h,'plastic',seg=12,tint=col); mb.cyl((x,0.2,Hh+0.03+h),r*0.45,0.04,'plastic',seg=8,tint=(0.1,0.1,0.1))
    mb.box((0.75,0.08,Hh+0.03),(0.85,0.32,Hh+0.06),'linen',tint=(0.95,0.95,0.95))  # folded towels
    mb.box((0.75,0.08,Hh+0.06),(0.85,0.32,Hh+0.09),'linen',tint=(0.85,0.25,0.25))
    obj=finish(mb,'work_barber_station',[],seed=10,grime=0.7,damp_h=0.3)
    return obj,dict(category='work',notes='Barber wall station 1.8 m: white cabinet counter (0.86 m), black top, 1.1 m mirror with LED strip, clippers, bottles, towels. Back face at y=+0.42 (place against a wall).')
def barber_chair():
    o=ph('BarberShopChair_01',2200,(0,0,0),rotz=math.pi)
    mb=MB(); mb.cyl((0,0,0),0.001,0.001,'metal_dark',seg=3)
    obj=finish(mb,'work_barber_chair',[o],seed=11,grime=0.3,damp_h=0.1)
    return obj,dict(category='work',notes='Hydraulic barber chair (Poly Haven BarberShopChair_01, CC0). Faces -Y (+Z in three.js). Seat ~0.55 m.')
def wall_sign(name,region,W,H,frame=(0.1,0.1,0.11),light=False):
    def b():
        mb=MB()
        mb.box((-W/2,0,0),(W/2,0.04,H),'metal_paint',tint=frame)
        panel(mb,-W/2+0.02,W/2-0.02,-0.001,0.02,H-0.02,region)
        if light:
            for x in (-W/3,W/3):
                tube(mb,[(x,0.02,H+0.02),(x,-0.25,H+0.12)],0.01,'metal_dark',sides=4); mb.cyl((x,-0.27,H+0.06),0.04,0.06,'emit_warm',seg=8)
        obj=finish(mb,name,[],seed=12,grime=0.6,damp_h=0.0,ground=False)
        return obj,dict(category='sign',notes=f'Wall sign {W} x {H} m ({region}); back at y=+0.04, base at z=0.')
    return b

# ===================================================== classroom
def blackboard():
    mb=MB(); W=2.6; H=1.25
    mb.box((-W/2-0.05,0,0),(W/2+0.05,0.04,H+0.1),'wood',tint=(0.5,0.36,0.24))
    panel(mb,-W/2,W/2,-0.002,0.05,H+0.05,'chalkboard')
    mb.box((-W/2,-0.08,0.0),(W/2,0.04,0.035),'wood',tint=(0.5,0.36,0.24))
    for i,x in enumerate([-0.9,-0.85,-0.3]): mb.obox((x,-0.04,0.045),(0.08,0.012,0.012),0.2*i,'plastic',tint=(0.97,0.97,0.95))
    mb.box((0.6,-0.07,0.035),(0.76,-0.02,0.07),'wood',tint=(0.4,0.3,0.25))  # duster
    obj=finish(mb,'work_blackboard',[],seed=13,grime=0.6,damp_h=0.0,ground=False)
    return obj,dict(category='work',notes='Wall chalkboard 2.6 x 1.25 m with wooden frame and chalk ledge; mount base at ~0.85 m. Back at y=+0.04.')
def school_desk():
    o=ph('SchoolDesk_01',1600,(0,0,0),rotz=math.pi); c=ph('SchoolChair_01',1600,(0,0.42,0),rotz=math.pi)
    mb=MB(); mb.box((-0.15,-0.1,0.761),(0.06,0.05,0.77),'paint_wood',tint=(0.96,0.96,0.93))
    obj=finish(mb,'work_school_desk',[o,c],seed=14,grime=0.5,damp_h=0.2)
    return obj,dict(category='work',notes='Pupil desk + chair (Poly Haven SchoolDesk_01/SchoolChair_01, CC0) with an exercise book; pupil faces -Y.')
def teacher_desk():
    mb=MB(); W=1.3; Dd=0.65; Hh=0.76; wood=(0.55,0.4,0.28)
    mb.box((-W/2,-Dd/2,Hh-0.035),(W/2,Dd/2,Hh),'wood',tint=wood)
    mb.box((-W/2+0.02,-Dd/2+0.02,0.05),(-W/2+0.42,Dd/2-0.02,Hh-0.035),'wood',tint=tuple(c*0.9 for c in wood))
    mb.box((W/2-0.05,-Dd/2+0.02,0),(W/2-0.02,Dd/2-0.02,Hh-0.035),'wood',tint=wood)
    mb.box((-W/2+0.42,Dd/2-0.03,0.35),(W/2-0.05,Dd/2-0.01,Hh-0.035),'wood',tint=wood)
    objs=[ph('office_notepads',500,(-0.25,0.0,Hh),rotz=0.2,scale=0.45),ph('stationery_supplies',500,(0.25,-0.1,Hh+0.07),scale=0.9),ph('wall_clock',900,(0.42,0.15,Hh+0.16),rotz=0.0,scale=0.5)]
    obj=finish(mb,'work_teacher_desk',objs,seed=15,grime=0.6,damp_h=0.2)
    return obj,dict(category='work',notes='Teacher desk 1.3 x 0.65 m with drawers, exercise books, pens, a small clock.')

# ===================================================== bank / office
def monitor(mb,cx,cy,cz,region,rot=0.0,w=0.56,h=0.33):
    n0=len(mb.faces)
    mb.box((-0.11,-0.08,0),(0.11,0.08,0.012),'plastic',tint=(0.08,0.08,0.09))
    mb.box((-0.025,0.02,0.012),(0.025,0.05,0.18),'plastic',tint=(0.08,0.08,0.09))
    mb.box((-w/2,0.0,0.12),(w/2,0.03,0.12+h),'plastic',tint=(0.06,0.06,0.07))
    mb.quad(V((-w/2+0.012,-0.001,0.132)),V((w/2-0.012,-0.001,0.132)),V((w/2-0.012,-0.001,0.108+h)),V((-w/2+0.012,-0.001,0.108+h)),'screen',uv=wr(region),grime=0,ao=0)
    mb.transform(Matrix.Translation(V((cx,cy,cz)))@Matrix.Rotation(rot,4,'Z'),n0)
def keyboard(mb,cx,cy,cz,rot=0.0):
    n0=len(mb.faces)
    mb.box((-0.22,-0.07,0),(0.22,0.07,0.018),'plastic',tint=(0.12,0.12,0.13))
    for r in range(4):
        for c in range(14): mb.box((-0.205+c*0.0295,-0.058+r*0.03,0.018),(-0.181+c*0.0295,-0.034+r*0.03,0.024),'plastic',tint=(0.2,0.2,0.22))
    mb.box((0.27,-0.03,0),(0.33,0.05,0.025),'plastic',tint=(0.12,0.12,0.13))
    mb.transform(Matrix.Translation(V((cx,cy,cz)))@Matrix.Rotation(rot,4,'Z'),n0)
def office_chair(mb,cx,cy,rot=0.0,col=(0.1,0.1,0.11)):
    n0=len(mb.faces)
    for k in range(5):
        a=2*math.pi*k/5; tube(mb,[(0,0,0.08),(0.3*math.cos(a),0.3*math.sin(a),0.06)],0.018,'plastic',sides=5,tint=(0.08,0.08,0.08))
        mb.cyl((0.3*math.cos(a),0.3*math.sin(a),0.0),0.025,0.05,'rubber',seg=8)
    mb.cyl((0,0,0.08),0.025,0.35,'chrome',seg=10)
    mb.box((-0.25,-0.24,0.43),(0.25,0.24,0.5),'fabric',tint=col)
    mb.box((-0.23,0.2,0.55),(0.23,0.26,1.05),'fabric',tint=col)
    tube(mb,[(0,0.22,0.47),(0,0.24,0.56)],0.02,'plastic',sides=5,tint=(0.08,0.08,0.08))
    for s in (-1,1): mb.box((s*0.25-0.02,-0.1,0.6),(s*0.25+0.02,0.12,0.63),'plastic',tint=(0.08,0.08,0.08)); tube(mb,[(s*0.25,0.05,0.5),(s*0.25,0.05,0.61)],0.012,'plastic',sides=4,tint=(0.08,0.08,0.08))
    mb.transform(Matrix.Translation(V((cx,cy,0)))@Matrix.Rotation(rot,4,'Z'),n0)
def office_desk(name,region):
    def b():
        d=ph('metal_office_desk',2500,(0,0,0),rotz=math.pi)
        mb=MB(); Hh=0.79
        monitor(mb,-0.25,0.2,Hh,region); monitor(mb,0.35,0.22,Hh,'kanban' if region=='code_screen' else 'bank_screen',rot=-0.25)
        keyboard(mb,-0.2,-0.12,Hh)
        mb.cyl((0.6,-0.15,Hh),0.04,0.1,'ceramic',seg=12,tint=(0.95,0.95,0.95))
        office_chair(mb,-0.2,-0.75,rot=math.pi)
        objs=[d,ph('office_notepads',400,(0.55,0.15,Hh),rotz=-0.3,scale=0.4)]
        obj=finish(mb,name,objs,seed=16,grime=0.4,damp_h=0.1)
        return obj,dict(category='work',notes=f'Office desk 2.0 x 0.95 m (Poly Haven metal_office_desk, CC0), two monitors ({region}), keyboard, mug, office chair at -Y (worker sits facing +Y... chair at y=-0.75, worker faces +Y toward the screens).',seat=[-0.2,-0.75])
    return b
def bank_counter():
    mb=MB(); W=3.2; Dd=0.7; Hh=1.05
    mb.box((-W/2,-Dd/2,0),(W/2,Dd/2,Hh-0.04),'paint_wood',tint=(0.18,0.42,0.3))
    grid_quad(mb,V((-W/2-0.03,-Dd/2-0.05,Hh-0.04)),V((1,0,0)),V((0,1,0)),W+0.06,Dd+0.05,'terrazzo',cu=0.8,cv=0.4)
    mb.box((-W/2-0.03,-Dd/2-0.05,Hh-0.08),(W/2+0.03,-Dd/2-0.04,Hh-0.04),'terrazzo')
    mb.box((-W/2,-Dd/2-0.006,0.08),(W/2,-Dd/2,0.14),'alu')
    # front logo strip
    mb.quad(V((-0.9,-Dd/2-0.007,0.45)),V((0.9,-Dd/2-0.007,0.45)),V((0.9,-Dd/2-0.007,0.79)),V((-0.9,-Dd/2-0.007,0.79)),'atlas_work',uv=wr('bank_sign'),grime=0)
    # glass partitions with speak holes and slots, 2 windows
    for x in (-W/2,-0.05,W/2-0.05):
        mb.box((x,-0.04,Hh),(x+0.05,0.04,Hh+0.85),'alu')
    for x0,x1 in ((-W/2+0.05,-0.05),(0.0,W/2-0.05)):
        mb.quad(V((x0,0,Hh+0.1)),V((x1,0,Hh+0.1)),V((x1,0,Hh+0.85)),V((x0,0,Hh+0.85)),'glass_clear',grime=0,ao=0)
        mb.quad(V((x1,0,Hh+0.1)),V((x0,0,Hh+0.1)),V((x0,0,Hh+0.85)),V((x1,0,Hh+0.85)),'glass_clear',grime=0,ao=0)
        mb.box((x0,-0.03,Hh),(x1,0.03,Hh+0.1),'alu')
        mb.box(((x0+x1)/2-0.18,-0.04,Hh+0.0),((x0+x1)/2+0.18,-0.035,Hh+0.06),'metal_dark')
    mb.box((-W/2,-0.04,Hh+0.85),(W/2,0.04,Hh+0.9),'alu')
    for x in (-0.8,0.8):
        monitor(mb,x,0.18,Hh-0.04,'bank_screen',rot=math.pi)
        keyboard(mb,x,0.0,Hh-0.04,rot=math.pi)
    office_chair(mb,-0.8,0.85,rot=0.0,col=(0.12,0.24,0.18)); office_chair(mb,0.8,0.85,rot=0.0,col=(0.12,0.24,0.18))
    pos_terminal(mb,-1.25,-0.15,Hh-0.04,rot=0.2)
    cash_stack(mb,1.2,0.1,Hh-0.04,'cash_note',10,0.3)
    obj=finish(mb,'work_bank_counter',[],seed=17,grime=0.3,damp_h=0.1)
    return obj,dict(category='work',notes='PalmTrust banking hall counter 3.2 x 0.7 m (top 1.05 m) with two glass teller windows, monitors and chairs on the +Y staff side. Customers queue on -Y.',seat=[-0.8,0.85])
def queue_posts():
    mb=MB()
    xs=[-1.2,0.0,1.2]
    for x in xs:
        mb.cyl((x,0,0),0.16,0.03,'chrome',seg=14); mb.cyl((x,0,0.03),0.025,0.92,'chrome',seg=10); mb.cyl((x,0,0.95),0.035,0.04,'chrome',seg=10)
    for a,b in zip(xs,xs[1:]):
        pts=catenary((a+0.03,0,0.9),(b-0.03,0,0.9),0.08,10)
        for p,q in zip(pts,pts[1:]): mb.quad(V((p.x,0,p.z-0.025)),V((q.x,0,q.z-0.025)),V((q.x,0,q.z+0.025)),V((p.x,0,p.z+0.025)),'fabric',tint=(0.12,0.4,0.28),grime=0); mb.quad(V((q.x,0,q.z-0.025)),V((p.x,0,p.z-0.025)),V((p.x,0,p.z+0.025)),V((q.x,0,q.z+0.025)),'fabric',tint=(0.12,0.4,0.28),grime=0)
    obj=finish(mb,'work_queue_posts',[],seed=18,grime=0.2,damp_h=0.0)
    return obj,dict(category='work',notes='Three chrome queue posts with green belts, 2.4 m run along X.')

# ===================================================== security
def security_booth():
    mb=MB(); W=1.8; Dd=1.6; H=2.5; cream=(0.9,0.86,0.74)
    ops_front=[dict(x0=0.2,x1=1.6,z0=1.0,z1=2.0,kind='window',reveal=0.12)]
    wall(mb,V((-W/2,-Dd/2,0)),V((1,0,0)),V((0,-1,0)),W,H,'plaster_paint',tint=cream,openings=ops_front)
    wall(mb,V((W/2,-Dd/2,0)),V((0,1,0)),V((1,0,0)),Dd,H,'plaster_paint',tint=cream,openings=[dict(x0=0.3,x1=1.3,z0=1.0,z1=2.0,kind='window',reveal=0.12)])
    wall(mb,V((W/2,Dd/2,0)),V((-1,0,0)),V((0,1,0)),W,H,'plaster_paint',tint=cream)
    wall(mb,V((-W/2,Dd/2,0)),V((0,-1,0)),V((-1,0,0)),Dd,H,'plaster_paint',tint=cream,openings=[dict(x0=0.3,x1=1.15,z0=0,z1=2.05,kind='door',reveal=0.12)])
    # inside faces (dark) so the booth reads as hollow through the windows
    mb.box((-W/2+0.12,-Dd/2+0.12,0.01),(W/2-0.12,Dd/2-0.12,0.02),'concrete',tint=(0.6,0.6,0.58))
    for (a,b) in (((-W/2+0.12,-Dd/2+0.12),(W/2-0.12,-Dd/2+0.12)),((W/2-0.12,-Dd/2+0.12),(W/2-0.12,Dd/2-0.12)),((W/2-0.12,Dd/2-0.12),(-W/2+0.12,Dd/2-0.12)),((-W/2+0.12,Dd/2-0.12),(-W/2+0.12,-Dd/2+0.12))):
        A=V((a[0],a[1],0)); B=V((b[0],b[1],0)); mb.quad(B,A,A+V((0,0,H)),B+V((0,0,H)),'plaster_paint',tint=(0.7,0.68,0.6))
    # wall thickness tops + band
    mb.box((-W/2,-Dd/2,0),(W/2,-Dd/2+0.12,0.0),'plaster_paint',tint=cream)
    for (x0,y0,x1,y1) in ((-W/2,-Dd/2,W/2,-Dd/2+0.12),(W/2-0.12,-Dd/2,W/2,Dd/2),(-W/2,Dd/2-0.12,W/2,Dd/2),(-W/2,-Dd/2,-W/2+0.12,Dd/2)):
        mb.box((x0,y0,0),(x1,y1,0.45),'metal_paint',tint=(0.25,0.42,0.36),skip=('+z','-z'))
    # glass
    mb.quad(V((-W/2+0.2,-Dd/2+0.06,1.0)),V((-W/2+1.6,-Dd/2+0.06,1.0)),V((-W/2+1.6,-Dd/2+0.06,2.0)),V((-W/2+0.2,-Dd/2+0.06,2.0)),'glass',grime=0)
    mb.quad(V((W/2-0.06,-Dd/2+0.3,1.0)),V((W/2-0.06,-Dd/2+1.3,1.0)),V((W/2-0.06,-Dd/2+1.3,2.0)),V((W/2-0.06,-Dd/2+0.3,2.0)),'glass',grime=0)
    # door leaf (open inward) metal
    mb.box((-W/2+0.15,Dd/2-0.35-0.85,0.02),(-W/2+0.19,Dd/2-0.35,2.03),'metal_paint',tint=(0.2,0.36,0.3))
    # flat roof slab with overhang
    mb.box((-W/2-0.35,-Dd/2-0.45,H),(W/2+0.35,Dd/2+0.3,H+0.14),'concrete',tint=(0.82,0.8,0.76))
    # sign on fascia front
    panel(mb,-0.85,0.85,-Dd/2-0.452,H-0.0+0.0,H+0.14,'security_sign') if False else None
    panel(mb,-0.8,0.8,-Dd/2-0.01,H-0.42,H-0.02,'security_sign')
    # counter + logbook inside the front window
    mb.box((-W/2+0.12,-Dd/2+0.12,0.95),(W/2-0.12,-Dd/2+0.45,0.99),'wood',tint=(0.5,0.38,0.27))
    mb.box((-0.3,-Dd/2+0.2,0.99),(0.05,-Dd/2+0.42,1.01),'paint_wood',tint=(0.15,0.3,0.6))
    # security light under the eave
    objs=[ph('security_light',800,(W/2-0.2,-Dd/2-0.2,H-0.05),rotz=0.0,scale=0.8)]
    obj=finish(mb,'work_security_booth',objs,seed=19,grime=1.1,damp_h=0.6)
    return obj,dict(category='work',notes='Estate gatehouse 1.8 x 1.6 m, 2.5 m walls, roof slab with overhang, windows front and right, door on the left (-X) side, "SECURITY POST" sign on the front.')
def boom_barrier():
    mb=MB(); L=4.2
    mb.box((-0.18,-0.18,0),(0.18,0.18,0.95),'metal_paint',tint=(0.85,0.75,0.1))
    mb.box((-0.2,-0.2,0.95),(0.2,0.2,1.0),'metal_dark')
    mb.cyl((0,0,0.85),0.07,0.12,'metal_dark',seg=10,axis='Y')
    # striped arm along +X
    n0=len(mb.faces)
    for i in range(8):
        x0=0.15+i*(L/8); x1=x0+L/8
        mb.box((x0,-0.035,0.82),(x1,0.035,0.9),'plastic',tint=(0.85,0.1,0.08) if i%2==0 else (0.96,0.96,0.94))
    mb.box((L+0.1,-0.06,0),(L+0.2,0.06,0.88),'metal_paint',tint=(0.85,0.75,0.1))  # rest post
    obj=finish(mb,'work_boom_barrier',[],seed=20,grime=0.8,damp_h=0.3)
    return obj,dict(category='work',notes=f'Yellow boom barrier housing with a {L} m red/white arm along +X at 0.86 m and a rest post.')
def post_sign(name,region,W,H,z0,poles=2,tint=(0.3,0.3,0.3)):
    def b():
        mb=MB()
        xs=[-W/2+0.12,W/2-0.12] if poles==2 else [0]
        for x in xs: mb.cyl((x,0.06,0),0.04,z0+H+0.05,'steel_galv',seg=8)
        mb.box((-W/2,0,z0),(W/2,0.04,z0+H),'metal_paint',tint=tint)
        panel(mb,-W/2+0.02,W/2-0.02,-0.001,z0+0.02,z0+H-0.02,region)
        obj=finish(mb,name,[],seed=21,grime=1.0,damp_h=0.3)
        return obj,dict(category='sign',notes=f'Post-mounted sign {W} x {H} m at {z0} m ({region}).')
    return b

# ===================================================== dispatch
def parcel(mb,cx,cy,cz,w,d,h,rot=0.0,label=True):
    n0=len(mb.faces)
    mb.box((-w/2,-d/2,0),(w/2,d/2,h),'paint_wood',tint=(0.72,0.55,0.36),skip=('+z',))
    top_panel(mb,-w/2,w/2,-d/2,d/2,h,'cardboard')
    if label: panel(mb,-min(0.09,w*0.35),min(0.09,w*0.35),-d/2-0.001,h*0.3,h*0.3+min(0.09,h*0.4),'parcel_label')
    mb.transform(Matrix.Translation(V((cx,cy,cz)))@Matrix.Rotation(rot,4,'Z'),n0)
def parcel_shelf():
    s=ph('Shelf_01',400,(0,0,0),rotz=math.pi)
    mb=MB(); rnd=random.Random(5)
    levels=[0.06,0.52,0.98,1.44]
    for z in levels:
        x=-0.45
        while x<0.4:
            w=rnd.uniform(0.16,0.3); h=rnd.uniform(0.12,0.34); d=rnd.uniform(0.16,0.22)
            parcel(mb,x+w/2,0.0,z,w,d,h,rot=rnd.uniform(-0.08,0.08),label=rnd.random()<0.7); x+=w+0.02
    obj=finish(mb,'work_parcel_shelf',[s],seed=22,grime=0.6,damp_h=0.2)
    return obj,dict(category='work',notes='Steel shelf (Poly Haven Shelf_01, CC0) loaded with labelled parcels, 1.0 x 0.26 x 2.08 m.')
def parcel_stack():
    mb=MB(); rnd=random.Random(9)
    z=0
    for i in range(4):
        w=rnd.uniform(0.35,0.5); d=rnd.uniform(0.3,0.4); h=rnd.uniform(0.18,0.3)
        parcel(mb,rnd.uniform(-0.04,0.04),rnd.uniform(-0.04,0.04),z,w,d,h,rot=rnd.uniform(-0.2,0.2)); z+=h
    parcel(mb,0.55,0.1,0,0.4,0.35,0.3,rot=0.4)
    obj=finish(mb,'work_parcel_stack',[],seed=23,grime=0.6,damp_h=0.2)
    return obj,dict(category='work',notes='Stack of four parcels plus one beside it.')
def delivery_box():
    mb=MB(); w=0.46; d=0.42; h=0.42
    mb.box((-w/2,-d/2,0),(w/2,d/2,h),'plastic',tint=(0.82,0.3,0.2))
    mb.box((-w/2-0.01,-d/2-0.01,h-0.06),(w/2+0.01,d/2+0.01,h+0.01),'plastic',tint=(0.7,0.22,0.15))
    for s in (-1,1): panel_x(mb,s*(w/2+0.001),-d/2+0.03,d/2-0.03,0.05,h-0.08,'dispatch_logo',facing=s)
    panel(mb,-w/2+0.03,w/2-0.03,-d/2-0.001,0.08,h-0.1,'dispatch_logo')
    mb.box((-0.06,d/2,h*0.4),(0.06,d/2+0.02,h*0.55),'metal_dark')
    obj=finish(mb,'work_delivery_box',[],seed=24,grime=0.7,damp_h=0.0)
    return obj,dict(category='work',notes='SwiftDrop delivery top box 0.46 x 0.42 x 0.43 m; mount on the okada rear rack.')

# ===================================================== stage / bar
def speaker(mb,cx,cy,cz,w=0.5,d=0.4,h=0.8,rot=0.0):
    n0=len(mb.faces)
    mb.box((-w/2,-d/2,0),(w/2,d/2,h),'plastic',tint=(0.06,0.06,0.065))
    panel(mb,-w/2+0.02,w/2-0.02,-d/2-0.002,0.02,h-0.02,'speaker')
    for (zc,r) in ((h*0.3,w*0.36),(h*0.75,w*0.16)):
        mb.cyl((0,-d/2-0.003,zc),r,0.01,'rubber',seg=16,axis='Y'); mb.cyl((0,-d/2-0.013,zc),r*0.35,0.012,'metal_dark',seg=10,axis='Y')
    mb.transform(Matrix.Translation(V((cx,cy,cz)))@Matrix.Rotation(rot,4,'Z'),n0)
def stage():
    mb=MB(); W=4.4; Dd=2.6; Hh=0.45
    for i in range(11):
        x0=-W/2+i*W/11; mb.box((x0+0.004,-Dd/2,Hh-0.04),(x0+W/11-0.004,Dd/2,Hh),'wood',tint=tuple(c*random.Random(i).uniform(0.85,1.05) for c in (0.42,0.3,0.2)))
    mb.box((-W/2,-Dd/2,0),(W/2,-Dd/2+0.02,Hh-0.04),'fabric',tint=(0.05,0.05,0.06))
    for x in (-W/2,W/2-0.02): mb.box((x,-Dd/2,0),(x+0.02,Dd/2,Hh-0.04),'fabric',tint=(0.05,0.05,0.06))
    # backdrop banner on a pipe frame
    for x in (-W/2+0.1,W/2-0.1): tube(mb,[(x,Dd/2-0.1,Hh),(x,Dd/2-0.1,Hh+2.9)],0.03,'steel_galv',sides=6)
    tube(mb,[(-W/2+0.1,Dd/2-0.1,Hh+2.9),(W/2-0.1,Dd/2-0.1,Hh+2.9)],0.03,'steel_galv',sides=6)
    panel(mb,-1.8,1.8,Dd/2-0.13,Hh+1.2,Hh+2.8,'stage_banner')
    mb.quad(V((-W/2+0.1,Dd/2-0.12,Hh)),V((W/2-0.1,Dd/2-0.12,Hh)),V((W/2-0.1,Dd/2-0.12,Hh+1.2)),V((-W/2+0.1,Dd/2-0.12,Hh+1.2)),'fabric',tint=(0.06,0.05,0.07))
    # speakers on stands + monitor wedges
    for s in (-1,1):
        tube(mb,[(s*(W/2+0.3),-Dd/2+0.4,0),(s*(W/2+0.3),-Dd/2+0.4,1.3)],0.02,'metal_dark',sides=6)
        for k in range(3):
            a=k*2*math.pi/3; tube(mb,[(s*(W/2+0.3),-Dd/2+0.4,0.5),(s*(W/2+0.3)+0.4*math.cos(a),-Dd/2+0.4+0.4*math.sin(a),0)],0.012,'metal_dark',sides=4)
        speaker(mb,s*(W/2+0.3),-Dd/2+0.4,1.3,rot=-s*0.25)
        speaker(mb,s*0.9,-Dd/2+0.35,Hh,0.42,0.38,0.3,rot=s*0.1)
    # mic stand at the front + cable
    tube(mb,[(0,-Dd/2+0.6,Hh),(0,-Dd/2+0.6,Hh+1.45)],0.01,'metal_dark',sides=6)
    for k in range(3):
        a=k*2*math.pi/3+0.5; tube(mb,[(0,-Dd/2+0.6,Hh+0.25),(0.25*math.cos(a),-Dd/2+0.6+0.25*math.sin(a),Hh+0.005)],0.008,'metal_dark',sides=4)
    tube(mb,[(0,-Dd/2+0.6,Hh+1.45),(0,-Dd/2+0.45,Hh+1.55)],0.008,'metal_dark',sides=4)
    mb.cyl((0,-Dd/2+0.42,Hh+1.56),0.024,0.1,'metal_dark',seg=8,axis='Y')
    tube(mb,[(0,-Dd/2+0.6,Hh+0.3),(0.3,-Dd/2+0.9,Hh+0.005),(1.2,-Dd/2+1.6,Hh+0.005)],0.006,'cable',sides=4)
    # amp + keyboard stand at the back-left
    mb.box((-1.6,Dd/2-0.7,Hh),(-1.0,Dd/2-0.35,Hh+0.45),'plastic',tint=(0.08,0.08,0.08)); panel(mb,-1.58,-1.02,Dd/2-0.701,Hh+0.05,Hh+0.4,'speaker')
    for x in (-0.6,0.6): tube(mb,[(1.0+x*0.5,Dd/2-0.8,Hh),(1.0-x*0.5,Dd/2-0.8,Hh+0.75)],0.015,'metal_dark',sides=4)
    mb.box((0.45,Dd/2-0.95,Hh+0.72),(1.55,Dd/2-0.65,Hh+0.8),'plastic',tint=(0.08,0.08,0.08))
    for i in range(30): mb.box((0.5+i*0.034,Dd/2-0.94,Hh+0.8),(0.53+i*0.034,Dd/2-0.82,Hh+0.81),'plastic',tint=(0.95,0.95,0.93))
    # festoon string lights across the front
    for (p0,p1) in (((-W/2-0.3,-Dd/2+0.4,1.9),(0,-Dd/2-0.2,2.6)),((0,-Dd/2-0.2,2.6),(W/2+0.3,-Dd/2+0.4,1.9))):
        pts=catenary(p0,p1,0.25,14); tube(mb,pts,0.004,'cable',sides=4)
        for p in pts[1:-1]: mb.cyl((p.x,p.y,p.z-0.07),0.022,0.05,'emit_warm',seg=8,cap_bot=True)
    tube(mb,[(0,-Dd/2-0.2,0),(0,-Dd/2-0.2,2.65)],0.03,'wood',sides=6,tint=(0.4,0.3,0.22)) if False else None
    obj=finish(mb,'work_stage',[],seed=25,grime=0.6,damp_h=0.2)
    return obj,dict(category='work',notes='Live-bar stage 4.4 x 2.6 m, 0.45 m high, banner backdrop, PA speakers on stands, wedges, mic stand, amp, keyboard, festoon bulbs (emit_warm). Performer stands near (0, -0.7) on the deck facing -Y.',perform=[0,-0.7,0.45])
def bar_counter():
    mb=MB(); W=2.4; Dd=0.6; Hh=1.05
    mb.box((-W/2,-Dd/2,0),(W/2,Dd/2,Hh-0.05),'wood',tint=(0.35,0.22,0.14))
    mb.box((-W/2-0.05,-Dd/2-0.08,Hh-0.05),(W/2+0.05,Dd/2,Hh),'wood',tint=(0.25,0.15,0.1))
    rnd=random.Random(4)
    for i in range(9):
        x=-1.0+i*0.24; col=[(0.08,0.35,0.12),(0.45,0.2,0.05),(0.75,0.6,0.15)][i%3]
        mb.cyl((x,0.12,Hh),0.035,0.2,'glass_louvre',seg=10,tint=col); mb.cyl((x,0.12,Hh+0.2),0.012,0.08,'glass_louvre',seg=6,tint=col)
    for x in (-0.7,0.1,0.8): mb.cyl((x,-0.2,Hh),0.035,0.12,'glass_clear',seg=10)
    obj=finish(mb,'work_bar_counter',[],seed=26,grime=0.6,damp_h=0.2)
    return obj,dict(category='work',notes='Bar counter 2.4 x 0.6 m (1.05 m) with bottles and glasses.')

BUILDERS={
 'work_room_barber':lambda:room('work_room_barber',5.0,4.2,3.0,'worn_tile',(0.62,0.78,0.86),band_tint=(0.18,0.36,0.52)),
 'work_room_class':lambda:room('work_room_class',7.0,6.0,3.2,'concrete',(0.93,0.88,0.7),band_tint=(0.25,0.45,0.32),lights=3),
 'work_room_bank':lambda:room('work_room_bank',7.0,5.0,3.2,'terrazzo',(0.95,0.95,0.93),band_tint=None,lights=3,window=False),
 'work_room_office':lambda:room('work_room_office',6.0,5.0,3.0,'wood_floor',(0.93,0.93,0.92),band_tint=(0.36,0.25,0.5),lights=2),
 'work_pos_stand':pos_stand,'work_pos_aframe':pos_aframe,
 'work_market_stall':market_stall,
 'work_buka_kitchen':buka_kitchen,'work_buka_menu':buka_menu,'work_bench_table':bench_table,
 'work_barber_station':barber_station,'work_barber_chair':barber_chair,
 'work_sign_barber':wall_sign('work_sign_barber','barber_sign',2.0,0.5,light=True),
 'work_poster_styles':wall_sign('work_poster_styles','barber_poster',0.6,0.75,frame=(0.8,0.8,0.78)),
 'work_blackboard':blackboard,'work_school_desk':school_desk,'work_teacher_desk':teacher_desk,
 'work_bank_counter':bank_counter,'work_queue_posts':queue_posts,
 'work_sign_bank':wall_sign('work_sign_bank','bank_sign',2.6,0.5,frame=(0.95,0.95,0.93)),
 'work_poster_bank':wall_sign('work_poster_bank','bank_poster',0.6,0.7,frame=(0.95,0.95,0.93)),
 'work_desk_code':office_desk('work_desk_code','code_screen'),'work_desk_help':office_desk('work_desk_help','desk_screen'),
 'work_kanban':wall_sign('work_kanban','kanban',1.6,0.8,frame=(0.75,0.75,0.75)),
 'work_security_booth':security_booth,'work_boom_barrier':boom_barrier,
 'work_sign_estate':post_sign('work_sign_estate','estate_sign',1.4,0.7,0.9,tint=(0.95,0.93,0.88)),
 'work_sign_park':post_sign('work_sign_park','park_sign',4.0,1.0,2.2,tint=(0.2,0.2,0.2)),
 'work_parcel_shelf':parcel_shelf,'work_parcel_stack':parcel_stack,'work_delivery_box':delivery_box,
 'work_sign_dispatch':wall_sign('work_sign_dispatch','dispatch_logo',1.6,0.8,frame=(0.7,0.2,0.15)),
 'work_stage':stage,'work_bar_counter':bar_counter,
 'work_ceiling_fan':lambda:(lambda o:(finish(MB().box((0,0,0),(0.001,0.001,0.001),'metal_dark'),'work_ceiling_fan',[o],seed=27,grime=0.2,damp_h=0,ground=False),dict(category='prop',notes='Ceiling fan (Poly Haven ceiling_fan, CC0), hangs 0.52 m below its origin.')))(ph('ceiling_fan',1800,(0,0,0))),
 'work_tv':lambda:(lambda o:(finish(MB().box((0,0,0),(0.001,0.001,0.001),'metal_dark'),'work_tv',[o],seed=28,grime=0.3,damp_h=0),dict(category='prop',notes='Small CRT television (Poly Haven television_02, CC0).')))(ph('television_02',1200,(0,0,0),rotz=math.pi)),
 'work_wall_clock':lambda:(lambda o:(finish(MB().box((0,0,0),(0.001,0.001,0.001),'metal_dark'),'work_wall_clock',[o],seed=29,grime=0.2,damp_h=0,ground=False),dict(category='prop',notes='Wall clock (Poly Haven wall_clock, CC0), centre at origin.')))(ph('wall_clock',1200,(0,0,0),rotz=math.pi)),
 'work_cash_register':lambda:(lambda o:(finish(MB().box((0,0,0),(0.001,0.001,0.001),'metal_dark'),'work_cash_register',[o],seed=30,grime=0.3,damp_h=0),dict(category='prop',notes='Cash register (Poly Haven CashRegister_01, CC0).')))(ph('CashRegister_01',2000,(0,0,0),rotz=math.pi,scale=0.6)),
}
