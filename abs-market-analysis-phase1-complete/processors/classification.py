import pandas as pd

def classify_geography(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    out["domestic_production_flag"] = out["plant_country"].eq("대한민국")
    out["korean_owned_flag"] = out["parent_hq_country"].eq("대한민국")

    out["market_scope"] = "글로벌"
    out.loc[out["domestic_production_flag"], "market_scope"] = "국내 생산"
    out.loc[out["korean_owned_flag"] & ~out["domestic_production_flag"], "market_scope"] = "한국계 해외생산"

    return out
