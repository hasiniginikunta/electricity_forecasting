"""
main.py — M2 Inference Entry Point
====================================
Generates a structured intelligence report for a single household.
Implements the 4-stage cold-start strategy.
Does NOT retrain models — loads pre-trained artifacts.

Usage:
    python main.py --household_id H0001
    python main.py --household_id H0001 --demo
"""
import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
from config.settings import DATA_DIR, ARTIFACTS_DIR
from preprocessing.pipeline import (
    filter_valid_consumption, impute_households, get_household_series,
)
from features.engineering import compute_consumption_features, compute_household_features
from trend_analysis.trend import analyse_trend
from anomaly_detection.detector import detect_anomalies
from benchmarking.peer_comparison import benchmark_household
from savings.targets import calculate_savings_target


def _load_data():
    hh = pd.read_csv(DATA_DIR / "synthetic_households.csv")
    cons = pd.read_csv(DATA_DIR / "synthetic_consumption.csv")
    hh = impute_households(hh)
    cons = filter_valid_consumption(cons)
    return hh, cons


def _load_cluster_artifacts():
    import joblib
    import json
    pipe_path = ARTIFACTS_DIR / "clustering" / "clustering_pipeline.pkl"
    label_map_path = ARTIFACTS_DIR / "clustering" / "cluster_label_map.json"
    if not pipe_path.exists():
        return None, None
    pipeline = joblib.load(pipe_path)
    label_map = {}
    if label_map_path.exists():
        with open(label_map_path) as f:
            label_map = {int(k): v for k, v in json.load(f).items()}
    return pipeline, label_map


def _cold_start_stage(n_records: int, n_households_total: int) -> int:
    """Determine which cold-start stage applies."""
    if n_records == 0:
        return 1
    if n_records < 3:
        return 2
    if n_households_total < 20:
        return 3
    return 4


def run_inference(household_id: str,
                  households: pd.DataFrame,
                  consumption: pd.DataFrame) -> dict:

    target_rows = households[households["household_id"] == household_id]
    if target_rows.empty:
        return {"household_id": household_id, "error": "household_not_found"}

    target_hh = target_rows.iloc[0]
    series = get_household_series(consumption, household_id)
    n_records = len(series)
    stage = _cold_start_stage(n_records, len(households))

    result = {
        "household_id": household_id,
        "data_source": str(target_hh.get("data_source", "unknown")),
        "cold_start_stage": stage,
        "n_consumption_records": n_records,
    }

    # Stage 1: no consumption data
    if stage == 1:
        result["data_status"] = "new_user"
        result["message"] = (
            "No consumption records found. Submit your first monthly reading "
            "to begin receiving personalised insights."
        )
        result["consumption_profile"] = None
        result["trend"] = None
        result["anomaly"] = None
        result["benchmark"] = None
        result["savings_target"] = None
        return result

    # Compute features
    cons_features = compute_consumption_features(series)
    hh_features = compute_household_features(target_hh, cons_features)

    # Trend
    trend = analyse_trend(series)

    # Anomaly
    # Stage 2 (1-2 records): detector returns insufficient_data rows.
    # We suppress the result entirely at this stage to avoid misleading output.
    anomaly_df = detect_anomalies(series)
    if stage == 2:
        anomaly_out = {
            "detected": False,
            "anomaly_status": "insufficient_data",
            "confidence": "insufficient_data",
            "severity": "none",
            "anomaly_score": None,
            "explanation": (
                f"Only {n_records} record(s) available. "
                "Anomaly detection requires at least 3 months of data."
            ),
        }
    else:
        latest_anomaly = anomaly_df.iloc[-1].to_dict() if not anomaly_df.empty else {}
        anomaly_out = {
            "detected": bool(latest_anomaly.get("is_anomaly", False)),
            "anomaly_status": latest_anomaly.get("anomaly_status", "normal"),
            "confidence": latest_anomaly.get("confidence", "none"),
            "severity": latest_anomaly.get("severity", "none"),
            "anomaly_score": latest_anomaly.get("anomaly_score"),
            "explanation": latest_anomaly.get("explanation"),
        }

    # Clustering (stage 3+)
    consumption_profile = None
    if stage >= 3:
        pipeline, label_map = _load_cluster_artifacts()
        if pipeline is not None and label_map:
            from features.engineering import build_feature_matrix
            from clustering.kmeans_model import predict_cluster
            single_hh = households[households["household_id"] == household_id]
            fm = build_feature_matrix(single_hh, consumption)
            if not fm.empty:
                profile_series = predict_cluster(pipeline, fm, label_map)
                consumption_profile = {
                    "profile": str(profile_series.iloc[0]),
                    "note": (
                        "SYNTHETIC data cluster assignment. "
                        "Cluster labels are indicative; best K varies across "
                        "training runs (ARI 0.70-1.0 across seeds)."
                    ),
                }

    # Benchmarking (stage 3+)
    benchmark = None
    if stage >= 3:
        benchmark = benchmark_household(household_id, households, consumption)

    # Savings target
    savings = calculate_savings_target(
        trend_result=trend,
        benchmark_result=benchmark or {},
        anomaly_result=anomaly_df.to_dict("records"),
        household_features=hh_features,
    )

    result.update({
        "data_status": "sufficient" if stage >= 3 else "limited",
        "consumption_profile": consumption_profile,
        "trend": {
            "status": trend.get("status"),
            "direction": trend.get("direction"),
            "percentage_change": trend.get("percentage_change"),
            "slope_kwh_per_month": trend.get("slope_kwh_per_month"),
            "rolling_3m_avg_kwh": trend.get("rolling_3m_avg"),
            "message": trend.get("message"),
        },
        "anomaly": anomaly_out,
        "benchmark": benchmark,
        "savings_target": savings,
    })

    return result


def main():
    parser = argparse.ArgumentParser(description="M2 Household Intelligence Inference")
    parser.add_argument("--household_id", type=str, default="H0001")
    parser.add_argument("--demo", action="store_true",
                        help="Run demo on first 3 households and print results")
    args = parser.parse_args()

    households, consumption = _load_data()

    if args.demo:
        sample_ids = households["household_id"].head(3).tolist()
        for hid in sample_ids:
            result = run_inference(hid, households, consumption)
            print(json.dumps(result, indent=2, default=str))
            print("-" * 60)
    else:
        result = run_inference(args.household_id, households, consumption)
        print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
