"""
Household segmentation via K-Means clustering.
K is selected by silhouette score over a configurable range.
Cluster labels are derived from actual cluster statistics, not hardcoded.

Evaluation metrics (silhouette, Davies-Bouldin) are computed on the same
scaled feature space that K-Means operates on — not on raw features.
This ensures the scores reflect the actual cluster geometry.

The label_map (cluster_id → profile string) is saved alongside the pipeline
so that new households can be predicted via pipeline.predict() and then
mapped to a human-readable label without needing a pre-existing ID lookup.
"""
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


# Features used for clustering — updated for Indian household context
CLUSTER_FEATURES = [
    "mean_kwh", "cv", "summer_sensitivity", "trend_slope_kwh_per_month",
    "kwh_per_resident", "has_solar", "has_air_conditioner",
    "has_inverter_ac", "has_electric_vehicle", "n_residents",
]


def _build_cluster_pipeline(k: int, seed: int) -> Pipeline:
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("kmeans", KMeans(n_clusters=k, random_state=seed, n_init=10)),
    ])


def _transform_features(pipeline: Pipeline, X: np.ndarray) -> np.ndarray:
    """Return the scaled feature representation used by K-Means."""
    imputed = pipeline.named_steps["imputer"].transform(X)
    scaled = pipeline.named_steps["scaler"].transform(imputed)
    return scaled


def select_k(feature_matrix: pd.DataFrame,
             k_min: int = 2, k_max: int = 8,
             seed: int = 42) -> dict:
    """Evaluate K values; silhouette and DB computed on scaled space."""
    X = feature_matrix[CLUSTER_FEATURES].values
    results = {}
    for k in range(k_min, k_max + 1):
        pipe = _build_cluster_pipeline(k, seed)
        labels = pipe.fit_predict(X)
        if len(set(labels)) < 2:
            continue
        X_scaled = _transform_features(pipe, X)
        sil = silhouette_score(X_scaled, labels)
        db = davies_bouldin_score(X_scaled, labels)
        results[k] = {"silhouette": round(sil, 4), "davies_bouldin": round(db, 4)}
    return results


def train_clustering(feature_matrix: pd.DataFrame,
                     k_min: int = 2, k_max: int = 8,
                     seed: int = 42) -> tuple:
    """
    Select best K, train final pipeline.
    Returns (pipeline, labels_series, eval_scores).
    """
    scores = select_k(feature_matrix, k_min, k_max, seed)
    best_k = max(scores, key=lambda k: scores[k]["silhouette"])
    pipe = _build_cluster_pipeline(best_k, seed)
    X = feature_matrix[CLUSTER_FEATURES].values
    labels = pipe.fit_predict(X)
    labels_series = pd.Series(labels, index=feature_matrix.index, name="cluster_id")
    eval_scores = {"best_k": best_k, "scores_by_k": scores}
    return pipe, labels_series, eval_scores


def label_clusters(feature_matrix: pd.DataFrame,
                   labels: pd.Series) -> tuple[pd.Series, dict]:
    """
    Derive human-readable cluster labels from actual cluster statistics.
    Returns (profile_labels_series, label_map dict).
    label_map maps integer cluster_id -> profile string and is saved so
    new households can be labelled after pipeline.predict().

    STABILITY NOTE: On 300 synthetic households, best K varies between 5
    and 6 across random seeds, with Adjusted Rand Index (ARI) of 0.70-1.0
    vs the reference seed. This means ~0-30% of household assignments may
    differ across training runs. Cluster profile labels (e.g.
    'summer_sensitive') are INDICATIVE, not definitive classifications.
    Do not present them to users as fixed household categories.
    """
    fm = feature_matrix.copy()
    fm["cluster_id"] = labels

    cluster_stats = fm.groupby("cluster_id").agg(
        mean_kwh=("mean_kwh", "median"),
        cv=("cv", "median"),
        summer_sensitivity=("summer_sensitivity", "median"),
        trend_slope=("trend_slope_kwh_per_month", "median"),
    )

    overall_median_kwh = fm["mean_kwh"].median()
    label_map = {}

    for cid, row in cluster_stats.iterrows():
        if row["mean_kwh"] < overall_median_kwh * 0.75:
            label = "low_consumption"
        elif row["mean_kwh"] > overall_median_kwh * 1.35:
            label = "high_baseline"
        elif pd.notna(row["summer_sensitivity"]) and row["summer_sensitivity"] > 0.25:
            label = "summer_sensitive"
        elif pd.notna(row["trend_slope"]) and row["trend_slope"] > 5:
            label = "increasing_trend"
        elif pd.notna(row["cv"]) and row["cv"] < 0.10:
            label = "consistent_consumption"
        else:
            label = f"moderate_cluster_{cid}"
        label_map[int(cid)] = label

    profile_labels = labels.map(label_map)
    return profile_labels, label_map


def predict_cluster(pipeline: Pipeline,
                    feature_matrix: pd.DataFrame,
                    label_map: dict) -> pd.Series:
    """
    Assign cluster profile labels to new households using the fitted pipeline.
    Works for any household — does not require a pre-existing ID lookup.
    """
    X = feature_matrix[CLUSTER_FEATURES].values
    cluster_ids = pipeline.predict(X)
    labels = [label_map.get(int(cid), f"cluster_{cid}") for cid in cluster_ids]
    return pd.Series(labels, index=feature_matrix.index, name="profile")


def save_clustering_artifacts(pipeline, labels: pd.Series,
                               profile_labels: pd.Series,
                               label_map: dict,
                               eval_scores: dict, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, out_dir / "clustering_pipeline.pkl")
    labels.to_csv(out_dir / "cluster_assignments.csv")
    profile_labels.to_csv(out_dir / "cluster_profile_labels.csv")
    with open(out_dir / "cluster_label_map.json", "w") as f:
        json.dump({str(k): v for k, v in label_map.items()}, f, indent=2)
    with open(out_dir / "clustering_eval.json", "w") as f:
        json.dump(eval_scores, f, indent=2)
    best_k = eval_scores["best_k"]
    print(f"[Clustering] Best K={best_k} | "
          f"Silhouette={eval_scores['scores_by_k'][best_k]['silhouette']} "
          "(computed on scaled feature space)")
    print("[Clustering] NOTE: Best K and cluster assignments vary across seeds "
          "(ARI 0.70-1.0 on 300hh synthetic data). "
          "Profile labels are indicative, not definitive classifications.")
