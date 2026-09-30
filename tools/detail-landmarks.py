"""Reference-informed landmark mass profiles, anchored to actual OSM polygons.
Section/roof subdivisions are explicitly approximate; this is not survey geometry.
"""
import json,sys,math
from pathlib import Path
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT/'python-libs'))
from shapely.geometry import Polygon,box,Point,LineString
from shapely.geometry.polygon import orient
from shapely import constrained_delaunay_triangles
from shapely.affinity import affine_transform
from pyproj import Transformer
project=Transformer.from_crs("EPSG:4326", "+proj=aeqd +lat_0=51.51 +lon_0=-0.106 +datum=WGS84 +units=m +no_defs",always_xy=True)
path=ROOT.parent/'dist/assets/city.json';city=json.loads(path.read_text(encoding='utf8'))
assert city['version']==2
raw=json.loads((ROOT/'london-osm.json').read_text(encoding='utf8'))
tags={f"{e['type']}/{e['id']}":e.get('tags',{}) for e in raw['elements']}
def polys(g):
 if g.is_empty:return []
 if g.geom_type=='Polygon':return [g]
 return [p for q in getattr(g,'geoms',[]) for p in polys(q)]
def volume(poly,base,top):
 """Closed solid with a planar or sampled height function, preserving holes."""
 out=[];height=top if callable(top) else lambda x,y:top
 bottom=base if callable(base) else lambda x,y:base
 def tri(a,b,c):out.extend([round(v,5) for p in [a,b,c] for v in p])
 for p in polys(poly):
  p=orient(p,sign=1.0)
  for t in constrained_delaunay_triangles(p).geoms:
   a,b,c=list(t.exterior.coords)[:3]
   # Make top faces point upward regardless of triangulator winding.
   if (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])<0:b,c=c,b
   tri((*a,height(*a)),(*b,height(*b)),(*c,height(*c)))
   tri((*c,bottom(*c)),(*b,bottom(*b)),(*a,bottom(*a)))
  for ring in [p.exterior,*p.interiors]:
   points=list(ring.coords)
   for a,b in zip(points,points[1:]):
    tri((*a,bottom(*a)),(*b,bottom(*b)),(*a,height(*a)))
    tri((*b,bottom(*b)),(*b,height(*b)),(*a,height(*a)))
 return out
# Crossrail's centre part is mapped separately; the roof spans the original complete outline.
source=next(e for e in raw['elements'] if e['type']=='way' and e['id']==281015404)
whole=Polygon([project.transform(p['lon'],p['lat']) for p in source['geometry']])
city['buildings']=[r for r in city['buildings'] if r.get('lm')!='crossrail']+[{'id':'way/281015404','name':'Crossrail Place','lm':'crossrail','r':[[[round(x,2),round(y,2)] for x,y in whole.exterior.coords][:-1]],'h':28,'z':0,'c':'height'}]
notes={}
for r in city['buildings']:
 lm=r.get('lm');t=tags.get(r['id'],{})
 if lm=='battersea' and t.get('man_made')=='chimney':r['form']='tapered_chimney'
 if lm=='crossrail' and r['id']=='way/281015404':
  p=Polygon(r['r'][0],r['r'][1:]);corners=list(p.minimum_rotated_rectangle.exterior.coords)
  a,b=max(zip(corners,corners[1:]),key=lambda ab:math.dist(*ab));length=math.dist(a,b)
  ux,uy=(b[0]-a[0])/length,(b[1]-a[1])/length;vx,vy=-uy,ux
  local=affine_transform(p,[ux,uy,vx,vy,0,0]);xmin,ymin,xmax,ymax=local.bounds;mid=(ymin+ymax)/2;radius=(ymax-ymin)/2
  mesh=[]
  for i in range(32):
   piece=local.intersection(box(xmin-1,ymin+(ymax-ymin)*i/32,xmax+1,ymin+(ymax-ymin)*(i+1)/32))
   world=affine_transform(piece,[ux,vx,uy,vy,0,0])
   mesh+=volume(world,r['z'],lambda x,y:18+10*math.sqrt(max(0,1-((x*vx+y*vy-mid)/radius)**2)))
  r['mesh']=mesh
  notes[lm]='실제 OSM 평면과 28 m 전체 높이. 긴 곡면 지붕은 단면을 근사한 매스이며 목재 격자·ETFE·실내 정원은 생략했습니다.'
 if lm=='peckham' and r['id']=='way/285971403':
  p=Polygon(r['r'][0],r['r'][1:]);xmin,ymin,xmax,ymax=p.bounds
  mesh=volume(p,r['z'],r['h'])
  # Mapped raised reading room retained, seven schematic supports added below it.
  for i in range(7):
   y=ymin+(ymax-ymin)*(.1+.8*i/6);cut=p.intersection(LineString([(xmin-1,y),(xmax+1,y)]))
   if cut.is_empty:continue
   x=cut.bounds[0]+min(2,(cut.bounds[2]-cut.bounds[0])*.25)
   foot=Point(x,y).buffer(.3,quad_segs=4);column=volume(foot,0,r['z'])
   for k in range(0,len(column),3):column[k]+=(column[k+2]/r['z'])*(.8 if i%2 else -.8)
   mesh+=column
  r['mesh']=mesh
  notes[lm]='실제 OSM 평면·상부 열람실(하부 10.5 m)·지붕 부재를 유지했습니다. 열린 하부의 경사 기둥 일곱 개는 참고 사진에 기반한 개략 배치입니다.'
notes['canadasquare']='실제 OSM 평면·분절과 235 m 높이, 25 m 피라미드 지붕을 유지했습니다. 외피와 창호는 생략한 매스입니다.'
notes['battersea']='실제 OSM 본체·분절 매스와 네 굴뚝의 위치를 유지했습니다. 굴뚝은 OSM 높이와 완만한 테이퍼로 표현하며 세부 외피는 생략했습니다.'
notes['laban']='실제 OSM 평면의 휘어진 입면과 건물 분절을 유지한 매스입니다. 반투명 외피와 내부 공간은 표현하지 않습니다.'
notes['navalcollege']='실제 네 코트의 건물 평면·중정과 OSM 건물 부재를 사용했습니다. 높이 미기재 부분과 지붕은 근사이며 중앙 시선축을 유지합니다.'
notes['queenshouse']='실제 OSM 평면·분절을 사용한 고전주의 매스입니다. 높이 미기재 부분은 추정이며 창호와 장식은 생략했습니다.'
notes['observatory']='Flamsteed House의 실제 평면과 OSM 지붕·부재를 사용했습니다. 미기재 높이는 추정이며 언덕의 지형 고도는 반영하지 않습니다.'
from curated_details import enrich
enrich(city,volume,raw)
from station_details import enrich_stations
enrich_stations(city,volume,raw)
english=json.loads((ROOT/'english-content.json').read_text(encoding='utf8'))
for b in city['landmarks']:
 b['massCount']=sum(r.get('lm')==b['id'] for r in city['buildings'])
 b['confidence']={c:sum(r.get('lm')==b['id'] and r['c']==c for r in city['buildings']) for c in ['height','levels','assumed']}
 if b['id'] in notes:b['modelNote']=notes[b['id']];b['modelSource']='OSM footprint and mapped parts; reference-informed approximate mass profile'
 b['modelHeight']=max(r['h'] for r in city['buildings'] if r.get('lm')==b['id'])
 b['height']=b['modelHeight']
 b.update(english[b['id']]);b.pop('ko',None)
city['stats']['masses']=len(city['buildings'])
city['stats']['heights']={c:sum(r['c']==c for r in city['buildings']) for c in ['height','levels','assumed']}
path.write_text(json.dumps(city,separators=(',',':'),ensure_ascii=False),encoding='utf8')
print(json.dumps({b['id']:{'parts':b['massCount'],'height':b['modelHeight']} for b in city['landmarks'][13:]}),flush=True)
