# Import + decimate Poly Haven CC0 models and place copies into assets.
import bpy, glob, math, bmesh
from mathutils import Matrix, Vector
_cache={}
def ph_load(pid,target_tris=None,pick=None,rename=None):
    key=(pid,target_tris,pick)
    if key in _cache: return _cache[key]
    g=glob.glob(f'/workspace/workkit/src/phm/{pid}/*.gltf')[0]
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=g)
    new=[o for o in bpy.data.objects if o not in before]
    meshes=[o for o in new if o.type=='MESH']
    if pick: meshes=[o for o in meshes if pick(o)]
    for o in new:
        if o not in meshes: bpy.data.objects.remove(o,do_unlink=True)
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes: o.select_set(True)
    bpy.context.view_layer.objects.active=meshes[0]
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    if len(meshes)>1: bpy.ops.object.join()
    ob=bpy.context.view_layer.objects.active
    tris=sum(len(p.vertices)-2 for p in ob.data.polygons)
    if target_tris and tris>target_tris*1.1:
        m=ob.modifiers.new('dec','DECIMATE'); m.ratio=target_tris/tris; m.use_collapse_triangulate=True
        bpy.ops.object.modifier_apply(modifier='dec')
    for i,mat in enumerate(ob.data.materials):
        nm=f'ph__{pid}__{mat.name}'
        if nm in bpy.data.materials and bpy.data.materials[nm]!=mat: ob.data.materials[i]=bpy.data.materials[nm]
        else: mat.name=nm
    me=ob.data
    if 'Col' not in me.color_attributes: me.color_attributes.new('Col','FLOAT_COLOR','CORNER')
    for a in ['grime','aoflag']:
        if a not in me.attributes: me.attributes.new(a,'INT','FACE')
    me.attributes['aoflag'].data.foreach_set('value',[60]*len(me.polygons))
    me.attributes['grime'].data.foreach_set('value',[0]*len(me.polygons))
    c=me.color_attributes['Col']; c.data.foreach_set('color',[1.0]*(4*len(me.loops)))
    if me.uv_layers and me.uv_layers[0].name!='UVMap': me.uv_layers[0].name='UVMap'
    ob.hide_render=True; ob.name=f'LIB_{pid}'
    bpy.context.scene.collection.objects.unlink(ob)
    _cache[key]=ob; return ob
def ph_place(lib,loc=(0,0,0),rotz=0.0,scale=1.0,tint=None,M=None,rotx=0.0):
    me=lib.data.copy(); ob=bpy.data.objects.new(lib.name+'_inst',me); bpy.context.scene.collection.objects.link(ob)
    T=Matrix.Translation(Vector(loc))@Matrix.Rotation(rotz,4,'Z')@Matrix.Rotation(rotx,4,'X')@Matrix.Scale(scale,4)
    if M is not None: T=M@T
    me.transform(T)
    if tint:
        c=me.color_attributes['Col']; c.data.foreach_set('color',[*tint,1.0]*len(me.loops))
    return ob
def join(objs,name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active=objs[0]
    if len(objs)>1: bpy.ops.object.join()
    ob=bpy.context.view_layer.objects.active; ob.name=name; ob.data.name=name
    me=ob.data
    if 'Col' in me.color_attributes: me.color_attributes.active_color=me.color_attributes['Col']; me.color_attributes.render_color_index=me.color_attributes.active_color_index
    return ob
