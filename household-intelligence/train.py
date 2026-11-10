"""
train.py — M2 Training Script
==============================
Generates SYNTHETIC data, trains all models, saves artifacts, prints evaluation.
Run once before inference. Do NOT retrain on every inference call.

Usage:
    python train.py
"""
import sys
from pathlib import Path

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config.settings import DATA_DIR, ARTIFACTS_DIR, SYNTHETIC_CONFIG, CLUSTERING_CONFIG
from data.synthetic_generator import save_synthetic_data
import pandas as pd

from preprocessing.pipeline import (
    validate_households, filter_valid_consumption,
    impute_households, HouseholdProfileTransformer,
)
from features.engineering import build_feature_matrix
from clustering.kmeans_model import (
    train_clustering, label_clusters, save_clustering_artifacts,
)
from evaluation.metrics import evaluate_clustering, save_evaluation_report


def main():
    print("=" * 60)
    print("M2 Household Intelligence Engine - Training")
    print("Dataset: SYNTHETIC")
    print("=" * 60)

    # 1. Generate synthetic data
    hh_path, cons_path = save_synthetic_data(
        DATA_DIR,
        n_households=SYNTHETIC_CONFIG["n_households"],
        n_months=SYNTHETIC_CONFIG["n_months"],
        seed=SYNTHETIC_CONFIG["random_seed"],
    )

    households = pd.read_csv(hh_path)
    consumption = pd.read_csv(cons_path)

    # 2. Validate and clean
    households = validate_households(impute_households(households))
    consumption = filter_valid_consumption(consumption)
    print(f"[Preprocessing] {len(households)} households, "
          f"{len(consumption)} valid consumption records")

    # 3. Feature engineering
    feature_matrix = build_feature_matrix(households, consumption)
    print(f"[Features] Feature matrix: {feature_matrix.shape}")

    # 4. Train clustering
    pipeline, labels, eval_scores = train_clustering(
        feature_matrix,
        k_min=CLUSTERING_CONFIG["k_min"],
        k_max=CLUSTERING_CONFIG["k_max"],
        seed=CLUSTERING_CONFIG["random_seed"],
    )
    profile_labels, label_map = label_clusters(feature_matrix, labels)

    # 5. Save clustering artifacts
    cluster_dir = ARTIFACTS_DIR / "clustering"
    save_clustering_artifacts(pipeline, labels, profile_labels, label_map, eval_scores, cluster_dir)

    # 6. Save preprocessing transformer
    transformer = HouseholdProfileTransformer()
    transformer.fit(households)
    transformer.save(ARTIFACTS_DIR / "preprocessing" / "profile_transformer.pkl")
    print(f"[Preprocessing] Transformer saved.")

    # 7. Save feature matrix
    fm_path = ARTIFACTS_DIR / "feature_matrix.csv"
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    feature_matrix.to_csv(fm_path)
    print(f"[Features] Feature matrix saved -> {fm_path}")

    # 8. Evaluation report
    cluster_report = evaluate_clustering(eval_scores)
    print("\n" + cluster_report)
    save_evaluation_report(cluster_report, ARTIFACTS_DIR / "evaluation",
                           "clustering_eval.txt")

    print("\n[Training complete] All artifacts saved to:", ARTIFACTS_DIR)


if __name__ == "__main__":
    main()
