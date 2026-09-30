import fs from 'node:fs';
import assert from 'node:assert/strict';
import {buildTileData} from '../dist/tile-geometry.js';
const city=JSON.parse(fs.readFileSync('dist/assets/city.json'));
assert.equal(city.version,3);assert.equal(city.units,'meters');
assert.equal(city.origin.lat,51.51);assert.equal(city.origin.lon,-.106);
assert.deepEqual(city.geographicBounds,[-.17,51.496,-.0715,51.56]);
const isokon=city.landmarks.find(b=>b.id==='isokon');assert(isokon?.massCount>0);
assert(isokon.lat>51.55&&isokon.lon<-.16);
let count=city.buildings.length,triangles=0,maxBytes=0,totalBytes=0;
for(const tile of city.tiles){
 const data=JSON.parse(fs.readFileSync('dist/'+tile.url.replace('./','')));
 assert.equal(data.buildings.length,tile.masses);count+=data.buildings.length;
 assert(data.buildings.every(b=>!b.lm));
 const batches=await buildTileData(data);
 let bytes=0;
 for(const b of Object.values(batches)){
  assert.equal(b.position.length,b.normal.length);
  assert(b.position.every(Number.isFinite));assert(b.normal.every(Number.isFinite));
  triangles+=b.position.length/9;bytes+=b.position.byteLength+b.normal.byteLength;
 }
 maxBytes=Math.max(maxBytes,bytes);totalBytes+=bytes;
}
assert.equal(count,city.stats.masses);assert.equal(city.tiles.length,110);
assert.equal(city.rhinoDownloads.reduce((n,d)=>n+d.masses,0),count);
for(const file of city.rhinoDownloads){const path='dist/'+file.url.replace('./','');assert(fs.existsSync(path));assert(fs.statSync(path).size<25*1024*1024)}
assert(fs.readFileSync('dist/assets/rhino/isokon-rhino6.3dm').subarray(0,32).toString().endsWith('60'));
console.log(JSON.stringify({masses:count,landmarks:city.landmarks.length,tiles:city.tiles.length,detailTriangles:triangles,maxTileGeometryBytes:maxBytes,wholeDetailGeometryBytes:totalBytes}));
