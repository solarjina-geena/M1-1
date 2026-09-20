ABS Market Intelligence V5 FINAL

목표
- 대시보드는 2장 유지
- 1장: 시장동향
- 2장: 변동분석 · 질문 · 기술동향
- 화면 수를 늘리지 않고 기간 탐색 기능만 강화

추가 기능
1. 국내 시장: 최근 1/3/5/10년, 전체, 직접 선택
2. 선택 기간이 KPI / 월별 추이 / 연간 동일기간 비교에 동시 적용
3. 글로벌 시장도 독립 기간 검색
4. 변동분석: 동일 기간 선택
5. 질문 Fact/Why가 선택 분석기간에 연동
6. NULL/미수집 월은 0 대체 금지
7. 특허 원본 미연결 시 가짜 그래프 생성 금지

설치
프로젝트 루트에 아래 2개 파일을 복사:
- dashboard_app_v5_final.py
- apply_dashboard_v5_final.py

실행
python .\apply_dashboard_v5_final.py
python -m streamlit run .\dashboard\app.py
