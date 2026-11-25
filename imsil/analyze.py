"""임실군 아파트 2026년 매매 실거래 분석 → data.json
입력: tx.tsv (국토부 아파트 매매 실거래, AptInfo get_apt_price, 법정동코드 52750)
"""
import csv, json, statistics as st
from collections import defaultdict

PY = 3.3058
R = list(csv.DictReader(open('tx.tsv', encoding='utf-8'), delimiter='\t'))
for r in R:
    r['price'] = int(r['price']); r['area'] = float(r['area']); r['floor'] = int(r['floor'])
    r['build'] = int(r['build']); r['m'] = int(r['ym'][4:])
    r['pp'] = r['price'] / r['area'] * PY          # 전용 3.3㎡(평)당 만원

def area_band(a):
    if a < 55: return 'A'
    if a < 62.5: return 'B'
    if a < 70: return 'C'
    return 'D'
AREA = {'A': '소형 전용 50㎡ 내외 (분양 약 20평형)', 'B': '전용 57~62㎡ (분양 약 24평형)',
        'C': '전용 63~70㎡ (분양 약 26~27평형)', 'D': '중형 전용 73~85㎡ (분양 약 30~34평형)'}
def floor_band(f):
    return 'L' if f <= 3 else ('M' if f <= 9 else 'H')
FLOOR = {'L': '저층 (1~3층)', 'M': '중층 (4~9층)', 'H': '고층 (10층 이상)'}
for r in R:
    r['ab'] = area_band(r['area']); r['fb'] = floor_band(r['floor']); r['q'] = (r['m'] - 1) // 3 + 1
    r['grp'] = f"{r['name']}|{round(r['area'])}"

def avg(v): return round(st.mean(v)) if v else None

def factors(prev, cur, label_prev, label_cur):
    """두 표본(prev, cur)의 평당가 차이를 만든 요인을 규칙 기반으로 분해"""
    out = []
    np_, nc = len(prev), len(cur)
    if min(np_, nc) <= 2:
        out.append(f"표본이 적음({label_prev} {np_}건 · {label_cur} {nc}건) — 거래 1~2건의 개별 사정이 평균을 크게 움직임")
    sh = lambda s: round(100 * sum(1 for r in s if r['build'] >= 2014) / len(s))
    a, b = sh(prev), sh(cur)
    if abs(a - b) >= 25:
        out.append(f"준신축(2014년 이후 준공) 거래 비중 {a}% → {b}% — 신축일수록 평당가가 높아 평균이 {'올라감' if b > a else '내려감'}")
    newc = sorted({r['name'] for r in cur if r['build'] >= 2024})
    if newc:
        out.append(f"신축 {', '.join(newc)} 첫 거래 포함 — 기존 단지보다 평당가가 크게 높음")
    fa, fbv = st.mean(r['floor'] for r in prev), st.mean(r['floor'] for r in cur)
    if abs(fa - fbv) >= 3:
        out.append(f"평균 거래 층 {fa:.1f}층 → {fbv:.1f}층 — 층 구성 차이")
    g1 = sum(1 for r in prev if r['floor'] == 1) / np_; g2 = sum(1 for r in cur if r['floor'] == 1) / nc
    if abs(g1 - g2) >= 0.25:
        out.append(f"1층 거래 비중 {round(g1*100)}% → {round(g2*100)}% — 1층은 통상 낮게 거래됨")
    old = sum(1 for r in cur if r['build'] < 1995) / nc - sum(1 for r in prev if r['build'] < 1995) / np_
    if abs(old) >= 0.25:
        out.append(f"1995년 이전 준공 노후 단지 비중 {'증가' if old > 0 else '감소'}({round(abs(old)*100)}%p)")
    # 동일 단지·동일 평형 비교(구성 효과 제거)
    gp, gc = defaultdict(list), defaultdict(list)
    for r in prev: gp[r['grp']].append(r['pp'])
    for r in cur: gc[r['grp']].append(r['pp'])
    common = [g for g in gc if g in gp]
    like = None
    nlike = sum(len(gp[g]) + len(gc[g]) for g in common)
    if common and nlike < 4:
        names = ', '.join(g.split('|')[0] for g in common)
        out.append(f"동일 단지·평형 비교 거래가 {nlike}건뿐({names}) — 층·수리 상태 차이를 걸러낼 수 없어 시세 판단에 쓰지 않음")
        common = []
    if common:
        w = [(len(gp[g]) + len(gc[g]), st.mean(gc[g]) / st.mean(gp[g]) - 1) for g in common]
        like = sum(n * x for n, x in w) / sum(n for n, _ in w) * 100
        names = ', '.join(g.split('|')[0] + f" {g.split('|')[1]}㎡" for g in common)
        out.append(f"동일 단지·평형({names}) 기준 변동 {like:+.1f}%")
    if like is None:
        verdict = '동일 단지·평형 비교 거래가 없거나 너무 적어(4건 미만) 실질 시세 변동인지 판단 불가 — 거래 구성 차이 가능성 높음'
    elif abs(like) < 2:
        verdict = '동일 단지·평형 기준으로는 ±2% 미만 → 시세 변동이 아니라 거래된 단지·층 구성이 달라서 생긴 차이로 판단'
    else:
        verdict = f"동일 단지·평형 기준으로도 {like:+.1f}% → 실제 시세 {'상승' if like > 0 else '하락'} 요인 있음"
    # 20자 이내 요약
    tags = []
    if like is not None and abs(like) >= 2:
        tags.append('전체적 가격상승' if like > 0 else '전체적 가격하락')
    if newc: tags.append('신축 거래 포함')
    elif abs(a - b) >= 25 or abs(old) >= 0.25: tags.append('신축·구축 구성차')
    if abs(fa - fbv) >= 3 or abs(g1 - g2) >= 0.25: tags.append('층별 차이')
    if min(np_, nc) <= 2: tags.append('개별 사정')
    if not tags: tags.append('거래 구성 차이')
    short = ''
    for t in tags:
        cand = (short + '·' + t) if short else t
        if len(cand) > 20: break
        short = cand
    return out, verdict, like, short

def seg_tables(key, labels):
    res = []
    for k, lab in labels.items():
        S = [r for r in R if r[key] == k]
        months = []
        for m in range(1, 12):
            s = [r for r in S if r['m'] == m]
            months.append({'m': m, 'n': len(s), 'pp': avg([r['pp'] for r in s]), 'price': avg([r['price'] for r in s])})
        mom = []
        prev_m = None
        for cell in months:
            if not cell['n']: mom.append(None); continue
            if prev_m is None: mom.append(None); prev_m = cell; continue
            ch = (cell['pp'] / prev_m['pp'] - 1) * 100
            gap = cell['m'] - prev_m['m']
            ent = {'ch': round(ch, 1), 'from': prev_m['m'], 'gap': gap, 'flag': abs(ch) >= 2}
            if ent['flag']:
                P = [r for r in S if r['m'] == prev_m['m']]; C = [r for r in S if r['m'] == cell['m']]
                ent['factors'], ent['verdict'], ent['like'], ent['short'] = factors(P, C, f"{prev_m['m']}월", f"{cell['m']}월")
            mom.append(ent); prev_m = cell
        qs = []
        for q in range(1, 5):
            s = [r for r in S if r['q'] == q]
            qs.append({'q': q, 'n': len(s), 'pp': avg([r['pp'] for r in s])})
        qoq = []
        pq = None
        for c in qs:
            if not c['n']: qoq.append(None); continue
            if pq is None: qoq.append(None); pq = c; continue
            ch = (c['pp'] / pq['pp'] - 1) * 100
            ent = {'ch': round(ch, 1), 'from': pq['q'], 'flag': abs(ch) >= 2}
            if ent['flag']:
                P = [r for r in S if r['q'] == pq['q']]; C = [r for r in S if r['q'] == c['q']]
                ent['factors'], ent['verdict'], ent['like'], ent['short'] = factors(P, C, f"{pq['q']}분기", f"{c['q']}분기")
            qoq.append(ent); pq = c
        res.append({'key': k, 'label': lab, 'n': len(S), 'months': months, 'mom': mom, 'quarters': qs, 'qoq': qoq,
                    'pp': avg([r['pp'] for r in S])})
    return res

monthly = []
for m in range(1, 12):
    s = [r for r in R if r['m'] == m]
    monthly.append({'m': m, 'n': len(s), 'avg': avg([r['price'] for r in s]),
                    'med': round(st.median([r['price'] for r in s])) if s else None,
                    'pp': avg([r['pp'] for r in s])})

# 층별 보정계수(감정평가 개별요인 비교용): 같은 단지·평형 그룹 안에서 층 구간 평균 / 그룹 평균 (3건 이상 그룹)
def vb(f): return 'F1' if f == 1 else ('L' if f <= 3 else ('M' if f <= 9 else 'H'))
VB = {'F1': '1층', 'L': '2~3층', 'M': '4~9층', 'H': '10층 이상'}
ratios = defaultdict(list)
G = defaultdict(list)
for r in R: G[r['grp']].append(r)
for g, s in G.items():
    if len(s) < 3: continue
    gm = st.mean(r['pp'] for r in s)
    for b in VB:
        v = [r['pp'] for r in s if vb(r['floor']) == b]
        if v: ratios[b].append((len(v), st.mean(v) / gm))
fc = {b: (sum(n * x for n, x in ratios[b]) / sum(n for n, _ in ratios[b]) if ratios[b] else None) for b in VB}
mid = fc['M']
# 표본이 적은 구간은 1.0 쪽으로 수축: coef' = 1 + (coef-1) * n/(n+10)
floor_coef = {b: {'label': VB[b], 'raw': round(v / mid, 4) if v else 1.0, 'coef': round(1 + (v / mid - 1) * sum(n for n, _ in ratios[b]) / (sum(n for n, _ in ratios[b]) + 10), 4) if v else 1.0, 'n': sum(n for n, _ in ratios[b])} for b, v in fc.items()}

# 시점수정률: 동일 단지·평형 그룹(10건 이상) 안의 월별 회귀 기울기(그룹 평균 대비 %/월)
slopes = []
for g, s in G.items():
    if len(s) < 10: continue
    xs = [r['m'] for r in s]; ys = [r['pp'] for r in s]
    mx, my = st.mean(xs), st.mean(ys)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    slopes.append((len(s), b / my * 100, g))
slopes.sort(reverse=True)
time_rate = round(slopes[0][1], 3)   # 표본이 가장 많은 그룹(지역 대표 단지)을 기본 시점수정률로
out = {
    'generated': '2026-11-24', 'source': '국토교통부 아파트 매매 실거래가(법정동코드 52750, 계약일 2026-01-01~2026-11-24 신고분)',
    'tx': [{k: r[k] for k in ('date', 'm', 'q', 'name', 'price', 'area', 'floor', 'build', 'dong', 'ab', 'fb')} | {'pp': round(r['pp'])} for r in sorted(R, key=lambda r: r['date'])],
    'monthly': monthly,
    'area': seg_tables('ab', AREA), 'floor': seg_tables('fb', FLOOR),
    'floor_coef': floor_coef, 'time_rate': time_rate, 'time_rate_grp': slopes[0][2].replace('|',' ')+'㎡',
    'group_rates': {g: round(x, 3) for n, x, g in slopes},
    'time_basis': [{'grp': g.replace('|', ' ') + '㎡', 'n': n, 'rate': round(x, 2)} for n, x, g in slopes],
}
json.dump(out, open('data.json', 'w', encoding='utf-8'), ensure_ascii=False)
print('tx', len(R), 'floor_coef', floor_coef, 'time_rate', time_rate, out['time_basis'])
for t in ('area', 'floor'):
    for s in out[t]:
        fl = [(i + 1, e['ch']) for i, e in enumerate(s['mom']) if e and e['flag']]
        fq = [(i + 1, e['ch']) for i, e in enumerate(s['qoq']) if e and e['flag']]
        print(t, s['key'], s['n'], 'MoM', fl, 'QoQ', fq)
