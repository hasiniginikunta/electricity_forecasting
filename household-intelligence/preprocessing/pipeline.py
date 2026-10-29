"""
Preprocessing pipeline for household and consumption data.
Handles validation, deduplication, missing values, encoding and scaling.
Saves fitted transformers to artifacts to prevent data leakage at inference.
"""
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.preprocessing import StandardScaler, OrdinalEncoder


# ── Schema constants ──────────────────────────────────────────────────────────
CONSUMPTION_MIN_KWH = 10.0
CONSUMPTION_MAX_KWH = 5000.0

CATEGORICAL_COLS = ["state", "home_type"]
BOOL_COLS = ["has_solar", "has_air_conditioner", "has_inverter_ac",
             "has_electric_vehicle", "has_electric_water_heater"]
NUMERIC_PROFILE_COLS = ["n_residents", "home_size_m2"]


# ── Household profile validation ──────────────────────────────────────────────
def validate_households(df: pd.DataFrame) -> pd.DataFrame:
    """Return cleaned household DataFrame with a 'validation_flag' column."""
    df = df.copy()
    flags = []
    for _, row in df.iterrows():
        issues = []
        n_res = row.get("n_residents")
        if pd.isna(n_res) or n_res < 1:
            issues.append("invalid_n_residents")
        elif n_res > 20:
            issues.append("implausible_n_residents")
        home_size = row.get("home_size_m2")
        if pd.notna(home_size) and home_size <= 0:
            issues.append("invalid_home_size")
        elif pd.notna(home_size) and home_size > 10000:
            issues.append("implausible_home_size")
        flags.append("|".join(issues) if issues else "ok")
    df["validation_flag"] = flags
    return df


# ── Consumption record validation ─────────────────────────────────────────────
def validate_consumption(df: pd.DataFrame) -> pd.DataFrame:
    """Flag impossible or duplicate consumption records.

    Order matters: duplicates are flagged first so that a duplicate record
    that also happens to be out-of-range is not silently kept as 'ok' if
    the first occurrence passes range checks.
    """
    df = df.copy()
    df["validation_flag"] = "ok"

    # 1. Duplicates first — same household + same month/year
    dup_mask = df.duplicated(subset=["household_id", "billing_year", "billing_month"],
                             keep="first")
    df.loc[dup_mask, "validation_flag"] = "duplicate"

    # 2. Out-of-range (only on non-duplicate rows to avoid masking)
    non_dup = df["validation_flag"] == "ok"
    mask_low = non_dup & (df["consumption_kwh"] < CONSUMPTION_MIN_KWH)
    mask_high = non_dup & (df["consumption_kwh"] > CONSUMPTION_MAX_KWH)
    df.loc[mask_low, "validation_flag"] = "below_minimum"
    df.loc[mask_high, "validation_flag"] = "above_maximum"

    return df


def filter_valid_consumption(df: pd.DataFrame) -> pd.DataFrame:
    validated = validate_consumption(df)
    return validated[validated["validation_flag"] == "ok"].copy()


# ── Missing value handling ────────────────────────────────────────────────────
def impute_households(df: pd.DataFrame) -> pd.DataFrame:
    """Impute missing household profile fields with sensible defaults."""
    df = df.copy()
    df["n_residents"] = df["n_residents"].fillna(df["n_residents"].median())
    df["home_size_m2"] = df["home_size_m2"].fillna(df["home_size_m2"].median())
    df["home_type"] = df["home_type"].fillna("apartment")
    df["state"] = df["state"].fillna("Telangana")
    for col in BOOL_COLS:
        if col in df.columns:
            df[col] = df[col].where(df[col].notna(), other=False)
    return df


# ── Encoding + scaling (fit on training data only) ────────────────────────────
class HouseholdProfileTransformer:
    """
    Encodes categorical columns and scales numerics.
    Fit on training households; transform at inference without refitting.
    """

    def __init__(self):
        self.encoder = OrdinalEncoder(handle_unknown="use_encoded_value",
                                      unknown_value=-1)
        self.scaler = StandardScaler()
        self._cat_cols = CATEGORICAL_COLS
        self._num_cols = NUMERIC_PROFILE_COLS + [c for c in BOOL_COLS]
        self._fitted = False

    def fit(self, df: pd.DataFrame) -> "HouseholdProfileTransformer":
        df = impute_households(df)
        # Only use columns that exist in this dataset
        cat_cols = [c for c in self._cat_cols if c in df.columns]
        num_cols = [c for c in self._num_cols if c in df.columns]
        self._cat_cols_fit = cat_cols
        self._num_cols_fit = num_cols
        self.encoder.fit(df[cat_cols])
        self.scaler.fit(df[num_cols].astype(float))
        self._fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("Transformer not fitted. Call fit() first.")
        df = impute_households(df)
        cat = self.encoder.transform(df[self._cat_cols_fit])
        num = self.scaler.transform(df[self._num_cols_fit].astype(float))
        return np.hstack([cat, num])

    def fit_transform(self, df: pd.DataFrame) -> np.ndarray:
        return self.fit(df).transform(df)

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)

    @staticmethod
    def load(path: Path) -> "HouseholdProfileTransformer":
        return joblib.load(path)


# ── Consumption series helpers ────────────────────────────────────────────────
def get_household_series(consumption_df: pd.DataFrame,
                         household_id: str) -> pd.Series:
    """
    Return a time-sorted Series of consumption_kwh for one household.
    Index is a Period (year-month). Missing months are NOT filled — gaps
    are preserved so downstream code can detect them explicitly.
    """
    hh = consumption_df[consumption_df["household_id"] == household_id].copy()
    hh["period"] = pd.to_datetime(
        hh[["billing_year", "billing_month"]].rename(
            columns={"billing_year": "year", "billing_month": "month"}
        ).assign(day=1)
    ).dt.to_period("M")
    hh = hh.sort_values("period").drop_duplicates("period")
    return hh.set_index("period")["consumption_kwh"]
