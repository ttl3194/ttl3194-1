# 임실 분석: 52750 월별 get_apt_price. 01 저장
- 02~04 저장
- 05~08 저장
- 09~11 저장. 총 수집 완료(MOLIT AptInfo). 다음: 분석 스크립트 analyze.py → report.html
- analyze.py 완료(data.json). 다음 report_template.html
- report 빌드됨 imsil_report.html

## 현재 상태 (2026-11-24 저장)
- 전북 지도: jeonbuk/jeonbuk_apt_map.html (게시 https://claude.ai/artifact/YBn284sHLrBHAdECzTvoH3)
  - 전주·군산·익산 30건↑, 나머지 11개 시군 5건↑ 단지 312곳
  - 임실군 클릭 → 창: 임실 시세분석(매도 예상가 맨 위, 월별 추이, 분기별 변동요인 20자 요약) + 임실 정적 지도
  - 빌드: cd jeonbuk && python3 build_page.py (map_template.html + cx.json + sgg_jb.json + ../imsil/imsil_report.html + imsil.html)
- 임실 시세분석: imsil/ (tx.tsv 원자료 69건 → analyze.py → data.json → report_template.html → imsil_report.html)
  - 별도 게시 https://claude.ai/artifact/2CGZev3iPra2V5gStuGWCn (같은 내용)
  - 비교사례·보정내역·원자료는 화면에서 숨김(요청 시 제공)
- 게시 환경 제약: 외부 지도 삽입(구글·네이버)·새 탭 이동 불가 → 페이지 내 창(dialog+srcdoc)으로 처리

## 다음 할 일
- 브이월드 지적도·건물 윤곽 반영: 클라우드에서 api.vworld.kr 접속이 TLS 단계에서 끊김(해외 IP 차단 추정)
  → 사용자 PC를 Remote Control로 연결한 뒤 그 PC에서 받기로 함(사용자 선택 2번). 아직 연결 폴더 없음.
  - 인증키는 저장소에 넣지 않음(사용자에게 다시 받거나 보안 입력으로 받을 것)
- 대상 지번(임실군): 이도리 982·272·332·182-2·385-2·212·183-3·214, 관촌리 584-2·489-5·498-6, 오수리 387-27·351-8·376-2
