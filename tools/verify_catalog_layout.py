"""Check every generated scene against the retained city using a spatial index."""
import json
from visit_spatial import root, CityIndex, LineString, Point, unary_union
idx=CityIndex()
def module(name):return json.loads((root/'dist'/name).read_text(encoding='utf-8').split(' = ',1)[1].strip().rstrip(';'))
routes=module('walk-routes.js');trees=module('visit-landscape.js')
def clear(a,b,d):return b.is_empty or a.distance(b)>d
assert set(routes)=={b['id'] for b in idx.city['landmarks'] if b.get('massCount')}
for id,items in routes.items():
    core=unary_union([p for _,p in idx.byLandmark[id]])
    near,water,roads=idx.nearby(core.buffer(70))
    for r in items:
        line=LineString(r['points']);z=r['elevation']
        assert clear(line,idx.blockers(near,z),.34),(id,r['name'],'body collision')
        if r['support']:
            # OSM multi-polygons can retain one source ID across several disjoint parts.
            supports=[(b,p) for b,p in near if b['id']==r['support'] and b.get('lm')==id and abs(z-b['h']-.025)<.001 and p.buffer(-.34).buffer(.002).covers(line)]
            assert supports,(id,'unsupported edge/height')
            b,p=supports[0]
            assert b.get('lm')==id
            assert not b.get('mesh') and not b.get('form'),(id,'non-flat form')
            assert not b.get('roof') or b['roof']['shape']=='flat',(id,'non-flat roof')
            assert abs(z-b['h']-.025)<.001,(id,'height')
            assert p.buffer(-.34).buffer(.002).covers(line),(id,'unsupported edge')
        else:
            assert z<.1 and core.buffer(12.01).covers(line),(id,'distant ground path')
            assert clear(line,water,.34) and clear(line,roads,.34),(id,'water/road')
    for t in trees.get(id,[]):
        p=Point(t['x'],t['north']);radius=t['radius']*1.12
        assert all(p.distance(poly)>radius for _,poly in near),(id,'tree/building overlap')
        assert clear(p,water,radius) and clear(p,roads,radius),(id,'tree/water/road')
print(f"All {len(routes)} modelled stops: support heights, body clearance, near-facade ground walks and {sum(map(len,trees.values()))} tree crowns pass.")
