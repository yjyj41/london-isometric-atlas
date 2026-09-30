# London Field Atlas

Read HANDOFF.md before continuing. This is an existing private Sites website. Preserve the project_id in .openai/hosting.json and update that Site; do not create a replacement. Use the available Sites skill and authenticated connector for publishing. Never store credentials in files or source archives.

The user's priorities are metric real 3D mass geometry, a fixed orthographic isometric camera, and Rhino 6/7-compatible edit-and-reimport workflows. Preserve metre units and coordinate origins. Keep OSM attribution and distinguish inferred heights from recorded values.

Run locally with `node serve.cjs`; no npm install or frontend build is needed. Source is dist/.

Current map: central, north, east and south London, 12.51 x 10.02 km, 151,248 masses and 21 landmarks, from Isokon to Canary Wharf, Greenwich and Peckham. dist/assets/city.json is a version-3 manifest with landmark records and 238 tile descriptors. JSON tiles preserve editing/Rhino geometry. Runtime uses assets/meshes/*.mesh.gz, exact triangles at every zoom. NEVER replace actual footprints with bounding boxes, representative buildings or random infill. Every packed vertex is verified within 1 cm of the source. Context GPU attribute/index buffers total 69.48 MB; budgets are 128 MiB desktop / 96 MiB mobile, excluding landmarks, ground, renderer and CPU memory. Two concurrent downloads, viewport loading and offscreen disposal. No source sampling or geometry LOD.

After geographic changes follow the regeneration sequence in README.md, including detail-landmarks.py before tile-city.py. Run pack-city.mjs after tile geometry changes, regenerate eight regional and 21 landmark Rhino 6 files when geometry changes, then verify-region.mjs. Preserve mapped OSM parts: do not extrude a second full parent building through them. Custom landmark profiles use the same recordGeometry in browser and Rhino. Crossrail uses its complete mapped footprint under a sampled curved canopy; Peckham keeps mapped raised volumes, with schematic support columns only. Model notes disclose approximations. Shared metre origin and existing import behavior must remain unchanged.

The intended continuation environment is Codex Cloud backed by a dedicated private GitHub repository. Check the current remote branch before publishing from a different PC, and merge newer work rather than overwriting it. Use fresh repo-scoped credentials through Sites; never force-push another machine's work.
