import assert from 'node:assert/strict';
import * as T from '../dist/vendor/three.module.js';
import {createPeople,walkRoutes} from '../dist/people.js';
import {prepareWalk,walkPose} from '../dist/walk-motion.js';

for(const routes of Object.values(walkRoutes))for(const route of routes){
 const path=prepareWalk(route.points);
 for(let t=0;t<400;t+=.13){
  const p=walkPose(path,t);
  assert(p.distance>=0&&p.distance<=path.length);
  const onSegment=route.points.slice(1).some((b,i)=>{
   const a=route.points[i],dx=b[0]-a[0],dy=b[1]-a[1];
   const u=((p.x-a[0])*dx+(p.north-a[1])*dy)/(dx*dx+dy*dy);
   return u>=-1e-8&&u<=1+1e-8&&Math.abs((p.x-a[0])*dy-(p.north-a[1])*dx)<1e-6;
  });
  assert(onSegment,'Walker left the reviewed path');
 }
 const end=walkPose(path,path.length/1.05+.75);
 assert.equal(end.moving,false);assert.equal(end.gait,0);
}
const scene=new T.Scene(),people=createPeople(scene),group=scene.getObjectByName('Visited-place walkers');
const camera=new T.OrthographicCamera(-10000,10000,10000,-10000,.1,40000);
camera.position.set(0,20000,0);camera.up.set(0,0,-1);camera.lookAt(0,0,0);camera.updateMatrixWorld();
const options={camera,pixelsPerMetre:5,hidden:false,reducedMotion:false,blocked:()=>false};
const count=()=>group.children[0].count;
people.update(0,options);assert.equal(count(),0);
for(const id of Object.keys(walkRoutes))people.setVisited(id,true,false);
people.update(100,options);assert.equal(count(),15);assert.equal(group.children.length,4);
const original=group.children[0].instanceMatrix.array.slice();
people.update(200,options);assert.notDeepEqual(group.children[0].instanceMatrix.array,original);
people.invalidate();people.update(300,{...options,reducedMotion:true});
const still=group.children[0].instanceMatrix.array.slice();
assert.equal(people.update(10000,{...options,reducedMotion:true}),false);
assert.deepEqual(group.children[0].instanceMatrix.array,still);
people.update(10100,{...options,pixelsPerMetre:1});assert.equal(count(),0);
people.update(10200,{...options,blocked:id=>id==='isokon'});assert.equal(count(),11);
people.setVisited('tate',false);people.update(10300,options);assert.equal(count(),9);
people.setEnabled(false);people.update(10400,options);assert.equal(count(),0);
people.setEnabled(true);people.update(10500,{...options,hidden:true});assert.equal(count(),0);
people.update(10600,options);assert.equal(count(),9);
camera.position.set(50000,20000,50000);camera.lookAt(50000,0,50000);camera.updateMatrixWorld();
people.invalidate();people.update(10700,options);assert.equal(count(),0,'Offscreen walkers are removed');
console.log('People: 3 bounded routes, 15 metric figures, 4 draws; visits, undo, toggle, culling, zoom, custom-model blocking and reduced motion verified.');
