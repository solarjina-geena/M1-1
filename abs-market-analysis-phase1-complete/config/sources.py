from datetime import date

SOURCES = {
    "trade": {
        "name": "관세청 수출입무역통계",
        "url": "https://unipass.customs.go.kr/ets/",
        "cost": "무료",
        "api_key_req": True,
        "update_cycle": "월",
        "raw_retention": True,
    },
    "dart": {
        "name": "금융감독원 DART 전자공시시스템",
        "url": "https://dart.fss.or.kr/",
        "cost": "무료",
        "api_key_req": True,
        "update_cycle": "분기/연",
        "raw_retention": True,
    },
    "kama": {
        "name": "한국자동차모빌리티산업협회",
        "url": "https://www.kama.or.kr/statistics/",
        "cost": "무료 공개 범위 사용",
        "api_key_req": False,
        "update_cycle": "월",
        "raw_retention": True,
    },
    "kipris": {
        "name": "KIPRIS 특허정보검색",
        "url": "https://www.kipris.or.kr/",
        "cost": "무료",
        "api_key_req": True,
        "update_cycle": "분기 권장",
        "raw_retention": True,
    },
    "bok": {
        "name": "한국은행 ECOS",
        "url": "https://ecos.bok.or.kr/",
        "cost": "무료",
        "api_key_req": True,
        "update_cycle": "월",
        "raw_retention": True,
    },
    "kosis": {
        "name": "국가통계포털 KOSIS",
        "url": "https://kosis.kr/",
        "cost": "무료",
        "api_key_req": True,
        "update_cycle": "통계별 상이",
        "raw_retention": True,
    },
    "technical": {
        "name": "공개 기술자료 / 제조사 공식자료",
        "url": "",
        "cost": "무료 공개자료만 사용",
        "api_key_req": False,
        "update_cycle": "수시",
        "raw_retention": True,
    },
}

def get_source_citation(source_key: str, basis_date: str | None = None) -> str:
    s = SOURCES.get(source_key, {})
    basis = f" | 기준: {basis_date}" if basis_date else ""
    return (
        f"출처: {s.get('name','알수없음')} ({s.get('url','')})"
        f"{basis} | 수집일: {date.today()}"
    )
