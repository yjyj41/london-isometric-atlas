// Screen-space callouts. Conservative projected bounds keep landmark silhouettes clear.
export const overlaps=(a,b,gap=0)=>a.x<b.x+b.w+gap&&a.x+a.w+gap>b.x&&a.y<b.y+b.h+gap&&a.y+a.h+gap>b.y;
export function placeCallout({bounds,anchor,size,viewport,obstacles,previous}){
 const {w,h}=size, gap=12, pad=9;
 const cx=anchor.x,cy=Math.max(bounds.y+Math.min(bounds.h*.3,48),anchor.y);
 const candidates=[
  {x:bounds.x+bounds.w+gap,y:cy-h/2},
  {x:bounds.x-gap-w,y:cy-h/2},
  {x:cx-w/2,y:bounds.y-gap-h},
  {x:cx-w/2,y:bounds.y+bounds.h+gap},
  {x:bounds.x+bounds.w+gap,y:bounds.y-gap-h},
  {x:bounds.x-gap-w,y:bounds.y-gap-h},
  {x:bounds.x+bounds.w+gap,y:bounds.y+bounds.h-h},
  {x:bounds.x-gap-w,y:bounds.y+bounds.h-h}
 ];
 const order=[...candidates.keys()];
 // Retain the same side while panning, unless it becomes obstructed.
 if(Number.isInteger(previous)){order.splice(order.indexOf(previous),1);order.unshift(previous)}
 for(const side of order){
  const p=candidates[side],r={x:Math.max(pad,Math.min(viewport.w-pad-w,p.x)),y:Math.max(pad,Math.min(viewport.h-pad-h,p.y)),w,h};
  if(w>viewport.w-2*pad||h>viewport.h-2*pad||obstacles.some(o=>overlaps(r,o,5)))continue;
  return {...r,side};
 }
 return null;
}
