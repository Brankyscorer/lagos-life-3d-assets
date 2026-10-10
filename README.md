# Lagos Life 3D: game assets

Static 3D assets for **Lagos Life** (Gidi Hustle), a three.js open-world life simulator set in Lagos. The game code lives in a separate repository and loads these files at runtime from jsDelivr:

```
https://cdn.jsdelivr.net/gh/Brankyscorer/lagos-life-3d-assets@v1/<path>
```

for example `.../@v1/env/env_street.glb` or `.../@v1/characters/player_male_01.glb`.

Tags are immutable releases. To change an asset, commit it and push a new tag (`v2`, ...), then point the game's `CDN_ASSET_BASE` (`src/game/assets/url.ts`) at the new tag.

## Contents

| Folder | What |
| --- | --- |
| `characters/` | Player bodies (male and female), rigged GLB with idle, walk, run, sit, sleep, wash, eat, phone and wave clips; a CC0 mannequin glTF |
| `npc/` | 12 street pedestrians (GLB) and `npc_manifest.json` |
| `env/` | Oloya Street kit: buildings, street, props, vehicles (GLB), day sky HDR, `env_manifest.json` |
| `models/` | Furniture and prop scans (glTF + bin + 1k textures) |
| `textures/` | 1k PBR texture sets (diffuse, normal, roughness) |
| `env-day.hdr` | Fallback day HDRI |
| `manifest.json` | Character id to file map (paths relative to this repo root) |

## Licences

- Characters and NPCs: Microsoft Rocketbox Avatar Library, MIT License.
- HDRIs, PBR textures and furniture scans: Poly Haven, CC0.
- Oloya Street kit: original work for this game, with CC0 textures from ambientCG and Poly Haven.

See [CREDITS.md](CREDITS.md) for per-file sources. (Paths in CREDITS.md say `public/assets/...`; that folder is the root of this repo.)
