"""Central configuration for the M2 Household Intelligence Engine.
Context: Indian household electricity consumption (primary: Telangana).
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Paths
DATA_DIR = BASE_DIR / "data"
ARTIFACTS_DIR = BASE_DIR / "artifacts"
MODELS_DIR = BASE_DIR / "models"

# Synthetic data generation
SYNTHETIC_CONFIG = {
    "n_households": 300,
    "n_months": 24,
    "random_seed": 42,
}

# Clustering
CLUSTERING_CONFIG = {
    "k_min": 2,
    "k_max": 8,
    "random_seed": 42,
}

# Anomaly detection
# Threshold = 3.0 selected from sweep on 300hh x 24mo (anomaly_fraction=0.03):
#   threshold=3.0 gives F1=0.567, FPR=0.0432 — best on both metrics.
#   See anomaly_detection/detector.py module docstring for full sweep table.
ANOMALY_CONFIG = {
    "zscore_threshold": 3.0,
    "isolation_forest_contamination": 0.05,
    "min_records_for_isolation_forest": 50,
}

# Benchmarking
BENCHMARKING_CONFIG = {
    "min_cohort_size": 5,          # minimum peers required to show benchmark
    "min_coverage_months": 2,      # minimum matching calendar months a peer must
                                   # have to be counted toward the cohort.
                                   # Reference window is 3 months; requiring 2/3
                                   # excludes peers with only incidental overlap.
}

# Trend analysis
TREND_CONFIG = {
    "min_records_for_trend": 3,    # minimum months to attempt trend
    "min_records_for_seasonal": 12,
}

# Savings
SAVINGS_CONFIG = {
    "max_target_pct": 20.0,        # cap savings target at 20%
    "min_target_pct": 3.0,
}

# Indian seasonal context
# Peak summer: March–June (high AC load); cool: November–February
INDIAN_SUMMER_MONTHS = {3, 4, 5, 6}
INDIAN_COOL_MONTHS = {11, 12, 1, 2}

# Electricity tariff range (INR/kWh) used in synthetic bill generation.
# Based on Telangana/AP domestic slab tariffs (TSSPDCL/APEPDCL, 2023-24).
# Range covers 0-200 units/month slab (~8 INR) to 200-400 units slab (~12 INR).
# Update this when modelling a different DISCOM or tariff year.
TARIFF_CONFIG = {
    "min_inr_per_kwh": 8.0,
    "max_inr_per_kwh": 12.0,
    "currency": "INR",
    "source_note": "Telangana/AP domestic slab tariff 2023-24 (TSSPDCL/APEPDCL)",
}
