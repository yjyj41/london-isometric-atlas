import {createAtlas,prepareRhino} from './mass-scene.js';
import {savedModels,saveModel,deleteModel} from './storage.js';
import {createVisitStore,VISITS_KEY} from './visits.js';
import {finishes} from './landmark-finishes.js';
import {mapStyles,readMapStyle,saveMapStyle} from './map-styles.js';
import {walkRoutes} from './walk-routes.js';
import {visitTrees} from './visit-landscape.js';
const $=s=>document.querySelector(s),esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let atlas,city,visits,selected=null,pending=null,buffer=null;
let showPeople=true,showLandscape=true;
const status=s=>$('#import-status').textContent=s;
function photoMarkup(b){
 const p=b.photo;if(!p)return '<p class="photo-pending">Reference photograph not yet available.</p>';
 return `<figure class="building-photo"><a class="photo-link" href="${esc(p.sourceUrl)}" target="_blank" rel="noopener noreferrer" aria-label="${esc(b.name)} photo source"><img src="${esc(p.url)}" alt="${esc(p.alt||b.name+' exterior')}" width="${p.width||800}" height="${p.height||600}" decoding="async"><span class="photo-unavailable" hidden>Photo unavailable. View the original image.</span></a><figcaption>Photo: ${esc(p.author)} · <a href="${esc(p.licenseUrl)}" target="_blank" rel="noopener noreferrer">${esc(p.license)}</a><span class="photo-edit-note">Resized and compressed for the web</span></figcaption></figure>`;
}
const pad=n=>String(n).padStart(2,'0');
function distanceKm(a,b){const r=Math.PI/180,x=(b.lon-a.lon)*r*Math.cos((a.lat+b.lat)*r/2),y=(b.lat-a.lat)*r;return Math.hypot(x,y)*6371}
function nearby(b,n=4){return city.landmarks.filter(o=>o.id!==b.id&&Number.isFinite(o.lat)).map(o=>({o,d:distanceKm(b,o)})).sort((a,c)=>a.d-c.d).slice(0,n)}
function fact(label,value,wide=false){return `<div${wide?' class="wide"':''}><dt>${label}</dt><dd>${value}</dd></div>`}
function setLink(id){try{const url=new URL(location.href);if(id)url.searchParams.set('b',id);else url.searchParams.delete('b');history.replaceState(null,'',url)}catch{}}
function closeDetail(){document.body.classList.add('detail-closed');setLink(null)}
function select(id,focus=true){const index=city.landmarks.findIndex(b=>b.id===id),b=city.landmarks[index];if(!b)return;selected=id;atlas?.select(id,focus);const m=atlas?.measurements(id);document.body.classList.remove('detail-closed');setLink(id);document.querySelectorAll('[data-id]').forEach(el=>{el.classList.toggle('active',el.dataset.id===id);el.setAttribute('aria-pressed',String(el.dataset.id===id))});
 const total=city.landmarks.length,dateLabel=b.id.startsWith('catalog-')?'RECORDED DATE':'COMPLETION',missing='<span class="missing">Not yet recorded</span>';
 const near=nearby(b).map(({o,d})=>`<li><button type="button" class="nearby-item" data-goto="${esc(o.id)}"><span>${esc(o.name)}</span><span class="nearby-d">${d<1?d.toFixed(2):d.toFixed(1)} km</span></button></li>`).join('');
 $('#detail').innerHTML=`<div class="detail-top"><span class="sheet-no">SHEET ${pad(index+1)} / ${total} · ${esc(b.type).toUpperCase()}</span><span class="sheet-nav"><button type="button" class="sheet-step" data-step="-1" aria-label="Previous building">‹</button><button type="button" class="sheet-step" data-step="1" aria-label="Next building">›</button><button type="button" class="close-detail" aria-label="Close building card">×</button></span></div><div class="sheet-body"><h2>${b.name}</h2><p class="building-subtitle">${b.subtitle}</p>${photoMarkup(b)}<dl class="facts">${fact('ARCHITECT',b.architect?esc(b.architect):missing)}${fact(dateLabel,b.year?esc(b.year):missing)}${fact('MODEL HEIGHT'+(m?.custom?' · MY MODEL':''),m?m.height.toFixed(1)+' m':'Location marker')}${fact('MODEL PARTS',m?b.massCount.toLocaleString('en-GB'):'3D model not available yet')}${m?fact('FOOTPRINT EXTENT · E–W × N–S',m.east.toFixed(1)+' × '+m.north.toFixed(1)+' m',true):''}</dl><div id="visit-panel"></div><div class="detail-links"><a href="https://www.google.com/maps/dir/?api=1&destination=${b.lat},${b.lon}&travelmode=walking" target="_blank" rel="noopener noreferrer">Directions ↗</a><button type="button" class="copy-link">Copy link</button>${b.massCount?`<a href="./assets/rhino/${id}-rhino6.3dm" download>Rhino 6/7 model ↓</a>`:''}</div><section class="sheet-section"><h3>FIELD NOTE</h3><p class="point">${b.point}</p></section><section class="sheet-section"><h3>MODEL NOTE</h3><p class="model-note">${esc(b.modelNote||'Massing based on OSM footprints. Unrecorded heights are estimated.')}</p></section>${near?`<section class="sheet-section"><h3>NEARBY</h3><ul class="nearby">${near}</ul></section>`:''}<div class="source-links"><a href="${b.source}" target="_blank" rel="noopener noreferrer">Architecture ↗</a> · <a href="${b.modelSourceUrl||'https://www.openstreetmap.org'}" target="_blank" rel="noopener noreferrer">Geometry source ↗</a></div></div>`;
 $('#detail').scrollTop=0;const photo=$('#detail .building-photo img');if(photo)photo.onerror=()=>{photo.hidden=true;$('#detail .photo-unavailable').hidden=false};
 $('.close-detail').onclick=closeDetail;
 for(const btn of document.querySelectorAll('#detail .sheet-step'))btn.onclick=()=>{const next=city.landmarks[(index+Number(btn.dataset.step)+total)%total];select(next.id);$(`#detail .sheet-step[data-step="${btn.dataset.step}"]`)?.focus({preventScroll:true})};
 for(const btn of document.querySelectorAll('#detail [data-goto]'))btn.onclick=()=>select(btn.dataset.goto);
 $('#detail .copy-link').onclick=async e=>{const btn=e.currentTarget;let ok=false;try{await navigator.clipboard.writeText(location.href);ok=true}catch{}btn.textContent=ok?'Link copied':'Copy the address bar';$('#visit-announcement').textContent=ok?'Link to '+b.name+' copied.':'';setTimeout(()=>{btn.textContent='Copy link'},1800)};
 renderVisitPanel()}
function renderVisitPanel(){
 if(!selected||!visits)return;
 const b=city.landmarks.find(b=>b.id===selected),done=visits.has(selected),p=finishes[selected];
 const custom=atlas?.measurements(selected)?.custom;
 const studyNote=p?.study==='photo'?'Approximate palette from the reference photo; roof colours and surface patterns are inferred.':p?.study==='limited-photo'?'Provisional palette from a limited reference view; some exterior colours are inferred.':p?.study==='provisional'?'Provisional material palette; exterior colours still need photographic verification.':'';
 const storageNote=visits.persistent?'Saved in this browser only.':'Browser storage unavailable. Changes last for this session only.';
 $('#visit-panel').innerHTML=`<button class="visit-toggle" type="button" aria-pressed="${done}" aria-describedby="visit-caption"><span class="visit-icon" aria-hidden="true">${done?'✓':'+'}</span><span>${done?'Visited':'Mark as visited'}</span><span class="visit-undo">${done?'Undo':''}</span></button><p id="visit-caption" class="visit-caption">${p?(done?esc(p.label):'Reveal this building’s exterior finishes.'):(done?'Added to your field record.':'Record your visit to this building.')} ${p?esc(studyNote):'This stop has no dedicated 3D model yet; your visit is still recorded.'}</p><p class="visit-storage ${visits.persistent?'':'unsaved'}">${storageNote}${custom?' Your Rhino model keeps its current appearance; restore the original to see these finishes.':''}</p>`;
 if(done&&walkRoutes[selected]&&!custom){
  const routes=walkRoutes[selected],roof=routes.some(r=>r.support),hasTrees=visitTrees[selected]?.length>0;
  $('#visit-panel').insertAdjacentHTML('beforeend',`<div class="people-controls"><label><input id="show-people" type="checkbox" ${showPeople?'checked':''}> People</label><button id="people-focus" type="button">Look closer ↗</button></div>${hasTrees?`<div class="people-controls landscape-controls"><label><input id="show-landscape" type="checkbox" ${showLandscape?'checked':''}> Trees & planting</label></div>`:''}<p class="people-note">Up to ${routes.reduce((n,r)=>n+r.people,0)} people close to the building${roof?' and on flat model surfaces':''}. ${hasTrees?'Illustrative activity and planting.':'No planting added: limited clear ground.'} Zoom in to see more; the selected building takes priority.</p>`);
  if(hasTrees)$('#show-landscape').onchange=e=>{showLandscape=e.target.checked;atlas?.setLandscape(showLandscape);};
  $('#show-people').onchange=e=>{showPeople=e.target.checked;atlas?.setPeople(showPeople);};
  $('#people-focus').onclick=()=>{if(!showPeople){showPeople=true;atlas?.setPeople(true);$('#show-people').checked=true;}atlas?.focusPeople(selected);if(matchMedia('(max-width:700px)').matches)document.body.classList.add('detail-closed');};
 }
 $('#visit-panel .visit-toggle').onclick=()=>{
  const state=visits.toggle(selected);
  for(const building of city.landmarks)atlas?.setVisited(building.id,visits.has(building.id),building.id===selected);
  renderVisitPanel();updateVisitIndicators();if(state.visited)$('#visit-panel button').classList.add('visit-reveal');$('#visit-panel button').focus({preventScroll:true});
  $('#visit-announcement').textContent=b.name+(state.visited?' marked as visited.'+(p&&!custom?' Exterior finishes revealed.':''):' removed from visited.')+(state.saved?' Saved in this browser.':' Not saved: browser storage is unavailable.');
 };
}
function updateVisitIndicators(){
 $('#visit-count').textContent=`${visits.count()} of ${city.landmarks.length} visited`;
 $('#visit-progress').value=visits.count();$('#visit-progress').max=city.landmarks.length;
 for(const el of document.querySelectorAll('.building-item')){
  const done=visits.has(el.dataset.id),b=city.landmarks.find(b=>b.id===el.dataset.id);
  el.classList.toggle('visited',done);el.querySelector('.visit-list-check').hidden=!done;
  el.setAttribute('aria-label',b.name+(done?' · visited':''));
 }
 if(typeof filterBuildings==='function'&&$('#filter-unvisited')?.getAttribute('aria-pressed')==='true')filterBuildings();
}
window.addEventListener('storage',e=>{
 if(!visits||(e.key!==VISITS_KEY&&e.key!==null))return;
 visits.reload();for(const b of city.landmarks)atlas?.setVisited(b.id,visits.has(b.id),false);
 updateVisitIndicators();renderVisitPanel();
});
$('#city-download').onclick=()=>$('#download-dialog').showModal();$('#close-download').onclick=()=>$('#download-dialog').close();
$('#about').onclick=()=>$('#about-dialog').showModal();$('#close-about').onclick=()=>$('#about-dialog').close();
$('#import-open').onclick=()=>{$('#import-target').value=selected||'city';$('#rhino-dialog').showModal()};$('#close-import').onclick=()=>$('#rhino-dialog').close();
function clearPending(){pending?.root.traverse(o=>{o.geometry?.dispose();o.material?.dispose()});pending=null;buffer=null;$('#apply-import').disabled=true}
async function analyze(){clearPending();const file=$('#rhino-file').files[0];if(!file)return;if(file.size>100*1024*1024){status('Choose a .3dm file no larger than 100 MB.');return}status('Reading your model…');$('#rhino-file').disabled=true;try{buffer=await file.arrayBuffer();pending=await prepareRhino(buffer.slice(0),$('#import-unit').value);status(`${file.name}\n${pending.objects.toLocaleString('en-GB')} meshes · ${pending.triangles.toLocaleString('en-GB')} triangles\n${Object.values(pending.size).map(n=>n.toFixed(2)).join(' × ')} m (East–west × north–south × height)${pending.warnings?'\nSome objects could not be read. Convert them to meshes in Rhino and save again.':''}`);$('#apply-import').disabled=false}catch(e){status('Import failed: '+e.message)}finally{$('#rhino-file').disabled=false}}
$('#rhino-file').onchange=analyze;$('#import-unit').onchange=analyze;
$('#apply-import').onclick=async()=>{if(!pending)return;const key=$('#import-target').value;if(key!=='city'){const center=pending.bounds.getCenter(pending.root.position.clone());if(Math.hypot(center.x,center.z)>2000){status('This model is far from the building origin. For a city file, select Entire city. Individual models must keep their supplied local origin.');return}}const item={key,buffer,name:$('#rhino-file').files[0].name,unit:$('#import-unit').value};atlas.applyImport(pending,key);pending=null;$('#apply-import').disabled=true;try{await saveModel(item);status('Applied and saved in this browser.')}catch{status('Applied for this session. Browser storage is full, so this model will not survive a reload.')}if(selected)select(selected,false)};
$('#restore-model').onclick=async()=>{const key=$('#import-target').value;atlas.restore(key);try{await deleteModel(key);status('Original model restored.')}catch{status('Original model restored on screen, but its saved browser copy could not be removed.')}if(selected)select(selected,false)};
try{
const response=await fetch('./assets/city.json');if(!response.ok)throw Error('Unable to load city data');city=await response.json();visits=createVisitStore(city.landmarks.map(b=>b.id),()=>window.localStorage);$('#count').textContent=city.landmarks.length;
$('#mass-count').textContent=city.stats.masses.toLocaleString('en-GB')+' model parts in 3D.';
$('#height-stats').textContent=`${city.stats.masses.toLocaleString('en-GB')} model parts: ${city.stats.heights.height.toLocaleString('en-GB')} with recorded OSM heights, ${city.stats.heights.levels.toLocaleString('en-GB')} estimated from storeys, and ${city.stats.heights.assumed.toLocaleString('en-GB')} with assumed or reference-informed heights.`;
for(const file of city.rhinoDownloads||[]){const link=document.createElement('a');link.href=file.url;link.download='';link.className='region-download';link.textContent=`${file.name} · ${file.masses.toLocaleString('en-GB')} model parts · ${(file.bytes/1048576).toFixed(1)} MB ↓`;$('#region-downloads').append(link)}

for(const [i,b]of city.landmarks.entries()){const el=document.createElement('button');el.className='building-item';el.dataset.id=b.id;const meta=[b.architect,(String(b.year||'').match(/\d{4}/)||[])[0]].filter(Boolean).map(esc).join(' · ')||b.subtitle;el.innerHTML=`<span class="num">${String(i+1).padStart(2,'0')}</span><span class="item-text"><strong>${b.name}</strong><small>${meta}</small></span><span class="visit-list-check" aria-hidden="true" hidden>✓</span><span class="arrow">↗</span>`;el.onclick=()=>select(b.id);$('#buildings').append(el);const option=document.createElement('option');option.value=b.id;option.textContent=b.name;$('#import-target').append(option)}
const search=$('#building-search');
const eras=[['all','All',()=>true],['pre1714','Before 1714',y=>y<1714],['georgian','Georgian',y=>y>=1714&&y<1837],['victorian','Victorian',y=>y>=1837&&y<1901],['early20','1901–1945',y=>y>=1901&&y<1946],['postwar','Post-war',y=>y>=1946&&y<1980],['contemporary','1980 on',y=>y>=1980],['undated','Undated',null]];
const yearOf=b=>{const m=String(b.year||'').match(/\d{4}/);return m?Number(m[0]):null};
const inEra=(b,key)=>{const e=eras.find(e=>e[0]===key),y=yearOf(b);if(key==='all')return true;if(key==='undated')return y===null;return y!==null&&e[2](y)};
let era='all',unvisitedOnly=false;
for(const [key,label] of eras){const n=city.landmarks.filter(b=>inEra(b,key)).length;if(!n&&key!=='all')continue;const btn=document.createElement('button');btn.type='button';btn.className='chip';btn.dataset.era=key;btn.setAttribute('aria-pressed',String(key===era));btn.innerHTML=`${label} <span class="chip-n">${n}</span>`;btn.onclick=()=>{era=key;for(const c of document.querySelectorAll('[data-era]'))c.setAttribute('aria-pressed',String(c.dataset.era===era));filterBuildings()};$('#era-filters').append(btn)}
$('#filter-unvisited').onclick=e=>{unvisitedOnly=!unvisitedOnly;e.currentTarget.setAttribute('aria-pressed',String(unvisitedOnly));filterBuildings()};
function filterBuildings(){const q=search.value.normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[’']/g,'');let count=0;
 for(const el of document.querySelectorAll('.building-item')){const b=city.landmarks.find(b=>b.id===el.dataset.id);const text=[b.name,b.subtitle,b.architect,...(b.aliases||[])].join(' ').normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[’']/g,'');el.hidden=!text.includes(q)||!inEra(b,era)||(unvisitedOnly&&visits.has(b.id));if(!el.hidden)count++}
 const filtered=q||era!=='all'||unvisitedOnly;
 $('#list-title').textContent=(era==='all'?'All stops':eras.find(e=>e[0]===era)[1])+(unvisitedOnly?' · unvisited':'')+(q?' · search':'');
 $('#count').textContent=filtered?`${count} / ${city.landmarks.length}`:String(city.landmarks.length);
 $('#search-result').textContent=filtered?`${count} of ${city.landmarks.length} buildings`:'';$('#search-empty').hidden=count!==0;
}
search.addEventListener('input',filterBuildings);
document.addEventListener('keydown',e=>{if(e.key==='/'&&!e.ctrlKey&&!e.metaKey&&!/^(INPUT|SELECT|TEXTAREA)$/.test(document.activeElement?.tagName)&&!document.querySelector('dialog[open]')){e.preventDefault();search.focus()}});
search.addEventListener('keydown',e=>{if(e.key==='Enter')document.querySelector('.building-item:not([hidden])')?.click()});
updateVisitIndicators();atlas=await createAtlas(city,id=>select(id,false));
const stylePicker=$('#map-style');stylePicker.value=readMapStyle(()=>window.localStorage);atlas.setStyle(stylePicker.value,false);stylePicker.disabled=false;
const styleSwitch=$('#style-switch');for(const option of stylePicker.options){const btn=document.createElement('button');btn.type='button';btn.dataset.style=option.value;btn.textContent=option.textContent;btn.setAttribute('aria-pressed',String(option.value===stylePicker.value));btn.onclick=()=>{if(stylePicker.value===option.value)return;stylePicker.value=option.value;stylePicker.dispatchEvent(new Event('change'))};styleSwitch.append(btn)}
stylePicker.onchange=()=>{for(const btn of styleSwitch.children)btn.setAttribute('aria-pressed',String(btn.dataset.style===stylePicker.value));const id=stylePicker.value;if(!Object.hasOwn(mapStyles,id))return;atlas.setStyle(id);const saved=saveMapStyle(id,()=>window.localStorage);$('#visit-announcement').textContent=`${stylePicker.selectedOptions[0].textContent} map style.`+(saved?'':' This choice could not be saved in this browser.');};
const labelKey='london-field-atlas.labels.v1';
try{const saved=JSON.parse(localStorage.getItem(labelKey));for(const key of ['names','numbers'])if(typeof saved?.[key]==='boolean')$('#show-'+key).checked=saved[key]}catch{}
function updateLabels(save=false){const options={names:$('#show-names').checked,numbers:$('#show-numbers').checked};atlas.setLabels(options);if(save)try{localStorage.setItem(labelKey,JSON.stringify(options))}catch{}}
for(const key of ['names','numbers'])$('#show-'+key).onchange=()=>updateLabels(true);
updateLabels();
$('#label-controls').addEventListener('keydown',e=>{if(e.key==='Escape'){$('#label-controls').open=false;$('#label-controls summary').focus()}});
document.addEventListener('pointerdown',e=>{if(!$('#label-controls').contains(e.target))$('#label-controls').open=false});
for(const id of visits.ids())atlas.setVisited(id,true,false);$('#zoom-in').onclick=()=>atlas.zoom(1.25);$('#zoom-out').onclick=()=>atlas.zoom(.8);$('#reset').onclick=()=>{atlas.reset();closeDetail()};$('#show-context').onchange=e=>atlas.setContext(e.target.checked);$('#show-confidence').onchange=e=>{atlas.setConfidence(e.target.checked);$('#confidence-legend').hidden=!e.target.checked};
$('#import-open').disabled=false;try{const models=await savedModels();models.sort((a,b)=>(b.key==='city')-(a.key==='city'));for(const item of models){try{atlas.applyImport(await prepareRhino(item.buffer.slice(0),item.unit),item.key)}catch(e){status(`${item.name} could not be restored: ${e.message}`)}}}catch(e){status('Browser storage is unavailable. Imported models will last for this session only.')}
$('#loading').hidden=true;const linked=new URLSearchParams(location.search).get('b');if(linked&&city.landmarks.some(b=>b.id===linked))select(linked);else document.body.classList.add('detail-closed');
}catch(e){console.error(e);$('#loading').hidden=true;$('#error').hidden=false;$('#error').textContent='Unable to load the 3D map: '+e.message}
