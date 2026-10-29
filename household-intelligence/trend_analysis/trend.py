"""
Household consumption trend analysis.
Uses statistical methods (linear regression, rolling averages).
Uses actual calendar month offsets so missing months create real gaps —
January and March are 2 months apart, not 1.
"""
import numpy as np
import pandas as pd
from scipy import stats
from config.settings import TREND_CONFIG


def analyse_trend(series: pd.Series) -> dict:
    """
    Analyse consumption trend for a single household.
    series: time-sorted pd.Series with Period index (year-month) and kWh values.
    Returns a structured result dict.
    """
    n = len(series)
    min_records = TREND_CONFIG["min_records_for_trend"]

    if n < min_records:
        return {
            "status": "insufficient_data",
            "n_records": n,
            "min_required": min_records,
            "direction": None,
            "percentage_change": None,
            "slope_kwh_per_month": None,
            "rolling_3m_avg": None,
            "message": f"Need at least {min_records} records; have {n}.",
        }

    vals = series.values.astype(float)

    # Use actual calendar month offsets from the first record.
    # This means a gap (e.g. missing February) is represented as a real
    # 2-month distance between January and March, not a 1-step distance.
    if hasattr(series.index, "ordinal"):
        x = np.array(series.index.ordinal, dtype=float)
        x = x - x[0]  # offset from first record
    else:
        # Fallback for plain integer index (no period info)
        x = np.arange(n, dtype=float)

    # Linear regression
    slope, intercept, r_value, p_value, _ = stats.linregress(x, vals)

    # Direction classification
    if p_value > 0.10:
        direction = "stable"
    elif slope > 0:
        direction = "increasing"
    else:
        direction = "decreasing"

    # Percentage change: first vs last 3 records (by calendar position)
    window = min(3, n // 2)
    early_mean = float(np.mean(vals[:window]))
    late_mean = float(np.mean(vals[-window:]))
    pct_change = ((late_mean - early_mean) / early_mean * 100) if early_mean > 0 else None

    # Rolling 3-month average (last 3 available records)
    rolling_avg = float(np.mean(vals[-3:])) if n >= 3 else None

    # Seasonal pattern detection (requires Period index with month attribute)
    seasonal_note = None
    if n >= TREND_CONFIG["min_records_for_seasonal"] and hasattr(series.index, "month"):
        monthly_means = series.groupby(series.index.month).mean()
        seasonal_range = float(monthly_means.max() - monthly_means.min())
        if seasonal_range > 0.3 * float(np.mean(vals)):
            seasonal_note = "strong_seasonal_pattern"
        else:
            seasonal_note = "weak_seasonal_pattern"

    return {
        "status": "ok",
        "n_records": n,
        "direction": direction,
        "slope_kwh_per_month": round(float(slope), 3),
        "r_squared": round(float(r_value ** 2), 4),
        "p_value": round(float(p_value), 4),
        "percentage_change": round(pct_change, 2) if pct_change is not None else None,
        "rolling_3m_avg": round(rolling_avg, 1) if rolling_avg is not None else None,
        "seasonal_pattern": seasonal_note,
        "message": None,
    }
