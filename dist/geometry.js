import * as T from './vendor/three.module.js';

// Source coordinates: local East / North / Up, one unit = one metre.
export function shapeOf(rings) {
  const shape = new T.Shape(rings[0].map(([x,y])=>new T.Vector2(x,y)));
  for (const ring of rings.slice(1)) shape.holes.push(new T.Path(ring.map(([x,y])=>new T.Vector2(x,y))));
  return shape;
}
export function extrusion(rings, base, top) {
  const geometry = new T.ExtrudeGeometry(shapeOf(rings), {depth:Math.max(.01,top-base),bevelEnabled:false,steps:1,curveSegments:1});
  geometry.translate(0,0,base);
  return geometry;
}
function loft(ring, levels) {
  const center = ring.reduce((a,p)=>[a[0]+p[0]/ring.length,a[1]+p[1]/ring.length],[0,0]);
  const verts=[], faces=[], n=ring.length;
  for(const [z,s] of levels) for(const p of ring) verts.push(center[0]+(p[0]-center[0])*s,center[1]+(p[1]-center[1])*s,z);
  for(let j=0;j<levels.length-1;j++)for(let i=0;i<n;i++){
    const a=j*n+i,b=j*n+(i+1)%n,c=(j+1)*n+i,d=(j+1)*n+(i+1)%n;
    faces.push(a,b,c,b,d,c);
  }
  const triangles=T.ShapeUtils.triangulateShape(ring.map(p=>new T.Vector2(...p)),[]);
  for(const [a,b,c] of triangles){faces.push(c,b,a);const t=(levels.length-1)*n;faces.push(a+t,b+t,c+t)}
  const g=new T.BufferGeometry();g.setAttribute('position',new T.Float32BufferAttribute(verts,3));g.setIndex(faces);g.computeVertexNormals();return g;
}
function slopedRoof(ring,base,height,dir) {
  const a=(dir??90)*Math.PI/180,dx=Math.sin(a),dy=Math.cos(a);
  const us=ring.map(p=>p[0]*dx+p[1]*dy),low=Math.min(...us),range=Math.max(.01,Math.max(...us)-low);
  const n=ring.length,verts=[],indices=[];
  for(const p of ring)verts.push(p[0],p[1],base);
  ring.forEach((p,i)=>verts.push(p[0],p[1],base+height*(us[i]-low)/range+.001));
  for(let i=0;i<n;i++){const j=(i+1)%n;indices.push(i,j,i+n,j,j+n,i+n)}
  for(const [a,b,c] of T.ShapeUtils.triangulateShape(ring.map(p=>new T.Vector2(...p)),[]))indices.push(c,b,a,a+n,b+n,c+n);
  const g=new T.BufferGeometry();g.setAttribute('position',new T.Float32BufferAttribute(verts,3));g.setIndex(indices);g.computeVertexNormals();return g;
}
export function recordGeometry(r) {
  const parts=[];
  if(r.form==='shard'){
    parts.push(loft(r.r[0],[[0,1],[r.h*.65,.38],[r.h*.93,.08],[r.h,.002]]));
  } else if(r.form==='gherkin'){
    const xs=r.r[0].map(p=>p[0]),ys=r.r[0].map(p=>p[1]),cx=(Math.max(...xs)+Math.min(...xs))/2,cy=(Math.max(...ys)+Math.min(...ys))/2;
    const radius=(Math.max(...xs)-Math.min(...xs)+Math.max(...ys)-Math.min(...ys))/4;
    const ring=Array.from({length:48},(_,i)=>[cx+radius*Math.cos(i*Math.PI/24),cy+radius*Math.sin(i*Math.PI/24)]);
    parts.push(loft(ring,[[0,1],[35,1.18],[70,1.28],[105,1.2],[135,1],[155,.75],[173,.38],[180,.002]]));
  } else if(r.roof && r.r.length===1 && ['dome','onion','pyramidal','cone','skillion'].includes(r.roof.shape)){
    const base=r.h-r.roof.h;
    if(base>r.z+.05)parts.push(extrusion(r.r,r.z,base));
    if(r.roof.shape==='skillion')parts.push(slopedRoof(r.r[0],base,r.roof.h,r.roof.dir));
    else if(['dome','onion'].includes(r.roof.shape)) {
      const levels=Array.from({length:11},(_,i)=>[base+r.roof.h*Math.sin(i*Math.PI/20),Math.max(.002,Math.cos(i*Math.PI/20))]);
      parts.push(loft(r.r[0],levels));
    } else parts.push(loft(r.r[0],[[base,1],[r.h,.002]]));
  } else parts.push(extrusion(r.r,r.z,r.h));
  return parts.map(g=>{
    // Rhino Z-up -> Three Y-up, preserves East and North and all dimensions.
    g.rotateX(-Math.PI/2);
    let n=g.index?g.toNonIndexed():g;
    n.deleteAttribute('uv');n.computeVertexNormals();
    if(n!==g)g.dispose();return n;
  });
}
export function flatGeometry(rings,level=0){const g=new T.ShapeGeometry(shapeOf(rings));g.translate(0,0,level);g.rotateX(-Math.PI/2);return g;}
