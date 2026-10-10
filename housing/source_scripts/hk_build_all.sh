# full housing kit rebuild: blender builders -> finalize kit -> compact -> assets_repo/housing
set -e
cd /workspace/workkit/scripts
KIT_OUT=/workspace/workkit/raw_hk /workspace/tools/blender-4.2.3-linux-x64/blender -b --factory-startup -P build.py -- housing_assets "$@" 2>&1 | grep -E "BUILT|Traceback|Error" || true
export PATH=/tmp/node-v22.20.0-linux-x64/bin:$PATH
cd /workspace/workkit
ids=$(ls raw_hk/*.glb | xargs -n1 basename | sed 's/.glb//' | tr '\n' ' ')
KIT_RAW=/workspace/workkit/raw_hk node scripts/finalize_hk.mjs kit /workspace/workkit/raw_hk_kit.glb $ids | tail -1
node scripts/compact.mjs /workspace/workkit/raw_hk_kit.glb /workspace/lagoslife/assets_repo/housing/housing_kit.glb | tail -1
python3 -c "
import json,glob,os
out={os.path.basename(f)[:-5]:json.load(open(f)) for f in sorted(glob.glob('/workspace/workkit/raw_hk/*.json'))}
json.dump(out,open('/workspace/lagoslife/assets_repo/housing/housing_manifest.json','w'),indent=1)"
cp /workspace/workkit/scripts/{housing_assets.py,housing_tex.py,finalize_hk.mjs,build.py,hk_build_all.sh} /workspace/lagoslife/assets_repo/housing/source_scripts/
cd /workspace/lagoslife/assets_repo && git add housing
