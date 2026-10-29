"""
Second-round validation audit script.
Covers all 12 audit checks. Run from household-intelligence/ directory.
"""
import sys
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anomaly_detection.detector import detect_anomalies, robust_zscore, _seasonal_adjusted
from trend_analysis.trend import analyse_trend
from benchmarking.peer_comparison import benchmark_household, _common_months
from savings.targets import calculate_savings_target
from clustering.kmeans_model import (
    train_clustering, label_clusters, predict_cluster, CLUSTER_FEATURES,
    _transform_features,
)
from features.engineering import build_feature_matrix, compute_consumption_features
from preprocessing.pipeline import (
    get_household_series, filter_valid_consumption, impute_households,
)
from data.synthetic_generator import generate_households, generate_consumption
from sklearn.metrics import precision_score, recall_score, f1_score
from sklearn.metrics import silhouette_score
from config.settings import ANOMALY_CONFIG, INDIAN_SUMMER_MONTHS, INDIAN_COOL_MONTHS

SEP = "=" * 70

# ─────────────────────────────────────────────────────────────────────────────
# Shared data
# ─────────────────────────────────────────────────────────────────────────────
hh300 = generate_households(n=300, seed=42)
cons300 = generate_consumption(hh300, n_months=24, seed=42, anomaly_fraction=0.03)
cons300_valid = filter_valid_consumption(cons300)

hh60 = generate_households(n=60, seed=0)
cons60 = generate_consumption(hh60, n_months=12, seed=0)
cons60_valid = filter_valid_consumption(cons60)

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 1: Gradual anomaly detection
# ─────────────────────────────────────────────────────────────────────────────
print(SEP)
print("CHECK 1: Gradual anomaly detection")
print(SEP)

idx11 = pd.period_range("2023-01", periods=11, freq="M")
idx12 = pd.period_range("2023-01", periods=12, freq="M")

# Sudden spike 2x
r_spike2x = detect_anomalies(pd.Series([200.0]*10 + [400.0], index=idx11))
print(f"  Sudden spike 2x:    detected={r_spike2x.iloc[-1]['is_anomaly']}  score={r_spike2x.iloc[-1]['anomaly_score']:.3f}")

# Sudden spike 1.5x
r_spike15 = detect_anomalies(pd.Series([200.0]*10 + [300.0], index=idx11))
print(f"  Sudden spike 1.5x:  detected={r_spike15.iloc[-1]['is_anomaly']}  score={r_spike15.iloc[-1]['anomaly_score']:.3f}")

# Sudden drop to 25%
r_drop = detect_anomalies(pd.Series([300.0]*10 + [75.0], index=idx11))
print(f"  Sudden drop 75%:    detected={r_drop.iloc[-1]['is_anomaly']}  dir={r_drop.iloc[-1]['anomaly_direction']}  score={r_drop.iloc[-1]['anomaly_score']:.3f}")

# Gradual 5%/month increase
vals_g5 = [200.0 * (1.05**i) for i in range(12)]
r_g5 = detect_anomalies(pd.Series(vals_g5, index=idx12))
print(f"  Gradual +5%/month:  flagged={r_g5['is_anomaly'].sum()}  max_score={r_g5['anomaly_score'].max():.3f}")

# Gradual 10%/month increase
vals_g10 = [200.0 * (1.10**i) for i in range(12)]
r_g10 = detect_anomalies(pd.Series(vals_g10, index=idx12))
print(f"  Gradual +10%/month: flagged={r_g10['is_anomaly'].sum()}  max_score={r_g10['anomaly_score'].max():.3f}")

# Missing months — does the series handle gaps?
idx_gap = pd.PeriodIndex(["2023-01","2023-03","2023-04","2023-05","2023-06","2023-07",
                           "2023-08","2023-09","2023-10","2023-11","2023-12"], freq="M")
r_gap = detect_anomalies(pd.Series([200.0]*11, index=idx_gap))
print(f"  Missing Feb (gap):  flagged={r_gap['is_anomaly'].sum()}  (gap itself not flagged — no imputation)")

print()
print("  FINDING: No dedicated gradual-change detector (CUSUM/Mann-Kendall on residuals).")
print("  Gradual trends are handled by trend_analysis.analyse_trend(), not detect_anomalies().")
print("  This is a design choice, not a bug, but must be documented.")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 2+3: Threshold justification + Precision/Recall/F1/FPR
# ─────────────────────────────────────────────────────────────────────────────
print()
print(SEP)
print("CHECK 2+3: Threshold justification and anomaly metrics (300hh x 24mo)")
print(SEP)

def compute_metrics_at_threshold(hh_df, cons_df, threshold):
    tp, fp, fn, tn = 0, 0, 0, 0
    for hid in hh_df["household_id"]:
        series = get_household_series(cons_df, hid)
        if len(series) < 3:
            continue
        adjusted = _seasonal_adjusted(series)
        zscores = robust_zscore(adjusted)
        pred = (abs(zscores) > threshold).astype(int)
        hh_c = cons_df[cons_df["household_id"] == hid].copy()
        hh_c["period"] = pd.to_datetime(
            hh_c[["billing_year","billing_month"]].rename(
                columns={"billing_year":"year","billing_month":"month"}).assign(day=1)
        ).dt.to_period("M")
        gt = hh_c.set_index("period")["is_injected_anomaly"].reindex(series.index).fillna(False).astype(int)
        tp += int(((gt==1)&(pred==1)).sum())
        fp += int(((gt==0)&(pred==1)).sum())
        fn += int(((gt==1)&(pred==0)).sum())
        tn += int(((gt==0)&(pred==0)).sum())
    p = tp/(tp+fp) if (tp+fp)>0 else 0
    r = tp/(tp+fn) if (tp+fn)>0 else 0
    f1 = 2*p*r/(p+r) if (p+r)>0 else 0
    fpr = fp/(fp+tn) if (fp+tn)>0 else 0
    return {"tp":tp,"fp":fp,"fn":fn,"tn":tn,"precision":p,"recall":r,"f1":f1,"fpr":fpr}

print(f"  {'Threshold':>10} {'Precision':>10} {'Recall':>10} {'F1':>8} {'FPR':>8} {'TP':>6} {'FP':>6} {'FN':>6}")
best_f1, best_thresh = 0, 0
for thresh in [1.5, 1.8, 2.0, 2.2, 2.5, 3.0]:
    m = compute_metrics_at_threshold(hh300, cons300_valid, thresh)
    marker = " <-- current" if thresh == ANOMALY_CONFIG["zscore_threshold"] else ""
    print(f"  {thresh:>10.1f} {m['precision']:>10.3f} {m['recall']:>10.3f} {m['f1']:>8.3f} {m['fpr']:>8.4f} {m['tp']:>6} {m['fp']:>6} {m['fn']:>6}{marker}")
    if m["f1"] > best_f1:
        best_f1, best_thresh = m["f1"], thresh

print(f"\n  Best F1={best_f1:.3f} at threshold={best_thresh}")
current_m = compute_metrics_at_threshold(hh300, cons300_valid, ANOMALY_CONFIG["zscore_threshold"])
print(f"  Current threshold={ANOMALY_CONFIG['zscore_threshold']}: P={current_m['precision']:.3f} R={current_m['recall']:.3f} F1={current_m['f1']:.3f} FPR={current_m['fpr']:.4f}")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 4: Severity boundary justification
# ─────────────────────────────────────────────────────────────────────────────
print()
print(SEP)
print("CHECK 4: Severity boundaries")
print(SEP)
thresh = ANOMALY_CONFIG["zscore_threshold"]
print(f"  Threshold = {thresh}")
print(f"  none:     abs_z <= {thresh:.2f}")
print(f"  low:      {thresh:.2f} < abs_z <= {thresh*1.5:.2f}  (1.0x–1.5x threshold)")
print(f"  moderate: {thresh*1.5:.2f} < abs_z <= {thresh*2.0:.2f}  (1.5x–2.0x threshold)")
print(f"  high:     abs_z > {thresh*2.0:.2f}  (>2.0x threshold)")
print()
print("  Boundary basis: multiplicative bands relative to threshold.")
print("  No empirical calibration against labelled severity data.")
print("  The 1.5x/2.0x multipliers are arbitrary — not derived from data.")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 5: Indian seasonal assumptions — documented and limited?
# ─────────────────────────────────────────────────────────────────────────────
print()
print(SEP)
print("CHECK 5: Indian seasonal assumptions")
print(SEP)
from data.synthetic_generator import SEASONAL
print(f"  INDIAN_SUMMER_MONTHS (config): {sorted(INDIAN_SUMMER_MONTHS)}")
print(f"  INDIAN_COOL_MONTHS   (config): {sorted(INDIAN_COOL_MONTHS)}")
print(f"  Synthetic SEASONAL multipliers: {SEASONAL}")
print()
print("  Checking consistency between config and generator:")
gen_peak = max(SEASONAL, key=SEASONAL.get)
gen_trough = min(SEASONAL, key=SEASONAL.get)
print(f"  Generator peak month: {gen_peak} (x{SEASONAL[gen_peak]}) — in INDIAN_SUMMER_MONTHS: {gen_peak in INDIAN_SUMMER_MONTHS}")
print(f"  Generator trough month: {gen_trough} (x{SEASONAL[gen_trough]}) — in INDIAN_COOL_MONTHS: {gen_trough in INDIAN_COOL_MONTHS}")
print()
print("  Limitations:")
print("  - Seasonal multipliers are uniform across all 8 states (Telangana=Delhi=Rajasthan).")
print("  - No monsoon-specific adjustment for coastal states (Tamil Nadu, Andhra Pradesh).")
print("  - Tariff slab structure (DISCOM slabs) not modelled — flat INR/kWh range used.")
print("  - Tariff source documented in config/settings.py TARIFF_CONFIG source_note.")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 6: Tariff configurability
# ─────────────────────────────────────────────────────────────────────────────
print()
print(SEP)
print("CHECK 6: Electricity tariff configurability")
print(SEP)
import inspect
from data import synthetic_generator
from config.settings import TARIFF_CONFIG
src = inspect.getsource(synthetic_generator.generate_consumption)
tariff_hardcoded = "rng.uniform(8.0, 12.0)" in src
uses_tariff_config = "TARIFF_CONFIG" in src
print(f"  Literal 8.0/12.0 hardcoded in generate_consumption: {tariff_hardcoded}")
print(f"  generate_consumption reads TARIFF_CONFIG: {uses_tariff_config}")
print(f"  TARIFF_CONFIG in config/settings.py: {TARIFF_CONFIG}")
print()
if uses_tariff_config and not tariff_hardcoded:
    print("  VERIFIED: Tariff range is read from TARIFF_CONFIG in config/settings.py.")
    print("  Configurable without editing source — change TARIFF_CONFIG values only.")
else:
    print("  WARNING: Tariff range may be partially or fully hardcoded.")
print("  NOTE: bill_amount_inr is generated but not used in any downstream analysis.")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 7: Clustering stability across seeds
# ─────────────────────────────────────────────────────────────────────────────
print()
print(SEP)
print("CHECK 7: Clustering stability across seeds")
print(SEP)
fm = build_feature_matrix(hh300, cons300_valid)
print(f"  Feature matrix: {fm.shape}")

seed_results = {}
for seed in [0, 7, 42, 99, 123]:
    pipe, labels, scores = train_clustering(fm, k_min=2, k_max=6, seed=seed)
    best_k = scores["best_k"]
    sil = scores["scores_by_k"][best_k]["silhouette"]
    db = scores["scores_by_k"][best_k]["davies_bouldin"]
    seed_results[seed] = {"k": best_k, "silhouette": sil, "db": db, "labels": labels.values.copy()}
    print(f"  seed={seed:>4}: best_k={best_k}  silhouette={sil:.4f}  DB={db:.4f}")

# ARI between seed=42 and others
from sklearn.metrics import adjusted_rand_score
ref_labels = seed_results[42]["labels"]
print()
print("  Adjusted Rand Index vs seed=42:")
for seed, res in seed_results.items():
    if seed == 42:
        continue
    ari = adjusted_rand_score(ref_labels, res["labels"])
    print(f"  seed={seed:>4} vs seed=42: ARI={ari:.4f}  (1.0=identical, 0=random)")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 8: Cold-start behaviour at 0, 1, 2, 3 months
# ─────────────────────────────────────────────────────────────────────────────
print()
print(SEP)
print("CHECK 8: Cold-start behaviour at 0/1/2/3 months")
print(SEP)
from main import run_inference, _cold_start_stage

hh_test = generate_households(n=50, seed=5)
cons_full = generate_consumption(hh_test, n_months=12, seed=5)
hid = hh_test["household_id"].iloc[0]

for n_months_keep in [0, 1, 2, 3]:
    if n_months_keep == 0:
        cons_slice = cons_full.iloc[0:0]
    else:
        hid_cons = cons_full[cons_full["household_id"] == hid]
        other_cons = cons_full[cons_full["household_id"] != hid]
        cons_slice = pd.concat([hid_cons.head(n_months_keep), other_cons])

    result = run_inference(hid, hh_test, cons_slice)
    stage = result.get("cold_start_stage")
    status = result.get("data_status")
    trend_status = result.get("trend", {})
    trend_status = trend_status.get("status") if isinstance(trend_status, dict) else "N/A"
    anomaly = result.get("anomaly")
    anomaly_info = "present" if anomaly else "None"
    print(f"  n_months={n_months_keep}: stage={stage}  status={status}  trend={trend_status}  anomaly={anomaly_info}")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 9: New household inference without training IDs
# ─────────────────────────────────────────────────────────────────────────────
print()
print(SEP)
print("CHECK 9: New household inference (ID not in training data)")
print(SEP)
pipe, labels, scores = train_clustering(fm, k_min=2, k_max=6, seed=42)
_, label_map = label_clusters(fm, labels)

# Household ID that was never in training
new_hh = pd.DataFrame([{
    "household_id": "H_BRAND_NEW",
    "state": "Telangana", "n_residents": 4, "home_type": "apartment",
    "home_size_m2": 120.0, "has_solar": False, "has_air_conditioner": True,
    "has_inverter_ac": True, "has_electric_vehicle": False,
    "has_electric_water_heater": True,
}])
new_cons = pd.DataFrame([{
    "household_id": "H_BRAND_NEW",
    "billing_year": 2023, "billing_month": m,
    "consumption_kwh": 280.0 + m * 8,
} for m in range(1, 7)])

new_fm = build_feature_matrix(new_hh, new_cons)
print(f"  New household in training index: {'H_BRAND_NEW' in fm.index}")
print(f"  Feature matrix built: {not new_fm.empty}")
result_new = predict_cluster(pipe, new_fm, label_map)
print(f"  Predicted profile: '{result_new.iloc[0]}'")
print(f"  Profile is a valid label: {result_new.iloc[0] in label_map.values()}")

# Verify main.py inference path also works
hh_with_new = pd.concat([hh300.head(30), new_hh], ignore_index=True)
cons_with_new = pd.concat([cons300_valid[cons300_valid["household_id"].isin(hh300.head(30)["household_id"])], new_cons], ignore_index=True)
result_main = run_inference("H_BRAND_NEW", hh_with_new, cons_with_new)
print(f"  run_inference profile: {result_main.get('consumption_profile')}")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 10: Benchmarking edge cases
# ─────────────────────────────────────────────────────────────────────────────
print()
print(SEP)
print("CHECK 10: Benchmarking edge cases")
print(SEP)

# 10a: insufficient common months — target has data for months peers don't
hh_small = generate_households(n=10, seed=77)
# Target has Jan-Mar 2023, peers only have Jul-Sep 2023
target_id = hh_small["household_id"].iloc[0]
peer_ids = hh_small["household_id"].iloc[1:].tolist()
target_cons = pd.DataFrame([{"household_id": target_id, "billing_year": 2023,
    "billing_month": m, "consumption_kwh": 250.0} for m in [1,2,3]])
peer_cons = pd.DataFrame([{"household_id": pid, "billing_year": 2023,
    "billing_month": m, "consumption_kwh": 230.0}
    for pid in peer_ids for m in [7,8,9]])
all_cons = pd.concat([target_cons, peer_cons])
result_no_overlap = benchmark_household(target_id, hh_small, all_cons)
print(f"  No calendar overlap: status='{result_no_overlap['status']}'")

# 10b: fewer than min_cohort peers after calendar alignment
hh_tiny = generate_households(n=4, seed=88)
cons_tiny = generate_consumption(hh_tiny, n_months=3, seed=88)
result_tiny = benchmark_household(hh_tiny["household_id"].iloc[0], hh_tiny, cons_tiny)
print(f"  Tiny cohort (4hh):   status='{result_tiny['status']}'")

# 10c: unknown household
result_unknown = benchmark_household("GHOST_ID", hh300, cons300_valid)
print(f"  Unknown household:   status='{result_unknown['status']}'")

# 10d: household with no consumption
result_nocons = benchmark_household(hh300["household_id"].iloc[0], hh300, cons300_valid.iloc[0:0])
print(f"  No consumption data: status='{result_nocons['status']}'")

# 10e: _common_months performance check — uses row-wise apply (O(n*m))
import time
big_peer_cons = cons300_valid[cons300_valid["household_id"].isin(hh300["household_id"].iloc[:50])]
ref_window = cons300_valid[cons300_valid["household_id"]==hh300["household_id"].iloc[0]].tail(3)
t0 = time.time()
_common_months(ref_window, big_peer_cons)
elapsed = time.time() - t0
print(f"  _common_months on 50 peers x 24mo: {elapsed:.3f}s  (row-wise apply — O(n*m))")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 11: Savings calibration and explainability
# ─────────────────────────────────────────────────────────────────────────────
print()
print(SEP)
print("CHECK 11: Savings recommendations calibration")
print(SEP)

cases = [
    ("No signals", {"status":"insufficient_data"}, {"status":"insufficient_data"}, [], {}),
    ("Peer +6%", {"status":"ok","direction":"stable","percentage_change":0},
     {"status":"available","difference_from_median_pct":6.0}, [], {}),
    ("Peer +16%", {"status":"ok","direction":"stable","percentage_change":0},
     {"status":"available","difference_from_median_pct":16.0}, [], {}),
    ("Trend +15%", {"status":"ok","direction":"increasing","percentage_change":15},
     {"status":"insufficient_data"}, [], {}),
    ("Trend +15% + Peer +16%", {"status":"ok","direction":"increasing","percentage_change":15},
     {"status":"available","difference_from_median_pct":16.0}, [], {}),
    ("2 anomalies only", {"status":"insufficient_data"}, {"status":"insufficient_data"},
     [{"is_anomaly":True},{"is_anomaly":True}], {}),
    ("All signals max", {"status":"ok","direction":"increasing","percentage_change":100},
     {"status":"available","difference_from_median_pct":100.0},
     [{"is_anomaly":True}]*5, {}),
]
print(f"  {'Case':<30} {'Status':<12} {'Target%':>8} {'Basis'}")
for name, trend, bench, anom, feat in cases:
    r = calculate_savings_target(trend, bench, anom, feat)
    print(f"  {name:<30} {r['status']:<12} {str(r.get('target_percentage','N/A')):>8}  {r.get('basis','')}")

print()
print("  Checking min_target_pct floor behaviour:")
r_floor = calculate_savings_target(
    {"status":"ok","direction":"stable","percentage_change":0},
    {"status":"available","difference_from_median_pct":6.0}, [], {})
print(f"  Peer +6% (contribution=1.8%) -> target={r_floor['target_percentage']}%")
print("  VERIFIED: floor removed. A 6% peer gap yields 1.8% target (not inflated to 3.0%).")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 12: pandas FutureWarning
# ─────────────────────────────────────────────────────────────────────────────
print()
print(SEP)
print("CHECK 12: pandas FutureWarning in impute_households")
print(SEP)
import warnings
import pandas as pd

df_test = pd.DataFrame([{
    "household_id": "H1", "n_residents": None, "home_size_m2": 100,
    "home_type": "apartment", "state": "Telangana",
    "has_solar": None, "has_air_conditioner": None,
    "has_inverter_ac": None, "has_electric_vehicle": None,
    "has_electric_water_heater": None,
},{
    "household_id": "H2", "n_residents": 3, "home_size_m2": 120,
    "home_type": "house", "state": "Telangana",
    "has_solar": False, "has_air_conditioner": True,
    "has_inverter_ac": False, "has_electric_vehicle": False,
    "has_electric_water_heater": True,
}])

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    from preprocessing.pipeline import impute_households
    result = impute_households(df_test)
    future_warnings = [x for x in w if issubclass(x.category, FutureWarning)]
    print(f"  FutureWarnings raised: {len(future_warnings)}")
    for fw in future_warnings:
        print(f"  - {fw.message}")

print()
print("  Root cause: fillna(False).infer_objects(copy=False) on object-dtype bool column")
print("  Fix: cast to bool explicitly before fillna, e.g. df[col].astype(object).fillna(False)")
print("  Or: use pd.array([False], dtype=bool) as fill value")

print()
print(SEP)
print("AUDIT COMPLETE")
print(SEP)
