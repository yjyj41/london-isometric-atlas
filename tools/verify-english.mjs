import fs from 'node:fs';
import assert from 'node:assert/strict';
const hangul=/[\uAC00-\uD7AF]/;
for(const name of fs.readdirSync('dist').filter(n=>/\.(js|html|md)$/.test(n))){
 assert(!hangul.test(fs.readFileSync('dist/'+name,'utf8')),`Untranslated interface in ${name}`);
}
const city=JSON.parse(fs.readFileSync('dist/assets/city.json'));
assert.equal(city.landmarks.length,289);
for(const b of city.landmarks){
 for(const key of ['name','subtitle','type','point','modelNote']){
  assert(typeof b[key]==='string'&&b[key].length>0,`${b.id}: missing ${key}`);
  assert(!hangul.test(b[key]),`${b.id}: untranslated ${key}`);
 }
 for(const key of ['year','architect'])assert(typeof b[key]==='string'&&!hangul.test(b[key]));
 if(b.photo){assert(b.photo.alt&&!hangul.test(b.photo.alt),`${b.id}: English photo description required`);assert(fs.existsSync('dist/'+b.photo.url.replace('./','')))}
 else assert.equal(b.photoStatus,'unresolved',`${b.id}: missing photo must be explicit`);
}
for(const r of city.rhinoDownloads)assert(!hangul.test(r.name));
assert(fs.readFileSync('dist/index.html','utf8').includes('lang="en-GB"'));
console.log('English interface, 289 building cards, available photographs and regional downloads verified.');
