"""Decorative visit scenes fitted to the retained metric model, not public-access routes."""
import json,sys,math
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tools/python-libs'))
from shapely.geometry import Polygon,LineString,Point,box
from shapely.ops import unary_union,substring
city=json.loads((root/'tools/city-full.json').read_text(encoding='utf-8'))
settings={
 'isokon':{'core':['detail/isokon/main-wing-0','detail/isokon/gallery-annex-0'],'decks':['detail/isokon/gallery-slab-1-0','detail/isokon/gallery-slab-2-0','detail/isokon/gallery-slab-3-0','detail/isokon/roof-terrace-slab-0'],'trees':14},
 'barbican':{'core':['relation/19324713'],'decks':['relation/19324713'],'trees':20},
 'tate':{'core':['way/123075369','way/542122683'],'decks':['way/542122683'],'trees':24}}
allRoutes={};landscape={};review=[]
def polys(g):return [p for p in (list(g.geoms) if hasattr(g,'geoms') else [g]) if p.geom_type=='Polygon' and p.area>2]
def lines(g):return [p for p in (list(g.geoms) if hasattr(g,'geoms') else [g]) if p.geom_type in ['LineString','LinearRing'] and p.length>8]
for id,cfg in settings.items():
 records=[b for b in city['buildings'] if b.get('lm')==id];sources={b['id']:b for b in records}
 core=unary_union([Polygon(sources[k]['r'][0],sources[k]['r'][1:]).buffer(0) for k in cfg['core']]);area=core.buffer(120);ab=area.bounds
 nearby=[]
 for b in city['buildings']:
  if not b.get('r'):continue
  xs=[p[0] for p in b['r'][0]];ys=[p[1] for p in b['r'][0]]
  if max(xs)<ab[0] or min(xs)>ab[2] or max(ys)<ab[1] or min(ys)>ab[3]:continue
  p=Polygon(b['r'][0],b['r'][1:]).buffer(0)
  if p.intersects(area):nearby.append((b,p))
 water=unary_union([Polygon(r[0],r[1:]).buffer(0) for r in city['water'] if Polygon(r[0],r[1:]).intersects(area)])
 roads=unary_union([LineString(r['p']).buffer(min(30,r['w'])/2+.6) for r in city['roads'] if not r.get('bridge') and LineString(r['p']).intersects(area)])
 obstacles=unary_union([p for b,p in nearby if b.get('z',0)<1.9 and b['h']>.1]+[water,roads])
 routes=[]
 def add(line,z,people,name,support=None):
  pts=[[round(x,3),round(y,3)] for x,y in line.coords]
  routes.append(dict(sourceId=support or 'model-courtyard-'+str(len(routes)),points=pts,elevation=round(z+.025,3),people=people,name=name,loop=Point(pts[0]).distance(Point(pts[-1]))<.01,support=support))
  review.append(dict(landmark=id,name=name,support=support,elevation=round(z+.025,3),length=round(line.length,2),people=people,kind='model-surface' if support else 'near-facade',clearance=round(line.distance(obstacles),3) if not support else None))
 # Fit people to actual gallery slabs / flat roof faces, excluding taller parts and low ceilings.
 for key in cfg['decks']:
  b=sources[key];surface=Polygon(b['r'][0],b['r'][1:]).buffer(0);z=b['h']
  blockers=unary_union([p for other,p in nearby if other is not b and other['h']>z+.05 and other.get('z',0)<z+1.9])
  safe=surface.buffer(-.55).difference(blockers.buffer(.5))
  if 'gallery-slab' in key:
   ring=surface.minimum_rotated_rectangle.exterior.coords;corners=list(ring)[:4]
   pairs=[(Point(corners[i]).distance(Point(corners[(i+1)%4])),i) for i in range(4)];_,i=min(pairs)
   a=((corners[i][0]+corners[(i+1)%4][0])/2,(corners[i][1]+corners[(i+1)%4][1])/2);j=(i+2)%4
   c=((corners[j][0]+corners[(j+1)%4][0])/2,(corners[j][1]+corners[(j+1)%4][1])/2)
   segments=lines(LineString([a,c]).intersection(safe))
   if segments:add(max(segments,key=lambda l:l.length),z,5,'Access gallery',key)
  else:
   for p in sorted(polys(safe),key=lambda p:p.area,reverse=True)[:1]:
    inner=p.buffer(-.55)
    if not inner.is_empty:p=max(polys(inner),key=lambda p:p.area)
    add(LineString(p.exterior.coords),z,9 if id=='isokon' else 22,'Roof terrace study',key)
 # Short walks directly alongside the architecture, rather than remote footpaths.
 boundary=core.buffer(3,join_style='round',quad_segs=4).boundary
 segments=lines(boundary.difference(obstacles.buffer(.6)))
 for line in sorted(segments,key=lambda l:l.length,reverse=True)[:3]:
  if line.length>110:line=substring(line,0,110)
  line=substring(line,.4,line.length-.4)
  add(line,.06,min(12,max(5,round(line.length/5))),'Forecourt and facade walk')
 assert any(r['support'] for r in routes),id
 assert any(not r['support'] for r in routes),id
 allRoutes[id]=routes
 # Small trees in open ground beside the model. Positions are schematic, not an inventory.
 buildingSolid=unary_union([p for b,p in nearby]);walkArea=unary_union([LineString(r['points']).buffer(1.7) for r in routes if not r['support']])
 treeSafe=core.buffer(22).difference(buildingSolid.buffer(2.2)).difference(water.buffer(2.2)).difference(roads.buffer(2.2)).difference(walkArea.buffer(1.3))
 candidates=[]
 minx,miny,maxx,maxy=core.buffer(20).bounds
 for x in range(math.floor(minx),math.ceil(maxx),5):
  for n in range(math.floor(miny),math.ceil(maxy),5):
   pt=Point(x,n)
   if treeSafe.contains(pt):candidates.append((pt.distance(core),x,n))
 # Prioritise close foreground planting, with at least 5m crown separation.
 candidates.sort(key=lambda v:v[0]+.015*(v[2]-miny)-.005*(v[1]-minx))
 trees=[]
 for d,x,n in candidates:
  if any(math.hypot(x-t['x'],n-t['north'])<6 for t in trees):continue
  trees.append(dict(x=x,north=n,height=round(4.2+(len(trees)%4)*.45,2),radius=round(1.65+(len(trees)%3)*.15,2)))
  if len(trees)>=cfg['trees']:break
 landscape[id]=trees
 print(id,len(routes),'routes',sum(r['people'] for r in routes),'people',len(trees),'trees')
(root/'dist/walk-routes.js').write_text('// Decorative paths fitted to model surfaces; not surveyed/public-access walking routes. Metres.\nexport const walkRoutes = '+json.dumps(allRoutes,separators=(',',':'))+';\n',encoding='utf-8')
(root/'dist/visit-landscape.js').write_text('// Schematic planting in checked open ground; not an actual tree inventory. Metres.\nexport const visitTrees = '+json.dumps(landscape,separators=(',',':'))+';\n',encoding='utf-8')
(root/'tools/walk-route-review.json').write_text(json.dumps(review,indent=2)+'\n',encoding='utf-8')
