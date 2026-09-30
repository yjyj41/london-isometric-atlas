// Preserve every source triangle; compress storage, never replace footprints with boxes.
import fs from 'node:fs';
import {gzipSync} from 'node:zlib';
import assert from 'node:assert/strict';
import * as T from '../dist/vendor/three.module.js';
import {mergeVertices} from '../dist/vendor/BufferGeometryUtils.js';
import {buildTileData} from '../dist/tile-geometry.js';
const city=JSON.parse(fs.readFileSync('dist/assets/city.json'));
let totalBytes=0,gpuBytes=0,triangles=0,maxError=0;
fs.mkdirSync('dist/assets/meshes',{recursive:true});
for(const tile of city.tiles){
 const data=JSON.parse(fs.readFileSync('dist/'+tile.url.replace('./','')));
 const batches=await buildTileData(data),header={version:1,batches:[]},chunks=[];let offset=0,bytes=0;
 function append(array){const padding=(4-offset%4)%4;if(padding){chunks.push(Buffer.alloc(padding));offset+=padding}const start=offset;const b=Buffer.from(array.buffer,array.byteOffset,array.byteLength);chunks.push(b);offset+=b.length;bytes+=b.length;return start}
 for(const [kind,attrs]of Object.entries(batches)){
  const raw=new T.BufferGeometry();raw.setAttribute('position',new T.BufferAttribute(attrs.position,3));raw.setAttribute('normal',new T.BufferAttribute(attrs.normal,3));
  const g=mergeVertices(raw,1e-5);raw.dispose();g.computeBoundingBox();
  const min=g.boundingBox.min.toArray(),size=g.boundingBox.getSize(new T.Vector3()).toArray();
  // Uniform scale retains world-space normals. Worst-case error is below 2cm.
  const scale=Math.max(...size,.01)/65535,p=g.attributes.position.array,n=g.attributes.normal.array;
  const positions=new Uint16Array(p.length),normals=new Int8Array(n.length);
  for(let i=0;i<p.length;i++){positions[i]=Math.round((p[i]-min[i%3])/scale);maxError=Math.max(maxError,Math.abs(positions[i]*scale+min[i%3]-p[i]));normals[i]=Math.round(Math.max(-1,Math.min(1,n[i]))*127)}
  const indices=g.attributes.position.count<65536?new Uint16Array(g.index.array):new Uint32Array(g.index.array);
  assert.equal(indices.length,attrs.position.length/3);triangles+=indices.length/3;
  header.batches.push({kind,min,scale,vertices:p.length/3,indexCount:indices.length,indexBytes:indices.BYTES_PER_ELEMENT,position:append(positions),normal:append(normals),index:append(indices)});
  g.dispose();
 }
 const json=Buffer.from(JSON.stringify(header)),padded=Math.ceil(json.length/4)*4,pre=Buffer.alloc(4+padded);pre.writeUInt32LE(padded);json.copy(pre,4);
 const compressed=gzipSync(Buffer.concat([pre,...chunks]),{level:9});
 const filename=`assets/meshes/${tile.id}.mesh.gz`;fs.writeFileSync('dist/'+filename,compressed);
 tile.mesh={url:'./'+filename,bytes:compressed.length,geometryBytes:bytes};delete tile.overview;
 totalBytes+=compressed.length;gpuBytes+=bytes;
}
assert(maxError<.03,'Position compression must remain within 3cm of source geometry');
city.stats.overviewMasses=0;city.stats.meshBytes=totalBytes;city.stats.meshGeometryBytes=gpuBytes;city.stats.meshTriangles=triangles;city.stats.maxPositionErrorM=maxError;
city.rendering='exact-footprints';
fs.writeFileSync('dist/assets/city.json',JSON.stringify(city));
const stats={...JSON.parse(fs.readFileSync('tools/performance.json')),...city.stats,initialBytes:fs.statSync('dist/assets/city.json').size,initialGzipBytes:gzipSync(fs.readFileSync('dist/assets/city.json')).length};
fs.writeFileSync('tools/performance.json',JSON.stringify(stats,null,2));
console.log(JSON.stringify({meshBytes:totalBytes,geometryBytes:gpuBytes,triangles,maxPositionErrorM:maxError,initialBytes:stats.initialBytes}));
