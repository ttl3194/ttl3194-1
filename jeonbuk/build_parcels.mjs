// vworld_parcels.json + ../imsil/tx.tsv → parcels_section.html (단지별 지적도·건물 윤곽)
// 그 결과를 imsil.html 의 <!--parcels--> 구간에 넣고, jeonbuk_apt_map.html 도 다시 만든다(build_page.py 와 같은 처리).
// 실행: cd jeonbuk && node build_parcels.mjs
import fs from 'fs';
const J = f => new URL(f, import.meta.url);
const P = JSON.parse(fs.readFileSync(J('vworld_parcels.json')));
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

// 지번 → 실거래 단지명(tx.tsv의 name). 건물명은 브이월드 도로명주소 건물 이름
const MAP = {
  '이도리 982': '전북임실코아루더베스트', '이도리 272': '신우', '이도리 332': '임실군이도리하이젠아파트',
  '이도리 182-2': '상원상아', '이도리 385-2': '라오니아1', '이도리 212': '아도훼밀리', '이도리 183-3': '삼강맨션',
  '이도리 214': '고운라피네1단지', '관촌리 584-2': '명진마을', '관촌리 489-5': '백우맨션', '관촌리 498-6': '수클래식',
  '오수리 387-27': '세원타워', '오수리 351-8': '오수효성상가프라자', '오수리 376-2': '훼미리',
};
const GUESS = { '이도리 214': '건물명이 등록돼 있지 않음. 15층 3개 동이라 고운라피네1단지로 봄' };

const tx = fs.readFileSync(J('../imsil/tx.tsv'), 'utf8').trim().split('\n').slice(1).map(l => l.split('\t'));
const stat = {};
for (const r of tx) { const s = stat[r[2]] ??= { n: 0, sum: 0 }; s.n++; s.sum += +r[3]; }
const won = v => v >= 10000 ? (v / 10000).toFixed(1).replace(/\.0$/, '') + '억' : v.toLocaleString() + '만';

const polys = g => g.type === 'MultiPolygon' ? g.coordinates : [g.coordinates];
const pip = ([x, y], ring) => { let c = false; for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) { const [xi, yi] = ring[i], [xj, yj] = ring[j]; if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi) c = !c; } return c; };
const inG = (pt, g) => polys(g).some(p => pip(pt, p[0]) && !p.slice(1).some(h => pip(pt, h)));
const cen = g => { const r = polys(g)[0][0]; let x = 0, y = 0; r.forEach(p => { x += p[0]; y += p[1]; }); return [x / r.length, y / r.length]; };

const W = 320, H = 240, PAD = 14;
function card(p) {
  const key = p.dong.split(' ')[1] + ' ' + p.jibun, name = MAP[key], st = stat[name] || { n: 0, sum: 0 };
  const [lon0, lat0] = cen(p.geom), kx = Math.cos(lat0 * Math.PI / 180) * 111320, ky = 110540;
  const m = ([lon, lat]) => [(lon - lon0) * kx, (lat0 - lat) * ky]; // 미터, 아래쪽 +y
  const ring = p.geom.type === 'MultiPolygon' ? p.geom.coordinates.flat() : p.geom.coordinates;
  let area = 0; for (const r of polys(p.geom)) r.forEach((rr, k) => { const q = rr.map(m); let a = 0; for (let i = 0; i < q.length - 1; i++) a += q[i][0] * q[i + 1][1] - q[i + 1][0] * q[i][1]; area += (k ? -1 : 1) * Math.abs(a / 2); });
  const pts = ring.flat().map(m), xs = pts.map(q => q[0]), ys = pts.map(q => q[1]);
  let [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
  const span = Math.max(x1 - x0, (y1 - y0) * W / H, 60) * 1.45, cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
  const s = (W - 2 * PAD) / span;
  const T = q => [W / 2 + (q[0] - cx) * s, H / 2 + (q[1] - cy) * s];
  const path = g => polys(g).map(pp => pp.map(r => 'M' + r.map(c => T(m(c)).map(v => v.toFixed(1)).join(',')).join('L') + 'Z').join('')).join('');
  const inside = [], around = [];
  for (const b of p.buildings) (inG(cen(b.geom), p.geom) ? inside : around).push(b);
  const bname = [...new Set(inside.map(b => b.props.buld_nm).filter(Boolean))].join(', ') || '(건물명 미등록)';
  const out = [`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(name)} 필지와 건물 윤곽">`,
    `<clipPath id="c${p.pnu}"><rect width="${W}" height="${H}"/></clipPath><g clip-path="url(#c${p.pnu})">`];
  for (const b of around) out.push(`<path class="b-out" d="${path(b.geom)}"><title>${esc(b.props.buld_nm || '건물')} · ${b.props.gro_flo_co}층</title></path>`);
  out.push(`<path class="pcl" d="${path(p.geom)}"><title>${esc(p.props.addr)} · ${esc(p.props.jibun)}</title></path>`);
  for (const b of inside) out.push(`<path class="b-in" d="${path(b.geom)}"><title>${esc(b.props.buld_nm || '건물')} · ${b.props.gro_flo_co}층</title></path>`);
  for (const b of inside) if (+b.props.gro_flo_co > 1) { const [x, y] = T(m(cen(b.geom))); out.push(`<text class="fl" x="${x.toFixed(1)}" y="${y.toFixed(1)}">${b.props.gro_flo_co}층</text>`); }
  const sb = [10, 20, 50, 100].find(v => v * s >= 50) || 100;
  out.push(`</g><g class="sb"><path d="M${PAD},${H - 12}h${(sb * s).toFixed(1)}"/><text x="${PAD}" y="${H - 18}">${sb}m</text></g><text class="nn" x="${W - 12}" y="18">북↑</text></svg>`);
  const jiga = +p.props.jiga;
  return `<div class="pc"><h3>${esc(name)} <small>${esc(p.dong)} ${esc(p.jibun)}</small></h3>${out.join('')}
<dl><dt>거래</dt><dd>${st.n}건${st.n ? ` · 평균 ${won(Math.round(st.sum / st.n))}` : ''}</dd><dt>지목·면적</dt><dd>${esc(p.props.jibun.split(' ').pop())} · ${Math.round(area).toLocaleString()}㎡(${(area / 3.3058).toFixed(0)}평)</dd>
<dt>공시지가</dt><dd>${jiga.toLocaleString()}원/㎡ (${p.props.gosi_year}.${p.props.gosi_month})</dd><dt>건물</dt><dd>${esc(bname)} · ${inside.length}동</dd></dl>${GUESS[key] ? `<p class="gs">${esc(GUESS[key])}</p>` : ''}</div>`;
}

const cards = P.map(p => ({ p, n: (stat[MAP[p.dong.split(' ')[1] + ' ' + p.jibun]] || { n: 0 }).n })).sort((a, b) => b.n - a.n).map(x => card(x.p));
const section = `<style>
.pgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px;padding:12px}
.pc{border:1px solid var(--line);border-radius:10px;overflow:hidden;background:var(--bg)}
.pc h3{font-size:.95rem;margin:0;padding:8px 10px;border-bottom:1px solid var(--line);background:var(--panel)}
.pc h3 small{display:block;color:var(--muted);font-weight:400;font-size:.78rem}
.pc svg{background:var(--panel)}
.pcl{fill:var(--land-hi);fill-opacity:.55;stroke:var(--accent);stroke-width:2;stroke-linejoin:round}
.b-out{fill:var(--land);stroke:var(--muted);stroke-width:.6;stroke-opacity:.6}
.b-in{fill:var(--dot);fill-opacity:.85;stroke:var(--panel);stroke-width:1}
.fl{fill:var(--fg);font-size:11px;font-weight:700;text-anchor:middle;dominant-baseline:middle;paint-order:stroke;stroke:var(--panel);stroke-width:3px}
.sb path{stroke:var(--fg);stroke-width:2}.sb text,.nn{fill:var(--muted);font-size:11px}.nn{text-anchor:end}
.pc dl{display:grid;grid-template-columns:auto 1fr;gap:2px 10px;margin:0;padding:8px 10px;font-size:.8rem}
.pc dt{color:var(--muted)}.pc dd{margin:0;font-variant-numeric:tabular-nums}
.pc .gs{margin:0;padding:0 10px 8px;font-size:.75rem;color:var(--muted)}
</style>
<div class="box">
  <h2>단지별 지적도·건물 윤곽 <small>· 임실군 아파트 14곳, 거래 많은 순</small></h2>
  <div class="legend"><span><i class="sw" style="background:var(--land-hi);border:2px solid var(--accent)"></i>단지 필지(지적 경계)</span><span><i class="sw" style="background:var(--dot)"></i>필지 안 건물</span><span><i class="sw" style="background:var(--land);border:1px solid var(--muted)"></i>주변 건물</span></div>
  <div class="pgrid">${cards.join('\n')}</div>
  <div class="note">자료: 브이월드 연속지적도(LP_PA_CBND_BUBUN)·도로명주소 건물(LT_C_SPBD), 받은 날 2026-11-24. 거래는 국토교통부 실거래(2026.1~11). 면적은 지적 경계로 계산한 값이라 대장 면적과 조금 다를 수 있음. 위쪽이 북쪽.</div>
</div>`;
fs.writeFileSync(J('parcels_section.html'), section);

// imsil.html 에 넣기
let im = fs.readFileSync(J('imsil.html'), 'utf8');
const block = `<!--parcels-->${section}<!--/parcels-->`;
im = im.includes('<!--parcels-->') ? im.replace(/<!--parcels-->[\s\S]*<!--\/parcels-->/, () => block)
  : im.replace(/(\n\s*<div class="box">\s*\n\s*<h2>단지 목록)/, mm => '\n' + block + mm);
if (!im.includes('<!--parcels-->')) throw new Error('imsil.html 삽입 위치를 못 찾음');
fs.writeFileSync(J('imsil.html'), im);

// build_page.py 와 같은 처리
const enc = t => JSON.stringify(t).replace(/<\//g, '<\\/');
const rep = fs.readFileSync(J('../imsil/imsil_report.html'), 'utf8');
const wrapped = '<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>' + rep + '</body></html>';
const page = fs.readFileSync(J('map_template.html'), 'utf8')
  .replace('__SGG__', () => fs.readFileSync(J('sgg_jb.json'), 'utf8')).replace('__CX__', () => fs.readFileSync(J('cx.json'), 'utf8'))
  .replace('__IMSIL_REPORT__', () => enc(wrapped)).replace('__IMSIL__', () => enc(im));
fs.writeFileSync(J('jeonbuk_apt_map.html'), page);
console.log('section', section.length, 'imsil', im.length, 'page', page.length);
