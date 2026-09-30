"""Complete river multipolygons omitted by bbox-only OSM API responses."""
from pathlib import Path
import sys,json,xml.etree.ElementTree as ET,zipfile,gzip
from urllib.request import Request,urlopen
sys.path.insert(0,str(Path(__file__).resolve().parent/'python-libs'))
from shapely.geometry import Polygon,LineString,Point
from shapely.ops import unary_union,polygonize
from pyproj import CRS,Transformer
root=Path(__file__).resolve().parent;assets=root.parent/'dist/assets'
city=json.loads((assets/'city.json').read_text(encoding='utf-8'))
transform=Transformer.from_crs('EPSG:4326',CRS.from_proj4(city['origin']['crs']),always_xy=True)
w,s,e,n=city['geographicBounds'];clip=Polygon([transform.transform(x,y) for x,y in [(w,s),(e,s),(e,n),(w,n)]])
surfaces=[Polygon(p[0],p[1:]) for p in city['water']]
for rid in [28934,70347]:
 path=root/'osm-tiles'/f'water-relation-{rid}.osm'
 if not path.exists():
  with urlopen(Request(f'https://api.openstreetmap.org/api/0.6/relation/{rid}/full',headers={'User-Agent':'LondonFieldAtlas/4.0 (architecture map)'}),timeout=60) as response:raw=response.read()
  ET.fromstring(raw);path.write_bytes(raw)
 doc=ET.parse(path).getroot()
 nodes={x.attrib['id']:transform.transform(float(x.attrib['lon']),float(x.attrib['lat'])) for x in doc.findall('node')}
 ways={x.attrib['id']:[nodes[n.attrib['ref']] for n in x.findall('nd')] for x in doc.findall('way')}
 relation=next(x for x in doc.findall('relation') if x.attrib['id']==str(rid))
 outer=[];inner=[]
 for member in relation.findall('member'):
  if member.attrib['type']!='way':continue
  (inner if member.attrib.get('role')=='inner' else outer).append(LineString(ways[member.attrib['ref']]))
 polygon=unary_union(list(polygonize(unary_union(outer))))
 if inner:polygon=polygon.difference(unary_union(list(polygonize(unary_union(inner)))))
 assert polygon.area>100000,f'Incomplete river relation {rid}'
 surfaces.append(polygon.intersection(clip))
def polys(g):
 if g.is_empty:return []
 if g.geom_type=='Polygon':return [g]
 return [p for q in getattr(g,'geoms',[]) for p in polys(q)]
union=unary_union(surfaces)
anchor=next(b['anchor'] for b in city['landmarks'] if b['id']=='millennium')
assert union.covers(Point(*anchor)),'River missing under Millennium Bridge'
water=[[[[round(x,2),round(y,2)] for x,y in ring.coords][:-1] for ring in [p.exterior,*p.interiors]] for p in polys(union) if p.area>20]
source={'origin':city['origin'],'relations':[28934,70347],'attribution':city['attribution'],'water':water}
(root/'water-surfaces.json').write_text(json.dumps(source,separators=(',',':')),encoding='utf-8')
city['water']=water
(assets/'city.json').write_text(json.dumps(city,separators=(',',':'),ensure_ascii=False),encoding='utf-8')
# Keep the downloadable editable data consistent; no Rhino mesh changes are needed.
with zipfile.ZipFile(assets/'city-data.zip') as z:
 names=z.namelist();data={name:z.read(name) for name in names}
for name in names:
 if name.endswith('.json'):
  full=json.loads(data[name]);full['water']=water;data[name]=json.dumps(full,separators=(',',':'),ensure_ascii=False).encode()
with zipfile.ZipFile(assets/'city-data.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for name,payload in data.items():z.writestr(name,payload)
fullpath=root/'city-full.json'
if fullpath.exists():
 full=json.loads(fullpath.read_text(encoding='utf-8'));full['water']=water;fullpath.write_text(json.dumps(full,separators=(',',':'),ensure_ascii=False),encoding='utf-8')
stats=json.loads((root/'performance.json').read_text(encoding='utf-8'));stats['initialBytes']=(assets/'city.json').stat().st_size;stats['initialGzipBytes']=len(gzip.compress((assets/'city.json').read_bytes()))
(root/'performance.json').write_text(json.dumps(stats,indent=2),encoding='utf-8')
print(json.dumps({'waterPolygons':len(water),'waterAreaM2':union.area,'initialBytes':stats['initialBytes'],'downloadZipBytes':(assets/'city-data.zip').stat().st_size}))
