# Blender 4.2 helper library (yard kit copy of the street kit envlib: same MB builder, AO/grime bake, export).
# Blender is Z-up; the glTF exporter converts to Y-up. Asset fronts face -Y (=> +Z in three.js).
import bpy, bmesh, math, random, json, os
from mathutils import Vector, Matrix, noise
from mathutils.bvhtree import BVHTree
TEX='/workspace/yard/tex'
META=json.load(open(f'{TEX}/tex_meta.json'))
_R=json.load(open(f'{TEX}/atlas_rects.json'))
RECTS={k:[v[0]/1024,v[1]/1024,v[2]/1024,v[3]/1024] for grp in _R.values() for k,v in grp.items()}
WHITE=(1,1,1)
V=Vector
def tile_of(mat):
    return META.get(mat,{}).get('tile_m',1.0)

def srgb(c):  # hex or tuple 0-255 -> tuple 0-1
    if isinstance(c,str): c=tuple(int(c[i:i+2],16) for i in (1,3,5))
    if max(c)>1.0: c=tuple(x/255 for x in c)
    return tuple(c)

class MB:
    """Face-soup mesh builder. Each face keeps its own verts (merged later)."""
    def __init__(s): s.faces=[]
    def face(s,pts,mat,tint=WHITE,uv=None,grime=1.0,ao=1.0):
        pts=[V(p) for p in pts]
        s.faces.append(dict(p=pts,mat=mat,tint=srgb(tint),uv=uv,grime=grime,ao=ao)); return s
    def quad(s,a,b,c,d,mat,**k): return s.face([a,b,c,d],mat,**k)
    def box(s,mn,mx,mat,skip=(),uvs=None,**k):
        x0,y0,z0=mn; x1,y1,z1=mx
        P=lambda x,y,z:V((x,y,z))
        F={'-z':[P(x0,y0,z0),P(x0,y1,z0),P(x1,y1,z0),P(x1,y0,z0)],
           '+z':[P(x0,y0,z1),P(x1,y0,z1),P(x1,y1,z1),P(x0,y1,z1)],
           '-y':[P(x0,y0,z0),P(x1,y0,z0),P(x1,y0,z1),P(x0,y0,z1)],
           '+y':[P(x1,y1,z0),P(x0,y1,z0),P(x0,y1,z1),P(x1,y1,z1)],
           '-x':[P(x0,y1,z0),P(x0,y0,z0),P(x0,y0,z1),P(x0,y1,z1)],
           '+x':[P(x1,y0,z0),P(x1,y1,z0),P(x1,y1,z1),P(x1,y0,z1)]}
        for key,pts in F.items():
            if key in skip: continue
            kk=dict(k)
            if uvs and key in uvs: kk['uv']=uvs[key]
            s.face(pts,mat,**kk)
        return s
    def obox(s,center,size,rotz,mat,skip=(),**k):
        """oriented box rotated about Z around its center"""
        n0=len(s.faces); hx,hy,hz=[v/2 for v in size]
        s.box((-hx,-hy,-hz),(hx,hy,hz),mat,skip=skip,**k)
        M=Matrix.Translation(V(center))@Matrix.Rotation(rotz,4,'Z')
        for f in s.faces[n0:]: f['p']=[M@p for p in f['p']]
        return s
    def cyl(s,c,r,h,mat,seg=12,cap_top=True,cap_bot=False,r2=None,axis='Z',rot=None,uvmode='cyl',**k):
        r2=r if r2 is None else r2; n0=len(s.faces)
        ring=lambda z,rr:[V((rr*math.cos(2*math.pi*i/seg),rr*math.sin(2*math.pi*i/seg),z)) for i in range(seg)]
        a=ring(0,r); b=ring(h,r2)
        circ=2*math.pi*r; t=tile_of(mat)
        for i in range(seg):
            j=(i+1)%seg
            uv=None
            if uvmode=='cyl':
                u0=i/seg*circ/t; u1=(i+1)/seg*circ/t
                uv=('uvs',[(u0,0),(u1,0),(u1,h/t),(u0,h/t)])
            s.face([a[i],a[j],b[j],b[i]],mat,uv=uv,**k)
        if cap_top: s.face(b,mat,**k)
        if cap_bot: s.face(list(reversed(a)),mat,**k)
        M=Matrix.Translation(V(c))
        if axis=='X': M=M@Matrix.Rotation(math.pi/2,4,'Y')
        if axis=='Y': M=M@Matrix.Rotation(-math.pi/2,4,'X')
        if rot is not None: M=M@rot
        for f in s.faces[n0:]: f['p']=[M@p for p in f['p']]
        return s
    def transform(s,M,start=0):
        for f in s.faces[start:]: f['p']=[M@p for p in f['p']]
    def extend(s,other,M=None):
        n0=len(s.faces)
        for f in other.faces: s.faces.append(dict(f,p=[p.copy() for p in f['p']]))
        if M is not None: s.transform(M,n0)

def grid_quad(mb,o,u,v,lu,lv,mat,cu=1.0,cv=1.0,extra_v=(),**k):
    """planar rectangle o + a*u + b*v, subdivided in ~cu x cv cells (for vertex AO / grime)"""
    nu=max(1,round(lu/cu)); us=[lu*i/nu for i in range(nu+1)]
    vs=sorted(set([0,lv]+[lv*i/max(1,round(lv/cv)) for i in range(max(1,round(lv/cv)))]+[e for e in extra_v if 0<e<lv]))
    for i in range(len(us)-1):
        for j in range(len(vs)-1):
            a=o+u*us[i]+v*vs[j]; b=o+u*us[i+1]+v*vs[j]; c=o+u*us[i+1]+v*vs[j+1]; d=o+u*us[i]+v*vs[j+1]
            mb.quad(a,b,c,d,mat,**k)

def rect_uv(name,flip=False,sub=None):
    u0,v0,u1,v1=RECTS[name]
    if sub:  # sub-rect in 0..1 of the rect (x0,y0,x1,y1) with y down
        sx0,sy0,sx1,sy1=sub; du=u1-u0; dv=v1-v0
        u0,u1=u0+du*sx0,u0+du*sx1; v0,v1=v0+dv*sy0,v0+dv*sy1
    # blender uv (v up): image top v0 -> 1-v0
    bl=(u0,1-v1); br=(u1,1-v1); tr=(u1,1-v0); tl=(u0,1-v0)
    if flip: bl,br,tr,tl=br,bl,tl,tr
    return ('uvs',[bl,br,tr,tl])

def wall(mb,o,ud,n,length,height,mat,tint=WHITE,openings=(),reveal=0.18,cell=1.2,extra_z=(0.12,0.35,0.8),trim=None,**k):
    """Outer wall face from base point o along unit ud (outward normal n), with openings.
    openings: dict(x0,x1,z0,z1,kind,fill...) in wall-local metres. Returns list of opening frames for fills."""
    o=V(o); ud=V(ud).normalized(); n=V(n).normalized(); up=V((0,0,1))
    xs={0.0,length}; zs={0.0,height}
    for e in extra_z:
        if 0<e<height: zs.add(e)
    nx=max(1,round(length/cell))
    for i in range(nx): xs.add(length*i/nx)
    nz=max(1,round(height/cell))
    for i in range(nz): zs.add(height*i/nz)
    for op in openings: xs|={op['x0'],op['x1']}; zs|={op['z0'],op['z1']}
    xs=sorted(x for x in xs if -1e-6<=x<=length+1e-6); zs=sorted(z for z in zs if -1e-6<=z<=height+1e-6)
    # dedupe near-equal
    def dd(a):
        r=[a[0]]
        for x in a[1:]:
            if x-r[-1]>0.02: r.append(x)
            else: r[-1]=x if x in (length,height) else r[-1]
        return r
    xs=dd(xs); zs=dd(zs)
    def inside(x,z):
        for op in openings:
            if op['x0']-1e-6<=x<=op['x1']+1e-6 and op['z0']-1e-6<=z<=op['z1']+1e-6: return True
        return False
    for i in range(len(xs)-1):
        for j in range(len(zs)-1):
            cx=(xs[i]+xs[i+1])/2; cz=(zs[j]+zs[j+1])/2
            if inside(cx,cz): continue
            a=o+ud*xs[i]+up*zs[j]; b=o+ud*xs[i+1]+up*zs[j]; c=o+ud*xs[i+1]+up*zs[j+1]; d=o+ud*xs[i]+up*zs[j+1]
            mb.quad(a,b,c,d,mat,tint=tint,**k)
    # reveals
    for op in openings:
        r=op.get('reveal',reveal)
        if r<=0: continue
        P=lambda x,z,dep=0: o+ud*x+up*z-n*dep
        x0,x1,z0,z1=op['x0'],op['x1'],op['z0'],op['z1']
        rm=op.get('reveal_mat',mat); rt=op.get('reveal_tint',tint)
        mb.quad(P(x0,z0),P(x0,z0,r),P(x0,z1,r),P(x0,z1),rm,tint=rt)       # left jamb
        mb.quad(P(x1,z0,r),P(x1,z0),P(x1,z1),P(x1,z1,r),rm,tint=rt)       # right jamb
        mb.quad(P(x0,z1),P(x0,z1,r),P(x1,z1,r),P(x1,z1),rm,tint=rt)       # head
        if op['kind']!='door' and op['kind']!='shop':
            mb.quad(P(x0,z0,r),P(x0,z0),P(x1,z0),P(x1,z0,r),rm,tint=rt)   # sill (inner)
        f=op.get('fill')
        if f: f(mb,P(x0,z0,r),ud,up,n,x1-x0,z1-z0,op)
    return mb

# ---------- opening fills ----------
def fill_window(mb,base,ud,up,n,w,h,op):
    win=op.get('win','win_louvre_0')
    mb.quad(base,base+ud*w,base+ud*w+up*h,base+up*h,'atlas_glass',uv=rect_uv(win),grime=0.0)
    # concrete sill protruding
    r=op.get('reveal',0.18)
    s0=base+n*(r+0.06)-ud*0.06-up*0.06
    sill_box(mb,s0,ud,n,up,w+0.12,r+0.06+0.02,0.06,'concrete',op.get('sill_tint',(0.85,0.85,0.82)))
    if op.get('bars',True):
        bt=op.get('bar_tint',(0.92,0.92,0.9))
        b0=base+n*(r+0.035)
        mb.quad(b0,b0+ud*w,b0+ud*w+up*h,b0+up*h,'bars',uv=rect_uv('bars'),tint=bt,grime=0.3)
def sill_box(mb,o,ud,n,up,lx,ly,lz,mat,tint):
    # box with corner o, extents along ud (lx), -n (ly, into wall), up (lz)
    P=lambda a,b,c:o+ud*a-n*b+up*c
    c=[P(0,0,0),P(lx,0,0),P(lx,ly,0),P(0,ly,0),P(0,0,lz),P(lx,0,lz),P(lx,ly,lz),P(0,ly,lz)]
    for f in [(0,1,5,4),(1,2,6,5),(3,0,4,7),(4,5,6,7),(3,2,1,0)]:
        mb.quad(*[c[i] for i in f],mat,tint=tint)
def wbox(mb,o,ud,up,n,lx,lz,ly,mat,tint=WHITE,**k):
    """box on wall: corner o, lx along ud, lz along up, ly outward along n"""
    P=lambda a,b,c:o+ud*a+up*b+n*c
    c=[P(0,0,0),P(lx,0,0),P(lx,lz,0),P(0,lz,0),P(0,0,ly),P(lx,0,ly),P(lx,lz,ly),P(0,lz,ly)]
    for f in [(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:
        mb.quad(*[c[i] for i in f],mat,tint=tint,**k)
def fill_door(mb,base,ud,up,n,w,h,op):
    d=op.get('door','door_wood_a')
    if w>1.3:  # double door
        mb.quad(base,base+ud*w/2,base+ud*w/2+up*h,base+up*h,'atlas_sign',uv=rect_uv(d),grime=0.5)
        mb.quad(base+ud*w/2,base+ud*w,base+ud*w+up*h,base+ud*w/2+up*h,'atlas_sign',uv=rect_uv(d,flip=True),grime=0.5)
    else:
        mb.quad(base,base+ud*w,base+ud*w+up*h,base+up*h,'atlas_sign',uv=rect_uv(d),grime=0.5)
def fill_shutter(mb,base,ud,up,n,w,h,op):
    openfrac=op.get('open',0.0); t=tile_of('shutter')
    hs=h*(1-openfrac)
    if openfrac>0:
        # dark shop interior behind the opening
        back=base-n*1.6
        mb.quad(back,back+ud*w,back+ud*w+up*h,back+up*h,'atlas_sign',uv=rect_uv('shop_interior'),ao=0.6)
        mb.quad(base-n*1.6,base+ud*w-n*1.6,base+ud*w,base,'concrete_floor',tint=(0.6,0.6,0.6))
        for side in (0,w):
            a=base+ud*side
            mb.quad(a-n*1.6,a,a+up*h,a-n*1.6+up*h,'plaster_paint',tint=(0.55,0.5,0.45))
        mb.quad(base+up*h,base+ud*w+up*h,base+ud*w+up*h-n*1.6,base+up*h-n*1.6,'plaster_paint',tint=(0.5,0.5,0.5))
    if hs>0.05:
        b=base+up*(h-hs)
        mb.quad(b,b+ud*w,b+ud*w+up*hs,b+up*hs,'shutter',uv=('plane',ud,up,t,b),tint=op.get('shutter_tint',WHITE),grime=0.6)
        # bottom bar
        wbox(mb,b-n*0.0,ud,up,n,w,0.06,0.04,'metal_paint',(0.25,0.25,0.25))
    # shutter box on top
    wbox(mb,base+up*h-up*0.0,ud,up,n,w,0.28,0.05+op.get('reveal',0.18),'metal_paint',op.get('box_tint',(0.6,0.6,0.58)))

# ---------- roofs ----------
def zinc_sheet(mb,a,b,c,d,mat,eave_dir,slope_dir,tint=WHITE):
    t=tile_of(mat)
    mb.quad(a,b,c,d,mat,uv=('plane',eave_dir,slope_dir,t,a),tint=tint,grime=0.4)
def hip_roof(mb,x0,y0,x1,y1,z,pitch_deg=18,overhang=0.6,mat='zinc_rusty',tint=WHITE,fascia_tint=(0.35,0.28,0.2),gable=False):
    x0-=overhang; y0-=overhang; x1+=overhang; y1+=overhang
    w=x1-x0; d=y1-y0; t=math.tan(math.radians(pitch_deg))
    if gable:  # ridge along X
        h=d/2*t; zr=z+h; ym=(y0+y1)/2
        A=V((x0,y0,z));B=V((x1,y0,z));C=V((x1,ym,zr));D=V((x0,ym,zr))
        zinc_sheet(mb,A,B,C,D,mat,V((1,0,0)),(C-B).normalized(),tint)
        A2=V((x1,y1,z));B2=V((x0,y1,z))
        zinc_sheet(mb,A2,B2,D,C,mat,V((-1,0,0)),(D-B2).normalized(),tint)
        # undersides
        mb.quad(B,A,D,C,'wood_planks',tint=(0.6,0.55,0.5),grime=0); mb.quad(B2,A2,C,D,'wood_planks',tint=(0.6,0.55,0.5),grime=0)
        # ridge cap
        for (p,q) in [(D,C)]:
            mb.quad(p+V((0,-0.15,-0.04)),q+V((0,-0.15,-0.04)),q+V((0,0,0.03)),p+V((0,0,0.03)),mat,tint=tint)
            mb.quad(q+V((0,0.15,-0.04)),p+V((0,0.15,-0.04)),p+V((0,0,0.03)),q+V((0,0,0.03)),mat,tint=tint)
        fas=[(A,B),(A2,B2)]
        return zr,fas
    h=min(w,d)/2*t; zr=z+h
    if w>=d:
        r0=V((x0+d/2,(y0+y1)/2,zr)); r1=V((x1-d/2,(y0+y1)/2,zr))
    else:
        r0=V(((x0+x1)/2,y0+w/2,zr)); r1=V(((x0+x1)/2,y1-w/2,zr))
    A=V((x0,y0,z));B=V((x1,y0,z));C=V((x1,y1,z));D=V((x0,y1,z))
    if w>=d:
        planes=[(A,B,r1,r0,V((1,0,0))),(C,D,r0,r1,V((-1,0,0))),(B,C,r1,None,V((0,1,0))),(D,A,r0,None,V((0,-1,0)))]
    else:
        planes=[(A,B,r0,None,V((1,0,0))),(C,D,r1,None,V((-1,0,0))),(B,C,r1,r0,V((0,1,0))),(D,A,r0,r1,V((0,-1,0)))]
    for p,q,r,s,ed in planes:
        mid=(p+q)/2; top=r if s is None else (r+s)/2
        sd=(V((top.x,top.y,top.z))-mid); sd=(sd-ed*sd.dot(ed)).normalized()
        pts=[p,q,r] if s is None else [p,q,r,s]
        t_=tile_of(mat)
        mb.face(pts,mat,uv=('plane',ed,sd,t_,p),tint=tint,grime=0.4)
        mb.face(list(reversed(pts)),'wood_planks',tint=(0.55,0.5,0.45),grime=0)
    # ridge & hip caps (thin strips)
    for p,q in [(r0,r1),(A,r0),(B,r1 if w>=d else r0),(C,r1),(D,r0 if w>=d else r1)]:
        dvec=(q-p); side=dvec.cross(V((0,0,1)));
        if side.length<1e-6: continue
        side.normalize(); side*=0.12
        mb.quad(p+side+V((0,0,0.0)),q+side,q+V((0,0,0.04)),p+V((0,0,0.04)),mat,tint=tint)
        mb.quad(q-side,p-side,p+V((0,0,0.04)),q+V((0,0,0.04)),mat,tint=tint)
    fas=[(A,B),(B,C),(C,D),(D,A)]
    return zr,fas
def fascia(mb,edges,h=0.22,tint=(0.35,0.28,0.2)):
    for p,q in edges:
        d=(q-p).normalized(); n=d.cross(V((0,0,1))).normalized()*-1
        a=p+n*0.0-V((0,0,h)); b=q-V((0,0,h))
        mb.quad(p-V((0,0,h))+n*0.02,q-V((0,0,h))+n*0.02,q+n*0.02,p+n*0.02,'wood_planks',tint=tint,uv=('plane',d,V((0,0,1)),2.0,p))

def parapet(mb,x0,y0,x1,y1,z,h=0.9,th=0.2,mat='plaster_paint',tint=WHITE,coping=True):
    pts=[V((x0,y0,z)),V((x1,y0,z)),V((x1,y1,z)),V((x0,y1,z))]
    for i in range(4):
        p=pts[i]; q=pts[(i+1)%4]; d=(q-p).normalized(); n=V((d.y,-d.x,0))
        L=(q-p).length
        grid_quad(mb,p,d,V((0,0,1)),L,h,mat,cu=1.5,cv=1.0,tint=tint)  # outer
        pi=p-n*th+d*th; L2=L-2*th
        grid_quad(mb,pi+d*L2,-d,V((0,0,1)),L2,h,mat,cu=2.0,cv=1.0,tint=tint)  # inner
        # coping (top)
        mb.quad(p+V((0,0,h))+n*0.04-d*0.04,q+V((0,0,h))+n*0.04+d*0.04,q+V((0,0,h))-n*(th+0.0)+d*0.04*0, p+V((0,0,h))-n*th,'concrete',tint=(0.75,0.74,0.7))
        if coping:
            wbox(mb,p+V((0,0,h))-d*0.04,d,V((0,0,1)),n,L+0.08,0.06,0.04,'concrete',(0.72,0.71,0.68))

# ---------- decals ----------
def decal(mb,o,ud,up,w,h,name,n,tint=WHITE,off=0.012,sub=None):
    o=V(o)+V(n)*off
    mb.quad(o,o+V(ud)*w,o+V(ud)*w+V(up)*h,o+V(up)*h,'decal',uv=rect_uv(name,sub=sub),tint=tint,grime=0,ao=0)

# ---------- mesh creation, AO, grime ----------
SUBDIV_MATS={'zinc_rusty','zinc_galv'}
def build_object(mb,name,mat_lib,merge=True):
    me=bpy.data.meshes.new(name); bm=bmesh.new()
    uvl=bm.loops.layers.uv.new('UVMap')
    col=bm.loops.layers.float_color.new('Col')
    gl=bm.faces.layers.int.new('grime'); al=bm.faces.layers.int.new('aoflag')
    matnames=[]
    for f in mb.faces:
        if f['mat'] not in matnames: matnames.append(f['mat'])
    for f in mb.faces:
        vs=[bm.verts.new(p) for p in f['p']]
        try: bf=bm.faces.new(vs)
        except ValueError: continue
        bf.material_index=matnames.index(f['mat'])
        uv=f['uv']; pts=f['p']
        if uv is None:
            bf.normal_update(); nrm=bf.normal; t=tile_of(f['mat'])
            ax=max(range(3),key=lambda i:abs(nrm[i]))
            if ax==2: uvs=[(p.x/t,p.y/t) for p in pts]
            elif ax==0: uvs=[(p.y/t,p.z/t) for p in pts]
            else: uvs=[(p.x/t,p.z/t) for p in pts]
        elif uv[0]=='uvs': uvs=uv[1]
        elif uv[0]=='plane':
            _,ud,vd,t,o=uv; uvs=[((p-o).dot(ud)/t,(p-o).dot(vd)/t) for p in pts]
        for l,u in zip(bf.loops,uvs):
            l[uvl].uv=u; l[col]=(f['tint'][0],f['tint'][1],f['tint'][2],1.0)
        bf[gl]=int(f['grime']*100); bf[al]=int(f['ao']*100)
    if merge: bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=0.0005)
    # subdivide big roof/ground faces so per-vertex AO and mottling have resolution
    big=[f for f in bm.faces if matnames[f.material_index] in SUBDIV_MATS and f.calc_area()>2.0]
    for f in big:
        if not f.is_valid: continue
        n=min(6,int(math.sqrt(f.calc_area())/1.0))
        if n>=1: bmesh.ops.subdivide_edges(bm,edges=list(f.edges),cuts=n,use_grid_fill=True)
    bm.to_mesh(me); bm.free()
    ob=bpy.data.objects.new(name,me); bpy.context.scene.collection.objects.link(ob)
    for m in matnames: me.materials.append(mat_lib(m))
    return ob

def shade(ob,angle=35):
    me=ob.data
    for p in me.polygons: p.use_smooth=True
    me.set_sharp_from_angle(angle=math.radians(angle))

def fibonacci_dirs(n):
    out=[]; ga=math.pi*(3-math.sqrt(5))
    for i in range(n):
        z=1-(i+0.5)/n  # hemisphere z in (0,1]
        r=math.sqrt(max(0,1-z*z)); th=ga*i
        out.append(V((r*math.cos(th),r*math.sin(th),z)))
    return out
DIRS=fibonacci_dirs(32)
def bake_ao_grime(ob,ground=True,maxd=2.5,strength=0.75,grime_amt=1.0,damp_h=0.6,seed=0,extra_bvh=None):
    """Ray-traced per-corner AO multiplied with procedural grime into the 'Col' attribute."""
    me=ob.data; bm=bmesh.new(); bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    # BVH includes a ground plane
    bm2=bm.copy()
    if ground:
        s=60; g=[bm2.verts.new(v) for v in [(-s,-s,0),(s,-s,0),(s,s,0),(-s,s,0)]]; bm2.faces.new(g)
    bvh=BVHTree.FromBMesh(bm2); bm2.free()
    col=bm.loops.layers.float_color['Col']; gl=bm.faces.layers.int.get('grime'); al=bm.faces.layers.int.get('aoflag')
    off=V((seed*13.1,seed*7.7,seed*3.3))
    ROOF_IDX={i for i,m in enumerate(me.materials) if m and m.name in SUBDIV_MATS}
    cache={}
    for f in bm.faces:
        n=f.normal; gr=(f[gl]/100.0 if gl else 1.0)*grime_amt; aoflag=(f[al]/100.0 if al else 1.0)
        # tangent frame
        t=n.orthogonal().normalized(); b=n.cross(t)
        for l in f.loops:
            p=l.vert.co
            key=(round(p.x,3),round(p.y,3),round(p.z,3),round(n.x,2),round(n.y,2),round(n.z,2))
            if key in cache: occ=cache[key]
            else:
                o=p+n*0.02+(f.calc_center_median()-p)*0.02
                hit=0.0; tot=0.0
                for d in DIRS:
                    w=d.z; dd=t*d.x+b*d.y+n*d.z
                    loc,nn,idx,dist=bvh.ray_cast(o,dd,maxd)
                    tot+=w
                    if loc is not None: hit+=w*(1-dist/maxd)**0.5
                occ=1-hit/tot; cache[key]=occ
            ao=1-strength*(1-occ)*aoflag
            c=l[col]; r,g_,b_=c[0],c[1],c[2]
            # grime: large mottling + darkening/greening at the base (rising damp) + dust on top faces
            if gr>0:
                q=p*0.6+off
                m=noise.fractal(q,0.7,2.0,3)*0.10*gr*(3.0 if f.material_index in ROOF_IDX else 1.0)
                damp=(max(0.0,1-p.z/damp_h)**1.5*0.30*gr*(1 if abs(n.z)<0.5 else 0.4)) if damp_h>0 else 0.0
                k=1+m-damp
                r*=k*(1-damp*0.15); g_*=k; b_*=k*(1-damp*0.25)
            l[col]=(min(1.0,max(0,r*ao)),min(1.0,max(0,g_*ao)),min(1.0,max(0,b_*ao)),1.0)
    bm.to_mesh(me); bm.free()

MAT_FLAT={ # base colour, roughness, metallic for untextured materials (tint goes in vertex colour)
 'glass':((0.06,0.07,0.075),0.08,0.0),'car_paint':((1,1,1),0.42,0.0),'plastic':((1,1,1),0.55,0.0),
 'rubber':((0.035,0.035,0.035),0.92,0.0),'chrome':((0.8,0.8,0.8),0.22,1.0),'metal_dark':((0.12,0.12,0.12),0.55,0.6),
 'steel_galv':((0.55,0.56,0.57),0.45,0.85),'fabric':((1,1,1),0.95,0.0),'ceramic':((0.9,0.9,0.88),0.3,0.0),
 'cable':((0.025,0.025,0.025),0.7,0.0),'water':((0.05,0.07,0.08),0.05,0.0),'alu':((0.75,0.75,0.74),0.42,1.0),'charcoal':((0.03,0.03,0.03),0.95,0.0),'glass_louvre':((0.14,0.17,0.17),0.1,0.0),'emit_warm':((1,0.85,0.6),0.4,0.0),'emit_cool':((0.92,0.96,1),0.4,0.0),
}
_mats={}
def mat_lib(name):
    if name in _mats: return _mats[name]
    m=bpy.data.materials.new(name); m.use_nodes=True
    bsdf=m.node_tree.nodes.get('Principled BSDF')
    if name in MAT_FLAT:
        c,r,mt=MAT_FLAT[name]; bsdf.inputs['Base Color'].default_value=(*c,1); bsdf.inputs['Roughness'].default_value=r; bsdf.inputs['Metallic'].default_value=mt
    _mats[name]=m; return m

def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True); _mats.clear()

def export_glb(objs,path):
    for o in objs:
        m=o.modifiers.new('tri','TRIANGULATE'); m.min_vertices=5; m.keep_custom_normals=True
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active=objs[0]
    bpy.ops.export_scene.gltf(filepath=path,export_format='GLB',use_selection=True,export_yup=True,export_apply=True,
        export_vertex_color='ACTIVE',export_image_format='NONE',export_materials='EXPORT',export_texcoords=True,export_normals=True,
        export_tangents=True,export_draco_mesh_compression_enable=False,export_extras=False,export_animations=False)

def tri_count(ob):
    return sum(len(p.vertices)-2 for p in ob.data.polygons)
