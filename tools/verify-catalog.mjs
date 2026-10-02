import fs from 'node:fs';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
const city=JSON.parse(fs.readFileSync('dist/assets/city.json'));
const full=JSON.parse(fs.readFileSync('tools/city-full.json'));
const baseline=JSON.parse(fs.readFileSync('tools/catalog-baseline.json'));
const review=JSON.parse(fs.readFileSync('tools/catalog-review.json'));
assert.equal(review.length,300);assert.equal(new Set(review.map(r=>r.number)).size,300);
assert.equal(city.landmarks.length,289);assert.equal(new Set(city.landmarks.map(b=>b.id)).size,289);
assert.deepEqual(['existing','add','merged','excluded'].map(s=>review.filter(r=>r.status===s).length),[33,256,6,5]);
const original=full.buildings.slice(0,baseline.originalMasses).map(({lm,...r})=>r);
assert.equal(crypto.createHash('sha256').update(JSON.stringify(original)).digest('hex'),baseline.geometrySha256,'Original geometry must remain unchanged');
for(const group of baseline.detailedGroups)assert.deepEqual(full.buildings.filter(r=>r.lm===group.id).map(r=>r.id),group.records,'Existing detailed model membership changed');
for(const r of review){
 if(['existing','add'].includes(r.status))assert(city.landmarks.some(b=>b.id===r.id));
 if(r.status==='merged'){const parent=review.find(p=>p.number===r.mergeInto);assert(city.landmarks.find(b=>b.id===parent.id)?.aliases.includes(r.name))}
 if(r.status==='excluded')assert(!city.landmarks.some(b=>b.id===r.id));
}
for(const b of city.landmarks){
 assert([b.lon,b.lat,...b.anchor,b.modelHeight].every(Number.isFinite));
 assert(b.lon>-.6&&b.lon<.3&&b.lat>51.3&&b.lat<51.8,`${b.name}: outside London`);
 const records=full.buildings.filter(r=>r.lm===b.id);assert.equal(records.length,b.massCount);
 if(!b.massCount)assert.equal(b.modelStatus,'location');
 if(b.id.startsWith('catalog-')){assert(b.locationSource?.startsWith('https://'));assert(b.massCount===0||b.osmRefs.length>0)}
}
assert.equal(city.catalog.photos,city.landmarks.filter(b=>b.photo).length);
assert.equal(city.catalog.modelled,city.landmarks.filter(b=>b.massCount).length);
assert.equal(city.catalog.photos,272);
console.log(`Catalogue verified: 289 stops, ${city.catalog.modelled} modelled, ${city.catalog.photos} photographed; original ${baseline.originalMasses} parts unchanged.`);
