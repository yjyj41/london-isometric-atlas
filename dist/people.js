import * as T from './vendor/three.module.js';
import {walkRoutes} from './walk-routes.js';
import {prepareWalk,walkPose} from './walk-motion.js';
export {walkRoutes};

// Four instanced draws, at most 18 people. Decorative figures are never pickable.
export function createPeople(scene){
 const capacity=18,group=new T.Group();group.name='Visited-place walkers';scene.add(group);
 const material=color=>new T.MeshStandardMaterial({color,roughness:.95});
 const meshes={head:new T.InstancedMesh(new T.SphereGeometry(.15,7,5),material('#c99c7c'),capacity),
  body:new T.InstancedMesh(new T.BoxGeometry(.42,.60,.25),material('#ffffff'),capacity),
  arms:new T.InstancedMesh(new T.BoxGeometry(.12,.55,.13),material('#ffffff'),capacity*2),
  legs:new T.InstancedMesh(new T.BoxGeometry(.145,.72,.17),material('#35414a'),capacity*2)};
 for(const mesh of Object.values(meshes)){mesh.count=0;mesh.frustumCulled=false;mesh.instanceMatrix.setUsage(T.DynamicDrawUsage);group.add(mesh);}
 const palette=['#a34e3e','#315c6c','#cfaa64','#5c6750','#5f526f','#a67750'];
 const routes=Object.entries(walkRoutes).flatMap(([id,items])=>items.map(r=>{
  const box=new T.Box3();for(const [x,n]of r.points)box.expandByPoint(new T.Vector3(x,r.elevation,-n));box.expandByScalar(2);
  return {...r,id,path:prepareWalk(r.points),box};
 }));
 const visited=new Set(),arrivals=new Map(),frustum=new T.Frustum(),matrix=new T.Matrix4(),root=new T.Object3D(),part=new T.Object3D();
 let enabled=true,invalid=true,lastFrame=-Infinity,lastCount=0,clock=0,lastTime=null;
 function setVisited(id,value,animate){
  if(value===visited.has(id))return;
  if(value){visited.add(id);arrivals.set(id,animate?clock+1.1:-Infinity);}else{visited.delete(id);arrivals.delete(id);}
  invalid=true;
 }
 function update(now,{camera,pixelsPerMetre,hidden,reducedMotion,blocked}){
  const dt=lastTime===null?0:Math.min(.1,(now-lastTime)/1000);lastTime=now;
  const moving=!hidden&&!reducedMotion&&enabled;
  // Stop the simulation when hidden or reduced motion is requested.
  if(moving)clock+=dt;
  frustum.setFromProjectionMatrix(matrix.multiplyMatrices(camera.projectionMatrix,camera.matrixWorldInverse));
  const visible=enabled&&!hidden&&pixelsPerMetre>=2.2?routes.filter(r=>visited.has(r.id)&&!blocked(r.id)&&frustum.intersectsBox(r.box)):[];
  const signature=visible.map(r=>r.id+':'+r.sourceId).join('|');
  if(signature!==group.userData.signature){group.userData.signature=signature;invalid=true;}
  if(!invalid&&(!visible.length||reducedMotion||now-lastFrame<1000/30))return false;
  lastFrame=now;invalid=false;let count=0;
  const put=(mesh,index,x,y,z,rotation=0)=>{part.position.set(x,y,z);part.rotation.set(rotation,0,0);part.scale.set(1,1,1);part.updateMatrix();matrix.multiplyMatrices(root.matrix,part.matrix);mesh.setMatrixAt(index,matrix);};
  for(const route of visible){
   const elapsed=clock-arrivals.get(route.id),appear=reducedMotion?1:Math.min(1,Math.max(0,elapsed/.55));
   if(appear<1)invalid=true;if(!appear)continue;
   for(let i=0;i<route.people&&count<capacity;i++){
    const pose=walkPose(route.path,clock,1.0+i*.06,i*(route.path.length/route.people/1.06+1.5));
    const gait=reducedMotion?0:pose.gait,scale=(.96+(i%3)*.025)*appear;
    root.position.set(pose.x,route.elevation,-pose.north);root.rotation.set(0,pose.heading,0);root.scale.setScalar(scale);root.updateMatrix();
    const colour=new T.Color(palette[i%palette.length]);meshes.body.setColorAt(count,colour);
    put(meshes.body,count,0,1.13,0);put(meshes.head,count,0,1.59,0);
    for(let side=0;side<2;side++){
     const sign=side?1:-1,angle=sign*gait,index=count*2+side;
     put(meshes.legs,index,sign*.115,.77-Math.cos(angle)*.36,-Math.sin(angle)*.36,angle);
     put(meshes.arms,index,sign*.28,1.40-Math.cos(angle)*.275,Math.sin(angle)*.275,-angle);
     meshes.arms.setColorAt(index,colour);
    }
    count++;
   }
  }
  meshes.head.count=meshes.body.count=count;meshes.arms.count=meshes.legs.count=count*2;
  for(const mesh of Object.values(meshes)){mesh.instanceMatrix.needsUpdate=true;if(mesh.instanceColor)mesh.instanceColor.needsUpdate=true;}
  group.visible=count>0;const changed=count>0||lastCount!==count;lastCount=count;return changed;
 }
 return {setVisited,update,setEnabled(value){enabled=value;invalid=true;},invalidate(){invalid=true;},
  focus(id){const route=routes.find(r=>r.id===id);return route?route.box.getCenter(new T.Vector3()):null;}};
}
