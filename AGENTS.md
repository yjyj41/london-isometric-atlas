# London Field Atlas

Read HANDOFF.md before continuing. This is an existing private Sites website. Preserve the project_id in .openai/hosting.json and update that Site; do not create a replacement. Use the available Sites skill and authenticated connector for publishing. Never store credentials in files or source archives.

The user's priorities are metric real 3D mass geometry, a fixed orthographic isometric camera, and Rhino 6/7-compatible edit-and-reimport workflows. Preserve metre units and coordinate origins. Keep OSM attribution and distinguish inferred heights from recorded values.

Run locally with `node serve.cjs`; no npm install or frontend build is needed. Source is dist/.

Current map: central and north London, 6.84 x 7.12 km, 67,215 masses and 13 landmarks including Isokon Flats. dist/assets/city.json is a version-3 streaming manifest, not the complete surrounding-building dataset. It contains all landmark masses, the overview, and paths to 110 detail tiles. Do not treat its buildings.length as the total city count. tools/verify-region.mjs validates tile coverage and geometry. Detailed geometry is capped at 48 MiB / 20 tiles on desktop and 24 MiB / 10 tiles on mobile. Keep fallback overview visible and avoid repeated eviction/re-download loops.

The intended continuation environment is Codex Cloud backed by a dedicated private GitHub repository. Check the current remote branch before publishing from a different PC, and merge newer work rather than overwriting it. Use fresh repo-scoped credentials through Sites; never force-push another machine's work.
