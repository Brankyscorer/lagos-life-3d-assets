# Lagos street environment kit (three.js-ready GLB)

Realistic Lagos street pieces: buildings, road, props and vehicles. Built in Blender 4.2 with CC0 PBR textures from Poly Haven and ambientCG and CC0 Poly Haven models (see CREDITS.md). AO and grime are baked into vertex colours.

## Files
- `kit/env_buildings.glb`, `kit/env_street.glb`, `kit/env_props.glb`, `kit/env_vehicles.glb`: one GLB per category. Each kit stores its textures once. Every asset is a named root node (node name = asset id). **These go in env.zip.**
- `singles/<id>.glb`: the same assets as standalone files, each with its own textures. Use them if you only need a few assets. They are too big together (~30 MB) for the upload zip.
- `env_manifest.json`: per-asset record: id, category, kit file, node name, single file, size in m (x, y = height, z), bbox, tri count, materials, footprint, snapping/tiling notes, emissive parts, light/attach anchors. Also has the street layout recipe.
- `previews/`: noon and dusk street renders, `contact_sheet_all.jpg`, `assets/<id>.png`.
- `source_scripts/`: every script used to download, process, build, finalise, validate and render.

## Conventions
- Metres, +Y up, origin on the ground (y=0) at the footprint centre.
- Street front faces **+Z**. Vehicles drive toward +Z.
- No Draco, meshopt or KTX2. A plain `GLTFLoader` works without a decoder.
- Materials are standard glTF PBR: base colour, normal, ORM (occlusion/roughness/metal) JPGs at 1K or 512. They use `COLOR_0` vertex colours (baked AO + damp + dirt), which GLTFLoader enables automatically. Tangents are included.
- gltf-validator: 0 errors and 0 warnings on all 4 kits and all 33 singles.

## Loading and placing
```js
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
const loader = new GLTFLoader();
const kits = {};
async function kit(file){ return kits[file] ??= loader.loadAsync('env/' + file); }
async function place(id, x, z, rotY = 0){
  const m = manifest.assets.find(a => a.id === id);
  const g = await kit(m.kit_file);
  const o = g.scene.getObjectByName(m.node).clone(true);   // clones share geometry and materials
  o.position.set(x, 0, z); o.rotation.y = rotY;
  o.traverse(c => { if (c.isMesh) {
    c.receiveShadow = true; c.castShadow = !c.material.transparent;
    if (c.material.transparent) {             // decals: stains, damp, oil, potholes, road paint
      c.material.depthWrite = false; c.material.polygonOffset = true;
      c.material.polygonOffsetFactor = -2; c.renderOrder = 1;
    }
  }});
  scene.add(o); return o;
}
```
Renderer settings used for the previews: `renderer.toneMapping = THREE.ACESFilmicToneMapping`, sRGB output, `PCFSoftShadowMap`, a directional sun with shadows, and an outdoor HDRI through PMREM as `scene.environment`. Any CC0 Poly Haven sky works; the HDRIs are not shipped. Without an environment map the metals and glass look dull.

## Street recipe (see `street_layout` in the manifest)
- **Road**: `street_road_10m` every 10 m along X at z=0. It contains the 7 m carriageway, kerbs, open drains with slab crossings, and faded lane dashes. Edges are at z=±4.4.
- **Sidewalk** (`street_sidewalk_10m`, top 0.15 m) at z=±5.4, or **laterite verge** (`street_shoulder_laterite_10m`) at z=±5.9.
- **Buildings**:
  - Far side: z ≤ -8 with rotY=0.
  - Near side: z ≥ +8 with rotY=π.
  - Footprints are in the manifest. Shop2's balcony overhangs +1.3 m.
- **Fences**: chain `bld_fence_wall_3m` (plastered) or `bld_fence_wall_3m_block` (sandcrete block) every 3 m along X. Use `bld_fence_gate` (6.5 m) for compounds.
- **Poles**:
  - Place `prop_electric_pole` every 25–35 m on one verge.
  - Place `prop_wire_span_30m` at a pole origin. It runs to +X; set `scale.x = spacing/30` and rotate about Y.
  - Wire attach heights are in `attach`.
- **Traffic**: Nigeria drives on the right. The +X lane is z>0 (rotY=+π/2 for a vehicle facing +X), and the -X lane is z<0.
- `street_pothole_decal` sits 1 cm above the asphalt. `street_speed_bump` crosses the road (rotate 90°).

## Day / night (emissive parts)
- `emit_warm` (lamp head, indicators) and `emit_cool` (kiosk and container tube lights) are emissive with `KHR_materials_emissive_strength` (4 and 3).
  - By day set `material.emissiveIntensity = 0`; at night restore it.
  - At night also add a `PointLight` at `light_anchor` (street lamp: [0, 8.05, 1.75]; kiosk: [0, 2.35, 1.18]). The previews used about 160 cd and 26 m range for lamps.
- `atlas_lens` (vehicle head and tail lamps) has its emissive map set but emissive factor 0. At night: `m.emissive.set(1,1,1); m.emissiveIntensity = 2`.

## Performance
- The full preview street uses about 56k triangles and about 380 draw calls (9 road tiles, 12 buildings, poles, wires, props, 4 vehicles).
- Materials are shared within each kit. For a big map, merge static clones per material (`BufferGeometryUtils.mergeGeometries`, keeping `color`) or use `InstancedMesh` for repeated tiles, fences and poles. This cuts draw calls by about 5×.
- Total texture memory per kit is 1K/512 JPG sets, roughly 20–40 MB GPU per kit uncompressed.

## Honest limits
- Architecture is procedural: boxes with real openings, reveals, balconies, parapets, tanks, AC units and decals. There are no interiors except shop and kiosk fronts.
- These are game-ready, not film-photoreal.
- Brands and signs are fictional.
- Vehicle wheels are part of the vehicle mesh, so they don't spin.
- The bench is a Poly Haven painted wooden bench (European style).
