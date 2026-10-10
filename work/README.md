# work/ - Lagos Life work scenes (A05)

- `work_kit.glb` (4464 KB): 38 nodes - 4 room shells (barber, classroom, bank, office) and props for the 12 careers (POS stand + A-frame, market stall, buka kitchen + menu + bench table, barber station/chair/signs, blackboard, school + teacher desks, bank counter + queue posts + signs, code/help desks + kanban, security booth + boom barrier + estate sign, motor-park sign, parcel shelf/stack/delivery box, stage + bar counter, ceiling fan, TV, wall clock, cash register).
- `work_anims_m.glb`, `work_anims_f.glb`: 9 looping work clips for the Rocketbox player skeleton.
- `work_manifest.json`: per-node notes, sizes and stand/seat points.

Loading: meshopt-compressed - use `GLTFLoader.setMeshoptDecoder`. Clone nodes into your own Group before placing (see manifest `compression`).

Rebuild: `blender -b --factory-startup -P source_scripts/build.py -- work_assets` then `node finalize.mjs kit work_kit_full.glb <ids>` and `node compact.mjs work_kit_full.glb work_kit.glb`.
