# ABS Market Intelligence

자동차 시장의 생산·내수·수출 시계열과 제동기술 전환 신호를 분석하는 1차 프로젝트입니다.

## 주요 결과

- 국내 자동차 월별 시계열 분석
- 글로벌 주요시장 공개자료 수집/정리
- 3개월 이동평균
- 12개월 변동성
- 동일기간(YTD) 비교
- 질문 기반 `Fact / Why / Action` 분석
- ABS → ESC → 통합제동 → Brake-by-Wire/EMB 기술동향
- Streamlit 2화면 탐색형 대시보드
- 기간검색: 1년 / 3년 / 5년 / 10년 / 전체 / 직접선택

## 분석 원칙

- NULL/미수집을 0으로 대체하지 않습니다.
- 서로 다른 vehicle scope의 지표를 임의 합산하지 않습니다.
- 부분연도를 완결연도처럼 비교하지 않습니다.
- 관찰(Fact)과 해석(Why)을 구분합니다.
- 근거가 없는 특허/점유율 숫자를 생성하지 않습니다.

## 실행

```powershell
python -m streamlit run .\dashboard\app.py
```

브라우저 기본 주소:

```text
http://localhost:8501
```

## 대시보드

### 01 시장동향
국내 생산·내수·수출 및 글로벌 주요시장의 시계열을 기간별로 탐색합니다.

### 02 변동분석 · 질문 · 기술동향
이동평균과 변동성, 질문 기반 해석, 제동기술 전환 신호를 함께 확인합니다.

## 제출 파일

- `REPORT.md` : 최종 분석 리포트
- `REQUEST_LIST.md` : 프로젝트 요구사항/변경이력
- `README.md` : 실행 및 프로젝트 설명
- `dashboard/app.py` : Streamlit 대시보드
- `requirements.txt` : 실행 의존성
- `data/` : 공개 가능 범위의 데이터 및 수집 결과
- 수집/검증 Python 스크립트

## 데이터 출처

프로젝트 과제물 작성에 활용한 자료 출처입니다. API 키 연동을 진행한 서비스와 공식 웹페이지·PDF·공개 문헌을 수집한 사이트를 구분했습니다.

### API 연동 사이트

| 기관 / 서비스 | 사이트 | 수집 목적 |
| --- | --- | --- |
| DART 전자공시 | opendart.fss.or.kr | 기업 공시, 사업보고서, 재무정보 |
| 관세청 무역통계 | data.go.kr | 자동차·부품 수출입 통계 |
| 한국은행 ECOS | ecos.bok.or.kr | 거시경제 및 산업 관련 시계열 |
| 통계청 KOSIS | kosis.kr | 국내·세계 자동차 생산 통계 |
| KIPRIS 특허정보 | plus.kipris.or.kr | 특허 검색 및 기술활동 분석 |

위 5개는 프로젝트에서 API 키 연동을 진행했던 서비스입니다. API 키 연동 확인이 실제 데이터 호출 성공 또는 수집 완료를 의미하지는 않습니다.

### 글로벌 자동차 시장 데이터 수집 사이트

| 국가 / 지역 | 기관 | 공식 사이트 / 서비스 | 수집 내용 |
| --- | --- | --- | --- |
| 글로벌·OECD | OECD | OECD SDMX | 국가별 신차등록 시계열 |
| 중국 | CAAM | caam.org.cn | 자동차 생산·판매 |
| 인도 | SIAM | siam.in | 자동차 생산·내수판매 |
| 브라질 | ANFAVEA | anfavea.com.br | 생산·수출·등록 |
| 멕시코 | INEGI | inegi.org.mx | 자동차 생산·판매·수출 |
| 한국 | KAMA | kama.or.kr | 국내 자동차 생산·내수·수출 |
| 한국 | KAIDA | kaida.co.kr | 수입차 등록 통계 |

CAAM·ANFAVEA 등은 일반적인 인증형 API 호출 외에 공식 웹페이지 또는 PDF 자료를 수집·분석하는 방식도 사용했습니다.

### 기술동향 근거 수집 사이트

| 기관 | 사이트 | 활용 |
| --- | --- | --- |
| Bosch Mobility | bosch-mobility.com | ABS 및 Brake-by-Wire 기술 |
| Continental | continental.com | 통합제동 및 차세대 제동기술 |
| ZF | zf.com | EMB·Brake-by-Wire 기술 |
| Hyundai Mobis | mobis.com | 통합전자제동 기술 |
| SAE Mobilus | saemobilus.sae.org | MGH-20 등 기술논문 |
| Google Patents | patents.google.com | 특허 기술문헌 |

### 수집 이력 확인 및 범위

API 키 연동을 확인했던 서비스는 5개이며, 글로벌 시장과 기술동향 분석에는 추가로 공식 사이트·PDF·공개 문헌을 활용했습니다. 위 목록 전체가 실제 API 호출에 성공했다는 의미는 아닙니다.

정확한 호출 URL, 수집일, 성공 여부는 `data/metadata/source_log.csv`와 `collectors/` 폴더를 대조해 확인해야 합니다. 세부 수집방식, 원본 파일 및 audit 정보는 프로젝트 데이터·스크립트와 `REPORT.md`의 설명을 함께 확인하십시오.

뉴스·주식 자료는 2차 과제로 남겨둔 부분이므로 수집 완료 API로 분류하지 않았습니다.

## 한계 및 다음 단계

1차 결과는 시장·기술 방향 탐색용입니다. 시장점유율, OEM/차종별 장착률, Coil Ass'y 적용량, 뉴스/주가 이벤트, 특허 원본 연결은 2차 분석에서 보강합니다.
