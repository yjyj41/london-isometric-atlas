import fs from 'node:fs';
import assert from 'node:assert/strict';
import {buildTileData} from '../dist/tile-geometry.js';
import {gunzipSync} from 'node:zlib';
import {decodeCityMesh} from '../dist/city-mesh.js';
const city=JSON.parse(fs.readFileSync('dist/assets/city.json'));
assert.equal(city.version,3);assert.equal(city.units,'meters');
assert.equal(city.origin.lat,51.51);assert.equal(city.origin.lon,-.106);
assert.deepEqual(city.geographicBounds,[-.17,51.496,-.0715,51.56]);
const isokon=city.landmarks.find(b=>b.id==='isokon');assert(isokon?.massCount>0);
assert(isokon.lat>51.55&&isokon.lon<-.16);
let count=city.buildings.length,triangles=0,maxBytes=0,totalBytes=0;
let packedBytes=0,packedDownloadBytes=0,maxError=0;
assert.equal(city.rendering,'exact-footprints');
function inside(point,ring){let result=false;for(let i=0,j=ring.length-1;i<ring.length;j=i++){
 const [x,y]=ring[i],[u,v]=ring[j];if((y>point[1])!==(v>point[1])&&point[0]<(u-x)*(point[1]-y)/(v-y)+x)result=!result;
}return result}
const bridge=city.landmarks.find(b=>b.id==='millennium').anchor;
assert(city.water.some(r=>inside(bridge,r[0])&&!r.slice(1).some(h=>inside(bridge,h))),'Complete Thames must extend beneath Millennium Bridge');
for(const tile of city.tiles){
 assert(!tile.overview,'Bounding-box proxies must never return');
 const data=JSON.parse(fs.readFileSync('dist/'+tile.url.replace('./','')));
 assert.equal(data.buildings.length,tile.masses);count+=data.buildings.length;
 assert(data.buildings.every(b=>!b.lm));
 const batches=await buildTileData(data);
 const compressed=fs.readFileSync('dist/'+tile.mesh.url.replace('./',''));
 const unpacked=gunzipSync(compressed),buffer=unpacked.buffer.slice(unpacked.byteOffset,unpacked.byteOffset+unpacked.byteLength);
 const packed=decodeCityMesh(buffer);let tileBytes=0;
 assert.equal(compressed.byteLength,tile.mesh.bytes);packedDownloadBytes+=compressed.byteLength;
 assert.equal(packed.length,Object.keys(batches).length);
 for(const b of packed){
  const original=batches[b.kind];assert.equal(b.index.length*3,original.position.length);
  // Compare every triangle vertex against actual source geometry, including holes,
  // roads, heights and original placement. This catches fake LOD and axis mistakes.
  for(let i=0;i<b.index.length;i++)for(let axis=0;axis<3;axis++){
   const j=b.index[i]*3+axis,error=Math.abs(b.position[j]*b.scale+b.min[axis]-original.position[i*3+axis]);
   maxError=Math.max(maxError,error);assert(error<.01,`${tile.id}: moved source vertex`);
   assert(Math.abs(b.normal[j]/127-original.normal[i*3+axis])<.005);
  }
  tileBytes+=b.position.byteLength+b.normal.byteLength+b.index.byteLength;
 }
 assert.equal(tileBytes,tile.mesh.geometryBytes);packedBytes+=tileBytes;
 let bytes=0;
 for(const b of Object.values(batches)){
  assert.equal(b.position.length,b.normal.length);
  assert(b.position.every(Number.isFinite));assert(b.normal.every(Number.isFinite));
  triangles+=b.position.length/9;bytes+=b.position.byteLength+b.normal.byteLength;
 }
 maxBytes=Math.max(maxBytes,bytes);totalBytes+=bytes;
}
assert.equal(count,city.stats.masses);assert.equal(city.tiles.length,110);
assert(packedBytes<40*1024*1024,'Entire real city must fit even the mobile geometry budget');
assert.equal(packedBytes,city.stats.meshGeometryBytes);
assert.equal(city.rhinoDownloads.reduce((n,d)=>n+d.masses,0),count);
for(const file of city.rhinoDownloads){const path='dist/'+file.url.replace('./','');assert(fs.existsSync(path));assert(fs.statSync(path).size<25*1024*1024)}
assert(fs.readFileSync('dist/assets/rhino/isokon-rhino6.3dm').subarray(0,32).toString().endsWith('60'));
console.log(JSON.stringify({masses:count,landmarks:city.landmarks.length,tiles:city.tiles.length,detailTriangles:triangles,maxTileGeometryBytes:maxBytes,wholeDetailGeometryBytes:totalBytes,packedBytes,packedDownloadBytes,maxPositionErrorM:maxError}));
