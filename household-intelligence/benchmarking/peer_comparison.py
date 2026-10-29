"""
Similar-household benchmarking (peer comparison).
Privacy: only aggregated, anonymised statistics are returned.
Seasonal fairness: target and peers are compared over the same calendar
months so that a household measured in summer is not compared against
peers measured in winter.

Coverage filter: a peer must have data for at least min_coverage_months
of the target's reference window to be counted toward the cohort.
This prevents a peer with only 1 incidental matching month from being
treated as equivalent to a peer with full coverage.
"""
import numpy as np
import pandas as pd
from config.settings import BENCHMARKING_CONFIG


def _filter_peers(households: pd.DataFrame,
                  target: pd.Series,
                  consumption: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """
    Filter households similar to the target.
    Returns (peers_df, tier) where tier indicates match quality:
      1 = same home_type + n_residents +/-1 + same state  (strongest match)
      2 = same home_type + n_residents +/-1, any state
      3 = n_residents +/-1 only                           (weakest match)
    """
    peers = households[households["household_id"] != target["household_id"]].copy()

    hids_with_data = consumption["household_id"].unique()
    peers = peers[peers["household_id"].isin(hids_with_data)]

    # Tier-1: same home_type + n_residents +/-1 + same state
    t1 = peers[
        (peers["home_type"] == target.get("home_type")) &
        (peers["n_residents"].between(
            target.get("n_residents", 2) - 1,
            target.get("n_residents", 2) + 1)) &
        (peers["state"] == target.get("state"))
    ]
    if len(t1) >= BENCHMARKING_CONFIG["min_cohort_size"]:
        return t1, 1

    # Tier-2: relax state constraint
    t2 = peers[
        (peers["home_type"] == target.get("home_type")) &
        (peers["n_residents"].between(
            target.get("n_residents", 2) - 1,
            target.get("n_residents", 2) + 1))
    ]
    if len(t2) >= BENCHMARKING_CONFIG["min_cohort_size"]:
        return t2, 2

    # Tier-3: only n_residents +/-1 — broadest fallback, lowest confidence
    t3 = peers[
        peers["n_residents"].between(
            target.get("n_residents", 2) - 1,
            target.get("n_residents", 2) + 1)
    ]
    return t3, 3


_TIER_CONFIDENCE = {
    1: "high",    # same state, home type, resident count
    2: "medium",  # same home type and resident count, different state
    3: "low",     # resident count only — treat comparison with caution
}


def _common_months(target_cons: pd.DataFrame,
                   peer_cons: pd.DataFrame) -> pd.DataFrame:
    """
    Return peer consumption restricted to the same (year, month) pairs
    that the target household has records for.
    This prevents comparing a target's summer months against peers' winter months.
    """
    target_periods = set(
        zip(target_cons["billing_year"], target_cons["billing_month"])
    )
    mask = peer_cons.apply(
        lambda r: (r["billing_year"], r["billing_month"]) in target_periods, axis=1
    )
    return peer_cons[mask]


def benchmark_household(household_id: str,
                         households: pd.DataFrame,
                         consumption: pd.DataFrame) -> dict:
    """
    Compare a household's consumption against its peer group over matching
    calendar periods. Returns aggregated statistics only.

    Coverage filter: peers must have data for at least
    BENCHMARKING_CONFIG['min_coverage_months'] of the target's reference
    window months. Peers below this threshold are excluded before the
    cohort size check is applied.
    """
    min_cohort = BENCHMARKING_CONFIG["min_cohort_size"]
    min_coverage = BENCHMARKING_CONFIG["min_coverage_months"]

    target_hh = households[households["household_id"] == household_id]
    if target_hh.empty:
        return {"status": "household_not_found"}
    target_hh = target_hh.iloc[0]

    target_cons = consumption[consumption["household_id"] == household_id]
    if target_cons.empty:
        return {"status": "no_consumption_data"}

    target_cons = target_cons.sort_values(["billing_year", "billing_month"])
    # Use last 3 available months as the reference window
    reference_window = target_cons.tail(3)
    n_reference_months = len(reference_window)
    target_recent_mean = float(reference_window["consumption_kwh"].mean())

    peers, match_tier = _filter_peers(households, target_hh, consumption)
    match_confidence = _TIER_CONFIDENCE[match_tier]
    if len(peers) < min_cohort:
        return {
            "status": "insufficient_data",
            "cohort_size": len(peers),
            "min_required": min_cohort,
            "message": (
                f"Only {len(peers)} comparable households found "
                f"(minimum {min_cohort} required). "
                "Peer comparison is not available yet."
            ),
        }

    peer_ids = peers["household_id"].tolist()
    peer_cons_all = consumption[consumption["household_id"].isin(peer_ids)]

    # Restrict peers to the same calendar months as the target's reference window
    aligned_peer_cons = _common_months(reference_window, peer_cons_all)

    if aligned_peer_cons.empty:
        return {
            "status": "insufficient_data",
            "cohort_size": 0,
            "min_required": min_cohort,
            "message": "No peers have data for the same calendar months as this household.",
        }

    # Count how many reference months each peer has data for
    peer_month_counts = (
        aligned_peer_cons
        .groupby("household_id")[["billing_year", "billing_month"]]
        .apply(lambda df: len(set(zip(df["billing_year"], df["billing_month"]))))
    )

    # Apply coverage filter: exclude peers below min_coverage_months threshold
    covered_peer_ids = peer_month_counts[peer_month_counts >= min_coverage].index
    aligned_peer_cons = aligned_peer_cons[
        aligned_peer_cons["household_id"].isin(covered_peer_ids)
    ]

    peer_means = (
        aligned_peer_cons
        .groupby("household_id")["consumption_kwh"]
        .mean()
    )

    # Recheck cohort size after coverage filtering
    if len(peer_means) < min_cohort:
        return {
            "status": "insufficient_data",
            "cohort_size": len(peer_means),
            "min_required": min_cohort,
            "message": (
                f"Only {len(peer_means)} peers have data for at least "
                f"{min_coverage} of the {n_reference_months} reference months "
                "(coverage filter). Peer comparison is not available yet."
            ),
        }

    p25 = float(np.percentile(peer_means, 25))
    p50 = float(np.percentile(peer_means, 50))
    p75 = float(np.percentile(peer_means, 75))
    diff_pct = round((target_recent_mean - p50) / p50 * 100, 1) if p50 > 0 else None

    # Summarise per-peer coverage for transparency
    peer_coverage = peer_month_counts[peer_month_counts >= min_coverage]

    return {
        "status": "available",
        "match_tier": match_tier,
        "match_confidence": match_confidence,
        "match_note": (
            None if match_tier == 1 else
            "State constraint relaxed — peers may be from different states."
            if match_tier == 2 else
            "Broad match (resident count only) — home type and state not matched. "
            "Treat this comparison with caution."
        ),
        "cohort_size": len(peer_means),
        "comparison_months": reference_window[["billing_year", "billing_month"]].to_dict("records"),
        "peer_coverage_months": {
            "min_required": min_coverage,
            "reference_window_size": n_reference_months,
            "peer_min": int(peer_coverage.min()),
            "peer_max": int(peer_coverage.max()),
        },
        "household_recent_mean_kwh": round(target_recent_mean, 1),
        "peer_p25_kwh": round(p25, 1),
        "peer_median_kwh": round(p50, 1),
        "peer_p75_kwh": round(p75, 1),
        "difference_from_median_pct": diff_pct,
        "relative_position": _position(target_recent_mean, p25, p50, p75),
    }


def _position(val: float, p25: float, p50: float, p75: float) -> str:
    if val <= p25:
        return "below_25th_percentile"
    elif val <= p50:
        return "below_median"
    elif val <= p75:
        return "above_median"
    else:
        return "above_75th_percentile"
