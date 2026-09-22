from pathlib import Path
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
import json
root=Path(__file__).parent/'osm-tiles';root.mkdir(exist_ok=True)
west,south,east,north=-.132,51.496,-.0715,51.523
for y in range(4):
 for x in range(4):
  p=root/f'{x}-{y}.osm'
  if p.exists():continue
  w=west+(east-west)*x/4;e=west+(east-west)*(x+1)/4
  s=south+(north-south)*y/4;n=south+(north-south)*(y+1)/4
  url=f'https://api.openstreetmap.org/api/0.6/map?bbox={w:.7f},{s:.7f},{e:.7f},{n:.7f}'
  with urlopen(Request(url,headers={'User-Agent':'LondonFieldAtlas/2.0'}),timeout=75) as r:raw=r.read()
  ET.fromstring(raw)
  p.write_bytes(raw)
  print(f'Tile {x+1},{y+1}: {len(raw)} bytes',flush=True)
nodes={};ways={};relations={}
for p in root.glob('*.osm'):
 doc=ET.parse(p).getroot()
 for el in doc:
  tags={t.attrib['k']:t.attrib['v'] for t in el.findall('tag')}
  if el.tag=='node':nodes[el.attrib['id']]={'lat':float(el.attrib['lat']),'lon':float(el.attrib['lon'])}
  if el.tag=='way':ways[el.attrib['id']]={'type':'way','id':int(el.attrib['id']),'tags':tags,'nodes':[n.attrib['ref'] for n in el.findall('nd')]}
  if el.tag=='relation':relations[el.attrib['id']]={'type':'relation','id':int(el.attrib['id']),'tags':tags,'members':[dict(m.attrib) for m in el.findall('member')]}
elements=[]
for w in ways.values():
 w['geometry']=[nodes.get(n) for n in w.pop('nodes')]
 if all(w['geometry']):elements.append(w)
for r in relations.values():
 for m in r['members']:
  if m['type']=='way' and m['ref'] in ways:m['geometry']=ways[m['ref']]['geometry']
 elements.append(r)
(root.parent/'london-osm.json').write_text(json.dumps({'elements':elements,'source':'OpenStreetMap API 0.6','downloaded':'2026-09-21'}))
print(f'Merged {len(nodes)} nodes, {len(ways)} ways, {len(relations)} relations',flush=True)
