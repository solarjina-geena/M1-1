# ABS Market Intelligence 진행보고서

## 2026-09-17

### 오늘 완료

- MGH20 Coil 기준
  - 8 EA/SYSTEM
  - ESTIMATED / 신뢰등급 B
  - SAE 기술자료 Source 연결 완료
  - Source ID: TECH_20260917184539

- 모델별 Coil 단위구조
  - iMEB3: IV 8 + OV 5 + HSV 1 = 14 EA/SYSTEM
  - MEB5.2: IV 6 + OV 4 + HSV 2 = 12 EA/SYSTEM
  - MEB5: 전체 12 EA/SYSTEM
  - MEB5 당사 공급 참여범위: OV 4 + HSV 2 = 6 EA/SYSTEM
  - MEB5 비독점이므로 6개를 실제 당사 공급량으로 간주하지 않음

- 시장과 당사 공급범위 분리
  - 전체 시스템 Coil 수량과 당사 공급대상 수량을 별도 관리
  - 실제 당사 공급량/점유율은 향후 내부 생산·판매 데이터 연결 후 계산
  - 비독점 공급비율 임의 추정 금지

- 계산엔진 확장
  - 모델별 IV / OV / HSV 수량 조회 기능 추가
  - 당사 공급대상 Coil 수량 계산 기능 추가
  - 검증 결과:
    - iMEB3 = 14 EA/SYSTEM
    - MEB5.2 = 12 EA/SYSTEM
    - MEB5 당사 공급대상 = 6 EA/SYSTEM

- iMEB 외부 기술근거
  - 현대모비스 공식 iMEB 기술자료 RAW 저장
  - Source ID: TECH_20260917192750
  - MODEL_IMEB3에 기술 Source 연결
  - 특정 차량의 iMEB3 적용 여부와 기술구조 근거는 분리 관리

- 차량 적용관계
  - vehicle_application_master.csv 신규 생성
  - APP_IMEB3_AVANTE_CN7_HEV 등록
  - 내부정보: iMEB3 아반떼 초기 적용
  - 외부자료: CN7 HEV 통합형 전자브레이크 적용 확인
  - Source ID: TECH_20260917192947
  - iMEB3 직접 연결 및 정확한 적용률은 아직 외부 미검증
  - verification_status = PARTIAL

### 계산 안전성 확인

2024 한국 승용차 생산량:
- 3,849,326대
- KOSIS ACTUAL

iMEB3 계산 입력:
- systems_per_vehicle = 1
- coils_per_system = 14
- fitment_rate = MISSING

결과:
- CALCULATION_UNAVAILABLE

적용률이 확인되지 않은 상태에서
한국 승용차 전체 생산량 × 14 Coil을 계산하지 않도록 정상 차단됨.

### 다음 작업

1. 아반떼 CN7 HEV 연도별 생산량 확보
2. 국내/해외 생산 구분
3. iMEB3 실제 적용 시작시점 및 적용범위 추가 검증
4. vehicle_application_master와 차량 생산량 연결
5. 적용차종 기준 Coil 잠재시장 계산
6. MEB5.2 / MEB5 적용차종 역추적 확대
7. 실제 당사 생산·판매 데이터 연결 후 시장점유율 계산

### 현재 원칙

- 확인되지 않은 값은 NULL/MISSING 유지
- 외부 검증값과 내부 제공값 분리
- 내부정보를 외부 검증자료로 표시하지 않음
- 추정값은 ESTIMATED 명시
- 비독점 공급은 실제 당사 공급량으로 간주하지 않음
- 적용차종/적용률 확인 전 전체 차량 생산량에 Coil 수량을 곱하지 않음
