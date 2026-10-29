"""
Personalised savings target calculation.

SIGNAL POLICY
-------------
Targets are estimates derived from measurable signals only:

  Signal 1 — Peer gap: household is above the peer group median over the
    same calendar period. The gap is quantified; only gaps > 5% contribute.

  Signal 2 — Increasing trend: statistically significant upward trend
    (p < 0.10) with > 10% change over the measured period.

  Signal 3 — Repeated HIGH anomalies: >= 2 months with anomaly_direction
    == 'high' (consumption spike). This suggests irregular high-use events
    that may be avoidable.

    LOW anomalies (sudden drops) are explicitly excluded. A drop indicates
    vacancy, a meter fault, or a billing error — not avoidable waste.
    Counting drops as a savings signal would be misleading.

    Anomalies alone (without a peer gap or trend signal) do NOT generate
    a savings target. Anomaly detection has ~40% precision on synthetic
    data; acting on anomalies without corroborating evidence is unreliable.

FLOOR REMOVAL
-------------
The previous min_target_pct=3.0 floor inflated weak signals. A 6% peer
gap produced a raw contribution of 1.8% which was then rounded up to 3.0%.
The floor is removed. Targets now reflect the actual computed signal
strength. Small signals produce small targets; no target is generated if
the total contribution is below 1.0%.

All targets are presented as estimates with an explicit disclaimer.
"""
from config.settings import SAVINGS_CONFIG

# Minimum meaningful target to report. Below this the signal is too weak
# to present as an actionable recommendation.
_MIN_REPORTABLE_PCT = 1.0


def calculate_savings_target(trend_result: dict,
                              benchmark_result: dict,
                              anomaly_result: list,
                              household_features: dict) -> dict:
    """
    Derive a realistic savings estimate from available data signals.

    Parameters
    ----------
    trend_result      : output of trend_analysis.analyse_trend()
    benchmark_result  : output of benchmarking.benchmark_household()
    anomaly_result    : list of anomaly dicts (from detect_anomalies)
    household_features: dict of computed features (context only, not used
                        as a direct savings signal)

    Returns
    -------
    dict with target_percentage (estimate), basis, explanation, disclaimer
    """
    reasons = []
    target_pct = 0.0
    has_primary_signal = False  # peer gap or trend — required for anomaly signal

    # Signal 1: household is measurably above peer median.
    # Tier-3 (low-confidence) peer results are excluded from generating a
    # savings target independently. They may still be shown as informational
    # comparisons in the UI, but the weak match (resident count only, no
    # home type or state alignment) is insufficient evidence for a savings
    # recommendation. Tier-1 and Tier-2 results are accepted.
    peer_confidence = benchmark_result.get("match_confidence", "high")
    peer_eligible = (
        benchmark_result.get("status") == "available"
        and peer_confidence in ("high", "medium")
    )
    if peer_eligible:
        diff = benchmark_result.get("difference_from_median_pct", 0) or 0
        if diff > 15:
            contribution = min(diff * 0.4, 10.0)
            target_pct += contribution
            has_primary_signal = True
            reasons.append(
                f"Your consumption is {diff:.1f}% above similar households in the same "
                f"period. Closing part of this gap could save an estimated "
                f"{contribution:.1f}% (estimate based on peer comparison)."
            )
        elif diff > 5:
            contribution = diff * 0.3
            target_pct += contribution
            has_primary_signal = True
            reasons.append(
                f"Your consumption is {diff:.1f}% above similar households. "
                f"An estimated {contribution:.1f}% reduction may be achievable "
                "(estimate based on peer comparison)."
            )

    # Signal 2: statistically significant increasing trend
    if trend_result.get("status") == "ok":
        direction = trend_result.get("direction")
        pct_change = trend_result.get("percentage_change") or 0
        if direction == "increasing" and pct_change > 10:
            contribution = min(pct_change * 0.25, 5.0)
            target_pct += contribution
            has_primary_signal = True
            reasons.append(
                f"Your consumption has risen by {pct_change:.1f}% over the measured "
                f"period. Reversing part of this trend could save an estimated "
                f"{contribution:.1f}% (estimate based on trend analysis)."
            )

    # Signal 3: repeated HIGH anomalies — only when a primary signal exists.
    # Only spikes (anomaly_direction == 'high') count as potential waste.
    # Drops (direction == 'low') indicate vacancy/fault, not avoidable waste.
    # Anomalies alone (no peer gap, no trend) are insufficient evidence.
    if has_primary_signal:
        high_anomalies = [
            a for a in anomaly_result
            if a.get("is_anomaly") and a.get("anomaly_direction") == "high"
        ]
        if len(high_anomalies) >= 2:
            contribution = 2.0
            target_pct += contribution
            reasons.append(
                f"{len(high_anomalies)} months with unusually high consumption "
                f"were detected. Investigating these could yield additional savings "
                f"(+{contribution:.1f}% estimate)."
            )

    # Cap at configured maximum
    max_t = SAVINGS_CONFIG["max_target_pct"]
    target_pct = min(target_pct, max_t)
    target_pct = round(target_pct, 1)

    # Do not report targets below the minimum meaningful threshold
    if not reasons or target_pct < _MIN_REPORTABLE_PCT:
        return {
            "status": "no_target",
            "target_percentage": None,
            "basis": "insufficient_signals",
            "explanation": (
                "Not enough data or measurable signals to generate a savings estimate. "
                "Continue submitting monthly readings to unlock personalised insights."
            ),
        }

    return {
        "status": "available",
        "target_percentage": target_pct,
        "basis": "data_driven_estimate",
        "explanation": " ".join(reasons),
        "disclaimer": (
            "This is a statistical estimate based on available data. "
            "Actual savings will depend on your specific usage patterns and actions taken."
        ),
    }
