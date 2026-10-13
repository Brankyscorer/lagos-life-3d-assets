# full learning kit rebuild: blender builders -> finalize kit -> compact -> assets_repo/learning (git add only)
set -e
cd /workspace/workkit/scripts
KIT_OUT=/workspace/workkit/raw_lk /workspace/tools/blender-4.2.3-linux-x64/blender -b --factory-startup -P build.py -- learning_assets "$@" 2>&1 | grep -E "BUILT|Traceback|Error" || true
export PATH=/tmp/node-v22.20.0-linux-x64/bin:$PATH
cd /workspace/workkit
ids=$(ls raw_lk/*.glb | xargs -n1 basename | sed 's/.glb//' | tr '\n' ' ')
mkdir -p /workspace/lagoslife/assets_repo/learning/source_scripts
KIT_RAW=/workspace/workkit/raw_lk node scripts/finalize_lk.mjs kit /workspace/workkit/raw_lk_kit.glb $ids | tail -1
node scripts/compact.mjs /workspace/workkit/raw_lk_kit.glb /workspace/lagoslife/assets_repo/learning/learning_kit.glb | tail -1
python3 -c "
import json,glob,os
out={os.path.basename(f)[:-5]:json.load(open(f)) for f in sorted(glob.glob('/workspace/workkit/raw_lk/*.json'))}
json.dump(out,open('/workspace/lagoslife/assets_repo/learning/learning_manifest.json','w'),indent=1)"
cp /workspace/workkit/scripts/{learning_assets.py,finalize_lk.mjs,build.py,lk_build_all.sh} /workspace/lagoslife/assets_repo/learning/source_scripts/
cd /workspace/lagoslife/assets_repo && git add learning
