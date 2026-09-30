"""Extend the atlas using one cached Geofabrik London extract, preserving existing buildings."""
import sys,json,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'python-libs'))
import osmium
from shapely.geometry import shape,box
BOUNDS=[-.17,51.47,.01,51.56];clip=box(*BOUNDS)
roads={'primary','secondary','tertiary','residential','pedestrian','unclassified','living_street'}
def relevant(t):return ('building' in t or 'building:part' in t or t.get('natural')=='water' or t.get('waterway')=='riverbank' or t.get('leisure') in ['park','garden'] or t.get('landuse') in ['grass','recreation_ground'] or t.get('highway') in roads or t.get('man_made')=='chimney' or t.get('name')=='Millennium Bridge')
def intersects(points):return points and min(p['lon'] for p in points)<=BOUNDS[2] and max(p['lon'] for p in points)>=BOUNDS[0] and min(p['lat'] for p in points)<=BOUNDS[3] and max(p['lat'] for p in points)>=BOUNDS[1]
factory=osmium.geom.GeoJSONFactory()
class Extract(osmium.SimpleHandler):
 def __init__(self):super().__init__();self.elements={};self.members={};self.invalid=[]
 def node(self,n):
  if n.tags.get('man_made')=='chimney' and BOUNDS[0]<=n.lon<=BOUNDS[2] and BOUNDS[1]<=n.lat<=BOUNDS[3]:self.elements[('node',n.id)]={'type':'node','id':n.id,'tags':dict(n.tags),'lon':n.lon,'lat':n.lat}
 def way(self,w):
  t=dict(w.tags)
  if not relevant(t):return
  if not all(n.location.valid() for n in w.nodes):return
  pts=[{'lon':n.lon,'lat':n.lat} for n in w.nodes]
  if intersects(pts):self.elements[('way',w.id)]={'type':'way','id':w.id,'tags':t,'geometry':pts}
 def relation(self,r):
  if not relevant(dict(r.tags)):return
  self.members[r.id]=[{'type':{'w':'way','n':'node','r':'relation'}[m.type],'ref':m.ref,'role':m.role} for m in r.members]
 def area(self,a):
  if a.from_way() or not relevant(dict(a.tags)):return
  try:data=json.loads(factory.create_multipolygon(a))
  except RuntimeError:
   self.invalid.append(a.orig_id());return
  if not shape(data).intersects(clip):return
  self.elements[('relation',a.orig_id())]={'type':'relation','id':a.orig_id(),'tags':dict(a.tags),'atlas_polygons':data['coordinates']}
source=ROOT/'osm-tiles/greater-london-260929.osm.pbf'
if not source.exists():
 source.parent.mkdir(exist_ok=True)
 urllib.request.urlretrieve('https://download.geofabrik.de/europe/united-kingdom/england/greater-london-260929.osm.pbf',source)
handler=Extract()
handler.apply_file(str(source),locations=True,idx='flex_mem')
print('Extracted',len(handler.elements),'invalid relation areas',handler.invalid,flush=True)
for (kind,id),e in handler.elements.items():
 if kind=='relation':e['members']=handler.members.get(id,[])
assert (ROOT/'london-osm.json').exists(),'Existing raw snapshot is required to preserve central/north sources; use the committed JSON tiles for ordinary edits.'
old=json.loads((ROOT/'london-osm.json').read_text(encoding='utf8'))
merged={(e['type'],e['id']):e for e in old['elements'] if relevant(e.get('tags',{}))}
preserved=0
for key,e in handler.elements.items():
 if key in merged and (e['tags'].get('building') or e['tags'].get('building:part')):preserved+=1;continue
 merged[key]=e
result={'elements':list(merged.values()),'source':'OpenStreetMap / Geofabrik Greater London 2026-09-29; existing central/north snapshot preserved','downloaded':'2026-09-30','bbox':BOUNDS}
(ROOT/'london-osm.json').write_text(json.dumps(result,separators=(',',':')),encoding='utf8')
print(json.dumps({'elements':len(merged),'preservedBuildingSources':preserved,'extracted':len(handler.elements)}),flush=True)
