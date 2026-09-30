# London Field Atlas

Read HANDOFF.md before continuing. This is an existing private Sites website. Preserve the project_id in .openai/hosting.json and update that Site; do not create a replacement. Use the available Sites skill and authenticated connector for publishing. Never store credentials in files or source archives.

The user's priorities are metric real 3D mass geometry, a fixed orthographic isometric camera, and Rhino 6/7-compatible edit-and-reimport workflows. Preserve metre units and coordinate origins. Keep OSM attribution and distinguish inferred heights from recorded values.

Run locally with `node serve.cjs`; no npm install or frontend build is needed. Source is dist/.

Current map: central and north London, 6.84 x 7.12 km, 67,215 masses and 13 landmarks including Isokon Flats. dist/assets/city.json is a version-3 manifest containing landmark records and 110 tile descriptors. JSON tiles preserve surrounding-building source geometry for editing and Rhino. Runtime uses assets/meshes/*.mesh.gz, packed exact triangles at every zoom. NEVER substitute bounding boxes or representative buildings: that destroys London street and courtyard morphology. Every packed vertex is verified within 1 cm of the source. All context geometry uses 31.2 MB of GPU attribute/index buffers; budget is 48 MiB desktop / 40 MiB mobile, independent of landmark, ground, renderer and CPU memory. Two concurrent downloads, viewport-based loading and disposal. Run node tools/pack-city.mjs after tile/source geometry changes, then node tools/verify-region.mjs. No source sampling or geometry LOD. Keep landmark shaping, origin, heights and Rhino files consistent.

The intended continuation environment is Codex Cloud backed by a dedicated private GitHub repository. Check the current remote branch before publishing from a different PC, and merge newer work rather than overwriting it. Use fresh repo-scoped credentials through Sites; never force-push another machine's work.
