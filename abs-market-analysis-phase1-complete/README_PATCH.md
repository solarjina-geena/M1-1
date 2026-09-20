# ABS Market Intelligence — Phase 1 Final Patch

이 패치는 **현재 PC에 있는 최신 `dashboard/app.py`의 디자인을 보존하면서**
1차 마무리 규칙만 안전하게 적용하기 위한 패치입니다.

## 적용
프로젝트 루트:
`D:\코디세이\LEVEL3 응용\M1-1\abs-market-analysis-phase1-complete`

PowerShell에서:

```powershell
python .\apply_phase1_final_patch.py
python -m streamlit run .\dashboard\app.py
```

## 자동 백업
처음 실행 시 기존 파일을 다음 이름으로 보관합니다.

`dashboard/app_before_phase1_final.py`

## 고정 원칙
- NULL/미수집 월을 0으로 만들지 않음
- 임의 보간하지 않음
- 실제 원자료가 0인 경우만 0으로 인정
- 시장분석 질문은 관찰(Fact) / 해석(Why) / 다음 확인(Action) 구분
- 기술·특허는 확인되지 않은 숫자를 새로 만들지 않음
- 시장점유율/추가 시장/뉴스/주식/OEM 장착률은 2차 과제
