"""Approximate architectural profiles on mapped station and courtyard footprints."""
import math
from shapely.geometry import Polygon,Point,box
from shapely.affinity import affine_transform

def enrich_stations(city,volume,raw):
 def frame(p):
  pts=list(p.minimum_rotated_rectangle.exterior.coords);a,b=max(zip(pts,pts[1:]),key=lambda ab:math.dist(*ab));d=math.dist(a,b);u=((b[0]-a[0])/d,(b[1]-a[1])/d);v=(-u[1],u[0]);return u,v,affine_transform(p,[*u,*v,0,0])
 def sampled(p,top,base=0,nx=24,ny=20):
  if p.is_empty:return []
  xmin,ymin,xmax,ymax=p.bounds;out=[]
  for i in range(nx):
   for j in range(ny):
    q=p.intersection(box(xmin+(xmax-xmin)*i/nx,ymin+(ymax-ymin)*j/ny,xmin+(xmax-xmin)*(i+1)/nx,ymin+(ymax-ymin)*(j+1)/ny))
    if not q.is_empty:out+=volume(q,base,top)
  return out
 def rings(p):return [[[round(x,3),round(y,3)] for x,y in ring.coords][:-1] for ring in [p.exterior,*p.interiors]]
 city['buildings']=[r for r in city['buildings'] if not r['id'].startswith('detail/stpancras/')]
 extra=[]
 for r in city['buildings']:
  lm=r.get('lm')
  if lm not in ['stpancras','kingscross','somerset']:continue
  p=Polygon(r['r'][0],r['r'][1:])
  if lm=='stpancras' and r['id']=='way/4256246':
   # Historic shed south of the modern extension, split at a disclosed approximate seam.
   historic=p.intersection(box(-2000,2000,-1000,2450));modern=p.difference(historic)
   u,v,q=frame(historic);lo,hi=q.bounds[1],q.bounds[3]
   def arch(x,y):return 18+12.5*math.sqrt(max(0,1-(2*(x*v[0]+y*v[1]-lo)/(hi-lo)-1)**2))
   r['mesh']=sampled(historic,arch)+volume(modern,0,23);r['h']=30.5
  if lm=='stpancras' and r['id']=='way/15694166':
   r['mesh']=volume(p,0,26)+sampled(p,lambda x,y:26+min(8,p.boundary.distance(Point(x,y))/1.1),26);r['h']=34;r['c']='assumed'
   # The listed clock tower is at the southeast corner of the hotel.
   x,y=max(p.exterior.coords,key=lambda xy:xy[0]-xy[1]);cx,cy=p.centroid.coords[0];d=math.hypot(cx-x,cy-y);x+=(cx-x)*6/d;y+=(cy-y)*6/d
   q=p.intersection(box(x-6,y-6,x+6,y+6))
   if q.geom_type=='Polygon' and q.area>10:
    extra.append({'id':'detail/stpancras/clock-tower','name':'Approximate clock tower','lm':lm,'r':rings(q),'z':26,'h':70,'c':'assumed','roof':{'shape':'pyramidal','h':12},'sourceId':r['id']})
  if lm=='kingscross' and p.area>10000:
   u,v,q=frame(p);lo,hi=q.bounds[1],q.bounds[3]
   def twin(x,y):
    t=(x*v[0]+y*v[1]-lo)/(hi-lo)
    return 12+12*abs(math.sin(2*math.pi*t))
   r['mesh']=sampled(p,twin,nx=30,ny=30);r['h']=24;r['c']='assumed'
  if lm=='somerset':
   r['mesh']=volume(p,0,22)+sampled(p,lambda x,y:22+min(3,p.boundary.distance(Point(x,y))/.9),22,nx=32,ny=32);r['h']=25;r['c']='assumed'
 city['buildings']+=extra
