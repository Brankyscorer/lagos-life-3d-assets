# Credits

External assets used by Gidi Hustle. Swapping a URL in `public/assets/manifest.json` changes which character file the loader requests. No code edit is required for that swap.

| Asset | Source | Licence |
| --- | --- | --- |
| Male and female Sims (`public/assets/characters/player_male_01.glb`, `player_female_01.glb`) | Microsoft Rocketbox Avatar Library, MIT License, https://github.com/microsoft/Microsoft-Rocketbox | MIT |
| Street pedestrians `public/assets/npc/npc_01.glb` … `npc_12.glb` (businessman, labourer, hoodie, carpenter, afro jacket, football jersey, police, patterned top, white uniform, nurse, hijab, knit dress) | Microsoft Rocketbox Avatar Library, MIT License. `npc_10`'s skin tone is a recolour toward a West African brown. Clips: idle, walk, talk, sit, phone. | MIT |
| Clips on those files: idle, walk, run, sit, sleep, wash, eat, phone, wave | Same Rocketbox export. Walk and run are in place. | MIT |
| Day HDRI `public/assets/env-day.hdr` | Poly Haven (kloofendal clear sky, 1k) | CC0 |
| PBR sets under `public/assets/textures/` (plaster, terracotta, asphalt, concrete, clay roof, sand, wood) | Poly Haven | CC0 |
| Furniture scans (sofa, bed frame, chair, plant, lamp, table, generator) | Poly Haven | CC0 |
| Face-me compound | Procedural rooms. Outside walls and the zinc roof take their plaster and rusty-zinc look from the street kit so the block matches the bungalows. | — |
| Oloya Street kit (`public/assets/env/env_buildings.glb`, `env_street.glb`, `env_props.glb`, `env_vehicles.glb`) | Original kit built for this game. Textures are CC0 from ambientCG and Poly Haven. AO and grime are baked into vertex colours. Shop signs are fictional. | CC0 |
| Day sky `public/assets/env/sky_day_1k.hdr` | Poly Haven | CC0 |
| Draco, Meshopt, and KTX2 decoders | three.js 0.186.1 examples, loaded from jsDelivr when a compressed glTF needs them | MIT |
| Interior lighting fallback | three.js `RoomEnvironment` if the HDRI fails | MIT |

If a character file 404s, the game logs one warning and uses the procedural capsule body. That fallback is not a scanned person.

The playable Sims are the Microsoft Rocketbox avatars: a Black man in a denim jacket, white tee, jeans and trainers, and a Black woman in a dark trouser suit and white shirt. Their embedded PBR textures are left as authored. The old Quaternius mannequin is not used.
