# London Field Atlas

Actual London footprints, streets and landmark masses in metres, with a fixed orthographic isometric camera. Coverage: 12.51 × 10.02 km, 151,426 masses, 33 landmarks from Isokon to Greenwich, including Canary Wharf, Bermondsey, Peckham and Battersea.

Run `node serve.cjs`. Source is `dist/`; no frontend build or npm install. Start at central London, use the full-map control to include the entire expanded extent, or select a landmark.

## Geometry and performance

All zoom levels preserve the original building shapes, courtyards, roads, positions and heights. No representative boxes or invented buildings. The 238 spatial tiles contain packed exact mesh triangles. The initial manifest is 3.96 MB; all surrounding meshes total 33.18 MB compressed and 69.38 MB in GPU geometry buffers. Only visible regions load, two at a time, and offscreen geometry is disposed. Geometry budget: 128 MiB desktop / 96 MiB mobile, excluding landmarks, ground and other browser memory.

After geometry changes run `node tools/pack-city.mjs`, then `node tools/verify-region.mjs`. Verification compares every packed triangle vertex with source geometry (maximum error under 1 cm), all 151,426 records and Rhino headers. Keep JSON tiles as editable source; packed assets are generated output.

## Rhino editing

Download one landmark's .3dm or the eight regional city ZIPs. All files use Rhino 6 format, also readable by Rhino 7. Units: metres. X east, Y north, Z up. City origin: WGS84 latitude 51.51, longitude -0.106, local azimuthal equidistant projection. Regional files share that origin and can be merged in Rhino. Individual landmarks use their own local anchor.

Keep origin, scale and orientation. Save visible mesh objects as .3dm and choose the matching target in Rhino 불러오기. NURBS should be meshed before import. Preserve LM:<building-id>|<object-id> object names for whole-city landmark selection. Upload limit: 100 MB / 3 million triangles. Imports stay in this browser's IndexedDB only; keep your own backup.

Data: © OpenStreetMap contributors, https://www.openstreetmap.org/copyright, ODbL 1.0. Central snapshot 2026-09-21 and northern/western extraction retained, plus Geofabrik Greater London snapshot 2026-09-29 for the east/south extension. Source details: tools/data-provenance.json. Footprints and placement are actual map data; heights use OSM height, levels × 3.2 m, or an explicitly assumed 12 m. Flat terrain; roofs and landmark forms are approximations, not survey/BIM models. Isokon retains its mapped placement and orientation, with 94 architectural parts and an approximate 14.25 m top height; detailed dimensions are reference-informed, not measured.

## Expanded landmarks and regeneration

Eight new cards, labels and Rhino masses: Battersea Power Station, Peckham Library, Laban Dance Centre, One Canada Square, Crossrail Place, Old Royal Naval College, Queen’s House and Royal Observatory / Flamsteed House. Mapped building parts supply Battersea’s four chimneys, Canada Square’s 25 m pyramid crown, Peckham’s raised reading room and roof pods, and the Naval College’s courts and domes. Crossrail’s curved canopy and Peckham’s seven leaning supports are reference-informed approximations, documented on the cards. No fictitious context buildings are added.

Ordinary edits need only the committed manifest, JSON tiles and mesh files. For a full geographic rebuild, retain tools/london-osm.json (the existing source snapshot), install tools/requirements.txt, then run:

```text
python tools/extend-from-pbf.py
python tools/build-city.py
python tools/detail-landmarks.py
python tools/tile-city.py
node tools/pack-city.mjs
node tools/export-meshes.mjs
python tools/export-region-rhino.py
node tools/verify-region.mjs
```

The extractor uses the cached dated Geofabrik PBF or downloads that snapshot if missing. Raw snapshots are ignored and are not required to run or edit the website; do not rerun legacy fetch-region.py or fetch-osm.py over the expanded data. The complete editable generated data are in dist/assets/city-data.zip. Install osmium only when rebuilding geographic source data.

The full context has 3,248,564 triangles. A merged Rhino city exceeds the browser’s 100 MB / 3 million triangle import limit; use regional/individual editing or ReduceMesh before reimport. The regional model files total about 266 MB uncompressed. Initial map data are ~3.96 MB before HTTP compression; 33.18 MB is the sum of all context tile downloads, not an initial-load requirement. GPU buffer figures exclude landmark meshes, terrain, textures, driver and CPU overhead. Performance depends on device/network; geometry remains exact at every zoom.


## Landmark detail and photographs (2026-09-30)

All 33 cards show a local, compressed exterior photograph above the description, with author, source and license links. Images are loaded only when that card is selected. Combined photo assets are about 2.4 MB; each image is under 200 KB. The individual image licenses and adaptation notes are embedded in tools/landmarks.json and city.json. Photographs are reference views and may show earlier conditions.

Six additions: National Theatre, Royal Festival Hall, Hayward Gallery, British Library, Coal Drops Yard and London Aquatics Centre. OSM parts preserve the National Theatre terraces and Festival Hall volumes. The 66 Hayward rooflights, Library roofs, Coal Drops lifted roofs, Aquatics curved shell and Isokon details use explicit approximate profiles in tools/curated_details.py, called by detail-landmarks.py. Cards distinguish these from measured models. Isokon has gallery slabs, parapets, exterior stair flights, rear balconies, the penthouse and gallery annex. All 33 individual Rhino files and eight regional models share the same browser geometry. Close zoom now supports inspecting small architectural details.


## English edition and six further landmarks (2026-09-30)

The complete interface, all 33 building cards, loading/error messages, accessibility labels and Rhino instructions are English (en-GB). English subtitles identify locations rather than repeat building names. Run node tools/verify-english.mjs after content edits. tools/english-content.json preserves English descriptions during geometry regeneration.

Six further landmarks: St Pancras International, King's Cross Station, Senate House, Somerset House, National Gallery and Bloomberg European Headquarters. Actual mapped footprints and parts are retained; roof profiles for the two stations and Somerset House are schematic and disclosed in the cards. National Gallery's mapped dome and Senate House's tower setbacks use original parts. All six include licensed photographs and Rhino 6 downloads. The previous 27 landmark geometries were compared with the preceding version and remain identical.

Current initial manifest: about 3.96 MB (about 0.64 MB gzip before regional download metadata); context meshes: 33.18 MB compressed and 69.38 MB GPU geometry. Photographs load only on selection. This release changes content and models, not the Site audience or local-only storage of imported models.
