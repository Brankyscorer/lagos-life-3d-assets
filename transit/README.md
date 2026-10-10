# Lagos Life transit + venue kit (Step 05)

`transit_kit.glb` (meshopt + quantized) holds 30 nodes; `transit_manifest.json` lists each node with its three.js bounding box, triangle count and notes.

- Vehicles: danfo, keke, okada, Gidi Ride cab, BRT bus. Each ships as a wheel-less `veh_<kind>_body` plus separate wheel nodes (`veh_wheel_*`), with the wheel axle positions in `wheels[]`, so wheels can spin. `veh_<kind>_lod1` is a merged, decimated far version (all <= 2k tris; every LOD0 body+wheels is <= 3k tris).
- Street: bus-stop shelter, zebra crossing, four billboards with original (invented) ads.
- Venues: Opebi Galleria mall front, Galleria Cinemas front + ticket booth, food-court shawarma counter, buka/market/hub sign boards, Ankara fabric stall, wheelbarrow.

Everything is procedural (Blender 4.2 scripts in `source_scripts/`) except two CC0 Poly Haven models (metal_trash_can, planter_box_01). All brands, adverts and film posters are invented for the game.
