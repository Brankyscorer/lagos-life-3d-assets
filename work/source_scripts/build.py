# usage: blender -b --factory-startup -P build.py -- <module> [ids...]
import sys, os, json, importlib, time
sys.path.insert(0,'/workspace/workkit/scripts')
import bpy
args=sys.argv[sys.argv.index('--')+1:]
mod=importlib.import_module(args[0]); ids=args[1:] or list(mod.BUILDERS)
import envlib
out='/workspace/workkit/raw'; os.makedirs(out,exist_ok=True)
for i in ids:
    t=time.time(); envlib.clear_scene()
    import phlib; phlib._cache.clear()
    ob,meta=mod.BUILDERS[i]()
    bb=[ob.matrix_world@__import__('mathutils').Vector(c) for c in ob.bound_box]
    mn=[min(v[k] for v in bb) for k in range(3)]; mx=[max(v[k] for v in bb) for k in range(3)]
    meta.update(id=i,tris=envlib.tri_count(ob),bbox_blender=[mn,mx],materials=[m.name for m in ob.data.materials])
    envlib.export_glb([ob],f'{out}/{i}.glb')
    json.dump(meta,open(f'{out}/{i}.json','w'),indent=1)
    print('BUILT',i,meta['tris'],'tris',[round(a,2) for a in mn],[round(a,2) for a in mx],f'{time.time()-t:.1f}s')
