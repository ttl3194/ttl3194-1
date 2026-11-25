"""map_template.html + 데이터 → jeonbuk_apt_map.html (임실 시세분석·지도 포함)"""
import json
s=open('map_template.html').read()
rep=open('../imsil/imsil_report.html').read()
wrapped='<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>'+rep+'</body></html>'
enc=lambda t: json.dumps(t,ensure_ascii=False).replace('</','<\\/')
open('jeonbuk_apt_map.html','w').write(s.replace('__SGG__',open('sgg_jb.json').read()).replace('__CX__',open('cx.json').read()).replace('__IMSIL_REPORT__',enc(wrapped)).replace('__IMSIL__',enc(open('imsil.html').read())))
