"""Reference-informed details. Retain OSM site geometry, disclose all schematic dimensions."""
import math
from shapely.geometry import Polygon,box,Point,LineString
from shapely.affinity import affine_transform

def enrich(city,volume,raw):
 notes={};city['buildings']=[r for r in city['buildings'] if not r['id'].startswith('detail/hayward/')];records=city['buildings']
 def polys(g):
  if g.is_empty:return []
  if g.geom_type=='Polygon':return [g]
  return [p for q in getattr(g,'geoms',[]) for p in polys(q)]
 def rings(p):return [[[round(x,3),round(y,3)] for x,y in ring.coords][:-1] for ring in [p.exterior,*p.interiors]]
 def frame(p):
  corners=list(p.minimum_rotated_rectangle.exterior.coords);a,b=max(zip(corners,corners[1:]),key=lambda ab:math.dist(*ab));d=math.dist(a,b);u=((b[0]-a[0])/d,(b[1]-a[1])/d);v=(-u[1],u[0]);return u,v,affine_transform(p,[*u,*v,0,0])
 def curved(p,fn,base,nx=32,ny=6):
  u,v,q=frame(p);xmin,ymin,xmax,ymax=q.bounds;mesh=[]
  for i in range(nx):
   for j in range(ny):
    piece=q.intersection(box(xmin+(xmax-xmin)*i/nx,ymin+(ymax-ymin)*j/ny,xmin+(xmax-xmin)*(i+1)/nx,ymin+(ymax-ymin)*(j+1)/ny))
    world=affine_transform(piece,[u[0],v[0],u[1],v[1],0,0]);mesh+=volume(world,base,fn)
  return mesh
 # Isokon: local axes aligned with the mapped main wing; east/front galleries face Lawn Road.
 from pyproj import Transformer
 tr=Transformer.from_crs('EPSG:4326',city['origin']['crs'],always_xy=True)
 source=next(e for e in raw['elements'] if e['type']=='way' and e['id']==319837891)
 p=Polygon([tr.transform(v['lon'],v['lat']) for v in source['geometry']]).simplify(.07,preserve_topology=True)
 p=Polygon([[round(x,2),round(y,2)] for x,y in p.exterior.coords]);old={'id':'way/319837891'};cx,cy=p.centroid.coords[0];a=math.radians(22);co,si=math.cos(a),math.sin(a)
 def world(q):return affine_transform(q,[co,-si,si,co,cx,cy])
 local=affine_transform(p,[co,si,-si,co,-cx*co-cy*si,cx*si-cy*co]);new=[]
 def add(name,q,z,h,mesh=None):
  for i,part in enumerate(polys(world(q))):
   rec={'id':f'detail/isokon/{name}-{i}','name':name,'lm':'isokon','r':rings(part),'z':z,'h':h,'c':'assumed','sourceId':old['id']}
   if mesh:rec['mesh']=mesh
   new.append(rec)
 add('main-wing',box(-6.05,-26.1,-1.1,17.15).intersection(local),0,11.2)
 # Recessed front bays: solid infill is set back from projecting access galleries.
 for level in range(4):
  z=level*2.8
  add(f'front-sill-{level}',box(-1.1,-25.6,-.7,16.5),z,z+.9)
  add(f'front-lintel-{level}',box(-1.1,-25.6,-.7,16.5),z+2.35,z+2.8)
  for bay in range(11):
   y=-25.6+bay*4.1;add(f'front-pier-{level}-{bay}',box(-1.1,y,-.7,y+.25),z+.9,z+2.35)
 for level in range(1,4):
  z=level*2.8
  add(f'gallery-slab-{level}',box(-.8,-23,1.45,16.9),z,z+.19)
  add(f'gallery-parapet-{level}',box(1.24,-23,1.45,16.9),z+.19,z+1.17)
  add(f'gallery-end-{level}',box(-.8,-23,1.45,-22.79),z+.19,z+1.17)
  # Diagonal external stair flights at the south end, with solid sloping balustrades.
  z0=(level-1)*2.8
  def rise(x,y):
   yy=-(x-cx)*si+(y-cy)*co
   return z0+2.8*(yy+27)/6.5
  q=box(-.6,-27,1.0,-20.5);w=world(q)
  add(f'external-stair-{level}',q,z0, z+.19,volume(w,lambda x,y:rise(x,y),lambda x,y:rise(x,y)+.19))
  q=box(1,-27,1.2,-20.5);w=world(q)
  add(f'stair-balustrade-{level}',q,z0,z+1.12,volume(w,lambda x,y:rise(x,y)+.15,lambda x,y:rise(x,y)+1.12))
 # Small projecting private balconies on the rear, distinct from the long access gallery.
 for level in range(1,4):
  for bay,y in enumerate([-23,-17,10]):
   z=level*2.8;add(f'rear-balcony-{level}-{bay}',box(-7.35,y,-5.85,y+3),z,z+.18)
   add(f'rear-parapet-{level}-{bay}',box(-7.35,y,-7.15,y+3),z+.18,z+1.08)
 add('roof-terrace-slab',box(-6.05,-26.1,1.4,17.1).intersection(local),11.2,11.45)
 add('roof-terrace-parapet',box(1.18,-23,1.4,16.9),11.45,12.25)
 add('penthouse',box(-5.85,1.5,-.4,15.6),11.45,14.05)
 add('penthouse-roof',box(-6.05,1.2,-.15,15.9),14.05,14.25)
 # Attached former garage, now the Isokon Gallery, sits below the residential wing.
 garage=local.intersection(box(1.3,1.7,11,21));add('gallery-annex',garage,0,3.0);add('gallery-annex-roof',garage,3,3.2)
 tower=box(-.5,14,3.1,19.6).buffer(.55,quad_segs=5).intersection(local)
 add('north-stair-tower',tower,0,12.7)
 add('entrance-canopy',box(1.3,13.6,5,16.1).intersection(local),2.65,2.85)
 city['buildings']=[r for r in records if r.get('lm')!='isokon']+new;records=city['buildings']
 notes['isokon']='실제 OSM 위치·방향을 유지하고 4개 층, 연속 갤러리·난간, 남측 외부 계단, 후면 발코니, 낮은 갤러리 별동과 옥상 펜트하우스를 구체화했습니다. 층고 2.8 m와 세부 치수·창호 간격은 사진 및 문화재 기록에 기반한 근사이며 실측 모델은 아닙니다.'
 for r in list(records):
  lm=r.get('lm');p=Polygon(r['r'][0],r['r'][1:])
  if lm=='aquatics':
   u,v,q=frame(p);xmin,ymin,xmax,ymax=q.bounds
   def top(x,y):
    t=(x*u[0]+y*u[1]-xmin)/(xmax-xmin);s=2*(x*v[0]+y*v[1]-ymin)/(ymax-ymin)-1
    return 10+35*max(0,math.sin(math.pi*t))**1.15*(1-.22*s*s)
   r['mesh']=curved(p,top,lambda x,y:top(x,y)-1.4)+curved(p.buffer(-6),lambda x,y:top(x,y)-1.4,0,nx=24,ny=4)
   r['h']=45;r['c']='assumed'
  if lm=='coaldrops':
   # The mapped curves already describe the roof's extended outline at the meeting point.
   u,v,q=frame(p);xmin,ymin,xmax,ymax=q.bounds
   def top(x,y):return 12+10*math.exp(-((x+1415.5)**2+(y-2930)**2)/(2*22**2))
   r['mesh']=curved(p,top,lambda x,y:top(x,y)-1.1,nx=40,ny=3)
   # Restore the narrow original warehouse below the lifted canopy, keeping the yard open.
   edge=max(zip(list(p.exterior.coords),list(p.exterior.coords)[1:]),key=lambda ab:math.dist(*ab))
   core=p.intersection(LineString(edge).buffer(14.5,cap_style=2))
   r['mesh']+=volume(core,0,11)
   r['h']=22;r['c']='assumed'
  if lm=='britishlibrary':
   u,v,q=frame(p);xmin,ymin,xmax,ymax=q.bounds
   # Stepped roof volumes follow the actual footprint; fine roof divisions remain schematic.
   base=volume(p,0,16);mesh=base
   for lo,hi,h in [(.12,.4,6),(.46,.66,9),(.71,.88,5)]:
    block=q.buffer(-2).intersection(box(xmin+(xmax-xmin)*lo,ymin,xmin+(xmax-xmin)*hi,ymax))
    if block.is_empty:continue
    yy0,yy1=block.bounds[1],block.bounds[3]
    worldpoly=affine_transform(block,[u[0],v[0],u[1],v[1],0,0])
    mesh+=curved(worldpoly,lambda x,y:16+h*(1-abs(2*(x*v[0]+y*v[1]-yy0)/(yy1-yy0)-1)),16,nx=8,ny=8)
   r['mesh']=mesh;r['h']=25;r['c']='assumed'
  if lm=='hayward':
   # The characteristic repeated skylights sit on the mapped gallery, never on nearby context.
   u,v,q=frame(p);xmin,ymin,xmax,ymax=q.bounds;centres=[]
   for i in range(int((xmax-xmin)/3)):
    for j in range(int((ymax-ymin)/3)):
     x,y=xmin+1.5+i*3,ymin+1.5+j*3;cell=box(x-1.25,y-1.25,x+1.25,y+1.25)
     if q.covers(cell):centres.append((x,y))
   centres=sorted(centres,key=lambda xy:Point(*xy).distance(q.centroid))[:66]
   for i,(x,y) in enumerate(centres):
    poly=affine_transform(box(x-1.25,y-1.25,x+1.25,y+1.25),[u[0],v[0],u[1],v[1],0,0])
    city['buildings'].append({'id':f'detail/hayward/skylight-{i}','name':'Pyramid rooflight','lm':lm,'r':rings(poly),'z':12,'h':14,'c':'assumed','roof':{'shape':'pyramidal','h':2},'sourceId':r['id']})
 notes.update(nationaltheatre='실제 OSM의 21개 건물 부재를 이용해 테라스·무대 타워의 높이 차이를 유지했습니다. 미기재 높이는 추정입니다.',festivalhall='실제 OSM 외곽 평면과 높은 중앙 공연장 매스를 유지했습니다. 높이는 OSM 층수에 기반한 추정입니다.',hayward='실제 OSM 평면 위에 특징적인 피라미드 채광창을 추가했습니다. 채광창의 위치·크기와 높이는 참고 사진에 기반한 개략 배치입니다.',britishlibrary='실제 OSM 평면 위에 높이가 다른 지붕 매스를 추가했습니다. 지붕 분할과 높이는 건축 사진을 참고한 개략 모델입니다.',coaldrops='실제 OSM의 두 창고와 휘어진 지붕 윤곽을 사용했습니다. 들어 올린 연결 지붕과 아래 열린 공간을 표현했으며 단면·높이는 근사입니다.',aquatics='실제 OSM의 레거시 모드 평면 위에 이중 곡률의 물결 지붕과 처마를 표현했습니다. 45 m 최고 높이를 기준으로 단면을 근사했으며 구조·실내는 생략했습니다.')
 for b in city['landmarks']:
  if b['id'] in notes:
   b['modelNote']=notes[b['id']];b['modelSource']='OSM geographic footprint with reference-informed approximate architectural details'
   b['modelReferences']=[b['source']]
   if b['id']=='isokon':b['modelReferences']+=['https://historicengland.org.uk/listing/the-list/list-entry/1379280','https://docomomo.com/wp-content/uploads/2022/04/Isokon-information-sheet.pdf']
