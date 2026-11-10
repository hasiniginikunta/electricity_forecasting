"""
Anomaly detection for household electricity consumption.

DESIGN SCOPE — what this module detects and does NOT detect
-----------------------------------------------------------
This module detects SUDDEN, ISOLATED deviations from a household's own
historical baseline using a robust Z-score (MAD-based method).

It detects:
  - Sudden spikes: a single month significantly above the household's median
  - Sudden drops: a single month significantly below the household's median
    (e.g. vacancy, meter fault, billing error)

It does NOT detect:
  - Gradual consumption increases or decreases over multiple months.
    Those are handled by trend_analysis.analyse_trend(), which uses linear
    regression over the full history. The two modules are complementary:
    anomaly detection catches one-off events; trend analysis catches
    sustained directional change.
  - Missing months. Gaps in the series are preserved as-is; no imputation
    is performed. A missing month is not itself flagged as an anomaly.

THRESHOLD SELECTION
-------------------
Threshold = 3.0 (MAD-based robust Z-score).

Justification from threshold sweep on 300 households x 24 months
(214 injected anomalies, anomaly_fraction=0.03):

  Threshold  Precision  Recall    F1    FPR
  1.5        0.173      0.991   0.295  0.1446
  1.8        0.230      0.991   0.373  0.1016
  2.0        0.269      0.986   0.423  0.0820
  2.2        0.299      0.981   0.459  0.0704
  2.5        0.336      0.958   0.498  0.0580
  3.0        0.403      0.953   0.567  0.0432  <-- selected

Threshold 3.0 gives the highest F1 (0.567) and lowest FPR (4.32%).
The audit report recommended 2.5 as a "better balance", but 3.0 strictly
dominates 2.5 on both F1 and FPR simultaneously. The only cost is 10
additional missed anomalies (FN=10 vs FN=9 at 2.5) out of 214 total —
a 0.5% recall reduction in exchange for 103 fewer false positives.

For a consumer-facing product, false positives (telling a user their
consumption is anomalous when it is not) are more harmful than false
negatives (missing a genuine anomaly that trend analysis may still catch).
Threshold 3.0 is therefore the correct operating point.

CONFIDENCE AND LANGUAGE
-----------------------
Because precision is 0.403 at threshold 3.0 (i.e. ~60% of flagged months
are still false positives on synthetic data), anomaly results are presented
as "possible_anomaly" with confidence="low" rather than as confirmed
detections. The explanation text explicitly states this is a statistical
signal requiring verification.

SEVERITY BOUNDARIES
-------------------
Severity bands are multiplicative relative to the threshold:
  none:     abs_z <= 3.0
  low:      3.0 < abs_z <= 4.5   (1.0x–1.5x threshold)
  moderate: 4.5 < abs_z <= 6.0   (1.5x–2.0x threshold)
  high:     abs_z > 6.0           (>2.0x threshold)

These boundaries are PROVISIONAL. They are not calibrated against
labelled severity data. They should be treated as indicative only
until real-world labelled data is available.

SEASONAL ADJUSTMENT
-------------------
Seasonal adjustment is only applied when each calendar month in the
series has >= 2 observations (i.e. at least 2 years of data). With
single-year data, each month appears once, making its mean equal to
itself — which would zero out every residual and destroy the signal.
"""
import numpy as np
import pandas as pd
from config.settings import ANOMALY_CONFIG

# Minimum records required for a meaningful anomaly assessment.
# With 1 record: MAD=0, std=0, all Z-scores are 0 — no signal.
# With 2 records: MAD is the half-range; both points always score
#   identically (|z|=0.674) regardless of their actual values.
# Neither case produces actionable output.
MIN_RECORDS_FOR_ANOMALY = 3


def _seasonal_adjusted(series: pd.Series) -> pd.Series:
    """
    Subtract monthly seasonal mean so anomaly detection operates on residuals.
    Only applied when each calendar month present has >= 2 records (multi-year).
    """
    if not hasattr(series.index, "month"):
        return series
    month_counts = series.groupby(series.index.month).transform("count")
    if month_counts.min() < 2:
        return series
    monthly_mean = series.groupby(series.index.month).transform("mean")
    overall_mean = series.mean()
    return series - monthly_mean + overall_mean


def robust_zscore(series: pd.Series) -> pd.Series:
    """Compute robust Z-scores using MAD (signed: positive=high, negative=low)."""
    median = series.median()
    mad = (series - median).abs().median()
    if mad == 0:
        mad = series.std()
    if mad == 0:
        return pd.Series(np.zeros(len(series)), index=series.index)
    return (series - median) / (1.4826 * mad)


def detect_anomalies(series: pd.Series) -> pd.DataFrame:
    """
    Detect sudden anomalies in a household's consumption series.
    Returns a DataFrame with one row per record.

    Requires at least MIN_RECORDS_FOR_ANOMALY (3) records. With fewer
    records the result has status='insufficient_data' and is_anomaly=False
    for all rows — do not use these rows to drive savings recommendations.

    Each flagged row carries:
      is_anomaly        : bool — True if abs_z > threshold
      anomaly_status    : 'possible_anomaly' | 'normal' | 'insufficient_data'
      confidence        : 'low' | 'none' | 'insufficient_data'
      anomaly_direction : 'high' | 'low' | 'none'
      anomaly_score     : abs(z), rounded to 3dp
      severity          : 'none' | 'low' | 'moderate' | 'high' (provisional)
      explanation       : human-readable string, or None
    """
    n = len(series)
    threshold = ANOMALY_CONFIG["zscore_threshold"]

    # Insufficient data — return marked rows, no anomaly assessment
    if n < MIN_RECORDS_FOR_ANOMALY:
        rows = []
        for period, kwh in series.items():
            rows.append({
                "period": period,
                "consumption_kwh": kwh,
                "anomaly_score": None,
                "anomaly_direction": "none",
                "is_anomaly": False,
                "anomaly_status": "insufficient_data",
                "confidence": "insufficient_data",
                "severity": "none",
                "explanation": (
                    f"Only {n} record(s) available. "
                    f"At least {MIN_RECORDS_FOR_ANOMALY} are required for anomaly detection."
                ),
            })
        df = pd.DataFrame(rows)
        df["is_anomaly"] = pd.array([False] * len(df), dtype=object)
        return df

    adjusted = _seasonal_adjusted(series)
    zscores = robust_zscore(adjusted)

    results = []
    for period, kwh in series.items():
        z = float(zscores[period])
        is_anom = bool(abs(z) > threshold)
        abs_z = abs(z)
        direction = "high" if z > 0 else ("low" if z < 0 else "none")
        status = "possible_anomaly" if is_anom else "normal"
        # Confidence is always 'low' when flagged — precision on synthetic
        # data is ~0.40, meaning ~60% of flags are false positives.
        confidence = "low" if is_anom else "none"
        results.append({
            "period": period,
            "consumption_kwh": kwh,
            "anomaly_score": round(abs_z, 3),
            "anomaly_direction": direction,
            "is_anomaly": is_anom,
            "anomaly_status": status,
            "confidence": confidence,
            "severity": _severity(abs_z, threshold),
            "explanation": _explain(kwh, series, z, threshold) if is_anom else None,
        })

    df = pd.DataFrame(results)
    df["is_anomaly"] = pd.array([bool(v) for v in df["is_anomaly"]], dtype=object)

    # Isolation Forest when enough data
    min_if = ANOMALY_CONFIG["min_records_for_isolation_forest"]
    if len(series) >= min_if:
        df = _add_isolation_forest(df, adjusted)

    return df


def _severity(abs_z: float, threshold: float) -> str:
    """
    Provisional severity bands — multiplicative relative to threshold.
    Not calibrated against labelled data; treat as indicative only.
    """
    if abs_z <= threshold:
        return "none"
    elif abs_z <= threshold * 1.5:
        return "low"
    elif abs_z <= threshold * 2.0:
        return "moderate"
    else:
        return "high"


def _explain(kwh: float, series: pd.Series, z: float, threshold: float) -> str:
    median = series.median()
    direction = "higher" if kwh > median else "lower"
    pct = abs(kwh - median) / median * 100
    anomaly_type = "spike" if z > 0 else "drop"
    return (
        f"Consumption ({kwh:.0f} kWh) is {pct:.0f}% {direction} than this "
        f"household's typical level ({median:.0f} kWh). "
        f"Detected as a possible {anomaly_type} (score: {abs(z):.2f}, "
        f"threshold: {threshold}). "
        "This is a statistical signal — please verify before acting on it."
    )


def _add_isolation_forest(df: pd.DataFrame, adjusted: pd.Series) -> pd.DataFrame:
    from sklearn.ensemble import IsolationForest
    contamination = ANOMALY_CONFIG["isolation_forest_contamination"]
    X = adjusted.values.reshape(-1, 1)
    clf = IsolationForest(contamination=contamination, random_state=42)
    scores = clf.fit_predict(X)  # -1 = anomaly, 1 = normal
    df["isolation_forest_flag"] = (scores == -1)
    return df
