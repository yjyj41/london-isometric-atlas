"""Fetch cached OSM map extracts sequentially; retry and subdivide oversized cells."""
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import xml.etree.ElementTree as ET
import json, time
from datetime import date
ROOT=Path(__file__).resolve().parent
cache=ROOT/'osm-tiles'; cache.mkdir(exist_ok=True)
regions=[('central',(-.132,51.496,-.0715,51.523),4,4),
         ('north',(-.17,51.523,-.0715,51.56),5,3),
         ('west',(-.17,51.496,-.132,51.523),2,3)]
files=[]
def fetch(name,bounds,depth=0):
    p=cache/(name+'.osm')
    if not p.exists():
        url='https://api.openstreetmap.org/api/0.6/map?bbox='+','.join(f'{v:.7f}' for v in bounds)
        for attempt in range(4):
            try:
                with urlopen(Request(url,headers={'User-Agent':'LondonFieldAtlas/3.0 (architecture mass study)'}),timeout=90) as response:
                    raw=response.read()
                ET.fromstring(raw); p.write_bytes(raw)
                print(name,len(raw),'bytes',flush=True);break
            except HTTPError as e:
                if e.code==400 and depth<3:
                    w,s,east,n=bounds;mid=(s+n)/2
                    fetch(name+'a',(w,s,east,mid),depth+1)
                    fetch(name+'b',(w,mid,east,n),depth+1);return
                if attempt==3:raise
                time.sleep(2*(attempt+1))
            except Exception:
                if attempt==3:raise
                time.sleep(2*(attempt+1))
    files.append(p)
for prefix,(west,south,east,north),nx,ny in regions:
    for y in range(ny):
        for x in range(nx):
            name=f'{x}-{y}' if prefix=='central' else f'{prefix}-{x}-{y}'
            fetch(name,(west+(east-west)*x/nx,south+(north-south)*y/ny,
                        west+(east-west)*(x+1)/nx,south+(north-south)*(y+1)/ny))
nodes={};ways={};relations={}
for p in files:
    for _,el in ET.iterparse(p,events=('end',)):
        if el.tag not in ['node','way','relation']:continue
        tags={t.attrib['k']:t.attrib['v'] for t in el.findall('tag')}
        if el.tag=='node':nodes[el.attrib['id']]={'lat':float(el.attrib['lat']),'lon':float(el.attrib['lon'])}
        if el.tag=='way':ways[el.attrib['id']]={'type':'way','id':int(el.attrib['id']),'tags':tags,'nodes':[n.attrib['ref'] for n in el.findall('nd')]}
        if el.tag=='relation':relations[el.attrib['id']]={'type':'relation','id':int(el.attrib['id']),'tags':tags,'members':[dict(m.attrib) for m in el.findall('member')]}
        el.clear()
elements=[]
for w in ways.values():
    w['geometry']=[nodes.get(n) for n in w.pop('nodes')]
    if all(w['geometry']):elements.append(w)
for r in relations.values():
    for m in r['members']:
        if m['type']=='way' and m['ref'] in ways:m['geometry']=ways[m['ref']]['geometry']
    elements.append(r)
(ROOT/'london-osm.json').write_text(json.dumps({'elements':elements,'source':'OpenStreetMap API 0.6','downloaded':str(date.today()),'bbox':[-.17,51.496,-.0715,51.56]}),encoding='utf-8')
print('Merged',len(nodes),'nodes,',len(ways),'ways,',len(relations),'relations',flush=True)
