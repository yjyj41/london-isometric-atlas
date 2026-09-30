import * as T from './vendor/three.module.js';

export function createTileStream(city,context,mats,changed){
 const small=matchMedia('(max-width:700px)').matches;
 const maxTiles=small?10:20,maxBytes=(small?24:48)*1024*1024;
 const badge=document.querySelector('#stream-status'),entries=new Map(),pending=new Map(),failed=new Map();
 const wanted=new Set(),deferred=new Set();let revision=0,running=0,timer,enabled=true,detail=false,totalBytes=0,downloadedBytes=0;
 const roadMat=new T.MeshStandardMaterial({color:0xf0f2f1,roughness:.92,side:T.DoubleSide});
 const box=new T.BoxGeometry(1,1,1),matrix=new T.Matrix4();
 const overview=new Map();
 for(const tile of city.tiles||[]){
  const root=new T.Group();
  for(const kind of ['height','levels','assumed']){
   const records=tile.overview.filter(r=>r[6]===kind);if(!records.length)continue;
   const mesh=new T.InstancedMesh(box,mats[kind],records.length);
   records.forEach(([x,y,w,d,h,z],i)=>{matrix.makeScale(Math.max(1,w),Math.max(.1,h-z),Math.max(1,d));matrix.setPosition(x,(h+z)/2,-y);mesh.setMatrixAt(i,matrix)});
   mesh.instanceMatrix.needsUpdate=true;mesh.computeBoundingSphere();root.add(mesh);
  }
  context.add(root);overview.set(tile.id,root);
 }
 let worker=null,workerBroken=false,workerBusy=false;
 const workerTasks=new Map();let taskNo=0;
 try{
  worker=new Worker(new URL('./tile-worker.js',import.meta.url),{type:'module'});
  worker.onmessage=({data})=>{const task=workerTasks.get(data.id);if(!task)return;workerTasks.delete(data.id);workerBusy=false;data.error?task.reject(Error(data.error)):task.resolve(data.batches)};
  worker.onerror=()=>{workerBroken=true;worker?.terminate();worker=null;workerBusy=false;for(const task of workerTasks.values())task.reject(Error('Worker unavailable'));workerTasks.clear()};
 }catch{workerBroken=true}
 async function build(records){
  if(worker&&!workerBroken){
   // One geometry worker limits peak CPU/memory, while two requests may download.
   while(workerBusy)await new Promise(r=>setTimeout(r,16));
   if(worker&&!workerBroken){workerBusy=true;const id=++taskNo;
    try{return await new Promise((resolve,reject)=>{workerTasks.set(id,{resolve,reject});worker.postMessage({id,records})})}
    catch{workerBroken=true;worker?.terminate();worker=null;workerBusy=false}
   }
  }
  const {buildTileData}=await import('./tile-geometry.js');return buildTileData(records,true);
 }
 function dispose(entry){context.remove(entry.root);entry.root.traverse(o=>o.geometry?.dispose());totalBytes-=entry.bytes;entries.delete(entry.id)}
 function trim(){
  for(const e of [...entries.values()].sort((a,b)=>a.used-b.used)){
   if(totalBytes<=maxBytes&&entries.size<=maxTiles)break;
   // The overview remains available if the GPU budget is exhausted.
   if(wanted.has(e.id)&&entries.size===1)break;
   overview.get(e.id).visible=true;if(wanted.has(e.id))deferred.add(e.id);dispose(e);
  }
 }
 function updateStatus(){
  const visible=[...entries.values()].filter(e=>e.root.visible).length;
  const errors=[...wanted].filter(id=>failed.has(id)).length;
  badge.textContent=!enabled?'주변 매스 숨김':errors?'일부 지역 로딩 실패 · 눌러서 재시도':detail?`상세 매스 · ${visible}/${wanted.size} 지역${running?' 불러오는 중…':deferred.size?' · 나머지는 단순화 표시':''}`:'전체 보기 · 단순화 매스 · 확대하면 상세 표시';
  badge.dataset.mode=!enabled?'hidden':errors?'error':detail?'detail':'overview';
  // Readable diagnostics help validate the real geometry budget without retaining raw records.
  badge.dataset.loadedTiles=entries.size;badge.dataset.visibleTiles=visible;badge.dataset.geometryBytes=totalBytes;badge.dataset.downloadedBytes=downloadedBytes;badge.dataset.activeRequests=running;
  badge.title=errors?'클릭하면 실패한 지역을 다시 불러옵니다.':'확대할 때 필요한 지역을 불러오고, 멀어진 지역은 메모리에서 해제합니다.';
 }
 async function load(tile){
  const controller=new AbortController();pending.set(tile.id,controller);running++;updateStatus();
  try{
   const response=await fetch(tile.url,{signal:controller.signal});if(!response.ok)throw Error('HTTP '+response.status);
   const records=await response.json();downloadedBytes+=tile.bytes;
   if(!wanted.has(tile.id)||!enabled)return;
   const packed=await build(records);
   if(!wanted.has(tile.id)||!enabled)return;
   const root=new T.Group();let bytes=0;
   for(const [kind,attrs]of Object.entries(packed)){
    const g=new T.BufferGeometry();g.setAttribute('position',new T.BufferAttribute(attrs.position,3));g.setAttribute('normal',new T.BufferAttribute(attrs.normal,3));
    bytes+=attrs.position.byteLength+attrs.normal.byteLength;
    const mesh=new T.Mesh(g,kind==='roads'?roadMat:mats[kind]);mesh.castShadow=kind!=='roads';mesh.receiveShadow=true;root.add(mesh);
   }
   const entry={id:tile.id,root,bytes,used:++revision};entries.set(tile.id,entry);context.add(root);totalBytes+=bytes;trim();
  }catch(error){if(error.name!=='AbortError'){failed.set(tile.id,error.message);console.warn('Tile load failed',tile.id,error.message)}}
  finally{pending.delete(tile.id);running--;refresh();pump();changed()}
 }
 function refresh(){
  for(const [id,o]of overview){const e=entries.get(id);o.visible=!(enabled&&detail&&wanted.has(id)&&e);if(e)e.root.visible=enabled&&detail&&wanted.has(id)}
  updateStatus();
 }
 function pump(){
  if(!enabled||!detail)return;
  for(const id of wanted){if(running>=2)break;if(entries.has(id)||pending.has(id)||failed.has(id)||deferred.has(id))continue;load(city.tiles.find(t=>t.id===id))}
 }
 function update(bounds,span,center){
  const previous=[...wanted].sort().join(',');detail=span<1200;wanted.clear();
  if(detail&&enabled){
   const tiles=city.tiles.filter(t=>t.bounds[0]<=bounds[2]&&t.bounds[2]>=bounds[0]&&t.bounds[1]<=bounds[3]&&t.bounds[3]>=bounds[1]);
   tiles.sort((a,b)=>Math.hypot((a.bounds[0]+a.bounds[2])/2-center[0],(a.bounds[1]+a.bounds[3])/2-center[1])-Math.hypot((b.bounds[0]+b.bounds[2])/2-center[0],(b.bounds[1]+b.bounds[3])/2-center[1]));
   for(const t of tiles.slice(0,maxTiles)){wanted.add(t.id);const e=entries.get(t.id);if(e)e.used=++revision}
  }
  for(const [id,c]of pending)if(!wanted.has(id))c.abort();
  if(previous!==[...wanted].sort().join(','))deferred.clear();
  // Release invisible detail immediately, rather than accumulating an unbounded city cache.
  for(const e of [...entries.values()])if(!wanted.has(e.id))dispose(e);
  refresh();clearTimeout(timer);timer=setTimeout(pump,120);changed();
 }
 function setEnabled(value){enabled=value;if(!value){for(const c of pending.values())c.abort();for(const e of [...entries.values()])dispose(e)}refresh();if(value)pump()}
 badge.onclick=()=>{for(const id of wanted)failed.delete(id);pump();refresh()};refresh();
 return {update,setEnabled};
}
