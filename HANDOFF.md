# 다른 컴퓨터에서 작업 이어가기

## 클라우드에서 이어가기
사용자는 파일 이동 없이 Codex Cloud 환경에서 계속 작업하기를 요청했습니다. ZIP 전달 방식은 최종 목표가 아닙니다.
기존 사이트 소스는 Sites의 비공개 Git 저장소에 있습니다. Codex Cloud 환경은 GitHub/GitLab 저장소 연결이 필요합니다. 클라우드에서 실행 가능한 전체 웹 소스와 인수인계 정보를 이 저장소에 준비했습니다.
비공개 GitHub 저장소 https://github.com/yjyj41/london-isometric-atlas 와 Codex Cloud 환경이 연결됐습니다. 초기 전체 소스는 GitHub에 직접 반영합니다. 첫 클라우드 실행에서 서버·JS 구문·데이터·Rhino 헤더 검사는 통과했으나, 대규모 바이너리 추가 diff를 추출하는 단계가 용량 제한으로 실패했습니다. 후속 작업에서는 기존 모델과 vendor 바이너리를 불필요하게 다시 커밋하거나 재생성하지 마세요.
설정 후 클라우드 작업 시작 문구:
> AGENTS.md와 HANDOFF.md를 읽고 런던 3D 지도 작업을 이어줘. node serve.cjs로 실행해 현재 상태를 확인하고, 실제 미터 스케일·고정 아이소메트릭·Rhino 6/7 호환을 유지해줘. 기존 .openai/hosting.json의 Sites 프로젝트를 재사용해줘.
브라우저 IndexedDB에만 저장한 개인 수정 모델은 소스 저장소에 없습니다. 원래 .3dm을 클라우드 작업에 별도로 제공해야 합니다.

## 현재 구현 (2026-09-22)
- 중앙 런던 약 4.2 × 3.0 km, 실제 OSM 윤곽 기반 16,741개 매스.
- 랜드마크 12곳. St Paul's, Shard, Gherkin, Tower Bridge, Tate Modern, Millennium Bridge, Barbican, Lloyd's, Westminster, Abbey, British Museum, Tower of London.
- Three.js 0.180, 직교 투영, 방위각 45°, 고도각 35.264°, 회전 잠금.
- X east / Y north / Z up의 미터 좌표. Three에서는 X east / Y up / Z south로 변환.
- AEQD 원점 위도 51.51, 경도 -0.106. 개별 Rhino 파일은 landmark.anchor 기준 로컬 좌표, 전체 도시는 공통 원점.
- Rhino 다운로드는 6 형식(archive header 60). Rhino 7에서도 사용. 파일은 메시이며 NURBS/BIM 아님.
- .3dm 재불러오기, 단위 인식, 전체 도시/개별 건물 교체, IndexedDB 유지, 원본 복원.
- 지형 평면. 높이 출처: OSM height 3,994 / 층수×3.2m 6,585 / 12m 가정 6,162. 지붕과 일부 랜드마크 형태는 근사. 측량용 모델 아님.

## 파일 구조와 실행
- dist/index.html, style.css, app.js: UI와 모델 불러오기.
- dist/mass-scene.js: Three 렌더러, 고정 카메라, 도시 배치, 모델 교체.
- dist/geometry.js: 동일 매스를 브라우저와 Rhino에 생성하는 공통 기하.
- dist/storage.js: 기기별 IndexedDB 저장소.
- dist/assets/city.json: 현재 매스 데이터, 원점, 랜드마크, OSM 출처. 원시 OSM 없이 기존 사이트 편집 가능.
- dist/assets/rhino/: 도시 ZIP과 개별 .3dm. 기존 다운로드 경로도 Rhino 6 파일로 유지.
- dist/vendor/: 필요한 JS/WASM 라이브러리 포함. 기본 실행에는 외부 패키지 설치 불필요.
- .openai/hosting.json: 기존 사이트 식별 정보. 인증정보 아님.
- node serve.cjs → http://127.0.0.1:4173 (Node.js 필요).

## 매스 다시 생성하기 (필요한 경우만)
프로젝트 루트에서 Python 환경에 `pip install -r tools/requirements.txt` 실행.
`node tools/export-meshes.mjs` 다음 `python tools/export-rhino.py` 실행.
rhino3dm 라이브러리 버전 8.35여도 출력 파일 버전은 반드시 Write(..., 6).
OSM 재수집은 `python tools/fetch-osm.py`, 이후 `python tools/build-city.py`. 이 작업은 인터넷과 시간이 필요하며 최신 OSM이므로 현재 스냅샷과 결과가 달라질 수 있음. 일반 UI 변경에는 실행 불필요.

## 배포와 충돌 방지
기존 사이트 ID: appgprj_6ab0f6c9e0f4819199adfc6864b7515d
현재 접근 범위: 소유자 전용. 사용자가 요청하지 않으면 공개로 변경하지 않음.
Sites 플러그인을 이용하고, 같은 소유자 계정/워크스페이스에서 기존 사이트를 열 것. 다른 PC의 인증·도구 사용 가능 여부는 그 PC에서 확인해야 함.
Sites source credential을 새로 발급받아 반환된 Git 저장소를 복제하면 최신 소스와 이력이 복구됨. 인증정보를 소스에 저장하지 말 것. 최신 원격 변경을 먼저 확인하고 강제 덮어쓰지 말 것.
이 PC에서는 bash가 없어 공식 로컬 패키징 도구가 실행되지 않아 push → save_site_version(원격 빌드) → deploy_private_site_version 경로 사용. 다른 환경에서 공식 패키징 가능하면 정상 archive 배포 사용.
클라우드 작업과 로컬 작업에서 동시에 배포하지 말 것.

## 확인한 기능과 미완료 범위
로컬 데스크톱/모바일 렌더링, St Paul's .3dm 원본 크기 왕복, 브라우저 새로고침 유지, 전체 도시 16,741개 메시 인식·교체·복원 확인. Rhino 6 파일은 헤더/객체명/메시 개수/미터 단위 검사 완료. 실제 Rhino 6 데스크톱 앱 실행 검증은 하지 않음.
런던 전체와 서버 모델 동기화·공동 편집은 미구현. Codex Cloud 환경은 연결 완료. 아래 2026-09-30 확장 기록이 현재 구현을 대체합니다.

## 2026-09-30 — Isokon / 북부 런던 확장
6.84 × 7.12 km, 67,215개 매스, Isokon 포함 13개 랜드마크. 중심부 기존 OSM 스냅샷과 새 북부·서부 추출 데이터를 합쳤습니다. 공통 미터 원점과 개별 랜드마크 로컬 원점 유지. Isokon은 way/319837891의 실제 윤곽, 높이는 12m 가정; 23.16 × 50.09 × 12m 매스이며 갤러리/발코니/상부 후퇴부는 단순화했습니다.
city.json v3는 전체 주변 건물 데이터가 아니라 랜드마크, 전체 보기 대표 매스와 110개 750m 상세 타일 색인입니다. 전체 윤곽 데이터는 city-data.zip으로 제공합니다. 초기 색인 약 1.09MB, 상세 타일 전체 14.19MB, 최대 타일 약 323KB. 배포 서버 압축은 서버 설정에 따릅니다.
확대 시 화면 주변 타일만 2개 요청 병렬로 받으며, 메시 구성은 worker에서 실행합니다. 상세 기하 버퍼는 desktop 48MiB/20타일, mobile 24MiB/10타일로 제한하고, 화면에서 멀어지면 dispose합니다. 이 제한은 전체 브라우저 RAM 제한이 아닙니다. 전체 보기 대표 박스, 랜드마크/지면/재질/렌더러 메모리는 별도입니다.
도시 Rhino는 southwest/southeast/northwest/northeast ZIP으로 나눠 약 5.3–10.5MiB입니다. 네 파일 모두 도시 공통 원점이며 Rhino에서 Import로 합칠 수 있습니다. 합친 전체 파일은 약 119MiB이므로 웹 재불러오기 100MB 제한에 맞추려면 ReduceMesh가 필요합니다. 개별 Isokon Rhino 파일은 로컬 원점이며 브라우저 분석 64 triangles와 원본 크기 일치를 확인했습니다.
수직 드래그 부호를 수정했고, 화면 +30px/+60px 드래그로 핀이 같은 +30px/+60px 이동하는 것을 검증했습니다. 전체 보기로 돌아오면 상세 기하 0 bytes/0 tiles가 되는 것도 확인했습니다. node tools/verify-region.mjs로 모든 기하와 개수 검증.
전체 재생성: python tools/fetch-region.py → python tools/build-city.py → python tools/tile-city.py → node tools/export-meshes.mjs → python tools/export-region-rhino.py. 기존 fetch-osm.py는 구형 중심부 추출 전용입니다. tools/city-full.json은 재생성 중간 데이터입니다.

OSM 데이터와 파생 매스는 ODbL 1.0. https://www.openstreetmap.org/copyright


## 2026-09-30 — 실제 도시 형상 복원 (위 확장의 표시 방식 대체)
대표 박스 11,637개를 없앴습니다. 그것은 실제 윤곽/방향/중정/가로를 훼손하고 인접 건물에 겹쳐 보이는 회귀였습니다. 이제 전체 보기부터 근접 보기까지 67,215개 원본 매스와 모든 도로의 동일한 실제 기하를 사용합니다. 랜드마크 제외 주변 기하는 1,461,278 triangles이며 하나도 생략하지 않았습니다.
node tools/pack-city.mjs는 JSON 타일에서 공유 recordGeometry로 기하를 생성해 indexed mesh + uniform tile-local Uint16 coordinates + Int8 normals + gzip으로 압축합니다. 모든 source triangle 위치 비교 최대 오차 0.007161m. 도로·중정·부재 사이 간격은 원본 그대로입니다. city-mesh.js가 브라우저/검증에서 동일한 형식을 읽습니다.
색인 625,531 bytes, 모든 주변 메시 다운로드 14,966,061 bytes, GPU 기하 attribute/index buffers 31,204,362 bytes (기존 펼친 기하 105,212,016 bytes). 48 MiB desktop / 40 MiB mobile 상한에 전체 도시가 들어갑니다. 이 수치는 브라우저 총 RAM이 아닙니다. 모든 확대 단계에서 화면 주변 지역을 두 개씩 요청, 화면 밖 기하는 해제합니다. 작은 박스 대체물은 없습니다. worker geometry 생성은 런타임에서 사용하지 않습니다.
시작 화면은 읽기 쉬운 중앙 런던 범위이며 전체 보기 버튼은 Isokon을 포함한 전 영역을 보여줍니다. 기존 수직 드래그 수정과 Rhino 6/7 다운로드/편집은 유지했습니다.
기하 변경 후: node tools/pack-city.mjs → node tools/verify-region.mjs. JSON 타일은 그대로 편집용 원본이며 압축 웹 메시로 Rhino 원본을 덮어쓰지 마세요. GitHub에서도 dist/assets/meshes/는 일반 소스로 추적하므로 bootstrap ZIP을 갱신할 필요 없이 새 클론에 포함됩니다.

템스강 누락도 복구했습니다. OSM bbox API가 multipolygon의 원거리 member를 누락해 강 폴리곤이 닫히지 않았습니다. relation/28934/full 및 relation/70347/full로 실제 강 윤곽을 완성했습니다. tools/water-surfaces.json에 투영된 원본을 보존하고 build-city.py가 재생성 시 병합합니다. 전체 데이터 ZIP에도 반영, Millennium Bridge 아래 수면 존재를 검증합니다. 물과 지면만 수정해 Rhino 건물 메시에는 변경이 없습니다.


## 2026-09-30 — 동·남부 확장 / 현재 구현
이 절이 위의 범위·개수·성능 수치를 대체합니다. 사용자가 승인한 Canary Wharf, Greenwich, Bermondsey, Peckham까지 확장했습니다. 경계 [-0.17,51.47,0.01,51.56], 약 12.51 × 10.02 km, 151,248개 매스, 238개 타일. 기존 중심부/북서쪽 건물 원본을 유지하고 Geofabrik Greater London 2026-09-29 추출로 동·남부를 채웠습니다. 실제 강·도크·공원·도로와 완성된 multipolygon을 사용합니다. 무작위 배치/대표 박스 없음.

새 랜드마크 8곳(총 21): Battersea Power Station, Peckham Library, Laban Dance Centre, One Canada Square, Crossrail Place, Old Royal Naval College, Queen’s House, Royal Observatory / Flamsteed House. 원 캐나다 스퀘어의 235 m 높이·25 m 피라미드, 배터시 네 굴뚝, 페컴 상부 열람실·지붕 부재, 해군대학 중정·돔은 OSM 부재 기반입니다. 크로스레일 곡면 지붕과 페컴의 경사 기둥은 실제 평면 위 개략 형상이며 카드에 명시했습니다. 지형은 여전히 평면입니다.

초기 색인 약 1.50 MB, 전체 주변 메시 다운로드 33.22 MB, GPU 기하 버퍼 69.48 MB(전체 RAM 아님). 128 MiB desktop / 96 MiB mobile 상한 안에 전체 문맥 기하가 들어갑니다. 두 타일씩 화면 영역을 로드하고 화면 밖은 해제. 전체 3,253,092개 주변 삼각형의 source vertex 비교 최대 오차 0.007161 m. 원점, 드래그 방향, 실제 평면과 높이는 유지했습니다.

Rhino 6/7: 여덟 지역 ZIP(6.5–13.0 MB), 21개 개별 모델. 지역들은 같은 도시 원점, 개별 건물은 각 anchor 원점. 지역 파일의 비압축 용량 합은 약 266 MB이고 전체 도시 삼각형도 웹 300만 제한을 넘으므로 전체를 합친 뒤 재불러올 때 ReduceMesh 필요. 지역 하나를 도시 대상으로 불러오면 그 지역만 표시하는 기존 동작입니다. 개별 모델은 브라우저 로컬 IndexedDB 저장입니다.

현재 재생성 순서는 README.md 참조. detail-landmarks.py를 tile-city.py보다 먼저 실행해야 합니다. Geofabrik 원본·기존 raw snapshot은 ignored files; 일반 UI/모델 편집은 커밋된 JSON/메시와 city-data.zip만 사용합니다. JSON 타일과 압축 메시의 버전을 함께 갱신하세요. GitHub의 bootstrap.py는 새 동·남부 번들 우선 복구 및 이전 번들과 일치하는 생성 파일 업그레이드를 지원합니다. 사용자 수정 파일은 보존하고 충돌을 알립니다.


## 2026-09-30 — 랜드마크 상세화·사진 / 현재 구현
이 절이 위의 랜드마크·매스 개수를 대체합니다. 총 27곳, 151,407개 모델 부재. Isokon은 실제 위치·방향 위에 94개 부재로 재구성: 연속 갤러리, 난간, 외부 계단, 후면 발코니, 옥상 펜트하우스와 낮은 갤러리 별동. 층고 2.8m / 최고 14.25m와 세부 치수는 문화재 기록·사진 기반 근사이며 실측이 아닙니다.
추가 6곳: National Theatre, Royal Festival Hall, Hayward Gallery, British Library, Coal Drops Yard, London Aquatics Centre. tools/curated_details.py는 detail-landmarks.py 내부에서 실행됩니다. 후자의 입력은 build-city.py의 v2 전체 자료여야 합니다.
모든 27개 카드에 실제 외관 사진·작가·라이선스·출처 링크. dist/assets/photos에 자체 호스팅, tools/landmarks.json의 photo 메타데이터를 보존할 것. 사진 총 약 2.4 MB, 각 200 KB 미만, 선택 시에만 불러옵니다. 자료 사진의 시점이 현재 건물 상태와 다를 수 있습니다.
238개 실제 윤곽 타일, 전체 주변 3,251,896 triangles / 다운로드 33.21 MB / GPU 기하 69.46 MB. 초기 색인 약 2.32 MB. 세부 모델을 위해 최대 확대 400으로 확장, 드래그·고정 카메라는 유지. 27개 개별 및 8개 지역 Rhino6 파일 갱신. GitHub의 새 landmark-detail 번들을 기존 번들보다 우선 복구하며 기존 번들은 안전한 사용자 편집 판별을 위해 유지합니다.


## 2026-09-30 — English edition / 33 landmarks (current)
The user intends to develop a web service and requested English throughout, plus more major buildings. All visible UI, dialogs, accessible names, 33 descriptions, model notes and photo captions are English. The Site audience remains owner-private. Added St Pancras International, King's Cross Station, Senate House, Somerset House, National Gallery and Bloomberg European Headquarters, with photos, selection labels and Rhino 6/7 files.
151,426 model parts, 238 tiles, 3,248,564 context triangles. Initial manifest about 3.96 MB, context download 33.18 MB, context GPU geometry 69.38 MB. Old 27 landmark geometries are identical to the preceding release. Keep English content in tools/english-content.json and tools/landmarks.json; detail-landmarks.py applies the English overrides after procedural notes. New approximate profiles live in tools/station_details.py. Run verify-english.mjs and verify-region.mjs after changes.


## Visited buildings and exterior finishes (2026-10-01)

All 33 landmark cards now have Mark as visited / Visited (Undo). Visits are explicitly device-local, as requested: localStorage key london-field-atlas.visits.v1, with versioned building IDs and timestamps. Refresh preserves visits. Directory and map pins show checkmarks; the directory shows a visited count. Storage failures are labelled session-only; unreadable stored records are not overwritten. Other-tab storage events update the UI, and writes merge the latest records before changing a building.

dist/landmark-finishes.js defines 33 reference-informed palettes based on the existing credited exterior photographs. A shared procedural surface shader gives glass mullions, Gherkin spiral/diagonal glazing, subtle brick joints, concrete board marks, metal ribs, coloured panels and roof finishes. These are approximations, not photo-mapped, surveyed or individually verified facade layouts. Existing named parts distinguish Battersea chimneys, Isokon gallery/render/recesses, station roofs and Hayward rooflights. Some adjacent masses in the older Tower Bridge selection group are deliberately left ivory.

A visited landmark transitions from ivory over 650 ms (instant with reduced-motion). Undo restores ivory. Height sources still controls surroundings only. Imported Rhino models retain their existing appearance and the visit card explains this; restoring an original reveals its saved visited finish. Neither the mass vertices/normals nor Rhino downloads change. Original landmark surface attributes add 1,040,376 bytes of GPU data; materials are created on demand, with no extra texture downloads and no additional mesh draw calls.

Verification: node tools/verify-visits.mjs checks all 33 palettes, unchanged geometry, visit reload/undo, multi-tab merging, unavailable storage and corrupt data. node tools/verify-english.mjs checks English UI. Browser QA covers reveal, undo, refresh persistence, desktop material previews and a 390px mobile viewport with a 44px visit button.
