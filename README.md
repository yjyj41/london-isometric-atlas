# London Field Atlas — Rhino mass workflow

1. Download the city ZIP and unzip, or download one building's .3dm from its card.
2. Open in Rhino 6 or 7 (also supported by Rhino 8). Downloads are saved in Rhino 6 file format. Files use metres, X east, Y north, Z up. City origin is latitude 51.51, longitude -0.106 (WGS84 local azimuthal equidistant projection).
3. Keep the origin, orientation and scale. Individual building files use a local origin at that building's anchor; the website applies that anchor automatically. Do not move a city model to a building-local origin or vice versa.
4. Models are editable meshes, not parametric NURBS/BIM. Use mesh editing tools or replace with your own geometry. For new NURBS, run Mesh and save the resulting visible mesh objects. Avoid duplicate visible surfaces and meshes.
5. Save as .3dm. In the website choose Rhino 불러오기, choose the matching target and file, check the displayed dimensions, then 지도에 적용.
6. For whole-city files preserve object names LM:<building-id>|<object-id> to preserve building selection. Other names become context. IDs: stpauls, shard, gherkin, towerbridge, tate, millennium, barbican, lloyds, westminster, abbey, museum, tower.
7. Files remain in this browser's IndexedDB only. Clearing browser data removes them. Keep your own .3dm backup. Original restore affects the selected target only.

One unit = 1 metre. Automatic metre/mm/cm/feet/inch units are supported. Override if necessary. Models are not normalized or automatically resized. Maximum upload: 100 MB and 3 million triangles, extent 25 km.

Data: © OpenStreetMap contributors, https://www.openstreetmap.org/copyright, ODbL 1.0. Extracted 2026-09-21. 16,741 masses. Footprints and coordinates are geographic data; height values include OSM-tagged heights, estimates of 3.2 m per floor and a 12 m fallback. Terrain is flat; roofs and landmark forms are approximations. Not a survey model. OSM-derived data are supplied in assets/city.json under ODbL. Geometry and templates derive from the same data.


## Codex Cloud

Use the private yjyj41/london-isometric-atlas environment and main branch. Read AGENTS.md and HANDOFF.md, then run `node serve.cjs`. The app runs without npm install. No source ZIP or local-computer transfer is needed. Keep binary model and vendor files unchanged unless the task specifically requires updating them; large binary changes can exceed cloud diff limits.


Current map: 67,215 masses, 6.84 x 7.12 km, 13 landmarks including Isokon. Streaming manifest + 110 detail tiles, generalized overview, worker geometry, bounded detail memory. Run node serve.cjs (offline asset restore); static-host build command python3 bootstrap.py, publish dist. Rhino 6/7 downloads are regional ZIPs; full data ZIP is available in the download dialog.


Current map: 67,215 masses, 6.84 x 7.12 km, 13 landmarks including Isokon. Streaming manifest + 110 detail tiles, generalized overview, worker geometry, bounded detail memory. Run node serve.cjs (offline asset restore); static-host build command python3 bootstrap.py, publish dist. Rhino 6/7 downloads are regional ZIPs; full data ZIP is available in the download dialog.
