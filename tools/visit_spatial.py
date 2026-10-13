"""Shared metric collision index for decorative scenes; never changes the city."""
import json, sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root/'tools/python-libs'))
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union
from shapely.strtree import STRtree

def parts(g, kind):
    if g.is_empty: return []
    if g.geom_type == kind: return [g]
    return [p for child in getattr(g, 'geoms', []) for p in parts(child, kind)]

class CityIndex:
    def __init__(self):
        self.city=json.loads((root/'tools/city-full.json').read_text(encoding='utf-8'))
        self.records=[b for b in self.city['buildings'] if b.get('r')]
        self.polygons=[Polygon(b['r'][0],b['r'][1:]).buffer(0) for b in self.records]
        self.index=STRtree(self.polygons)
        self.water=[Polygon(w[0],w[1:]).buffer(0) for w in self.city['water']]
        self.waterIndex=STRtree(self.water)
        self.roads=[LineString(r['p']).buffer(min(30,r['w'])/2+.6) for r in self.city['roads'] if not r.get('bridge')]
        self.roadIndex=STRtree(self.roads)
        self.byLandmark={}
        for b,p in zip(self.records,self.polygons):
            if b.get('lm'): self.byLandmark.setdefault(b['lm'],[]).append((b,p))
    def nearby(self, area):
        near=[(self.records[i],self.polygons[i]) for i in self.index.query(area,predicate='intersects')]
        water=unary_union([self.water[i] for i in self.waterIndex.query(area,predicate='intersects')])
        roads=unary_union([self.roads[i] for i in self.roadIndex.query(area,predicate='intersects')])
        return near,water,roads
    @staticmethod
    def blockers(near,z):
        return unary_union([p for b,p in near if b['h']>z+.04 and b.get('z',0)<z+1.85])
