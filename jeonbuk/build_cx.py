import json, re, math
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
h=json.load(open('hjd.geojson'))
jb=[f for f in h['features'] if f['properties']['sido']=='52' or '전북' in f['properties']['sidonm']]
# group by sgg name
from collections import defaultdict
sggpolys=defaultdict(list); dongs=defaultdict(list)
for f in jb:
    p=f['properties']; g=shape(f['geometry'])
    sg=p['sggnm']; sggpolys[sg].append(g)
    nm=p['adm_nm'].split()[-1]
    dongs[sg].append((nm,g))
def key(sg): return sg.replace('전주시','전주시 ') if sg.startswith('전주시') else sg
# complexes
rows=[]
import csv
def load(fn,ref):
    with open(fn) as fh:
        r=csv.DictReader(fh,delimiter='\t')
        for x in r: x['ref']=ref; rows.append(x)
load('/home/user/ttl3194-1/jeonbuk/complexes.tsv',False)
load('/home/user/ttl3194-1/jeonbuk/complexes5.tsv',True)
unmatched=set()
def find(sg,d):
    sgk=sg.replace(' ','')
    cand=dongs[sgk]
    if ' ' in d:
        t=d.split()[0]
        m=[g for n,g in cand if n==t]
        if m: return m
    base=re.sub(r'\d+가$','',d)
    stem=base[:-1] if base.endswith('동') else base
    m=[g for n,g in cand if n==base or re.fullmatch(re.escape(stem)+r'\d*동',n) or re.fullmatch(re.escape(stem)+r'\d+가동',n)]
    if m: return m
    m=[g for n,g in cand if stem in n or n.replace('동','') in stem]
    if m: return m
    return None
MAN={('전주시 덕진구','장동'):'혁신동',('전주시 덕진구','중동'):'혁신동',('전주시 덕진구','만성동'):'혁신동',('전주시 덕진구','반월동'):'조촌동',('전주시 완산구','태평동'):'중앙동',('군산시','미장동'):'수송동',('군산시','지곡동'):'수송동',('군산시','미룡동'):'미성동',('군산시','산북동'):'미성동',('군산시','오식도동'):'소룡동',('군산시','대명동'):'월명동',('익산시','부송동'):'어양동',('남원시','조산동'):'향교동',('남원시','내척동'):'향교동',('남원시','신정동'):'도통동',('남원시','월락동'):'도통동',('남원시','고죽동'):'도통동',('김제시','옥산동'):'교월동',('김제시','서암동'):'요촌동'}
LOW={'김제시','부안군','고창군','순창군','남원시','임실군','장수군','진안군','무주군'}
out=[]; cnt=defaultdict(int); seen=set()
for x in rows:
    kk=(x['sigungu'],x['name'])
    if kk in seen: continue
    seen.add(kk)
    sg=x['sigungu']; d=x['dong']
    m=find(sg,d)
    if (sg,d) in MAN: m=[g for n,g in dongs[sg.replace(' ','')] if n==MAN[(sg,d)]]
    if not m:
        unmatched.add((sg,d)); c=unary_union(sggpolys[sg.replace(' ','')]).representative_point()
    else:
        c=unary_union(m).representative_point()
    k=(sg,d); i=cnt[k]; cnt[k]+=1
    a=i*2.4; r=0.0018*math.sqrt(i)
    out.append({'sg':sg,'dong':d,'name':x['name'],'tx':int(x['tx']),'year':int(x['year']) if x['year'] else None,
      'hh':int(x['households']) if x['households'] else None,'avg':int(x['avg_price']),'lo':1 if x['sigungu'] in LOW else 0,
      'lon':round(c.x+r*math.cos(a),5),'lat':round(c.y+r*math.sin(a),5)})
print('unmatched',unmatched)
json.dump(out,open('/home/user/ttl3194-1/jeonbuk/cx.json','w'),ensure_ascii=False,separators=(',',':'))
import os; print(len(out))
