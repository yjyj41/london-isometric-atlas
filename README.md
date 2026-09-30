# London Field Atlas

Actual London footprints, streets and landmark masses in metres, with a fixed orthographic isometric camera. Coverage: 6.84 × 7.12 km, 67,215 masses, 13 landmarks including Isokon Flats.

Run `node serve.cjs`. Source is `dist/`; no frontend build or npm install. Start at central London, use the full-map control to include Belsize Park, or select a landmark.

## Geometry and performance

All zoom levels preserve the original building shapes, courtyards, roads, positions and heights. No representative boxes or invented buildings. The 110 spatial tiles contain packed exact mesh triangles. The initial manifest is 0.63 MB; all surrounding meshes total 14.97 MB compressed and 31.20 MB in GPU geometry buffers. Only visible regions load, two at a time, and offscreen geometry is disposed. Geometry budget: 48 MiB desktop / 40 MiB mobile, excluding landmarks, ground and other browser memory.

After geometry changes run `node tools/pack-city.mjs`, then `node tools/verify-region.mjs`. Verification compares every packed triangle vertex with source geometry (maximum error under 1 cm), all 67,215 records and Rhino headers. Keep JSON tiles as editable source; packed assets are generated output.

## Rhino editing

Download one landmark's .3dm or the four regional city ZIPs. All files use Rhino 6 format, also readable by Rhino 7. Units: metres. X east, Y north, Z up. City origin: WGS84 latitude 51.51, longitude -0.106, local azimuthal equidistant projection. Regional files share that origin and can be merged in Rhino. Individual landmarks use their own local anchor.

Keep origin, scale and orientation. Save visible mesh objects as .3dm and choose the matching target in Rhino 불러오기. NURBS should be meshed before import. Preserve LM:<building-id>|<object-id> object names for whole-city landmark selection. Upload limit: 100 MB / 3 million triangles. Imports stay in this browser's IndexedDB only; keep your own backup.

Data: © OpenStreetMap contributors, https://www.openstreetmap.org/copyright, ODbL 1.0. Central snapshot 2026-09-21 plus northern/western extraction 2026-09-30. Footprints and placement are actual map data; heights use OSM height, levels × 3.2 m, or an explicitly assumed 12 m. Flat terrain; roofs and landmark forms are approximations, not survey/BIM models. Isokon has an actual footprint and assumed 12 m height.

## Codex Cloud

Use the private yjyj41/london-isometric-atlas environment, main branch. Read AGENTS.md and HANDOFF.md. `node serve.cjs` restores missing original model/vendor assets offline; no file transfer from this PC is needed. For another static host: build `python3 bootstrap.py`, publish `dist`. Packed meshes are tracked directly, and bootstrap preserves edited files. Keep existing Rhino and vendor bundles unchanged unless their source data changes.
