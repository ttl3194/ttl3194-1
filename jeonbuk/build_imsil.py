import json, math, html
J='/home/user/ttl3194-1/jeonbuk/'
d=json.load(open(J+'dong_jb.json')); F=[x for x in d['features'] if x['properties']['sg']=='임실군']
CX=sorted([x for x in json.load(open(J+'cx.json')) if x['sg']=='임실군'],key=lambda x:-x['tx'])
from shapely.geometry import shape, Point
S=[(f['properties']['n'],shape(f['geometry'])) for f in F]
for c in CX: c['in']=[n for n,g in S if g.contains(Point(c['lon'],c['lat']))]
cnt={n:sum(1 for c in CX if n in c['in']) for n,_ in S}
lat0=35.6; kx=math.cos(math.radians(lat0))
def rings(g):
    if g.geom_type=='Polygon': return [g.exterior]+list(g.interiors)
    return [r for p in g.geoms for r in [p.exterior]+list(p.interiors)]
lons=[c['lon'] for c in CX]; lats=[c['lat'] for c in CX]
def render(bbox,W,H,pad,label_size,dotr,zoom=False):
    x0,y0,x1,y1=bbox
    sx=(W-2*pad)/((x1-x0)*kx); sy=(H-2*pad)/(y1-y0); s=min(sx,sy)
    ox=pad+((W-2*pad)-(x1-x0)*kx*s)/2; oy=pad+((H-2*pad)-(y1-y0)*s)/2
    P=lambda lon,lat:(ox+(lon-x0)*kx*s, oy+(y1-lat)*s)
    out=[f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="임실군 읍면 지도">']
    for n,g in S:
        dd=''.join('M'+'L'.join('%.1f,%.1f'%P(*c) for c in r.coords)+'Z' for r in rings(g))
        cls='myeon has' if cnt[n] else 'myeon'
        out.append(f'<path class="{cls}" d="{dd}"><title>{n}{" · 단지 "+str(cnt[n])+"곳" if cnt[n] else ""}</title></path>')
    for n,g in S:
        p=g.representative_point(); x,y=P(p.x,p.y)
        if zoom and (n=='임실읍' or not (x0<p.x<x1 and y0<p.y<y1)): continue
        if cnt[n] and not zoom: y-=22
        t=f'{n} {cnt[n]}' if cnt[n] else n
        out.append(f'<text class="lbl{" has" if cnt[n] else ""}" x="{x:.1f}" y="{y:.1f}" font-size="{label_size}">{t}</text>')
    for i,c in enumerate(CX):
        x,y=P(c['lon'],c['lat'])
        if zoom:
            cx_,cy_=P(sum(lons)/len(lons),sum(lats)/len(lats)); a=math.radians(-90+120*(i-1)); x,y=(cx_,cy_) if i==0 else (cx_+150*math.cos(a),cy_+120*math.sin(a))
        r=max(dotr*0.45, dotr*math.sqrt(c['tx']/30))
        tip=f"{c['name']} · {c['dong']} · 2026년 매매 {c['tx']}건 · {c['year']}년 준공 · {c['hh']}세대"
        out.append(f'<circle class="dot" cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}"><title>{html.escape(tip)}</title></circle>')
        if zoom:
            out.append(f'<text class="num" x="{x:.1f}" y="{y+4:.1f}" font-size="{dotr*0.7:.0f}">{i+1}</text>')
            out.append(f'<text class="lbl" x="{x:.1f}" y="{y+r+14:.1f}" font-size="13">{html.escape(c["name"])} {c["tx"]}건</text>')
    out.append('</svg>'); return '\n'.join(out)
from shapely.ops import unary_union
allb=unary_union([g for _,g in S]).bounds
full=render(allb,600,560,20,12,14)
lons=[c['lon'] for c in CX]; lats=[c['lat'] for c in CX]; m=0.015
zb=(min(lons)-m,min(lats)-m,max(lons)+m,max(lats)+m)
zoom=render(zb,600,560,20,14,22,True)
def won(v): return (f"{v/10000:.1f}".rstrip('0').rstrip('.')+'억') if v>=10000 else f"{v:,}만"
rows=''.join(f'<tr><td class="n">{i+1}</td><td>{c["name"]}</td><td>{c["dong"]}</td><td class="n">{c["tx"]}</td><td class="n">{c["year"]}</td><td class="n">{c["hh"]}</td><td class="n">{won(c["avg"])}</td></tr>' for i,c in enumerate(CX))
t=open('/home/user/ttl3194-1/jeonbuk/imsil_static_template.html').read()
t=t.replace('__FULL__',full).replace('__ZOOM__',zoom).replace('__ROWS__',rows)
open(J+'imsil.html','w').write(t); print(len(t))
