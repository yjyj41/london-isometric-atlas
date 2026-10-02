"""Export eight city regions at the shared origin plus local landmark models, Rhino 6."""
import sys,json,pathlib,zipfile,shutil,math
ROOT=pathlib.Path(__file__).resolve().parent;project=ROOT.parent
sys.path.insert(0,str(ROOT/'python-libs'))
import rhino3dm as r
city=json.loads((ROOT/'city-full.json').read_text(encoding='utf-8'))
out=project/'dist/assets/rhino';out.mkdir(exist_ok=True)
names={'southwest':'Southwest · Battersea / Westminster','southcentral':'South Central · South Bank / Borough','southeast':'Southeast · Bermondsey / Peckham','greenwich':'Greenwich · Canary Wharf / Greenwich','northwest':'Northwest · Isokon / Belsize Park','northcentral':'North Central · Islington / Clerkenwell','northeast':'Northeast · Hackney / Stepney','bow':'Bow · Bow / Old Ford'}
core=[-4445,-4450,8090,5570]
if city.get('coreGeographicBounds'):
 from pyproj import Transformer
 tr=Transformer.from_crs(4326,city['origin']['crs'],always_xy=True)
 west,south,east,north=city['coreGeographicBounds'];p=[tr.transform(x,y) for x,y in [(west,south),(east,south),(east,north),(west,north)]]
 core=[min(q[0] for q in p),min(q[1] for q in p),max(q[0] for q in p),max(q[1] for q in p)]
def region_of(rec):
 ring=rec['r'][0];x=sum(p[0] for p in ring)/len(ring);y=sum(p[1] for p in ring)/len(ring)
 if not(core[0]<=x<=core[2] and core[1]<=y<=core[3]):return f'outer-{math.floor(x/5000)}-{math.floor(y/5000)}'
 column=sum(x>=v for v in [-750,2250,5250])
 return (['southwest','southcentral','southeast','greenwich'] if y<1000 else ['northwest','northcentral','northeast','bow'])[column]
outer={region_of(rec) for rec in city['buildings'] if region_of(rec).startswith('outer-')}
for key in sorted(outer):
 sample=next(rec for rec in city['buildings'] if region_of(rec)==key);xy=sample['r'][0][0]
 nearby=min(city['landmarks'],key=lambda b:math.dist(xy,b['anchor']))
 names[key]='Outer London · near '+nearby['name']
files={k:r.File3dm() for k in list(names)+[b['id'] for b in city['landmarks'] if b['massCount']]}
anchors={b['id']:b['anchor'] for b in city['landmarks']}
for f in files.values():
 f.Settings.ModelUnitSystem=r.UnitSystem.Meters;f.Settings.ModelAbsoluteTolerance=.01
for i,(rec,line) in enumerate(zip(city['buildings'],open(ROOT/'meshes.ndjson',encoding='utf-8'))):
 data=json.loads(line);assert data['id']==rec['id']
 region=region_of(rec)
 for key in [region]+([rec['lm']] if rec.get('lm') else []):
  f=files[key];anchor=anchors.get(key,[0,0]);mesh=r.Mesh()
  for x,y,z in data['verts']:mesh.Vertices.Add(x-anchor[0],y-anchor[1],z)
  for n in range(0,len(data['verts']),3):mesh.Faces.AddFace(n,n+1,n+2)
  mesh.Vertices.CombineIdentical(True,True);mesh.Normals.ComputeNormals();mesh.Compact()
  attr=r.ObjectAttributes();attr.Name=('LM:'+rec['lm']+'|' if rec.get('lm') else 'CTX|')+rec['id']
  attr.SetUserString('source','OpenStreetMap ODbL 1.0');attr.SetUserString('height_confidence',rec['c'])
  attr.SetUserString('coordinates','X east, Y north, Z up; metres');f.Objects.AddMesh(mesh,attr)
 if i%10000==0:print('Rhino',i,'/',len(city['buildings']),flush=True)
downloads=[]
for key,f in files.items():
 path=out/(key+'-rhino6.3dm');assert f.Write(str(path),6)
 assert path.read_bytes()[:32].endswith(b'60')
 check=r.File3dm.Read(str(path));assert len(check.Objects)==len(f.Objects)
 assert check.Settings.ModelUnitSystem==r.UnitSystem.Meters
 if key in names:
  archive=out/(key+'-rhino6.zip')
  with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:z.write(path,path.name)
  assert archive.stat().st_size<25*1024*1024,'Region too large for static hosting'
  downloads.append({'id':key,'name':names[key],'url':'./assets/rhino/'+archive.name,'masses':len(f.Objects),'bytes':archive.stat().st_size,'modelBytes':path.stat().st_size})
  path.unlink()
 elif not key.startswith('catalog-'):shutil.copy2(path,out/(key+'.3dm'))
 print(key,len(f.Objects),flush=True)
manifest_path=project/'dist/assets/city.json';manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
manifest['rhinoDownloads']=downloads
manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
with zipfile.ZipFile(project/'dist/assets/city-data.zip','w',zipfile.ZIP_DEFLATED) as z:z.write(ROOT/'city-full.json','city.json')
print(json.dumps(downloads,ensure_ascii=False),flush=True)
