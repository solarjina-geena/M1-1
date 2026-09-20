import pandas as pd
from pathlib import Path

# ============================================================
# [작업 목적]
# 2026년 자동차산업 자료의 "공식 원문 목록"을 저장합니다.
#
# [왜 하는가?]
# Google 검색 결과를 매번 다시 찾지 않고,
# 우리가 직접 확인한 산업통상부 원문만 사용하기 위해서입니다.
#
# [중요]
# - 아직 생산/내수/수출 숫자를 MASTER에 넣지 않습니다.
# - MASTER는 변경하지 않습니다.
# - 다음 단계의 원문/첨부 검증용 기준 목록입니다.
# ============================================================


# ------------------------------------------------------------
# [1단계] 저장할 폴더 지정
# ------------------------------------------------------------

BASE = Path("data/raw/motie")
BASE.mkdir(parents=True, exist_ok=True)

OUT = BASE / "motie_2026_official_sources.csv"


# ------------------------------------------------------------
# [2단계] 직접 확인한 산업통상부 공식 원문 등록
#
# source_type 설명
# MONTHLY   = 일반 월간 자동차산업 동향
# QUARTERLY = 분기자료 안에 해당 월 실적 포함
# SPECIAL   = 제목은 다르지만 해당 월 자동차산업 실적 공식자료
# ------------------------------------------------------------

rows = [

    {
        "period": "2026-01",
        "source_title": "2026년 1월 자동차산업 동향",
        "source_date": "2026-02-19",
        "source_type": "MONTHLY",
        "source_url":
        "https://www.motir.go.kr/kor/article/ATCL4fcf3d8c6/657/view",
        "source_status": "OFFICIAL_CONFIRMED"
    },

    {
        "period": "2026-02",
        "source_title": "2026년 2월 자동차산업 동향",
        "source_date": "2026-03-18",
        "source_type": "MONTHLY",
        "source_url":
        "https://www.motir.go.kr/kor/article/ATCL3f49a5a8c/171605/view",
        "source_status": "OFFICIAL_CONFIRMED"
    },

    {
        "period": "2026-03",
        "source_title": "2026년 1분기 자동차산업 동향",
        "source_date": "2026-04-15",
        "source_type": "QUARTERLY",
        "source_url":
        "https://www.motir.go.kr/kor/article/ATCL3f49a5a8c/171730/view",
        "source_status": "OFFICIAL_CONFIRMED"
    },

    {
        "period": "2026-04",
        "source_title": "2026년 4월 자동차산업 동향",
        "source_date": "2026-05-20",
        "source_type": "MONTHLY",
        "source_url":
        "https://www.motir.go.kr/kor/article/ATCL3f49a5a8c/171849/view",
        "source_status": "OFFICIAL_CONFIRMED"
    },

    {
        "period": "2026-05",
        "source_title": "2026년 5월 자동차산업 동향",
        "source_date": "2026-06-17",
        "source_type": "MONTHLY",
        "source_url":
        "https://www.motir.go.kr/kor/article/ATCL3f49a5a8c/171937/view",
        "source_status": "OFFICIAL_CONFIRMED"
    },

    {
        "period": "2026-06",
        "source_title": "2026년 6월 자동차산업 동향",
        "source_date": "2026-07-15",
        "source_type": "MONTHLY",
        "source_url":
        "https://www.motir.go.kr/kor/article/ATCL3f49a5a8c/172028/view",
        "source_status": "OFFICIAL_CONFIRMED"
    },

    {
        "period": "2026-07",
        "source_title": "7월 자동차 수출 역대 최대… 민관 원팀, 미래차 전환·상생협력에 한뜻",
        "source_date": "2026-08-13",
        "source_type": "SPECIAL",
        "source_url":
        "https://www.motir.go.kr/kor/article/ATCL3f49a5a8c/172105/view",
        "source_status": "OFFICIAL_CONFIRMED"
    },

    {
        "period": "2026-08",
        "source_title": "2026년 8월 자동차산업 동향",
        "source_date": "2026-09-17",
        "source_type": "MONTHLY",
        "source_url":
        "https://www.motir.go.kr/kor/article/ATCL3f49a5a8c/172213/view",
        "source_status": "OFFICIAL_CONFIRMED"
    },
]


# ------------------------------------------------------------
# [3단계] CSV로 저장
# ------------------------------------------------------------

df = pd.DataFrame(rows)

df.to_csv(
    OUT,
    index=False,
    encoding="utf-8-sig"
)


# ------------------------------------------------------------
# [4단계] 저장 결과 확인
#
# 여기서는 반드시 8 / 8이 나와야 합니다.
# 숫자 검증은 아직 하지 않습니다.
# ------------------------------------------------------------

print("=" * 100)
print("MOTIE 2026 OFFICIAL SOURCE INDEX")
print("=" * 100)

print()
print(df[
    [
        "period",
        "source_date",
        "source_type",
        "source_title"
    ]
].to_string(index=False))

print()
print("=" * 100)
print("RESULT")
print("=" * 100)

print("TARGET          : 8")
print("OFFICIAL SOURCE :", len(df))
print("FIRST           :", df["period"].min())
print("LAST            :", df["period"].max())
print()
print("OUTPUT :", OUT)

print()
print(">>> SOURCE INDEX 8 / 8 <<<")
print()
print("※ 공식 원문 위치만 확정")
print("※ 생산/내수/수출 아직 미검증")
print("※ MASTER 변경 없음")
