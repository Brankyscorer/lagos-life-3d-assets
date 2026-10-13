# Lagos Life car kit (Step 10, tag v8): original procedural private vehicles (no taxi parts).
# usage: blender -b --factory-startup -P car_assets.py -- <out.glb>
# Blender Z up, metres, fronts face -Y, origin at ground centre. Paint material "car_paint" is near-white so the game can tint it.
import bpy, bmesh, sys, math
from mathutils import Vector as V
out=sys.argv[sys.argv.index('--')+1]
for o in list(bpy.data.objects): bpy.data.objects.remove(o,do_unlink=True)
MATS={}
def mat(n,c,r,m=0.0,e=None,a=1.0):
    if n in MATS: return MATS[n]
    mt=bpy.data.materials.new(n); mt.use_nodes=True; b=mt.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value=(*c,1); b.inputs['Roughness'].default_value=r; b.inputs['Metallic'].default_value=m
    if e: b.inputs['Emission Color'].default_value=(*e,1); b.inputs['Emission Strength'].default_value=2.0
    if a<1: b.inputs['Alpha'].default_value=a; mt.blend_method='BLEND'
    MATS[n]=mt; return mt
PAINT=lambda: mat('car_paint',(0.85,0.85,0.85),0.28,0.35)
GLASS=lambda: mat('car_glass',(0.04,0.05,0.06),0.05,0.2)
RUB=lambda: mat('car_rubber',(0.03,0.03,0.03),0.9)
CHR=lambda: mat('car_chrome',(0.8,0.8,0.8),0.2,1.0)
TRIM=lambda: mat('car_trim',(0.06,0.06,0.065),0.6)
HEAD=lambda: mat('car_headlight',(0.95,0.95,0.9),0.1,0,(1,0.97,0.88))
TAIL=lambda: mat('car_taillight',(0.6,0.03,0.03),0.2,0,(0.9,0.05,0.04))
SEAT=lambda: mat('car_seat',(0.09,0.07,0.06),0.8)

def poly_obj(name,verts,faces,mats_per_face,material_list,bevel=0.0,seg=2):
    me=bpy.data.meshes.new(name); me.from_pydata(verts,[],faces); me.update()
    ob=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(ob)
    for m in material_list: me.materials.append(m)
    for p,i in zip(me.polygons,mats_per_face): p.material_index=i
    if bevel:
        md=ob.modifiers.new('bv','BEVEL'); md.width=bevel; md.segments=seg; md.limit_method='ANGLE'
    return ob
def box(name,c,s,material,bevel=0.0,seg=2):
    x,y,z=c; a,b,h=[v/2 for v in s]
    vs=[(x-a,y-b,z-h),(x+a,y-b,z-h),(x+a,y+b,z-h),(x-a,y+b,z-h),(x-a,y-b,z+h),(x+a,y-b,z+h),(x+a,y+b,z+h),(x-a,y+b,z+h)]
    fs=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    return poly_obj(name,vs,fs,[0]*6,[material],bevel,seg)
def cabin(name,w,y0,y1,z0,z1,tw,ty0,ty1):
    # lower rect (w, y0..y1) at z0; roof rect (tw, ty0..ty1) at z1. sides+front+back glass, roof paint
    a,t=w/2,tw/2
    vs=[(-a,y0,z0),(a,y0,z0),(a,y1,z0),(-a,y1,z0),(-t,ty0,z1),(t,ty0,z1),(t,ty1,z1),(-t,ty1,z1)]
    fs=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    return poly_obj(name,vs,fs,[0,0,1,1,1,1],[PAINT(),GLASS()],0.03,2)
def pillars(prefix,w,y0,y1,z0,z1,tw,ty0,ty1,n_mid):
    # thin painted pillars on top of the glass so windows read as framed
    obs=[]
    for k,(ya,yb) in enumerate([(y0,ty0),(y1,ty1)]+[(y0+(y1-y0)*f,ty0+(ty1-ty0)*f) for f in n_mid]):
        for sx in (-1,1):
            p0=V((sx*(w/2+0.005),ya,z0)); p1=V((sx*(tw/2+0.005),yb,z1))
            mid=(p0+p1)/2; d=p1-p0; L=d.length
            o=box(f'{prefix}_p{k}{sx}',(0,0,0),(0.03,0.07,L),PAINT())
            o.location=mid; o.rotation_mode='QUATERNION'; o.rotation_quaternion=V((0,0,1)).rotation_difference(d.normalized())
            obs.append(o)
    return obs
def wheel(name,x,y,r,wd):
    bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=r,depth=wd,location=(x,y,r),rotation=(0,math.pi/2,0)); t=bpy.context.object; t.name=name
    t.data.materials.append(RUB()); bpy.ops.object.shade_smooth()
    bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=r*0.58,depth=wd+0.02,location=(x,y,r),rotation=(0,math.pi/2,0)); h=bpy.context.object
    h.data.materials.append(CHR()); return [t,h]
def join(objs,name):
    for o in objs:
        bpy.context.view_layer.objects.active=o
        for md in list(o.modifiers): bpy.ops.object.modifier_apply(modifier=md.name)
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active=objs[0]; bpy.ops.object.join(); ob=bpy.context.object; ob.name=name; ob.data.name=name
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    return ob

def car(name,L,W,body_h,clear,r,cab):
    hl=L/2; z0=clear; z1=clear+body_h; o=[]
    # body: side profile with sloped bonnet/boot (8-vertex extruded profile)
    nose=cab['nose']; tail=cab['tail']
    prof=[(-hl,z0+0.05),(hl,z0+0.05),(hl,z1-tail),(hl-0.18,z1),(-hl+0.25,z1),(-hl,z1-nose)]
    a=W/2; vs=[(-a,y,z) for y,z in prof]+[(a,y,z) for y,z in prof]; n=len(prof)
    fs=[tuple(range(n))[::-1],tuple(range(n,2*n))]+[(i,(i+1)%n,n+(i+1)%n,n+i) for i in range(n)]
    o.append(poly_obj(name+'_body',vs,fs,[0]*len(fs),[PAINT()],0.06,3))
    c=cabin(name+'_cab',W-0.08,cab['y0'],cab['y1'],z1-0.01,z1+cab['h'],W-0.26,cab['ty0'],cab['ty1']); o.append(c)
    o+=pillars(name,W-0.08,cab['y0'],cab['y1'],z1,z1+cab['h'],W-0.26,cab['ty0'],cab['ty1'],cab.get('mid',[0.5]))
    # bumpers, grille, lights, mirrors, handles
    o.append(box(name+'_bf',(0,-hl-0.02,z0+0.16),(W-0.04,0.12,0.2),TRIM(),0.04))
    o.append(box(name+'_bb',(0,hl+0.02,z0+0.16),(W-0.04,0.12,0.2),TRIM(),0.04))
    o.append(box(name+'_gr',(0,-hl-0.005,z1-nose-0.1),(W*0.42,0.04,0.14),TRIM(),0.01))
    for sx in (-1,1):
        o.append(box(name+f'_hl{sx}',(sx*(a-0.2),-hl-0.01,z1-nose-0.08),(0.3,0.04,0.11),HEAD(),0.015))
        o.append(box(name+f'_tl{sx}',(sx*(a-0.17),hl+0.01,z1-tail-0.08),(0.26,0.04,0.1),TAIL(),0.015))
        o.append(box(name+f'_mr{sx}',(sx*(a+0.06),cab['y0']+0.12,z1+0.08),(0.1,0.06,0.09),PAINT(),0.02))
        o.append(box(name+f'_sk{sx}',(sx*(a+0.005),0,z0+0.08),(0.04,L*0.62,0.08),TRIM(),0.01))
        for y in cab['wheels']: o+=wheel(name+f'_w{sx}{y}',sx*(a-0.12),y,r,0.24)
        for y in cab.get('handles',[]): o.append(box(name+f'_dh{sx}{y}',(sx*(a+0.01),y,z1-0.12),(0.02,0.14,0.03),CHR(),0.005))
    # wheel arches (dark) as thin boxes above tyres
    for sx in (-1,1):
        for y in []: o.append(box(name+f'_ar{sx}{y}',(sx*(a+0.004),y,2*r+0.02),(0.03,2.1*r,0.06),TRIM(),0.02))
    if cab.get('rails'):
        for sx in (-1,1): o.append(box(name+f'_rr{sx}',(sx*(W/2-0.2),(cab['ty0']+cab['ty1'])/2,z1+cab['h']+0.03),(0.04,(cab['ty1']-cab['ty0'])*0.9,0.04),CHR(),0.01))
    if cab.get('spare'): o+=[box(name+'_sp',(0,hl+0.1,z0+0.55),(0.62,0.2,0.62),RUB(),0.12)]
    return join(o,name)

sedan=car('car_sedan',4.5,1.78,0.62,0.18,0.31,dict(nose=0.14,tail=0.08,y0=-0.85,y1=1.05,h=0.48,ty0=-0.35,ty1=0.62,wheels=[-1.38,1.38],handles=[-0.25,0.55],mid=[0.48]))
suv=car('car_suv',4.75,1.92,0.78,0.26,0.37,dict(nose=0.1,tail=0.04,y0=-0.95,y1=2.05,h=0.62,ty0=-0.5,ty1=1.95,wheels=[-1.45,1.45],handles=[-0.3,0.7],mid=[0.33,0.7],rails=True,spare=True))
for ob,x in ((sedan,0),(suv,0)): pass

# motorbike (private: no rack, no box)
o=[]
o+=wheel('b_wf',0,-0.68,0.3,0.1)+wheel('b_wr',0,0.68,0.3,0.12)
def tube(n,p0,p1,r,mt):
    p0,p1=V(p0),V(p1); d=p1-p0
    bpy.ops.mesh.primitive_cylinder_add(vertices=10,radius=r,depth=d.length,location=(p0+p1)/2); t=bpy.context.object; t.name=n
    t.rotation_mode='QUATERNION'; t.rotation_quaternion=V((0,0,1)).rotation_difference(d.normalized()); t.data.materials.append(mt); return t
o+=[tube('b_fork',(0,-0.68,0.3),(0,-0.5,0.95),0.025,CHR()),tube('b_frame',(0,-0.5,0.85),(0,0.3,0.5),0.035,TRIM()),tube('b_sw',(0,0.15,0.42),(0,0.68,0.3),0.03,TRIM()),
    tube('b_bar',(-0.36,-0.48,0.98),(0.36,-0.48,0.98),0.015,CHR()),tube('b_exh',(0.14,-0.1,0.3),(0.16,0.75,0.42),0.035,CHR())]
o.append(box('b_tank',(0,-0.2,0.85),(0.3,0.42,0.2),PAINT(),0.08))
o.append(box('b_seat',(0,0.3,0.82),(0.28,0.58,0.09),SEAT(),0.04))
o.append(box('b_eng',(0,0.0,0.45),(0.26,0.34,0.3),TRIM(),0.04))
o.append(box('b_tailc',(0,0.66,0.76),(0.22,0.3,0.1),PAINT(),0.04))
o.append(box('b_fend',(0,-0.7,0.64),(0.12,0.4,0.03),PAINT(),0.012))
o.append(box('b_hl',(0,-0.56,0.92),(0.14,0.06,0.12),HEAD(),0.03))
o.append(box('b_tl',(0,0.82,0.74),(0.1,0.03,0.05),TAIL(),0.01))
bike=join(o,'car_bike')
for ob in bpy.data.objects:
    for p in ob.data.polygons: p.use_smooth=False
    ob.data.shade_auto_smooth(angle=math.radians(35)) if hasattr(ob.data,'shade_auto_smooth') else None
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_materials='EXPORT',export_animations=False)
for ob in (sedan,suv,bike): print('BUILT',ob.name,sum(len(p.vertices)-2 for p in ob.data.polygons),'tris')
