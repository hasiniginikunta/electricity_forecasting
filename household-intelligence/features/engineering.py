"""
Feature engineering for household consumption profiles.
Features are derived per household from their consumption history.
Only features with clear interpretive value are included.
Indian seasonal context: peak summer March–June, cool November–February.
"""
import numpy as np
import pandas as pd
from scipy import stats
from config.settings import INDIAN_SUMMER_MONTHS, INDIAN_COOL_MONTHS


def compute_consumption_features(series: pd.Series) -> dict:
    """
    Compute statistical features from a household's consumption time series.
    series: pd.Series with Period index, values in kWh.
    Returns a dict of features (or NaN where insufficient data).
    """
    n = len(series)
    if n == 0:
        return {"n_records": 0}

    vals = series.values.astype(float)
    feat = {
        "n_records": n,
        "mean_kwh": float(np.mean(vals)),
        "median_kwh": float(np.median(vals)),
        "std_kwh": float(np.std(vals, ddof=1)) if n > 1 else np.nan,
        "min_kwh": float(np.min(vals)),
        "max_kwh": float(np.max(vals)),
        "range_kwh": float(np.max(vals) - np.min(vals)),
        "cv": float(np.std(vals, ddof=1) / np.mean(vals)) if n > 1 else np.nan,
    }

    # Month-to-month percentage change.
    # When months are missing the raw np.diff() treats non-adjacent records
    # as consecutive, overstating the per-month rate of change. We normalise
    # by the actual calendar gap (in months) between each pair of records.
    if n > 1 and hasattr(series.index, "ordinal"):
        ordinals = np.array(series.index.ordinal, dtype=float)
        gaps = np.diff(ordinals)          # calendar months between records
        gaps = np.where(gaps == 0, 1, gaps)  # guard against duplicates
        raw_pct = np.diff(vals) / vals[:-1] * 100
        pct_per_month = raw_pct / gaps
        feat["mean_pct_change"] = float(np.mean(pct_per_month))
        feat["mean_abs_pct_change"] = float(np.mean(np.abs(pct_per_month)))
    elif n > 1:
        pct_changes = np.diff(vals) / vals[:-1] * 100
        feat["mean_pct_change"] = float(np.mean(pct_changes))
        feat["mean_abs_pct_change"] = float(np.mean(np.abs(pct_changes)))
    else:
        feat["mean_pct_change"] = np.nan
        feat["mean_abs_pct_change"] = np.nan

    # Seasonal features — Indian summer (Mar–Jun) vs cool (Nov–Feb)
    if hasattr(series.index, "month"):
        months = series.index.month
        summer_vals = vals[np.isin(months, list(INDIAN_SUMMER_MONTHS))]
        cool_vals = vals[np.isin(months, list(INDIAN_COOL_MONTHS))]
        non_summer = vals[~np.isin(months, list(INDIAN_SUMMER_MONTHS))]

        feat["summer_mean_kwh"] = float(np.mean(summer_vals)) if len(summer_vals) else np.nan
        feat["cool_mean_kwh"] = float(np.mean(cool_vals)) if len(cool_vals) else np.nan

        if len(summer_vals) and len(non_summer) and np.mean(non_summer) > 0:
            feat["summer_sensitivity"] = float(
                (np.mean(summer_vals) - np.mean(non_summer)) / np.mean(non_summer)
            )
        else:
            feat["summer_sensitivity"] = np.nan
    else:
        feat["summer_mean_kwh"] = np.nan
        feat["cool_mean_kwh"] = np.nan
        feat["summer_sensitivity"] = np.nan

    # Linear trend slope (kWh per month) — use actual calendar offsets so
    # missing months create real gaps in the regression x-axis, consistent
    # with trend_analysis/trend.py. np.arange(n) would treat Jan and Mar as
    # 1 step apart when Feb is missing, inflating the slope.
    if n >= 3:
        if hasattr(series.index, "ordinal"):
            x = np.array(series.index.ordinal, dtype=float)
            x = x - x[0]
        else:
            x = np.arange(n, dtype=float)
        slope, _, _, _, _ = stats.linregress(x, vals)
        feat["trend_slope_kwh_per_month"] = float(slope)
    else:
        feat["trend_slope_kwh_per_month"] = np.nan

    return feat


def compute_household_features(household_row: pd.Series,
                                consumption_features: dict) -> dict:
    """
    Combine household profile fields with consumption features.
    household_row: one row from the households DataFrame.
    consumption_features: output of compute_consumption_features().
    """
    feat = dict(consumption_features)

    n_res = household_row.get("n_residents", np.nan)
    mean_kwh = feat.get("mean_kwh", np.nan)

    if pd.notna(n_res) and n_res > 0 and pd.notna(mean_kwh):
        feat["kwh_per_resident"] = mean_kwh / n_res
    else:
        feat["kwh_per_resident"] = np.nan

    home_size = household_row.get("home_size_m2", np.nan)
    if pd.notna(home_size) and home_size > 0 and pd.notna(mean_kwh):
        feat["kwh_per_m2"] = mean_kwh / home_size
    else:
        feat["kwh_per_m2"] = np.nan

    feat["has_solar"] = int(bool(household_row.get("has_solar", False)))
    feat["has_air_conditioner"] = int(bool(household_row.get("has_air_conditioner", False)))
    feat["has_inverter_ac"] = int(bool(household_row.get("has_inverter_ac", False)))
    feat["has_electric_vehicle"] = int(bool(household_row.get("has_electric_vehicle", False)))
    feat["has_electric_water_heater"] = int(bool(household_row.get("has_electric_water_heater", False)))
    feat["n_residents"] = float(n_res) if pd.notna(n_res) else np.nan

    return feat


def build_feature_matrix(households: pd.DataFrame,
                          consumption: pd.DataFrame) -> pd.DataFrame:
    """
    Build one feature row per household by combining profile + consumption features.
    Only households with at least 1 consumption record are included.
    """
    from preprocessing.pipeline import get_household_series

    rows = []
    for _, hh in households.iterrows():
        hid = hh["household_id"]
        series = get_household_series(consumption, hid)
        if len(series) == 0:
            continue
        cf = compute_consumption_features(series)
        hf = compute_household_features(hh, cf)
        hf["household_id"] = hid
        rows.append(hf)

    return pd.DataFrame(rows).set_index("household_id")
