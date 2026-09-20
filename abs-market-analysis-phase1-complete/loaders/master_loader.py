from __future__ import annotations

from pathlib import Path

import pandas as pd

from config.settings import PATH_CONFIG


METADATA_DIR = Path(PATH_CONFIG["metadata"])


def load_technology_master() -> pd.DataFrame:
    path = METADATA_DIR / "technology_master.csv"
    return pd.read_csv(path, dtype="string")


def load_product_model_master() -> pd.DataFrame:
    path = METADATA_DIR / "product_model_master.csv"
    return pd.read_csv(path, dtype="string")


def load_model_technology_map() -> pd.DataFrame:
    path = METADATA_DIR / "model_technology_map.csv"
    return pd.read_csv(path, dtype="string")

def load_market_assumption_master() -> pd.DataFrame:
    path = METADATA_DIR / "market_assumption_master.csv"
    return pd.read_csv(path, dtype="string")

def validate_master_relations() -> dict:
    technologies = load_technology_master()
    models = load_product_model_master()
    mapping = load_model_technology_map()

    technology_ids = set(
        technologies["technology_id"].dropna().astype(str)
    )
    model_ids = set(
        models["model_id"].dropna().astype(str)
    )

    mapped_technology_ids = set(
        mapping["technology_id"].dropna().astype(str)
    )
    mapped_model_ids = set(
        mapping["model_id"].dropna().astype(str)
    )

    unknown_technology_ids = sorted(
        mapped_technology_ids - technology_ids
    )
    unknown_model_ids = sorted(
        mapped_model_ids - model_ids
    )

    duplicate_technologies = (
        technologies[
            technologies.duplicated("technology_id", keep=False)
        ]["technology_id"]
        .dropna()
        .astype(str)
        .tolist()
    )

    duplicate_models = (
        models[
            models.duplicated("model_id", keep=False)
        ]["model_id"]
        .dropna()
        .astype(str)
        .tolist()
    )

    result = {
        "technology_count": len(technologies),
        "model_count": len(models),
        "mapping_count": len(mapping),
        "unknown_technology_ids": unknown_technology_ids,
        "unknown_model_ids": unknown_model_ids,
        "duplicate_technology_ids": duplicate_technologies,
        "duplicate_model_ids": duplicate_models,
        "valid": not any(
            [
                unknown_technology_ids,
                unknown_model_ids,
                duplicate_technologies,
                duplicate_models,
            ]
        ),
    }

    return result
def validate_market_assumptions() -> dict:
    assumptions = load_market_assumption_master()
    technologies = load_technology_master()
    models = load_product_model_master()

    technology_ids = set(
        technologies["technology_id"].dropna().astype(str)
    )
    model_ids = set(
        models["model_id"].dropna().astype(str)
    )

    used_technology_ids = set(
        assumptions["technology_id"].dropna().astype(str)
    )
    used_model_ids = set(
        assumptions["model_id"].dropna().astype(str)
    )

    unknown_technology_ids = sorted(
        used_technology_ids - technology_ids
    )
    unknown_model_ids = sorted(
        used_model_ids - model_ids
    )

    duplicate_assumption_ids = (
        assumptions[
            assumptions.duplicated("assumption_id", keep=False)
        ]["assumption_id"]
        .dropna()
        .astype(str)
        .tolist()
    )

    return {
        "assumption_count": len(assumptions),
        "unknown_technology_ids": unknown_technology_ids,
        "unknown_model_ids": unknown_model_ids,
        "duplicate_assumption_ids": duplicate_assumption_ids,
        "valid": not any(
            [
                unknown_technology_ids,
                unknown_model_ids,
                duplicate_assumption_ids,
            ]
        ),
    }