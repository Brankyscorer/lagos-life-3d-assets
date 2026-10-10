# Lagos Life - yard kit (face-me-I-face-you compound)

One uncompressed GLB, `yard_kit.glb` (5.38 MB, 45 nodes, 22,574 triangles in total), that dresses the shared compound yard behind the Oloya Street rooms (the `spawn=yard` scene). It uses the same pipeline and format as the street kit (`env/`).

- **Format:** glTF 2.0 binary, no Draco/meshopt/KTX2. Plain `GLTFLoader` loads it. Metres, +Y up.
- **Orientation:** every node faces **+Z**. Room fronts, windows, doors, the toilet block and the sink go on the yard facade (z = -5.85) with `rotY = Math.PI`.
- **Vertex colours:** `COLOR_0` holds baked AO, grime, damp bands and splash marks. Keep `vertexColors` on.
- **Textures:** CC0 Poly Haven sets at 512-1024 px, plus two own-work atlases: garment prints (`yard_atlas.jpg`) and RGBA decals/signs (`yard_decals.png`).
- **Validation:** gltf-validator reports 0 errors, 0 warnings, 0 infos and 0 hints.
- **Materials worth knowing:**
  - `decal` (alpha BLEND): use depthWrite false, polygonOffset -2/-2, renderOrder 1 and no shadow casting.
  - `emit_warm`: bulkhead lamps. Set the intensity to 0 by day and about 4 at night.
  - `atlas_fabric`, `zinc_rusty` and the Poly Haven model materials are double-sided.
  - The plant leaves use alpha MASK.
- **Picking a node:** `gltf.scene.getObjectByName(id)` returns it. Clone it per placement. A node with several materials is a Group with child meshes.

## Placement recipe

`yard_manifest.json -> placement` holds the full yard layout in the game's current world coordinates (the same frame as `oloya.ts`):

- **items:** 75 placements (node, pos, rotY, optional X scale, group, floor flag).
- **colliders:** 14 `addSolid`-style colliders.
- **remove_procedural:** the procedural meshes these placements replace.
- **cream_dado_shrink:** the rule that moves the procedural cream/dado wall boxes 0.22 m back, behind the fronts.

The layout:

- **Ground:** 4 x `yard_ground_5p54x6p6` at x = -5.53 / 0.01 / 5.55 / 11.09, z = -9.15. They tile seamlessly in X with rotY 0.
- **Walkway:** 3 x `yard_walkway_1p5x2p2` at x = 1.0, z = -6.95 / -9.15 / -11.35. It runs from the passage to the gate.
- **Facade (z = -5.85, rotY = PI):** each run is X-scaled to fit exactly.
  - NW corner: one plain module.
  - Rooms A and B (x -7.64..-0.05): door with the blue wooden door, louvre window, 2 plain modules, casement window, plain.
  - Room C and the back store (1.85..7.45): plain, louvre window, plain, door with the burglar-proof metal door.
  - Low block (7.45..13.7): plain, toilet/bathroom block, casement window, plain.
  - The toilet door lands at x = 9.01, next to the game's `prop:toilet` spot (9.05, -6.55).
- **Boundary:**
  - South: low dwarf walls with pillars, plus the green steel gate centred at x = 0.95, z = -12.37. Both gate leaves stand open into the yard.
  - East and west: 2.25 m walls.
- **Laundry:** a 6 m clothesline at (5.6, -7.0) along X, with towel, shirt, Ankara wrapper, singlet, trousers and bedsheet.
- **Props:**
  - tank stand (-3.75, -8.65), sink + tap and step slab (-3.26, -6.1)
  - drum, buckets and basin by the sink
  - charcoal stove + pot with soot in the NW corner
  - chair stack by the passage (2.3, -6.28)
  - plastic table (4.75, -9.35) by the existing yard chairs
  - bench (-0.4, -9.32)
  - generator + zinc canopy (7.15, -8.05)
  - potted plants by the gate and the east wall
  - puddle/splash stains

## Assets

| id | category | size x × h × depth (m) | tris |
|---|---|---|---|
| `yard_basin` | prop | 0.70 x 0.20 x 0.70 | 246 |
| `yard_bench_wood` | furniture | 1.50 x 0.45 x 0.41 | 144 |
| `yard_bucket_blue` | prop | 0.34 x 0.43 x 0.34 | 234 |
| `yard_bucket_red` | prop | 0.34 x 0.43 x 0.34 | 234 |
| `yard_chair_stack` | furniture | 0.68 x 1.19 x 0.73 | 2400 |
| `yard_clothesline_6m` | prop | 6.24 x 2.03 x 0.23 | 512 |
| `yard_coal_stove` | prop | 0.36 x 0.31 x 0.36 | 458 |
| `yard_door_metal` | door | 0.95 x 2.12 x 0.16 | 950 |
| `yard_door_wood_blue` | door | 1.05 x 2.17 x 0.18 | 284 |
| `yard_door_wood_brown` | door | 1.05 x 2.17 x 0.18 | 284 |
| `yard_door_wood_green` | door | 1.05 x 2.17 x 0.18 | 284 |
| `yard_front_door_1p8` | front | 1.80 x 2.90 x 0.54 | 160 |
| `yard_front_plain_0p9` | front | 0.90 x 2.90 x 0.26 | 68 |
| `yard_front_plain_0p9_low` | front | 0.90 x 2.60 x 0.26 | 64 |
| `yard_front_window_1p8` | front | 1.80 x 2.90 x 0.29 | 152 |
| `yard_front_window_1p8_low` | front | 1.80 x 2.60 x 0.29 | 142 |
| `yard_garment_bedsheet` | garment | 1.61 x 1.02 x 0.11 | 1612 |
| `yard_garment_shirt` | garment | 0.92 x 0.77 x 0.04 | 644 |
| `yard_garment_singlet` | garment | 0.46 x 0.69 x 0.03 | 600 |
| `yard_garment_towel` | garment | 0.73 x 0.54 x 0.07 | 420 |
| `yard_garment_trousers` | garment | 0.43 x 1.05 x 0.03 | 376 |
| `yard_garment_wrapper` | garment | 1.20 x 0.98 x 0.10 | 1100 |
| `yard_gate_1p5` | wall | 1.92 x 1.96 x 0.79 | 374 |
| `yard_gen_canopy` | prop | 1.70 x 1.38 x 1.32 | 104 |
| `yard_generator` | prop | 1.32 x 0.58 x 0.84 | 2044 |
| `yard_ground_5p54x6p6` | ground | 5.54 x 0.00 x 6.60 | 1344 |
| `yard_pot` | prop | 0.38 x 0.23 x 0.31 | 258 |
| `yard_potted_plant` | prop | 0.63 x 0.77 x 0.59 | 2399 |
| `yard_sink_tap` | prop | 0.75 x 1.20 x 0.57 | 208 |
| `yard_stain_puddle_a` | decal | 1.60 x 0.00 x 1.60 | 2 |
| `yard_stain_puddle_b` | decal | 1.80 x 0.00 x 0.90 | 2 |
| `yard_stain_soot` | decal | 0.80 x 0.00 x 0.80 | 2 |
| `yard_stain_splash` | decal | 0.70 x 0.00 x 0.70 | 2 |
| `yard_step_slab_a` | ground | 0.63 x 0.08 x 0.44 | 72 |
| `yard_step_slab_b` | ground | 0.52 x 0.08 x 0.50 | 72 |
| `yard_table_plastic` | furniture | 0.81 x 0.72 x 0.81 | 284 |
| `yard_tank_stand` | prop | 1.10 x 2.12 x 1.20 | 766 |
| `yard_toilet_block_front` | front | 3.00 x 3.05 x 0.72 | 560 |
| `yard_walkway_1p5x2p2` | ground | 1.51 x 0.08 x 2.19 | 252 |
| `yard_wall_3m` | wall | 3.01 x 2.25 x 0.26 | 120 |
| `yard_wall_low_3m` | wall | 3.01 x 1.05 x 0.26 | 84 |
| `yard_wall_pillar_low` | wall | 0.36 x 1.26 x 0.36 | 26 |
| `yard_water_drum` | prop | 0.49 x 0.95 x 0.48 | 1233 |
| `yard_window_casement` | window | 1.02 x 1.02 x 0.12 | 302 |
| `yard_window_louvre` | window | 1.02 x 1.02 x 0.15 | 696 |

The spare door colours (`yard_door_wood_brown`, `yard_door_wood_green`) fit any `yard_front_door_1p8` opening. They also suit the corridor-side room doors.

## Rebuild

The scripts are in `source_scripts/`, and `make.sh` runs the whole pipeline:

1. Blender 4.2 builds the assets: `blender -b --factory-startup -P build.py -- yard_assets [ids]`.
2. `finalize.mjs` assigns the textures and merges the assets into one kit with gltf-transform.
3. `env_validate.mjs` runs gltf-validator.
4. `render_scene.mjs` renders the previews with three.js in headless Chrome. `yard_scene.py` builds the preview configs from `layout.py`.

`layout.py` is the single source of the placement recipe. `prep_yard_tex.py` builds the texture sets and atlases.

`gen_yardkit_ts.py` writes the drop-in game module `integration/yardkit.ts` from the same recipe:

- **Exports:** `mountYardKit`, `YARD_PLACES`, `YARD_SOLIDS`, `setYardLamps` and `yardKitStatus`.
- **Draw calls:** it merges the 75 placements into about 51 draw calls.
- **Tested:** type-checked with three 0.186. The harness in `integration/` mounted it in headless Chrome with no errors.
