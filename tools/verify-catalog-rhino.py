"""Verify every available individual Rhino file against shared browser geometry."""
import json,sys,math
from pathlib import Path
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT/'python-libs'))
import rhino3dm as r
city=json.loads((ROOT/'city-full.json').read_text(encoding='utf-8'))
expected={b['id']:[math.inf,math.inf,math.inf,-math.inf,-math.inf,-math.inf] for b in city['landmarks'] if b['massCount']}
for rec,line in zip(city['buildings'],(ROOT/'meshes.ndjson').open(encoding='utf-8')):
 if not rec.get('lm'):continue
 data=json.loads(line);assert data['id']==rec['id'];bounds=expected[rec['lm']]
 for v in data['verts']:
  for axis in range(3):bounds[axis]=min(bounds[axis],v[axis]);bounds[axis+3]=max(bounds[axis+3],v[axis])
maximum=0
for b in city['landmarks']:
 if not b['massCount']:continue
 path=ROOT.parent/'dist/assets/rhino'/f"{b['id']}-rhino6.3dm"
 assert path.read_bytes()[:32].endswith(b'60');doc=r.File3dm.Read(str(path));assert doc.Settings.ModelUnitSystem==r.UnitSystem.Meters
 assert len(doc.Objects)==b['massCount'];bounds=[math.inf]*3+[-math.inf]*3
 for obj in doc.Objects:
  assert obj.Attributes.Name.startswith('LM:'+b['id']+'|')
  for v in obj.Geometry.Vertices:
   values=[v.X+b['anchor'][0],v.Y+b['anchor'][1],v.Z]
   for axis in range(3):bounds[axis]=min(bounds[axis],values[axis]);bounds[axis+3]=max(bounds[axis+3],values[axis])
 error=max(abs(x-y) for x,y in zip(bounds,expected[b['id']]))
 maximum=max(maximum,error);assert error<.01,(b['id'],error)
print(f"Verified {len(expected)} Rhino 6 models: metre units, local origins, mesh counts and browser bounds. Maximum error {maximum:.6f} m.")
