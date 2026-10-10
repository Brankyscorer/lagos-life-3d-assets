# Lagos Life transit + venue kit (Step 05). Blender Z-up, fronts face -Y (= +Z in three.js). Metres, origin on the ground.
# Vehicles are split into a wheel-less body plus one wheel mesh per type so the game can spin wheels; *_lod1 are merged, decimated far versions.
import math, random, json, bpy
from mathutils import Vector as V, Matrix
from envlib import *
import envlib
from assets_buildings import finish
from assets_props import tube
import assets_vehicles as AV
from phlib import ph_load, ph_place, join

_TR=json.load(open('/workspace/env/tex/transit_rects.json'))
envlib.MAT_FLAT.update({'atlas_transit':((1,1,1),0.6,0.0),'glass_clear':((0.8,0.9,0.92),0.05,0.0)})
def tr(name,flip=False):
    u0,v0,u1,v1=[c/2048 for c in _TR[name]]
    bl=(u0,1-v1); br=(u1,1-v1); tr_=(u1,1-v0); tl=(u0,1-v0)
    if flip: bl,br,tr_,tl=br,bl,tl,tr_
    return ('uvs',[bl,br,tr_,tl])
def tpanel(mb,o,u,v,w,h,region,mat='atlas_transit',**k):
    o=V(o); u=V(u).normalized(); v=V(v).normalized()
    mb.quad(o,o+u*w,o+u*w+v*h,o+v*h,mat,uv=tr(region),grime=k.pop('grime',0.15),**k)
ROT=Matrix.Rotation(-math.pi/2,4,'Z')   # vehicle builders model front=+X, then rotate to -Y
def three_of(c):  # pre-rotation Blender point -> three.js
    return [round(c[1],3),round(c[2],3),round(c[0],3)]

# ------------------------------------------------------------------ wheel capture for the existing env vehicles
_orig_wheel=AV.wheel
class Capture:
    def __init__(s,keep=False,seg=None): s.calls=[]; s.keep=keep; s.seg=seg
    def __call__(s,mb,c,R,Rr,W,side,seg=16,**k):
        s.calls.append(dict(c=tuple(c),R=R,Rr=Rr,W=W,side=side,seg=seg,k=k))
        if s.keep: _orig_wheel(mb,c,R,Rr,W,side,seg=s.seg or seg,**k)
def run_captured(builder,keep=False,seg=None):
    cap=Capture(keep,seg); AV.wheel=cap
    try: ob,meta=builder()
    finally: AV.wheel=_orig_wheel
    return ob,meta,cap.calls
def wheel_obj(name,call,seg=None,spokes=None):
    mb=MB(); k=dict(call['k'])
    if spokes is not None: k['spokes']=spokes
    _orig_wheel(mb,(0,0,0),call['R'],call['Rr'],call['W'],1,seg=seg or call['seg'],**k)
    mb.transform(ROT)
    return finish(mb,name,[],seed=7,grime=0.4,damp_h=0,ground=False,smooth=50)
def wheels_meta(calls,wheel_ids):
    return [dict(pos=three_of(c['c']),radius=c['R'],mirror=c['side']<0,wheel=w) for c,w in zip(calls,wheel_ids)]
def decimate(ob,target):
    tris=tri_count(ob)
    if tris>target:
        bpy.context.view_layer.objects.active=ob
        m=ob.modifiers.new('dec','DECIMATE'); m.ratio=target/tris*0.97; m.use_collapse_triangulate=True
        bpy.ops.object.modifier_apply(modifier='dec')
    return ob
def rename(ob,name): ob.name=name; ob.data.name=name; return ob

ENV_VEH={'danfo':AV.danfo,'keke':AV.keke,'okada':AV.okada}
def env_body(kind):
    def b():
        ob,meta,calls=run_captured(ENV_VEH[kind])
        rename(ob,f'veh_{kind}_body')
        ids=[f'veh_wheel_{kind}' + ('_r' if kind=='okada' and i==1 else '') for i in range(len(calls))]
        return ob,dict(category='vehicle',notes=f'{kind} body without wheels; place wheel nodes at wheels[].pos (three.js, axle centre) and spin them about local X. mirror=true: rotate the wheel PI about Y.',wheels=wheels_meta(calls,ids))
    return b
def env_wheel(kind,index=0):
    def b():
        envlib.clear_scene(); _,_,calls=run_captured(ENV_VEH[kind]); envlib.clear_scene()
        nm=f'veh_wheel_{kind}'+('_r' if index==1 else '')
        ob=wheel_obj(nm,calls[index])
        return ob,dict(category='vehicle',notes=f'{kind} wheel, axle along X through the origin, outer face +X. Radius {calls[index]["R"]} m.',radius=calls[index]['R'])
    return b
def env_lod1(kind,target):
    def b():
        ob,meta,calls=run_captured(ENV_VEH[kind],keep=True,seg=8)
        rename(ob,f'veh_{kind}_lod1'); decimate(ob,target)
        return ob,dict(category='vehicle',notes=f'{kind} LOD1 (wheels merged, decimated) for distant traffic.')
    return b

# ------------------------------------------------------------------ cab (Gidi Ride sedan)
def sedan_parts(mb,wheel_fn):
    W=0.88  # half width
    PAINT=(0.93,0.94,0.95); GRN=(0.08,0.55,0.32)
    T=[(0.22,2.22,-2.22,0.80,0.25),(0.30,2.30,-2.30,0.86,0.3),(0.55,2.33,-2.32,0.88,0.32),(0.78,2.30,-2.30,0.88,0.32),(0.86,2.22,-2.25,0.86,0.30),
       (0.90,0.95,-1.40,0.84,0.22),(1.12,0.45,-1.05,0.76,0.2),(1.36,-0.05,-0.72,0.64,0.18),(1.43,-0.15,-0.62,0.58,0.15)]
    rings=[AV.rrect(f,r,w,rad,z,3) for z,f,r,w,rad in T]
    n=len(rings[0])
    for k in range(len(rings)-1):
        for i in range(n):
            j=(i+1)%n; a,b,c,d=rings[k][i],rings[k][j],rings[k+1][j],rings[k+1][i]; ctr=(a+b+c+d)/4
            if 5<=k<=6: mat='glass'; tint=WHITE
            else: mat='car_paint'; tint=GRN if 0.55<=ctr.z<=0.62 else PAINT
            mb.quad(a,b,c,d,mat,tint=tint,grime=0.6 if mat=='car_paint' else 0)
    mb.face(rings[-1],'car_paint',tint=PAINT,grime=0.4); mb.face(list(reversed(rings[0])),'metal_dark',tint=(0.3,0.3,0.3))
    # pillars over the glass band (A, B, C) on both sides + roof-edge strip
    def gx(z,front=True):
        (z0,f0,r0,_,_),(z1,f1,r1,_,_)=T[5],T[7]
        t=(z-z0)/(z1-z0); return (f0+(f1-f0)*t) if front else (r0+(r1-r0)*t)
    def hwz(z): (z0,_,_,w0,_),(z1,_,_,w1,_)=T[5],T[7]; return w0+(w1-w0)*(z-z0)/(z1-z0)
    for s in (-1,1):
        for (xa,xb) in ((-0.42,-0.30),):
            p=[V((xa,s*(hwz(0.9)+0.006),0.9)),V((xb,s*(hwz(0.9)+0.006),0.9)),V((xb+0.05,s*(hwz(1.36)+0.006),1.36)),V((xa+0.05,s*(hwz(1.36)+0.006),1.36))]
            if s>0: p=[p[1],p[0],p[3],p[2]]
            mb.quad(*p,'car_paint',tint=(0.05,0.05,0.05),grime=0)
        # A and C pillars: thin strips along the glass corners
        for front in (True,False):
            pts=[V((gx(z,front)+(-0.06 if front else 0.06),s*(hwz(z)-0.02),z)) for z in (0.9,1.36)]
            q=[pts[0],pts[0]+V((0.0,s*0.03,0)),pts[1]+V((0.0,s*0.03,0)),pts[1]]
            if s>0: q=[q[1],q[0],q[3],q[2]]
            mb.quad(*q,'car_paint',tint=(0.05,0.05,0.05),grime=0)
        # green side stripe
        p=[V((-1.95,s*0.884,0.50)),V((1.95,s*0.884,0.50)),V((1.95,s*0.884,0.57)),V((-1.95,s*0.884,0.57))]
        if s>0: p=[p[1],p[0],p[3],p[2]]
        mb.quad(*p,'car_paint',tint=GRN,grime=0.3)
        # door shut lines + handles + Gidi Ride logo on the front door
        for x in (0.98,-0.36,-1.45):
            p=[V((x,s*0.885,0.3)),V((x+0.012,s*0.885,0.3)),V((x+0.012,s*0.885,0.86)),V((x,s*0.885,0.86))]
            if s>0: p=[p[1],p[0],p[3],p[2]]
            mb.quad(*p,'cable',grime=0)
        for x in (0.62,-0.75): mb.obox((x,s*0.89,0.80),(0.14,0.02,0.03),0,'chrome',grime=0)
        if s<0: tpanel(mb,(0.2,s*0.887,0.6),(1,0,0),(0,0,1),0.48,0.24,'cab_logo')
        else: tpanel(mb,(0.68,s*0.887,0.6),(-1,0,0),(0,0,1),0.48,0.24,'cab_logo')
        mb.obox((0.88,s*0.93,0.98),(0.1,0.1,0.08),0,'car_paint',tint=PAINT)  # mirror
        mb.obox((0.85,s*0.86,0.98),(0.06,0.08,0.03),0,'metal_dark')
        # wheel-arch shadows
        for xw in (1.38,-1.38):
            seg=10; pts=[V((xw+0.38*math.cos(math.pi*i/seg),s*0.886,0.31+0.38*math.sin(math.pi*i/seg))) for i in range(seg+1)]
            pts=[V((xw+0.38,s*0.886,0.22))]+pts+[V((xw-0.38,s*0.886,0.22))]
            mb.face(pts if s<0 else list(reversed(pts)),'cable',grime=0)
    # lights, grille, plates, roof sign
    for s in (-1,1):
        tpanel(mb,(2.315,s*0.72-(0.12 if s>0 else 0)+0.0,0.62),(0,1,0),(0,0,1),0.24,0.12,'headlight',grime=0)
        tpanel(mb,(-2.305,s*0.72+(0.12 if s<0 else 0),0.66),(0,-1,0),(0,0,1),0.24,0.12,'taillight',grime=0)
    tpanel(mb,(2.325,-0.36,0.44),(0,1,0),(0,0,1),0.72,0.14,'grille',grime=0)
    tpanel(mb,(2.335,-0.2,0.28),(0,1,0),(0,0,1),0.4,0.12,'plate',grime=0.2)
    tpanel(mb,(-2.325,0.2,0.42),(0,-1,0),(0,0,1),0.4,0.12,'plate',grime=0.2)
    mb.box((2.30,-0.84,0.22),(2.35,0.84,0.34),'plastic',tint=(0.025,0.025,0.025)); mb.box((-2.35,-0.84,0.22),(-2.30,0.84,0.36),'plastic',tint=(0.025,0.025,0.025))
    mb.box((-0.55,-0.2,1.43),(-0.25,0.2,1.56),'plastic',tint=(0.08,0.5,0.3))   # roof sign box
    tpanel(mb,(-0.56,0.18,1.45),(0,-1,0),(0,0,1),0.36,0.09,'cab_logo'); tpanel(mb,(-0.24,-0.18,1.45),(0,1,0),(0,0,1),0.36,0.09,'cab_logo')
    for xw in (1.38,-1.38):
        for s in (-1,1): wheel_fn(mb,(xw,s*0.77,0.31),0.31,0.19,0.2,s,seg=16)
def cab_body():
    calls=[]; mb=MB()
    sedan_parts(mb,lambda mb_,c,R,Rr,W,side,seg=16,**k: calls.append(dict(c=c,R=R,Rr=Rr,W=W,side=side,seg=seg,k=k)))
    mb.transform(ROT); ob=finish(mb,'veh_cab_body',[],seed=41,grime=0.4,damp_h=0.3,smooth=40)
    return ob,dict(category='vehicle',notes='Gidi Ride cab: white sedan, green stripe, door logos and roof sign. Body without wheels; wheels[] gives three.js axle centres.',wheels=wheels_meta(calls,['veh_wheel_cab']*4))
def cab_wheel():
    mb=MB(); AV.wheel(mb,(0,0,0),0.31,0.19,0.2,1,seg=16); mb.transform(ROT)
    return finish(mb,'veh_wheel_cab',[],seed=7,grime=0.3,damp_h=0,ground=False,smooth=50),dict(category='vehicle',notes='Cab wheel (195/65R15 look), axle along X.',radius=0.31)
def cab_lod1():
    mb=MB(); sedan_parts(mb,lambda mb_,c,R,Rr,W,side,seg=16,**k: AV.wheel(mb_,c,R,Rr,W,side,seg=8)); mb.transform(ROT)
    ob=finish(mb,'veh_cab_lod1',[],seed=41,grime=0.4,damp_h=0.3,smooth=40); decimate(ob,1900)
    return ob,dict(category='vehicle',notes='Cab LOD1')

# ------------------------------------------------------------------ BRT bus
def bus_parts(mb,wheel_fn):
    L=6.0; HW=1.27; BLUE=(0.02,0.12,0.42); WHT=(0.95,0.95,0.95); RED=(0.78,0.12,0.16)
    T=[(0.30,L-0.05,-L+0.05,HW-0.03,0.12),(0.38,L,-L,HW,0.14),(1.15,L,-L,HW,0.14),(1.25,L-0.01,-L+0.01,HW,0.14),(2.62,L-0.12,-L+0.02,HW,0.14),(2.95,L-0.2,-L+0.06,HW-0.02,0.2),(3.05,L-0.35,-L+0.2,HW-0.12,0.28)]
    rings=[AV.rrect(f,r,w,rad,z,3) for z,f,r,w,rad in T]; n=len(rings[0])
    for k in range(len(rings)-1):
        for i in range(n):
            j=(i+1)%n; a,b,c,d=rings[k][i],rings[k][j],rings[k+1][j],rings[k+1][i]; ctr=(a+b+c+d)/4
            if k==3: mat='glass'; tint=WHITE
            elif k==2: mat='car_paint'; tint=WHT
            else: mat='car_paint'; tint=BLUE if ctr.z<2.9 else WHT
            mb.quad(a,b,c,d,mat,tint=tint,grime=0.7 if mat!='glass' else 0)
    mb.face(rings[-1],'car_paint',tint=WHT,grime=1.0); mb.face(list(reversed(rings[0])),'metal_dark',tint=(0.3,0.3,0.3))
    for s in (-1,1):
        # window mullions every 1.2 m
        for x in [-L+0.6+1.2*i for i in range(10)]:
            p=[V((x,s*(HW+0.004),1.25)),V((x+0.08,s*(HW+0.004),1.25)),V((x+0.08,s*(HW+0.004),2.62)),V((x,s*(HW+0.004),2.62))]
            if s>0: p=[p[1],p[0],p[3],p[2]]
            mb.quad(*p,'car_paint',tint=(0.08,0.08,0.09),grime=0)
        # livery band under the windows
        if s<0: tpanel(mb,(-L+0.4,s*(HW+0.006),0.86),(1,0,0),(0,0,1),7.2,0.9,'brt_livery')
        else: tpanel(mb,(L-1.2,s*(HW+0.006),0.86),(-1,0,0),(0,0,1),7.2,0.9,'brt_livery')
        mb.quad(*( [V((-L+0.1,s*(HW+0.005),0.4)),V((L-0.1,s*(HW+0.005),0.4)),V((L-0.1,s*(HW+0.005),0.5)),V((-L+0.1,s*(HW+0.005),0.5))][::(1 if s<0 else -1)] ),'car_paint',tint=RED,grime=0.4)
        for xw in (3.6,-2.6):
            seg=10; pts=[V((xw+0.62*math.cos(math.pi*i/seg),s*(HW+0.005),0.5+0.62*math.sin(math.pi*i/seg))) for i in range(seg+1)]
            pts=[V((xw+0.62,s*(HW+0.005),0.3))]+pts+[V((xw-0.62,s*(HW+0.005),0.3))]
            mb.face(pts if s<0 else list(reversed(pts)),'cable',grime=0)
    # doors on the kerb side (right of travel = -Y before rotation): two double doors with glass
    for x0 in (4.2,0.2):
        mb.quad(V((x0,-HW-0.01,0.38)),V((x0+1.2,-HW-0.01,0.38)),V((x0+1.2,-HW-0.01,2.62)),V((x0,-HW-0.01,2.62)),'glass',grime=0)
        for x in (x0,x0+0.58,x0+1.16): mb.box((x,-HW-0.03,0.38),(x+0.05,-HW-0.005,2.62),'metal_dark')
        mb.box((x0,-HW-0.03,1.3),(x0+1.2,-HW-0.005,1.36),'metal_dark')
    # front: big windscreen + destination display + lights
    mb.quad(V((L+0.005,-HW+0.1,1.0)),V((L+0.005,HW-0.1,1.0)),V((L-0.1,HW-0.1,2.5)),V((L-0.1,-HW+0.1,2.5)),'glass',grime=0)
    tpanel(mb,(L-0.115,-0.8,2.62),(0,1,0),(0,0,0.95),1.6,0.26,'brt_dest',grime=0)
    for s in (-1,1):
        tpanel(mb,(L+0.006,s*0.95-(0.28 if s>0 else 0),0.55),(0,1,0),(0,0,1),0.28,0.16,'headlight',grime=0)
        tpanel(mb,(-L-0.006,s*0.95+(0.28 if s<0 else 0),0.6),(0,-1,0),(0,0,1),0.28,0.3,'taillight',grime=0)
    mb.box((L,-HW,0.3),(L+0.08,HW,0.52),'plastic',tint=(0.12,0.12,0.12)); mb.box((-L-0.08,-HW,0.3),(-L,HW,0.52),'plastic',tint=(0.12,0.12,0.12))
    tpanel(mb,(L+0.085,-0.25,0.33),(0,1,0),(0,0,1),0.5,0.15,'plate',grime=0.2)
    mb.quad(V((-L-0.004,HW-0.2,1.4)),V((-L-0.004,-HW+0.2,1.4)),V((-L-0.004,-HW+0.2,2.5)),V((-L-0.004,HW-0.2,2.5)),'glass',grime=0)
    mb.box((-2.5,-0.9,3.05),(0.5,0.9,3.3),'car_paint',tint=(0.85,0.86,0.87))   # roof AC pod
    for s in (-1,1): mb.obox((L+0.15,s*1.38,2.3),(0.08,0.06,0.35),0,'metal_dark')
    for xw in (3.6,-2.6):
        for s in (-1,1): wheel_fn(mb,(xw,s*(HW-0.17),0.5),0.5,0.3,0.3,s,seg=18)
def brt_body():
    calls=[]; mb=MB()
    bus_parts(mb,lambda mb_,c,R,Rr,W,side,seg=16,**k: calls.append(dict(c=c,R=R,Rr=Rr,W=W,side=side,seg=seg,k=k)))
    mb.transform(ROT); ob=finish(mb,'veh_brt_body',[],seed=42,grime=0.5,damp_h=0.4,smooth=35)
    return ob,dict(category='vehicle',notes='12 m BRT bus, blue/white with red skirt line, doors on the kerb (right) side. Body without wheels.',wheels=wheels_meta(calls,['veh_wheel_brt']*4))
def brt_wheel():
    mb=MB(); AV.wheel(mb,(0,0,0),0.5,0.3,0.3,1,seg=18); mb.transform(ROT)
    return finish(mb,'veh_wheel_brt',[],seed=7,grime=0.4,damp_h=0,ground=False,smooth=50),dict(category='vehicle',notes='BRT wheel',radius=0.5)
def brt_lod1():
    mb=MB(); bus_parts(mb,lambda mb_,c,R,Rr,W,side,seg=16,**k: AV.wheel(mb_,c,R,Rr,W,side,seg=8)); mb.transform(ROT)
    ob=finish(mb,'veh_brt_lod1',[],seed=42,grime=0.5,damp_h=0.4,smooth=35); decimate(ob,1900)
    return ob,dict(category='vehicle',notes='BRT LOD1')

# ------------------------------------------------------------------ street furniture
def bus_shelter():
    mb=MB(); Wd=4.2; D=1.5; H=2.7; BLUE=(0.06,0.3,0.65)
    for x in (-Wd/2+0.1,Wd/2-0.1):
        for y in (0.6,):
            mb.box((x-0.05,y-0.05,0),(x+0.05,y+0.05,H),'metal_paint',tint=BLUE)
        mb.box((x-0.04,-0.5,0),(x+0.04,-0.42,H-0.15),'metal_paint',tint=BLUE)
    # sloped roof with fascia
    roof=[V((-Wd/2-0.2,-D/2-0.35,H-0.12)),V((Wd/2+0.2,-D/2-0.35,H-0.12)),V((Wd/2+0.2,D/2+0.1,H+0.05)),V((-Wd/2-0.2,D/2+0.1,H+0.05))]
    mb.quad(*roof,'metal_paint',tint=(0.85,0.86,0.88),grime=1.2); mb.quad(*[roof[i]+V((0,0,-0.04)) for i in (1,0,3,2)],'metal_paint',tint=(0.6,0.62,0.65))
    tpanel(mb,(-Wd/2-0.2,-D/2-0.36,H-0.44),(1,0,0),(0,0,1),1.3,0.32,'stop_sign')
    mb.box((-Wd/2-0.2+1.3,-D/2-0.36,H-0.44),(Wd/2+0.2,-D/2-0.34,H-0.12),'metal_paint',tint=BLUE)
    # back glass + ad panel + map
    mb.quad(V((Wd/2-0.15,0.62,0.25)),V((-Wd/2+0.15,0.62,0.25)),V((-Wd/2+0.15,0.62,2.3)),V((Wd/2-0.15,0.62,2.3)),'glass_clear',grime=0)
    mb.quad(V((-Wd/2+0.15,0.6,0.25)),V((Wd/2-0.15,0.6,0.25)),V((Wd/2-0.15,0.6,2.3)),V((-Wd/2+0.15,0.6,2.3)),'glass_clear',grime=0)
    mb.box((-Wd/2+0.15,0.6,0.2),(Wd/2-0.15,0.66,0.26),'metal_paint',tint=BLUE); mb.box((-Wd/2+0.15,0.6,2.3),(Wd/2-0.15,0.66,2.36),'metal_paint',tint=BLUE)
    tpanel(mb,(Wd/2-0.35,0.58,0.95),(-1,0,0),(0,0,1),1.3,0.65,'stop_map')
    # side panel with ad
    mb.box((-Wd/2+0.05,-0.42,0.3),(-Wd/2+0.12,0.58,2.1),'metal_paint',tint=BLUE)
    tpanel(mb,(-Wd/2+0.125,0.5,0.4),(0,-1,0),(0,0,1),0.84,1.6,'poster_2')
    # bench: steel frame + slats
    for x in (-1.2,0,1.2): mb.box((x-0.03,0.2,0),(x+0.03,0.55,0.45),'steel_galv')
    for i in range(4): mb.box((-1.6,0.2+i*0.09,0.43),(1.6,0.27+i*0.09,0.46),'steel_galv',tint=(0.9,0.9,0.9))
    for i in range(3): mb.box((-1.6,0.55,0.55+i*0.1),(1.6,0.58,0.62+i*0.1),'steel_galv',tint=(0.9,0.9,0.9))
    # kerb slab + bin
    mb.box((-Wd/2-0.3,-D/2-0.4,0),(Wd/2+0.3,D/2+0.2,0.06),'concrete',tint=(0.8,0.8,0.78),grime=1.5)
    bin_=ph('metal_trash_can',600,(Wd/2+0.6,0.2,0),0)
    obj=finish(mb,'stop_shelter',[bin_],seed=51,grime=0.8,damp_h=0.4)
    return obj,dict(category='street',notes='Bus-stop shelter 4.2 m wide, blue LAMATA-style, BUS STOP fascia on the road side (+Z), bench, route map, bin. Passengers wait at z 0.1..0.5 behind the kerb slab front edge (z +1.15).',wait=[0,0,-0.3])
def ph(pid,tris,loc=(0,0,0),rotz=0.0,scale=1.0,tint=None):
    import glob
    if not glob.glob(f'/workspace/env/src/phm/{pid}/*.gltf'):
        import phlib as P; src=f'/workspace/workkit/src/phm/{pid}'
        import shutil,os
        if os.path.exists(src): shutil.copytree(src,f'/workspace/env/src/phm/{pid}')
    return ph_place(ph_load(pid,target_tris=tris),loc,rotz,scale,tint=tint)
def billboard(n):
    def b():
        mb=MB(); Wd=6.0; Hh=3.0; z0=4.2
        for x in (-1.8,1.8):
            mb.cyl((x,0.25,0),0.14,z0+0.2,'metal_paint',seg=10,tint=(0.35,0.36,0.38))
            mb.box((x-0.3,-0.05,0),(x+0.3,0.55,0.25),'concrete',tint=(0.75,0.74,0.7))
        mb.box((-Wd/2-0.12,0.0,z0-0.12),(Wd/2+0.12,0.22,z0+Hh+0.12),'metal_paint',tint=(0.18,0.18,0.2))
        tpanel(mb,(-Wd/2,-0.005,z0),(1,0,0),(0,0,1),Wd,Hh,f'ad_{n}',grime=0.35)
        # catwalk + lamps
        mb.box((-Wd/2,-0.75,z0-0.32),(Wd/2,0.0,z0-0.26),'steel_galv',tint=(0.7,0.7,0.7))
        for i in range(25): x=-Wd/2+i*Wd/24; tube(mb,[(x,-0.75,z0-0.26),(x,-0.75,z0+0.6)],0.012,'steel_galv',sides=3)
        tube(mb,[(-Wd/2,-0.75,z0+0.6),(Wd/2,-0.75,z0+0.6)],0.018,'steel_galv',sides=4)
        for x in (-2.0,0,2.0):
            tube(mb,[(x,0,z0+Hh+0.1),(x,-0.8,z0+Hh+0.4)],0.02,'metal_dark',sides=4); mb.obox((x,-0.85,z0+Hh+0.35),(0.4,0.18,0.1),0,'metal_dark'); mb.obox((x,-0.85,z0+Hh+0.29),(0.36,0.14,0.01),0,'emit_cool',grime=0)
        obj=finish(mb,f'bb_billboard_{n}',[],seed=60+n,grime=0.9,damp_h=0.5)
        return obj,dict(category='street',notes=f'Roadside billboard 6 x 3 m (face 4.2-7.2 m up) with original ad {n}, catwalk and lamps. Faces +Z.')
    return b
def zebra():
    mb=MB()
    for i in range(9):
        y=-3.8+i*0.95
        grid_quad(mb,V((-1.5,y,0.012)),V((1,0,0)),V((0,1,0)),3.0,0.5,'plastic',cu=1.0,cv=0.5,tint=(0.92,0.92,0.88),grime=1.4)
    for x in (-2.3,2.3): grid_quad(mb,V((x-0.15,-4.2,0.012)),V((1,0,0)),V((0,1,0)),0.3,8.4,'plastic',cu=0.3,cv=1.0,tint=(0.92,0.92,0.88),grime=1.4)
    obj=finish(mb,'street_zebra',[],seed=70,grime=1.0,damp_h=0,ground=True)
    return obj,dict(category='street',notes='Zebra crossing paint across a 8.4 m road along three.js Z, 3 m wide along X, with stop lines at x=+-2.3. Sits 1 cm above the road.')
def wheelbarrow():
    mb=MB(); G=(0.25,0.45,0.3)
    tray=[V((-0.35,-0.3,0.45)),V((0.35,-0.3,0.45)),V((0.45,0.45,0.75)),V((-0.45,0.45,0.75))]
    mb.quad(V((-0.25,-0.25,0.35)),V((0.25,-0.25,0.35)),V((0.3,0.35,0.35)),V((-0.3,0.35,0.35)),'metal_paint',tint=G)
    for a,b_ in ((0,1),(1,2),(2,3),(3,0)):
        lo=[V((-0.25,-0.25,0.35)),V((0.25,-0.25,0.35)),V((0.3,0.35,0.35)),V((-0.3,0.35,0.35))]
        mb.quad(lo[b_],lo[a],tray[a],tray[b_],'metal_paint',tint=G); mb.quad(lo[a],lo[b_],tray[b_],tray[a],'metal_paint',tint=G)
    for s in (-1,1):
        tube(mb,[(s*0.22,-0.55,0.25),(s*0.25,0.0,0.4),(s*0.3,1.0,0.55)],0.018,'metal_dark',sides=5)
        tube(mb,[(s*0.2,0.1,0.38),(s*0.2,0.25,0.0)],0.015,'metal_dark',sides=4)
    AV.wheel(mb,(0,-0.55,0.22),0.22,0.1,0.08,1,seg=12); mb.transform(Matrix.Rotation(math.pi/2,4,'Z'),len(mb.faces)-1) if False else None
    # yams in the tray
    for i in range(6): mb.obox((-0.2+i*0.08,0.0+(i%3)*0.1,0.6),(0.07,0.32,0.07),0.3*i,'wood',tint=(0.55,0.4,0.28))
    obj=finish(mb,'mk_wheelbarrow',[],seed=80,grime=1.0,damp_h=0.2)
    return obj,dict(category='prop',notes='Market wheelbarrow with yams; handles toward +Y (three -Z).')
def fabric_stall():
    mb=MB()
    legs=[(-1.0,-0.4),(1.0,-0.4),(-1.0,0.4),(1.0,0.4)]
    for x,y in legs: mb.box((x-0.03,y-0.03,0),(x+0.03,y+0.03,0.8),'wood',tint=(0.5,0.36,0.24))
    mb.box((-1.05,-0.45,0.8),(1.05,0.45,0.85),'wood_planks',tint=(0.65,0.5,0.35))
    for i in range(10):
        r=0.07; x=-0.9+i*0.2; region=f'fabric_{i%4+1}'
        n0=len(mb.faces); mb.cyl((x,-0.35,0.85+r),r,0.7,'atlas_transit',seg=8,axis='Y',uvmode=None,cap_top=True,cap_bot=True)
        u0,v0,u1,v1=[c/2048 for c in _TR[region]]
        for f in mb.faces[n0:]:
            pts=f['p']; f['uv']=('uvs',[(u0+(u1-u0)*((p.y+0.35)/0.7),1-v0-(v1-v0)*((math.atan2(p.z-(0.85+r),p.x-x)/math.pi+1)/2)) for p in pts])
    # back rack with hanging fabrics
    for x in (-1.0,1.0): mb.box((x-0.03,0.42,0),(x+0.03,0.48,2.0),'wood',tint=(0.5,0.36,0.24))
    mb.box((-1.05,0.42,1.95),(1.05,0.48,2.0),'wood',tint=(0.5,0.36,0.24))
    for i in range(4):
        x=-0.95+i*0.5; tpanel(mb,(x,0.4,0.9),(1,0,0),(0,0,1),0.45,1.05,f'fabric_{(i+2)%4+1}',mat='atlas_transit')
    obj=finish(mb,'mk_fabric_stall',[],seed=81,grime=0.7,damp_h=0.3)
    return obj,dict(category='prop',notes='Ankara fabric stall: table with rolled bolts and a hanging rack. Trader stands at three (0,0,-1.0) behind it? No: customers at +Z, trader behind at z=-0.9.')

# ------------------------------------------------------------------ venue facades
def sign_board(name,region,Wd,Hh,z0,posts=True,frame=(0.12,0.12,0.13),light=True):
    def b():
        mb=MB()
        if posts:
            for x in (-Wd/2+0.2,Wd/2-0.2): mb.box((x-0.05,0.0,0),(x+0.05,0.1,z0),'metal_paint',tint=(0.25,0.25,0.27))
        mb.box((-Wd/2-0.06,0.0,z0-0.06),(Wd/2+0.06,0.12,z0+Hh+0.06),'metal_paint',tint=frame)
        tpanel(mb,(-Wd/2,-0.004,z0),(1,0,0),(0,0,1),Wd,Hh,region)
        if light:
            for x in [(-Wd/2+Wd*(i+0.5)/3) for i in range(3)]:
                tube(mb,[(x,0.0,z0+Hh+0.06),(x,-0.4,z0+Hh+0.25)],0.012,'metal_dark',sides=4); mb.obox((x,-0.42,z0+Hh+0.2),(0.18,0.1,0.06),0,'metal_dark')
        obj=finish(mb,name,[],seed=hash(name)%50,grime=0.7,damp_h=0.3)
        return obj,dict(category='street',notes=f'Sign board {Wd} x {Hh} m at {z0} m, artwork {region}, faces +Z.')
    return b
def mall_front():
    mb=MB(); Wd=16.0; H=7.5; D=0.6
    # concrete frame + cladding
    grid_quad(mb,V((-Wd/2,0,0)),V((1,0,0)),V((0,0,1)),Wd,H,'plaster_paint',cu=2,cv=1.5,tint=(0.9,0.89,0.86))
    for x in (-Wd/2,-Wd/2+5.0,Wd/2-5.0,Wd/2-0.6):
        mb.box((x,-0.6,0),(x+0.6,0.0,H),'concrete',tint=(0.75,0.75,0.74))
    # glass storefront between columns + mullions
    for (xa,xb) in ((-Wd/2+0.6,-Wd/2+5.0),(-Wd/2+5.6,Wd/2-5.0),(Wd/2-4.4,Wd/2-0.6)):
        mb.quad(V((xa,-0.3,0.15)),V((xb,-0.3,0.15)),V((xb,-0.3,4.2)),V((xa,-0.3,4.2)),'glass',grime=0)
        x=xa
        while x<xb-0.1: mb.box((x,-0.34,0.15),(x+0.06,-0.28,4.2),'alu'); x+=1.45
        mb.box((xa,-0.34,2.6),(xb,-0.28,2.66),'alu'); mb.box((xa,-0.34,4.2),(xb,-0.28,4.3),'alu')
        mb.quad(V((xa,-0.05,0.15)),V((xb,-0.05,0.15)),V((xb,-0.05,4.2)),V((xa,-0.05,4.2)),'emit_cool',grime=0,ao=0)  # bright interior
    # entrance canopy + sign
    mb.box((-3.5,-3.0,4.4),(3.5,0.0,4.65),'metal_paint',tint=(0.15,0.15,0.17))
    for x in (-3.3,3.3): mb.cyl((x,-2.8,0),0.09,4.4,'alu',seg=10)
    for x in (-2.4,0,2.4): mb.obox((x,-1.5,4.38),(0.6,0.6,0.02),0,'emit_warm',grime=0)
    tpanel(mb,(-4.5,-0.65,5.0),(1,0,0),(0,0,1),9.0,1.7,'mall_sign')
    # sliding doors
    for x in (-1.2,0.0): mb.box((x,-0.36,0.15),(x+0.04,-0.3,2.6),'metal_dark')
    # entrance steps + planters + bollards
    mb.box((-Wd/2,-3.6,0),(Wd/2,0.0,0.15),'concrete',tint=(0.82,0.81,0.78),grime=1.2)
    for x in (-6.0,-4.4,4.4,6.0): mb.cyl((x,-3.4,0.15),0.1,0.8,'steel_galv',seg=8)
    pl=[ph('planter_box_01',1200,(x,-2.0,0.15),0) for x in (-5.2,5.2)]
    obj=finish(mb,'mall_front',pl,seed=90,grime=0.6,damp_h=0.4)
    return obj,dict(category='building',notes='Opebi Galleria mall front 16 x 7.5 m: glass storefronts, entrance canopy (x -3.5..3.5, z 0..3), sign, planters. Entrance at three (0,0,1.5).',entrance=[0,0,1.5])
def foodcourt_counter():
    mb=MB(); Wd=3.6
    mb.box((-Wd/2,-0.35,0),(Wd/2,0.35,1.0),'metal_paint',tint=(0.85,0.3,0.12)); mb.box((-Wd/2-0.05,-0.42,1.0),(Wd/2+0.05,0.38,1.06),'steel_galv',tint=(0.9,0.9,0.9))
    mb.box((-Wd/2,0.9,0),(Wd/2,1.0,2.9),'plaster_paint',tint=(0.95,0.92,0.85))
    tpanel(mb,(-1.2,0.88,1.9),(1,0,0),(0,0,1),2.4,1.2,'foodcourt_menu')
    # shawarma spit: tapered meat cone + heater panel
    for xx in (-1.0,1.0):
        mb.cyl((xx,0.55,1.06),0.04,0.75,'chrome',seg=8)
        mb.cyl((xx,0.55,1.15),0.17,0.55,'wood',seg=12,r2=0.11,tint=(0.62,0.38,0.2),cap_top=True)
        mb.box((xx-0.25,0.78,1.06),(xx+0.25,0.82,1.9),'metal_dark'); mb.box((xx-0.2,0.77,1.2),(xx+0.2,0.775,1.8),'emit_warm',grime=0)
    # wraps + drinks on the counter
    for i in range(5): mb.cyl((-0.4+i*0.18,-0.15,1.06),0.035,0.14,'plastic',seg=8,tint=[(0.9,0.1,0.1),(0.1,0.5,0.9),(0.95,0.75,0.1)][i%3])
    for i in range(3): mb.obox((0.3+i*0.2,-0.1,1.1),(0.08,0.2,0.08),0.2,'fabric',tint=(0.96,0.94,0.9))
    obj=finish(mb,'fc_counter',[],seed=91,grime=0.4,damp_h=0.3)
    return obj,dict(category='prop',notes='Food-court shawarma counter 3.6 m with menu board and two spits. Customer stands at three (0,0,0.9); cook behind at z -0.6.')
def cinema_front():
    mb=MB(); Wd=8.0; H=4.5
    grid_quad(mb,V((-Wd/2,0,0)),V((1,0,0)),V((0,0,1)),Wd,H,'plaster_paint',cu=2,cv=1.5,tint=(0.25,0.05,0.12))
    tpanel(mb,(-2.6,-0.02,3.3),(1,0,0),(0,0,1),5.2,1.1,'cinema_sign')
    for x,pn in ((-3.6,'poster_1'),(2.4,'poster_2')):
        mb.box((x-0.06,-0.12,0.8),(x+1.26,0.0,2.86),'metal_dark'); tpanel(mb,(x,-0.125,0.86),(1,0,0),(0,0,1),1.2,1.94,pn)
        mb.box((x,-0.13,0.82),(x+1.2,-0.125,0.86),'emit_warm',grime=0)
    # ticket booth
    mb.box((-1.6,-1.2,0),(1.6,-0.1,1.1),'wood',tint=(0.35,0.1,0.12)); mb.box((-1.65,-1.25,1.1),(1.65,-0.05,1.15),'steel_galv')
    mb.quad(V((-1.5,-1.0,1.15)),V((1.5,-1.0,1.15)),V((1.5,-1.0,2.6)),V((-1.5,-1.0,2.6)),'glass_clear',grime=0)
    mb.box((-1.6,-1.25,2.6),(1.6,-0.1,2.75),'metal_dark'); tpanel(mb,(-1.2,-1.26,2.62),(1,0,0),(0,0,1),2.4,0.6,'ticket_sign')
    for x in (-1.0,1.0): mb.box((x-0.3,-0.9,1.15),(x+0.3,-0.86,1.5),'plastic',tint=(0.1,0.1,0.1))
    # rope queue posts
    for i in range(4): mb.cyl((-2.4+i*1.6,-2.4,0),0.03,0.95,'chrome',seg=8); mb.cyl((-2.4+i*1.6,-2.4,0),0.15,0.03,'chrome',seg=10)
    for i in range(3): tube(mb,[(-2.4+i*1.6,-2.4,0.9),(-1.6+i*1.6,-2.4,0.72),(-0.8+i*1.6,-2.4,0.9)],0.02,'fabric',sides=4,tint=(0.6,0.05,0.1))
    obj=finish(mb,'cinema_front',[],seed=92,grime=0.4,damp_h=0.3)
    return obj,dict(category='building',notes='Galleria Cinemas front wall 8 x 4.5 m with lit sign, two poster lightboxes, ticket booth (customer at three (0,0,1.6)) and rope queue.')

BUILDERS={
 'veh_danfo_body':env_body('danfo'),'veh_keke_body':env_body('keke'),'veh_okada_body':env_body('okada'),
 'veh_wheel_danfo':env_wheel('danfo'),'veh_wheel_keke':env_wheel('keke'),'veh_wheel_okada':env_wheel('okada',0),'veh_wheel_okada_r':env_wheel('okada',1),
 'veh_danfo_lod1':env_lod1('danfo',1900),'veh_keke_lod1':env_lod1('keke',1500),'veh_okada_lod1':env_lod1('okada',1200),
 'veh_cab_body':cab_body,'veh_wheel_cab':cab_wheel,'veh_cab_lod1':cab_lod1,
 'veh_brt_body':brt_body,'veh_wheel_brt':brt_wheel,'veh_brt_lod1':brt_lod1,
 'stop_shelter':bus_shelter,'street_zebra':zebra,
 'bb_billboard_1':billboard(1),'bb_billboard_2':billboard(2),'bb_billboard_3':billboard(3),'bb_billboard_4':billboard(4),
 'mk_wheelbarrow':wheelbarrow,'mk_fabric_stall':fabric_stall,
 'sg_buka':sign_board('sg_buka','buka_sign',4.0,0.75,2.6),'sg_market':sign_board('sg_market','market_sign',6.0,0.75,3.4),
 'sg_hub':sign_board('sg_hub','hub_sign',3.0,0.75,2.8,posts=False),
 'mall_front':mall_front,'fc_counter':foodcourt_counter,'cinema_front':cinema_front,
}
