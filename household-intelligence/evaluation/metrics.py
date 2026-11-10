"""
Evaluation utilities for all M2 components.
Clearly distinguishes synthetic-data evaluation from real-world performance.
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import precision_score, recall_score, f1_score


# ── Clustering evaluation ─────────────────────────────────────────────────────
def evaluate_clustering(eval_scores: dict) -> str:
    best_k = eval_scores["best_k"]
    best = eval_scores["scores_by_k"][best_k]
    lines = [
        "[SYNTHETIC DATA EVALUATION - Clustering]",
        f"  Best K : {best_k}",
        f"  Silhouette Score : {best['silhouette']} (higher is better, max 1.0)",
        f"  Davies-Bouldin   : {best['davies_bouldin']} (lower is better)",
        "",
        "  All K scores:",
    ]
    for k, s in eval_scores["scores_by_k"].items():
        lines.append(f"    K={k}: silhouette={s['silhouette']}, DB={s['davies_bouldin']}")
    return "\n".join(lines)


# ── Anomaly detection evaluation ──────────────────────────────────────────────
def evaluate_anomaly_detection(anomaly_df: pd.DataFrame,
                                true_label_col: str = "is_injected_anomaly") -> str:
    """
    Evaluate anomaly detection against known injected anomalies (synthetic only).
    anomaly_df must contain 'is_anomaly' (predicted) and true_label_col.
    """
    if true_label_col not in anomaly_df.columns:
        return "[Anomaly Eval] No ground-truth labels available."

    y_true = anomaly_df[true_label_col].astype(int)
    y_pred = anomaly_df["is_anomaly"].astype(int)

    p = precision_score(y_true, y_pred, zero_division=0)
    r = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    n_true = int(y_true.sum())
    n_pred = int(y_pred.sum())

    return "\n".join([
        "[SYNTHETIC DATA EVALUATION - Anomaly Detection]",
        f"  Injected anomalies : {n_true}",
        f"  Detected anomalies : {n_pred}",
        f"  Precision : {p:.3f}",
        f"  Recall    : {r:.3f}",
        f"  F1 Score  : {f1:.3f}",
        "  Note: Evaluation is on SYNTHETIC injected anomalies only.",
        "  Real-world performance may differ.",
    ])


# ── Trend evaluation ──────────────────────────────────────────────────────────
def evaluate_trend_detection(test_cases: list) -> str:
    """
    test_cases: list of dicts with keys 'expected_direction' and 'result' (trend dict).
    """
    correct = sum(
        1 for tc in test_cases
        if tc["result"].get("direction") == tc["expected_direction"]
    )
    total = len(test_cases)
    lines = [
        "[SYNTHETIC DATA EVALUATION - Trend Detection]",
        f"  Correct direction : {correct}/{total}",
    ]
    for tc in test_cases:
        got = tc["result"].get("direction", "N/A")
        exp = tc["expected_direction"]
        status = "✓" if got == exp else "✗"
        ok = "OK" if got == exp else "FAIL"
        lines.append(f"    [{ok}] expected={exp}, got={got}")
    return "\n".join(lines)


# ── Benchmarking evaluation ───────────────────────────────────────────────────
def evaluate_benchmarking(results: list) -> str:
    available = sum(1 for r in results if r.get("status") == "available")
    insufficient = sum(1 for r in results if r.get("status") == "insufficient_data")
    not_found = sum(1 for r in results if r.get("status") not in
                    ("available", "insufficient_data"))
    return "\n".join([
        "[SYNTHETIC DATA EVALUATION - Benchmarking]",
        f"  Available benchmarks    : {available}",
        f"  Insufficient cohort     : {insufficient}",
        f"  Other (no data etc.)    : {not_found}",
    ])


def save_evaluation_report(report: str, out_dir: Path, filename: str = "eval_report.txt"):
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / filename
    path.write_text(report, encoding="utf-8")
    print(f"[Evaluation] Report saved -> {path}")
