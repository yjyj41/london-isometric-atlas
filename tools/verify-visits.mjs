import fs from 'node:fs';
import assert from 'node:assert/strict';
import {createVisitStore,VISITS_KEY} from '../dist/visits.js';
import {recordGeometry} from '../dist/geometry.js';
import {addFinishAttribute,finishes} from '../dist/landmark-finishes.js';

const city=JSON.parse(fs.readFileSync('dist/assets/city.json'));
const ids=city.landmarks.map(b=>b.id);
assert.deepEqual(Object.keys(finishes).sort(),[...ids].sort());
let value=null;const memory={getItem:()=>value,setItem:(key,v)=>{assert.equal(key,VISITS_KEY);value=v;}};
const a=createVisitStore(ids,()=>memory),b=createVisitStore(ids,()=>memory);
assert.equal(a.count(),0);
assert.deepEqual(a.toggle('gherkin'),{visited:true,saved:true});
assert.equal(createVisitStore(ids,()=>memory).has('gherkin'),true);
// A stale second tab must merge the first tab's visit rather than overwrite it.
b.toggle('isokon');a.reload();assert.equal(a.count(),2);
a.toggle('gherkin');assert.equal(createVisitStore(ids,()=>memory).has('gherkin'),false);
assert.equal(createVisitStore(ids,()=>memory).has('isokon'),true);
assert.throws(()=>a.toggle('not-a-building'));
const unavailable=createVisitStore(ids,()=>{throw Error('Blocked storage');});
assert.deepEqual(unavailable.toggle('gherkin'),{visited:true,saved:false});
assert.equal(unavailable.has('gherkin'),true);assert.equal(unavailable.persistent,false);
const damaged='{invalid json';value=damaged;
const invalid=createVisitStore(ids,()=>memory);assert.equal(invalid.persistent,false);
invalid.toggle('gherkin');assert.equal(value,damaged,'Do not overwrite an unreadable stored record');
value=JSON.stringify({version:1,visited:{isokon:'2026-10-01T12:00:00Z',unknown:'2026-10-01',gherkin:'bad-date'}});
assert.deepEqual(createVisitStore(ids,()=>memory).ids(),['isokon']);

let parts=0,vertices=0,extraBytes=0;
for(const r of city.buildings.filter(r=>r.lm)){
 const gs=recordGeometry(r);
 gs.forEach((g,index)=>{
  const positions=g.attributes.position.array.slice(),normals=g.attributes.normal.array.slice();
  addFinishAttribute(g,r,index,gs.length);
  assert.deepEqual(g.attributes.position.array,positions,`${r.id}: position changed`);
  assert.deepEqual(g.attributes.normal.array,normals,`${r.id}: normal changed`);
  assert.equal(g.attributes.atlasFinish.count,g.attributes.position.count);
  assert([...g.attributes.atlasFinish.array].every(n=>Number.isInteger(n)&&n>=0&&n<=6));
  if(r.lm==='battersea'&&r.form==='tapered_chimney')assert([...g.attributes.atlasFinish.array].every(n=>n===5));
  parts++;vertices+=g.attributes.position.count;extraBytes+=g.attributes.atlasFinish.array.byteLength;
  g.dispose();
 });
}
console.log(JSON.stringify({landmarks:ids.length,parts,vertices,extraAttributeBytes:extraBytes,storage:'reload, undo, multi-tab merge, blocked and damaged storage verified',geometry:'positions and normals unchanged'}));
