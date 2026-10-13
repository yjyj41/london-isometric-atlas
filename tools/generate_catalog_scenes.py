"""Fit decorative activity to all retained models. No new geometry or survey claims."""
import json, math
from visit_spatial import root, CityIndex, Polygon, LineString, Point, unary_union, parts
from shapely.ops import substring
idx=CityIndex()
seed=json.loads((root/'tools/visit-scene-pilots.json').read_text(encoding='utf-8'))
allRoutes=seed['routes']; landscape=seed['trees']; review=seed['review']; exceptions=[]
placed=[t for ts in landscape.values() for t in ts]
for lm in idx.city['landmarks']:
    id=lm['id']
    if not lm.get('massCount') or id in allRoutes: continue
    records=idx.byLandmark[id]
    core=unary_union([p for b,p in records])
    near,water,roads=idx.nearby(core.buffer(70))
    ground=unary_union([idx.blockers(near,.085),water,roads])
    routes=[]
    def add(line,z,name,support=None):
        if line.length<6:return
        if line.length>140:line=substring(line,0,140)
        pts=[[round(x,3),round(n,3)] for x,n in line.coords]
        people=min(20,max(3,int(line.length/4)))
        routes.append(dict(sourceId=(support or 'facade')+'#'+str(len(routes)),points=pts,elevation=round(z+.025,3),people=people,name=name,loop=Point(pts[0]).distance(Point(pts[-1]))<.01,support=support))
        review.append(dict(landmark=id,name=name,support=support,elevation=round(z+.025,3),length=round(line.length,2),people=people,kind='model-surface' if support else 'near-facade'))
    # Only broad, flat model tops; never curved meshes, spires or roof slivers.
    # These are decorative studies, not claims of publicly accessible roof terraces.
    decks=[]
    for b,p in records:
        if b.get('form') or b.get('mesh') or (b.get('roof') and b['roof'].get('shape')!='flat'):continue
        if b['h']<2 or b['h']>85 or p.area<100:continue
        safe=p.buffer(-1.2).difference(idx.blockers(near,b['h']+.025).buffer(.65))
        for s in parts(safe,'Polygon'):
            if s.area>50 and s.buffer(-1).area>15:decks.append((s.area,b,s))
    for _,b,p in sorted(decks,key=lambda x:x[0],reverse=True)[:2]:
        add(LineString(p.exterior.coords),b['h'],'Flat model roof study',b['id'])
    # Start close to actual facades, searching slightly further only on tight sites.
    for offset in [3,5,8,12]:
        candidates=parts(core.buffer(offset,quad_segs=4).boundary.difference(ground.buffer(.7)),'LineString')
        for line in sorted(candidates,key=lambda g:g.length,reverse=True)[:3]:
            if line.length>7:add(substring(line,.5,line.length-.5),.06,'Near-building walk')
        if any(not r['support'] for r in routes):break
    if not routes:exceptions.append(dict(id=id,name=lm['name'],reason='No clear nearby ground or suitable flat model surface'))
    else:allRoutes[id]=routes
    buildingSolid=unary_union([p for _,p in near])
    walks=unary_union([LineString(r['points']).buffer(3) for r in routes if not r['support']])
    safe=core.buffer(20).difference(buildingSolid.buffer(2.3)).difference(water.buffer(2.3)).difference(roads.buffer(2.3)).difference(walks)
    minx,miny,maxx,maxy=safe.bounds if not safe.is_empty else (0,0,0,0)
    candidates=[]
    step=max(5,math.sqrt(max(1,(maxx-minx)*(maxy-miny))/16000))
    for i in range(math.ceil((maxx-minx)/step)):
        for j in range(math.ceil((maxy-miny)/step)):
            x=round(minx+i*step,3);n=round(miny+j*step,3);pt=Point(x,n)
            if safe.contains(pt):candidates.append((pt.distance(core),x,n))
    trees=[]
    limit=min(20,max(6,int(math.sqrt(core.area)/4)))
    for _,x,n in sorted(candidates):
        if any(abs(x-t['x'])<6 and abs(n-t['north'])<6 and math.hypot(x-t['x'],n-t['north'])<6 for t in placed):continue
        t=dict(x=x,north=n,height=round(4.2+(len(trees)%4)*.45,2),radius=round(1.65+(len(trees)%3)*.15,2))
        trees.append(t);placed.append(t)
        if len(trees)>=limit:break
    landscape[id]=trees
    print(id,len(routes),'routes',sum(r['people'] for r in routes),'people',len(trees),'trees',flush=True)
(root/'dist/walk-routes.js').write_text('// Decorative paths fitted to model surfaces; not surveyed/public-access walking routes. Metres.\nexport const walkRoutes = '+json.dumps(allRoutes,separators=(',',':'))+';\n',encoding='utf-8')
(root/'dist/visit-landscape.js').write_text('// Schematic planting in checked open ground; not an actual tree inventory. Metres.\nexport const visitTrees = '+json.dumps(landscape,separators=(',',':'))+';\n',encoding='utf-8')
(root/'tools/walk-route-review.json').write_text(json.dumps(review,indent=2)+'\n',encoding='utf-8')
(root/'tools/visit-scene-exceptions.json').write_text(json.dumps(exceptions,indent=2)+'\n',encoding='utf-8')
print('TOTAL',len(allRoutes),'places',sum(len(r) for r in allRoutes.values()),'routes',sum(r['people'] for rs in allRoutes.values() for r in rs),'people',sum(len(ts) for ts in landscape.values()),'trees; exceptions',exceptions)
