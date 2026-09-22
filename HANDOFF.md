# London Atlas — Codex Cloud

클라우드 환경: yjyj41/london-isometric-atlas / main
GitHub: https://github.com/yjyj41/london-isometric-atlas (private)
Live Site: https://london-isometric-atlas.yjoooong.chatgpt.site

## Start
Run `node serve.cjs` from the repository root. Node automatically invokes `python3 bootstrap.py` (Windows: python) to restore missing bundled assets, then serves http://127.0.0.1:4173. Cloud has Node and Python. No npm install, network fetch or user file transfer is needed. Source files in dist/ and tools/ are normal Git-tracked files.

## Asset bundle
london-atlas-cloud-source.zip is a versioned asset bundle retained to avoid Codex large-binary diff limits. bootstrap.py validates SHA256 and extracts only dist/assets and dist/vendor. It never overwrites files that already exist, and never extracts source code or instruction files. Generated asset folders are gitignored. UI/source edits persist through ordinary commits and PRs. For intentional model changes, commit only individual changed assets with `git add -f path` (bootstrap respects tracked overrides), or deliberately refresh the bundle and its checksum. Do not add all generated assets to an ordinary UI change. A first attempt to add the entire model set through a Codex diff exceeded its size limit; do not repeat it.

## Invariants
16,741 OSM-derived masses; 12 landmarks; metric scale; fixed orthographic isometric camera. Origin AEQD lat 51.51 lon -0.106, X east/Y north/Z up; Three uses X east/Y up/Z south. Landmark files have local anchors. Rhino downloads are version 6 (header 60), meshes, compatible with Rhino 7. Preserve OSM attribution, approximate height notes, and units. Height counts: 3994 OSM heights, 6585 levels x 3.2 m, 6162 fallback 12 m. Flat terrain and simplified roofs are intentional limitations.

## Continue work
Read AGENTS.md, run the server, then implement the user's next request. No expansion to all London has been requested yet. Do not change the product during cloud setup. Browser-imported personal models live only in that browser's IndexedDB and are not included here.

## Publishing
Preserve .openai/hosting.json project_id appgprj_6ab0f6c9e0f4819199adfc6864b7515d and owner-private access. Use Sites skills/connectors when available. GitHub code commits are NOT automatic live deployment. Before packaging for Sites run bootstrap.py so dist has assets; exclude the source asset ZIP from hosted dist. Never force-push unrelated Sites history; use an authenticated Sites checkout and copy the desired source there. Never put authentication tokens in files.

## Validation
The first cloud run verified local HTTP 200, JS syntax, city.json 16741 masses, all 24 Rhino headers=60 and both valid city ZIPs. No Chromium executable was available, so no new cloud screenshot was obtained. Local desktop/mobile rendering and import roundtrip had been verified earlier. Actual Rhino 6 application testing was not performed.
