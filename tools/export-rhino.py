import sys,json,pathlib
sys.path.insert(0,str(pathlib.Path('tools/python-libs').resolve()))
import rhino3dm as r
city=json.loads(pathlib.Path('dist/assets/city.json').read_text(encoding='utf-8'))
out=pathlib.Path('dist/assets/rhino');out.mkdir(exist_ok=True)
files={k:r.File3dm() for k in ['city']+[b['id'] for b in city['landmarks']]}
anchors={b['id']:b['anchor'] for b in city['landmarks']}
for f in files.values():
 f.Settings.ModelUnitSystem=r.UnitSystem.Meters
 f.Settings.ModelAbsoluteTolerance=.01
for rec,line in zip(city['buildings'],open('tools/meshes.ndjson')):
 data=json.loads(line)
 assert data['id']==rec['id']
 for key in ['city']+([rec['lm']] if rec.get('lm') else []):
  f=files[key];anchor=anchors[key] if key!='city' else [0,0]
  mesh=r.Mesh()
  for x,y,z in data['verts']:mesh.Vertices.Add(x-anchor[0],y-anchor[1],z)
  for i in range(0,len(data['verts']),3):mesh.Faces.AddFace(i,i+1,i+2)
  mesh.Vertices.CombineIdentical(True,True);mesh.Normals.ComputeNormals();mesh.Compact()
  attr=r.ObjectAttributes();attr.Name=('LM:'+rec['lm']+'|' if rec.get('lm') else 'CTX|')+rec['id']
  attr.SetUserString('source','OpenStreetMap ODbL 1.0');attr.SetUserString('height_confidence',rec['c'])
  attr.SetUserString('coordinates','X east, Y north, Z up; metres')
  # Mesh geometry is intentional: matches the browser mass exactly and remains editable in Rhino.
  f.Objects.AddMesh(mesh,attr)
for key,f in files.items():
 path=out/('london-mass-city-rhino6.3dm' if key=='city' else key+'-rhino6.3dm')
 assert f.Write(str(path),6)
 check=r.File3dm.Read(str(path));assert len(check.Objects)==len(f.Objects)
 assert path.read_bytes()[:32].endswith(b'60'),path.read_bytes()[:32]
 assert check.Settings.ModelUnitSystem==r.UnitSystem.Meters
 for before,after in zip(f.Objects,check.Objects):
  assert before.Attributes.Name==after.Attributes.Name
  assert len(before.Geometry.Vertices)==len(after.Geometry.Vertices)
  assert len(before.Geometry.Faces)==len(after.Geometry.Faces)
 print(key,len(f.Objects),path.stat().st_size)

# Keep each hosted asset below static-hosting size limits.
import zipfile,shutil
citypath=out/'london-mass-city-rhino6.3dm'
with zipfile.ZipFile(out/'london-mass-city-rhino6.zip','w',zipfile.ZIP_DEFLATED) as z:z.write(citypath,citypath.name)
citypath.unlink()
shutil.copy2(out/'london-mass-city-rhino6.zip',out/'london-mass-city.zip')
for b in city['landmarks']:shutil.copy2(out/(b['id']+'-rhino6.3dm'),out/(b['id']+'.3dm'))
