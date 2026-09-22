import fs from 'node:fs';
import {recordGeometry} from '../dist/geometry.js';
const city=JSON.parse(fs.readFileSync('dist/assets/city.json'));
const out=fs.openSync('tools/meshes.ndjson','w');
for(const r of city.buildings){const verts=[];for(const g of recordGeometry(r)){const a=g.attributes.position.array;for(let i=0;i<a.length;i+=3)verts.push([a[i],-a[i+2],a[i+1]]);g.dispose()}fs.writeSync(out,JSON.stringify({id:r.id,verts})+'\n')}
fs.closeSync(out);console.log('Exported',city.buildings.length);
