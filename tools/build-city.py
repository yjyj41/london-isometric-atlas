import sys,json,re,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'python-libs'))
from shapely.geometry import Polygon,Point,LineString,box
from shapely.ops import polygonize,unary_union
from shapely.strtree import STRtree
from pyproj import CRS,Transformer
ROOT=Path(__file__).parent;OUT=ROOT.parent/'dist/assets'
raw=json.loads((ROOT/'london-osm.json').read_text(encoding='utf-8'))
proj='+proj=aeqd +lat_0=51.51 +lon_0=-0.106 +datum=WGS84 +units=m +no_defs'
tr=Transformer.from_crs('EPSG:4326',CRS.from_proj4(proj),always_xy=True)
west,south,east,north=raw.get('bbox',[-.132,51.496,-.0715,51.523])
clip=Polygon([tr.transform(x,y) for x,y in [(west,south),(east,south),(east,north),(west,north)]])
def points(g):return [tr.transform(p['lon'],p['lat']) for p in g if p and 'lon' in p]
def polys(g):
 if g.is_empty:return []
 if g.geom_type=='Polygon':return [g]
 return [p for q in getattr(g,'geoms',[]) for p in polys(q)]
def shape(e):
 try:
  if e['type']=='way':
   p=points(e.get('geometry',[]))
   if len(p)<4 or math.dist(p[0],p[-1])>.5:return None
   return Polygon(p).buffer(0).intersection(clip)
  outer=[];inner=[]
  for m in e.get('members',[]):
   p=points(m.get('geometry',[]))
   if len(p)<2:continue
   (inner if m.get('role')=='inner' else outer).append(LineString(p))
  if not outer:return None
  result=unary_union(list(polygonize(unary_union(outer))))
  if inner:result=result.difference(unary_union(list(polygonize(unary_union(inner)))))
  return result.intersection(clip)
 except Exception:return None
def num(s,default=None):
 if s is None:return default
 m=re.search(r'[-+]?\d*\.?\d+',str(s))
 if not m:return default
 v=float(m.group())
 return v*.3048 if any(k in str(s) for k in ['ft',"'"]) else v
def coords(poly):return [[[round(x,2),round(y,2)] for x,y in ring.coords][:-1] for ring in [poly.exterior,*poly.interiors]]
elements=raw['elements'];geoms={};building=[];water=[];parks=[];roads=[];relation_members=set()
for e in elements:
 t=e.get('tags',{});is_b=(t.get('building') not in [None,'no','construction'] or t.get('building:part') not in [None,'no']) and t.get('location')!='underground'
 is_w=t.get('natural')=='water' or t.get('waterway')=='riverbank'
 is_p=t.get('leisure') in ['park','garden'] or t.get('landuse') in ['grass','recreation_ground']
 if is_b or is_w or is_p or t.get('name')=='Tower of London':
  p=shape(e)
  if p is not None and not p.is_empty:
   geoms[(e['type'],e['id'])]=p
   if is_b:
    building.append((e,p))
    if e['type']=='relation':relation_members.update(int(m['ref']) for m in e.get('members',[]) if m['type']=='way')
   if is_w:water.extend(polys(p))
   if is_p:parks.extend(polys(p))
 if e['type']=='way' and t.get('highway') in ['primary','secondary','tertiary','residential','pedestrian','unclassified','living_street']:
  pts=points(e.get('geometry',[]))
  if len(pts)>1:
   g=LineString(pts).intersection(clip)
   for l in [g] if g.geom_type=='LineString' else getattr(g,'geoms',[]):
    if l.geom_type=='LineString' and l.length>3:roads.append({'p':[[round(x,2),round(y,2)] for x,y in l.simplify(.5).coords],'w':num(t.get('width'),{'primary':12,'secondary':10,'tertiary':8,'pedestrian':5}.get(t['highway'],6)),'bridge':t.get('bridge')=='yes'})
print('Parsed',len(building),'building elements',flush=True)
bs=json.loads((ROOT/'landmarks.json').read_text(encoding='utf-8'))
refs={'stpauls':('way',369161987),'shard':('way',31110737),'gherkin':('way',4959489),'tate':('way',24642569),'lloyds':('way',23988892),'westminster':('relation',1567699),'abbey':('way',364313092),'museum':('relation',177044)}
zones={k:geoms[v] for k,v in refs.items() if v in geoms}
isokon=[(e,p) for e,p in building if 'isokon' in e.get('tags',{}).get('name','').lower() or 'lawn road flats' in e.get('tags',{}).get('name','').lower()]
if any(b['id']=='isokon' for b in bs):
 assert isokon,'Isokon OSM footprint missing'
 isokon_e,isokon_p=max(isokon,key=lambda pair:pair[1].area)
 zones['isokon']=isokon_p.buffer(.3)
 refs['isokon']=(isokon_e['type'],isokon_e['id'])
 inverse=Transformer.from_crs(CRS.from_proj4(proj),'EPSG:4326',always_xy=True)
 lon,lat=inverse.transform(isokon_p.centroid.x,isokon_p.centroid.y)
 for b in bs:
  if b['id']=='isokon':b['lat']=lat;b['lon']=lon
for b in bs:
 b['anchor']=[round(v,3) for v in tr.transform(b['lon'],b['lat'])]
 b['modelSource']='OSM footprint + height/levels; simplified roof masses'
 if b['id']=='towerbridge':zones[b['id']]=Point(*b['anchor']).buffer(195)
 if b['id']=='tower':
  matches=[p for e,p in building if e.get('tags',{}).get('name')=='White Tower']
  zones[b['id']]=Point(*b['anchor']).buffer(140)
 if b['id']=='barbican':
  names=['Barbican Arts Centre','Shakespeare Tower','Cromwell Tower','Lauderdale Tower','Frobisher Crescent','Defoe House','Gilbert House','Thomas More House','Andrewes House','Willoughby House','Ben Jonson House','Breton House','Bunyan Court','Bryer Court','Seddon House','Speed House','Mountjoy House']
  zones[b['id']]=unary_union([p for e,p in building if e.get('tags',{}).get('name') in names]).buffer(1)
 b['modelSourceUrl']='https://www.openstreetmap.org/'+('/'.join(map(str,refs[b['id']]))) if b['id'] in refs else 'https://www.openstreetmap.org/copyright'
parts=[(e,p) for e,p in building if e.get('tags',{}).get('building:part') not in [None,'no']]
tree=STRtree([p for _,p in parts]);records=[];sources={'height':0,'levels':0,'assumed':0}
for e,p in building:
 t=e['tags'];part=t.get('building:part') not in [None,'no']
 if e['type']=='way' and e['id'] in relation_members and not part:continue
 if not part:
  children=[parts[int(i)][1] for i in tree.query(p) if parts[int(i)][0]['id']!=e['id'] and p.buffer(.4).covers(parts[int(i)][1].representative_point())]
  if children:
   # OSM outlines are not extruded through their mapped parts. Keep only uncovered ground.
   p=p.difference(unary_union(children))
 h=num(t.get('height'));lv=num(t.get('building:levels'));rh=max(0,num(t.get('roof:height'),0));z=max(0,num(t.get('min_height'),num(t.get('building:min_level'),0)*3.2))
 confidence='height' if h is not None else 'levels' if lv is not None else 'assumed'
 if h is None:h=(lv*3.2 if lv is not None else 12)+rh
 if h<=z or h>450:continue
 for poly in polys(p):
  if poly.area<.3:continue
  center=poly.representative_point();landmark=next((k for k,v in zones.items() if v.covers(center)),None)
  if not landmark and poly.area<3:continue
  if landmark=='shard' or landmark=='gherkin':continue
  simple=poly.simplify(.07 if landmark else .22,preserve_topology=True)
  record={'id':f"{e['type']}/{e['id']}",'name':t.get('name',''),'r':coords(simple),'h':round(h,2),'z':round(z,2),'c':confidence}
  if landmark:record['lm']=landmark
  if t.get('roof:shape') and rh>0:
   record['roof']={'shape':t['roof:shape'],'h':round(min(rh,h-z),2),'dir':num(t.get('roof:direction'))}
  records.append(record);sources[confidence]+=1
# Deliberately approximate tapered forms using real footprints and referenced heights.
for id,h in [('shard',309.6),('gherkin',180)]:
 poly=max(polys(zones[id]),key=lambda p:p.area)
 records.append({'id':'manual/'+id,'lm':id,'r':coords(poly.simplify(.25)),'h':h,'z':0,'c':'height','form':id,'name':id})
 sources['height']+=1
# Millennium Bridge is a mapped pedestrian bridge, not a building footprint.
bridge_lines=[e for e in elements if e['type']=='way' and e.get('tags',{}).get('name')=='Millennium Bridge' and e.get('tags',{}).get('bridge')=='yes']
for e in bridge_lines:
 pts=points(e.get('geometry',[]))
 if len(pts)<2:continue
 for p in polys(LineString(pts).buffer(2,cap_style=2)):
  records.append({'id':f"way/{e['id']}",'lm':'millennium','r':coords(p),'h':11,'z':10,'c':'assumed','name':'Millennium Bridge deck'})
  sources['assumed']+=1
for b in bs:
 subset=[r for r in records if r.get('lm')==b['id']]
 b['massCount']=len(subset);b['modelHeight']=max((r['h'] for r in subset),default=0)
 b['confidence']={c:sum(r['c']==c for r in subset) for c in sources}
 b['height']=309.6 if b['id']=='shard' else b['height']
 b['modelNote']='높이 태그와 층수 추정이 혼합된 OSM 매스입니다. 지붕은 단순화했습니다.'
 if b['id'] in ['shard','gherkin']:b['modelNote']='실제 평면 위치와 참고 높이를 사용한 근사 곡면·테이퍼 매스입니다.'
 if b['id']=='millennium':b['modelNote']='OSM 보행 경로 중심선에 폭 4 m, 데크 레벨 10 m를 가정한 매스입니다.'
 if b['id']=='isokon':b['modelNote']='실제 OSM 건물 윤곽을 사용한 개략 매스입니다. 높이 태그가 없어 12 m를 가정했습니다. 갤러리·발코니·상부 후퇴부는 단순화했습니다.'
print('Landmarks',[(b['id'],b['massCount'],b['modelHeight']) for b in bs],flush=True)
# The bbox endpoint omits distant members needed to close Thames multipolygons.
# Preserve the completed source surfaces fetched by repair-water.py.
water_source=ROOT/'water-surfaces.json'
if water_source.exists():
 complete=json.loads(water_source.read_text(encoding='utf-8'))
 assert complete['origin']['crs']==proj
 water.extend(Polygon(p[0],p[1:]).intersection(clip) for p in complete['water'])
water=polys(unary_union(water));parks=polys(unary_union(parks))
result={'version':2,'units':'meters','origin':{'lat':51.51,'lon':-.106,'crs':proj,'axes':'X east, Y north, Z up'},'bounds':[round(v,1) for v in clip.bounds],'attribution':'© OpenStreetMap contributors · ODbL 1.0','date':raw.get('downloaded','2026-09-21'),'geographicBounds':[west,south,east,north],'buildings':records,'water':[coords(p.simplify(.3)) for p in water if p.area>20],'parks':[coords(p.simplify(.5)) for p in parks if p.area>50],'roads':roads,'landmarks':bs,'stats':{'masses':len(records),'heights':sources}}
OUT.mkdir(exist_ok=True)
(OUT/'city.json').write_text(json.dumps(result,separators=(',',':'),ensure_ascii=False),encoding='utf-8')
print('Saved',len(records),'masses;',len(water),'water polygons;',len(roads),'roads;',sources,flush=True)
