# Lagos Life people kit: one Rocketbox avatar -> GLB with its armature and two skinned meshes,
# "<id>_head" (head, face, hair/lash cards above the neck seam) and "<id>_body" (outfit + hands),
# no animation (the game drives them with the player skeleton + clips). 512 px textures.
# usage: blender -b -P people_build.py -- <Avatar> <id> <out.glb>
import bpy, sys, os
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:]
avatar, pid, out = args[0], args[1], args[2]
ROOT='/workspace/rb'
bpy.ops.wm.read_factory_settings(use_empty=True)
before=set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=f'{ROOT}/av/{avatar}/{avatar}.fbx', use_anim=False, automatic_bone_orientation=False)
objs=[o for o in bpy.data.objects if o not in before]
arm=[o for o in objs if o.type=='ARMATURE'][0]
mesh=[o for o in objs if o.type=='MESH'][0]
for o in objs:
    if o.type=='EMPTY': bpy.data.objects.remove(o)
arm.animation_data_clear()
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
bpy.ops.object.select_all(action='DESELECT')
arm.select_set(True); mesh.select_set(True); bpy.context.view_layer.objects.active=arm
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
arm.name='Armature'; arm.data.name='Armature'
texdir=f'{ROOT}/tex/{avatar}/512'
def img(name):
    for ext in ('.jpg','.png'):
        p=f'{texdir}/{name}{ext}'
        if os.path.exists(p): return bpy.data.images.load(p)
    raise Exception('missing '+name)
for m in mesh.data.materials:
    base=m.name.split('.')[0]
    nt=m.node_tree; nt.nodes.clear()
    o=nt.nodes.new('ShaderNodeOutputMaterial'); b=nt.nodes.new('ShaderNodeBsdfPrincipled'); nt.links.new(b.outputs[0],o.inputs[0])
    b.inputs['Metallic'].default_value=0.0
    if base.endswith('opacity'):
        t=nt.nodes.new('ShaderNodeTexImage'); t.image=img(base+'_color')
        nt.links.new(t.outputs['Color'],b.inputs['Base Color']); nt.links.new(t.outputs['Alpha'],b.inputs['Alpha'])
        b.inputs['Roughness'].default_value=0.7
        m.blend_method='CLIP'; m.alpha_threshold=0.5; m.use_backface_culling=False
    else:
        t=nt.nodes.new('ShaderNodeTexImage'); t.image=img(base+'_color'); nt.links.new(t.outputs['Color'],b.inputs['Base Color'])
        n=nt.nodes.new('ShaderNodeTexImage'); n.image=img(base+'_normal'); n.image.colorspace_settings.name='Non-Color'
        nm=nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(n.outputs['Color'],nm.inputs['Color']); nt.links.new(nm.outputs['Normal'],b.inputs['Normal'])
        b.inputs['Roughness'].default_value=0.55 if base.endswith('head') else 0.8
        m.use_backface_culling=True
    m.name=f'{pid}_{base.split("_",1)[1]}'
# neck seam height: verts shared by head + body faces
mats=[m.name for m in mesh.data.materials]
vm={}
for p in mesh.data.polygons:
    k='head' if mats[p.material_index].endswith('head') else ('body' if mats[p.material_index].endswith('body') else 'other')
    for v in p.vertices: vm.setdefault(v,set()).add(k)
seam=[mesh.data.vertices[v].co.z for v,s in vm.items() if 'head' in s and 'body' in s]
seamz=sum(seam)/len(seam)
# mark faces: head material, or other (opacity/keffiyeh) above the seam -> head part
bpy.ops.object.select_all(action='DESELECT'); mesh.select_set(True); bpy.context.view_layer.objects.active=mesh
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
# drop garments that are not part of the outfit set (e.g. a keffiyeh draped over head and shoulders)
for p in mesh.data.polygons:
    p.select = 'keffiyeh' in mats[p.material_index]
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.delete(type='FACE'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
# head part = head skin + every hair/lash/brow card (opacity), wherever it hangs (long hair falls below the seam)
for p in mesh.data.polygons:
    name=mats[p.material_index]
    p.select = not name.endswith('body')
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.separate(type='SELECTED'); bpy.ops.object.mode_set(mode='OBJECT')
parts=[o for o in bpy.data.objects if o.type=='MESH']
head=[o for o in parts if o is not mesh][0]
mesh.name=f'{pid}_body'; mesh.data.name=f'{pid}_body'
head.name=f'{pid}_head'; head.data.name=f'{pid}_head'
for o in parts:
    # drop unused material slots
    used={p.material_index for p in o.data.polygons}
    bpy.context.view_layer.objects.active=o
    for i in reversed(range(len(o.data.materials))):
        if i not in used:
            o.active_material_index=i; bpy.ops.object.material_slot_remove()
zs=[(v.co.z) for v in mesh.data.vertices]+[v.co.z for v in head.data.vertices]
print('PART',pid,avatar,'seam %.3f'%seamz,'height %.3f'%max(zs),'head tris',sum(len(p.vertices)-2 for p in head.data.polygons),'body tris',sum(len(p.vertices)-2 for p in mesh.data.polygons))
bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', export_yup=True, export_apply=False, export_animations=False,
    export_def_bones=False, export_image_format='AUTO', export_texcoords=True, export_normals=True, export_tangents=True,
    export_skins=True, export_morph=False, export_extras=False, export_cameras=False, export_lights=False)
print('EXPORTED',out)
