"""Check scene support, body clearance and schematic crown clearance against source geometry."""
import json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'tools/python-libs'))
from shapely.geometry import Polygon,LineString,Point
from shapely.ops import unary_union
city=json.loads((root/'tools/city-full.json').read_text(encoding='utf-8'))
def module(name):return json.loads((root/'dist'/name).read_text(encoding='utf-8').split(' = ',1)[1].strip().rstrip(';'))
routes=module('walk-routes.js');trees=module('visit-landscape.js')
for id,items in routes.items():
 pts=[p for r in items for p in r['points']];xmin=min(p[0] for p in pts)-40;xmax=max(p[0] for p in pts)+40;ymin=min(p[1] for p in pts)-40;ymax=max(p[1] for p in pts)+40
 near=[]
 for b in city['buildings']:
  if not b.get('r'):continue
  xs=[p[0] for p in b['r'][0]];ys=[p[1] for p in b['r'][0]]
  if max(xs)<xmin or min(xs)>xmax or max(ys)<ymin or min(ys)>ymax:continue
  near.append((b,Polygon(b['r'][0],b['r'][1:]).buffer(0)))
 for r in items:
  line=LineString(r['points']);z=r['elevation']
  blockers=unary_union([p for b,p in near if b['h']>z+.04 and b.get('z',0)<z+1.85])
  assert line.distance(blockers)>.34,(id,r['name'],'body collision',line.distance(blockers))
  if r['support']:
   b,p=next((b,p) for b,p in near if b['id']==r['support'])
   assert abs(z-b['h']-.025)<.001,(id,'height')
   assert p.buffer(-.34).buffer(.002).covers(line),(id,'unsupported edge')
  else:
   assert z<.1
   water=unary_union([Polygon(w[0],w[1:]).buffer(0) for w in city['water']])
   assert line.distance(water)>.34,(id,'water')
 for t in trees[id]:
  p=Point(t['x'],t['north']);assert all(p.distance(poly)>t['radius']*1.12 for _,poly in near),(id,'tree/building overlap')
 print(id,': support heights, body clearance and tree crowns pass')
