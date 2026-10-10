import bpy, sys, os, math
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:]
avatar, gender, res, out = args[0], args[1], int(args[2]), args[3]
ROOT='/workspace/rb'
CLIPS = {
 'w_talk':     f'{gender}_gestic_talk_excited_01',
 'w_terminal': f'{gender}_work_table',
 'w_mid':      f'{gender}_work_mid',
 'w_guard':    f'{gender}_documents_check',
 'w_teach':    f'{gender}_moderate_01',
 'w_desk':     f'{gender}_sit_table_idle_neutral_01',
 'w_film':     f'{gender}_take_picture',
 'w_perform':  f'{gender}_dancing_cool',
 'w_cheer':    f'{gender}_cheer_01',
}

bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.render.fps=30
def imp(path):
    before=set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path, use_anim=True, automatic_bone_orientation=False)
    return [o for o in bpy.data.objects if o not in before]

objs=imp(f'{ROOT}/av/{avatar}/{avatar}.fbx')
arm=[o for o in objs if o.type=='ARMATURE'][0]
mesh=[o for o in objs if o.type=='MESH'][0]
for o in objs:
    if o.type=='EMPTY': bpy.data.objects.remove(o)
# drop avatar's dummy action
arm.animation_data_clear()
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
# apply 0.01 scale so armature is in metres with scale 1
bpy.ops.object.select_all(action='DESELECT')
arm.select_set(True); mesh.select_set(True); bpy.context.view_layer.objects.active=arm
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
arm.name='Armature'; arm.data.name='Armature'
mesh.name=f'{avatar}_mesh'
bpy.context.view_layer.update()
mw=mesh.matrix_world
zs=[(mw@v.co).z for v in mesh.data.vertices]
print('AVATAR height min/max', min(zs), max(zs))



# rest pelvis height for skeleton-size matching
def pelvis_h(a):
    # leg length (thigh head -> foot head) in world units, independent of current animation
    b=a.data.bones; s=a.matrix_world.to_scale()[0]
    return ((b['Bip01 L Calf'].head_local-b['Bip01 L Thigh'].head_local).length+(b['Bip01 L Foot'].head_local-b['Bip01 L Calf'].head_local).length)*s
tgt_ph=pelvis_h(arm)
FEET=['Bip01 L Foot','Bip01 R Foot','Bip01 L Toe0','Bip01 R Toe0']
def foot_min_rest(a):
    return min(min((a.matrix_world@a.data.bones[b].head_local).z,(a.matrix_world@a.data.bones[b].tail_local).z) for b in FEET)
tgt_foot=foot_min_rest(arm)
print('rest foot min',tgt_foot)

# ---- constraints on target
bones=[pb.name for pb in arm.pose.bones]
def bake_clip(clipname, fname):
    path=None
    for p in (f'{ROOT}/anims/{fname}.fbx',):
        if os.path.exists(p): path=p
    sobjs=imp(path)
    src=[o for o in sobjs if o.type=='ARMATURE'][0]
    act=src.animation_data.action
    fs,fe=int(act.frame_range[0]), int(act.frame_range[1])
    # src armature object animation (root) is inside the same action (object-level fcurves)
    src_ph=pelvis_h(src)
    k=tgt_ph/src_ph
    print('SCALE',clipname,round(k,4))
    # wrap source in an empty so we can scale / rotate it
    holder=bpy.data.objects.new('holder',None); scene.collection.objects.link(holder)
    for o in sobjs:
        if o.parent is None: o.parent=holder
    holder.scale=(k,k,k)
    if clipname=='sleep':
        holder.rotation_euler=(-math.pi/2,0,0); holder.location=(0,0,0.13)
    bpy.context.view_layer.update()
    if clipname!='sleep':
        mn=1e9
        for f in range(fs,fe+1):
            scene.frame_set(f)
            for b in FEET:
                pb=src.pose.bones[b]
                mn=min(mn,(src.matrix_world@pb.head).z,(src.matrix_world@pb.tail).z)
        holder.location.z += tgt_foot-mn
        print('GROUND',clipname,'offset',round(tgt_foot-mn,3))
        bpy.context.view_layer.update()
    cons=[]
    for b in bones:
        if b not in src.pose.bones: continue
        pb=arm.pose.bones[b]
        c=pb.constraints.new('COPY_ROTATION'); c.target=src; c.subtarget=b; c.target_space='WORLD'; c.owner_space='WORLD'; cons.append((pb,c))
        if b=='Bip01 Pelvis':
            c2=pb.constraints.new('COPY_LOCATION'); c2.target=src; c2.subtarget=b; c2.target_space='WORLD'; c2.owner_space='WORLD'; cons.append((pb,c2))
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True); bpy.context.view_layer.objects.active=arm
    bpy.ops.object.mode_set(mode='POSE'); bpy.ops.pose.select_all(action='SELECT')
    arm.animation_data_create(); arm.animation_data.action=None
    bpy.ops.nla.bake(frame_start=fs, frame_end=fe, only_selected=False, visual_keying=True, clear_constraints=True, use_current_action=False, bake_types={'POSE'})
    bpy.ops.object.mode_set(mode='OBJECT')
    newact=arm.animation_data.action; newact.name=clipname
    # shift to start at frame 0
    for fc in newact.fcurves:
        for kp in fc.keyframe_points:
            kp.co.x-=fs; kp.handle_left.x-=fs; kp.handle_right.x-=fs
    # remove horizontal root drift for locomotion (keep in-place)
    pel=[fc for fc in newact.fcurves if fc.data_path=='pose.bones["Bip01 Pelvis"].location']
    drift=[]
    for fc in pel:
        v=[kp.co.y for kp in fc.keyframe_points]; drift.append(round(v[-1]-v[0],3))
    if clipname in ('walk','run'):
        for fc in pel:
            kps=list(fc.keyframe_points); v0=kps[0].co.y; d=kps[-1].co.y-v0; n=len(kps)-1
            if abs(d)>0.05:
                for i,kp in enumerate(kps):
                    off=d*i/n; kp.co.y-=off; kp.handle_left.y-=off; kp.handle_right.y-=off
    print('CLIP',clipname,fname,'frames',fe-fs+1,'pelvis local drift',drift)
    for f in (0,(fe-fs)//2):
        scene.frame_set(f); bpy.context.view_layer.update()
        fz=min(min((arm.matrix_world@arm.pose.bones[b].head).z,(arm.matrix_world@arm.pose.bones[b].tail).z) for b in FEET)
        print('CHECK',clipname,'frame',f,'target foot min z',round(fz,3),'pelvis z',round((arm.matrix_world@arm.pose.bones['Bip01 Pelvis'].head).z,3))
    newact.use_fake_user=True
    tr=arm.animation_data.nla_tracks.new(); tr.name=clipname; tr.strips.new(clipname, 0, newact); tr.mute=True
    arm.animation_data.action=None
    # cleanup source
    for o in sobjs+[holder]: bpy.data.objects.remove(o, do_unlink=True)
    for a in list(bpy.data.actions):
        if a.name not in CLIPS: bpy.data.actions.remove(a)
    for a in list(bpy.data.armatures):
        if a.users==0: bpy.data.armatures.remove(a)
for cn,fn in CLIPS.items(): bake_clip(cn,fn)
# reset to rest
for pb in arm.pose.bones:
    pb.location=(0,0,0); pb.rotation_quaternion=(1,0,0,0); pb.rotation_euler=(0,0,0); pb.scale=(1,1,1)
for a in list(bpy.data.objects):
    if a is not arm: bpy.data.objects.remove(a)
bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', export_yup=True, export_apply=False,
    export_animations=True, export_animation_mode='ACTIONS', export_nla_strips=True,
    export_force_sampling=True, export_optimize_animation_size=True, export_def_bones=False,
    export_anim_single_armature=True, export_reset_pose_bones=True,
    export_image_format='AUTO', export_texcoords=True, export_normals=True, export_tangents=True,
    export_skins=False, export_morph=False, export_extras=False, export_cameras=False, export_lights=False)
print('EXPORTED',out)
