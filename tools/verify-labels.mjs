import assert from 'node:assert/strict';
import {placeCallout,overlaps} from '../dist/label-layout.js';
const building={x:250,y:200,w:100,h:250};
const input={bounds:building,anchor:{x:300,y:210},size:{w:145,h:38},viewport:{w:1000,h:700},obstacles:[building,{x:0,y:0,w:1000,h:170},{x:700,y:300,w:280,h:350}]};
const first=placeCallout(input);
assert.ok(first);assert.ok(input.obstacles.every(o=>!overlaps(first,o,5)));
// A pan translates the model and retains the label side and relative placement.
const moved=placeCallout({...input,bounds:{...building,x:building.x+20},anchor:{x:320,y:210},obstacles:[{...building,x:270}],previous:first.side});
assert.equal(moved.side,first.side);assert.equal(moved.x,first.x+20);
// A newly opened card invalidates the previous side instead of covering it.
const blocked=placeCallout({...input,obstacles:[...input.obstacles,first],previous:first.side});
assert.ok(blocked);assert.notEqual(blocked.side,first.side);assert.ok(!overlaps(first,blocked,5));
// No safe space means omit the callout; never place it over a model/control.
assert.equal(placeCallout({...input,obstacles:[{x:0,y:0,w:1000,h:700}]}),null);
// Small viewports, including long labels, remain within their edges.
const mobile=placeCallout({...input,bounds:{x:120,y:170,w:50,h:100},anchor:{x:145,y:170},size:{w:200,h:55},viewport:{w:390,h:500},obstacles:[{x:120,y:170,w:50,h:100}]});
assert.ok(mobile);assert.ok(mobile.x>=9&&mobile.x+mobile.w<=381&&mobile.y>=9&&mobile.y+mobile.h<=491);
console.log('Callout silhouette/control avoidance, pan stability, card collision and narrow viewport checks passed.');
