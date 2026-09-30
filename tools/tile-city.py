"""Split detailed footprint data into 750m tiles and produce a lightweight overview."""
import json,math,gzip,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'python-libs'))
from collections import defaultdict
from shapely.geometry import Polygon,LineString
ROOT=Path(__file__).resolve().parent; assets=ROOT.parent/'dist/assets'
city=json.loads((assets/'city.json').read_text(encoding='utf-8'))
assert city['version']==2,'Run build-city.py before tile-city.py'
(ROOT/'city-full.json').write_text(json.dumps(city,separators=(',',':'),ensure_ascii=False),encoding='utf-8')
tile_size=750; groups=defaultdict(lambda:{'buildings':[],'roads':[]}); cells=defaultdict(dict)
def key(x,y):return (math.floor(x/tile_size),math.floor(y/tile_size))
def write(path,data):
 path.write_text(json.dumps(data,separators=(',',':'),ensure_ascii=False),encoding='utf-8')
 return path.stat().st_size
for b in city['buildings']:
 if b.get('lm'):continue
 p=Polygon(b['r'][0],b['r'][1:]);x,y=p.centroid.coords[0];k=key(x,y)
 groups[k]['buildings'].append(b)
 # A representative real footprint per 60m cell; dimensions/heights are generalized at overview scale.
 c=(math.floor(x/60),math.floor(y/60));old=cells[k].get(c)
 if old is None or p.area*(b['h']-b['z'])>old[0]:
  w,s,e,n=p.bounds
  cells[k][c]=(p.area*(b['h']-b['z']),[round(x,1),round(y,1),round(min(100,e-w),1),round(min(100,n-s),1),b['h'],b['z'],b['c']])
for road in city['roads']:
 for a,b in zip(road['p'],road['p'][1:]):
  if math.dist(a,b)<.1:continue
  k=key((a[0]+b[0])/2,(a[1]+b[1])/2)
  groups[k]['roads'].append({'p':[a,b],'w':road['w'],'bridge':road.get('bridge',False)})
tiles=[];folder=assets/'tiles';folder.mkdir(exist_ok=True)
for (x,y),data in sorted(groups.items()):
 if not data['buildings'] and not data['roads']:continue
 id=f'{x}_{y}';filename=f'tiles/{id}.json'
 data.update(id=id,version=3)
 size=write(assets/filename,data)
 pts=[v for b in data['buildings'] for ring in b['r'] for v in ring]+[v for r in data['roads'] for v in r['p']]
 bounds=[min([x*tile_size]+[p[0] for p in pts]),min([y*tile_size]+[p[1] for p in pts]),max([(x+1)*tile_size]+[p[0] for p in pts]),max([(y+1)*tile_size]+[p[1] for p in pts])]
 tiles.append({'id':id,'url':'./assets/'+filename,'bounds':bounds,'masses':len(data['buildings']),'bytes':size,'overview':[entry[1] for entry in cells[(x,y)].values()]})
city['version']=3;city['tiles']=tiles;city['buildings']=[b for b in city['buildings'] if b.get('lm')]
# Water and parks keep actual geography, simplified only to 2m for the initial map.
for field in ['water','parks']:
 result=[]
 for rings in city[field]:
  p=Polygon(rings[0],rings[1:]).simplify(2,preserve_topology=True)
  if p.is_empty:continue
  result.append([[[round(x,1),round(y,1)] for x,y in ring.coords][:-1] for ring in [p.exterior,*p.interiors]])
 city[field]=result
city['roads']=[]
city['stats'].update(tiles=len(tiles),tileSize=tile_size,overviewMasses=sum(len(t['overview']) for t in tiles),detailBytes=sum(t['bytes'] for t in tiles),maxTileBytes=max(t['bytes'] for t in tiles))
initial=write(assets/'city.json',city)
stats={**city['stats'],'initialBytes':initial,'initialGzipBytes':len(gzip.compress((assets/'city.json').read_bytes())),'extentKm':[(city['bounds'][2]-city['bounds'][0])/1000,(city['bounds'][3]-city['bounds'][1])/1000]}
write(ROOT/'performance.json',stats)
print(json.dumps(stats),flush=True)
