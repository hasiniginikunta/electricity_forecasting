# M2 Household Intelligence Engine

Generates personalised electricity consumption insights for Indian households.
Context: Telangana/AP primary; 8 Indian states supported.
All data used in development is **SYNTHETIC**.

---

## Installation

Requires Python 3.10+.

```bash
pip install -r requirements.txt
```

Dependencies (pinned to the versions used to generate bundled artifacts):

| Package | Pinned version |
|---|---|
| numpy | 2.2.6 |
| pandas | 2.3.3 |
| scikit-learn | 1.7.2 |
| scipy | 1.15.3 |
| joblib | 1.5.3 |
| pytest | >=7.4 |

The sklearn version must match the pinned version exactly. Pickle artifacts
(`clustering_pipeline.pkl`, `profile_transformer.pkl`) were serialised with
sklearn 1.7.2. Loading them under a different sklearn version may raise
`InconsistentVersionWarning` or fail silently. Do not suppress version
mismatch warnings — regenerate artifacts with `python train.py` if the
environment changes.

---

## Training

Run once from the `household-intelligence/` directory to generate synthetic data and save all model artifacts:

```bash
python train.py
```

This will:
1. Generate `data/synthetic_households.csv` and `data/synthetic_consumption.csv` (300 households, 24 months, seed=42)
2. Train K-Means clustering (K selected by silhouette score over K=2..8)
3. Save artifacts to `artifacts/`:
   - `artifacts/clustering/clustering_pipeline.pkl` — fitted sklearn Pipeline (imputer + scaler + KMeans)
   - `artifacts/clustering/cluster_label_map.json` — integer cluster ID -> profile string
   - `artifacts/clustering/cluster_assignments.csv` — training household assignments
   - `artifacts/clustering/cluster_profile_labels.csv` — human-readable profile labels
   - `artifacts/clustering/clustering_eval.json` — silhouette/DB scores per K
   - `artifacts/preprocessing/profile_transformer.pkl` — fitted OrdinalEncoder + StandardScaler
   - `artifacts/feature_matrix.csv` — 300x22 feature matrix
   - `artifacts/evaluation/clustering_eval.txt` — text evaluation report

---

## Inference

Run inference for a single household (requires artifacts from `train.py`):

```bash
python main.py --household_id H0001
python main.py --demo   # runs first 3 households
```

Output is JSON printed to stdout. See **M2 Output Schema** below.

---

## Inputs

### Household profile (`synthetic_households.csv`)

| Column | Type | Description |
|---|---|---|
| `household_id` | string | Unique identifier |
| `state` | string | One of 8 Indian states |
| `n_residents` | int | Number of residents (1-20) |
| `home_type` | string | `house`, `apartment`, `flat`, `villa` |
| `home_size_m2` | float | Floor area in m² |
| `has_solar` | bool | Rooftop solar installed |
| `has_air_conditioner` | bool | AC present |
| `has_inverter_ac` | bool | Inverter-type AC |
| `has_electric_vehicle` | bool | EV present |
| `has_electric_water_heater` | bool | Electric geyser present |

### Consumption records (`synthetic_consumption.csv`)

| Column | Type | Description |
|---|---|---|
| `household_id` | string | Foreign key to households |
| `billing_year` | int | Year of billing period |
| `billing_month` | int | Month of billing period (1-12) |
| `consumption_kwh` | float | Monthly consumption in kWh |
| `bill_amount_inr` | float | Bill amount in INR (synthetic only) |
| `is_injected_anomaly` | bool | Ground-truth label (synthetic only) |

Valid consumption range: 10-5000 kWh/month. Records outside this range or duplicates are filtered before use.

---

## M2 Output Schema

`run_inference()` returns a dict. `main.py` serialises it as JSON.

```json
{
  "household_id": "H0001",
  "data_source": "SYNTHETIC",
  "cold_start_stage": 4,
  "n_consumption_records": 24,
  "data_status": "sufficient",

  "consumption_profile": {
    "profile": "summer_sensitive",
    "note": "SYNTHETIC data cluster assignment. Cluster labels are indicative; best K varies across training runs (ARI 0.70-1.0 across seeds)."
  },

  "trend": {
    "status": "ok",
    "direction": "stable",
    "percentage_change": -3.82,
    "slope_kwh_per_month": -0.867,
    "rolling_3m_avg_kwh": 285.1,
    "message": null
  },

  "anomaly": {
    "detected": false,
    "anomaly_status": "normal",
    "confidence": "none",
    "severity": "none",
    "anomaly_score": 1.603,
    "explanation": null
  },

  "benchmark": {
    "status": "available",
    "match_tier": 1,
    "match_confidence": "high",
    "match_note": null,
    "cohort_size": 5,
    "comparison_months": [
      {"billing_year": 2024, "billing_month": 10},
      {"billing_year": 2024, "billing_month": 11},
      {"billing_year": 2024, "billing_month": 12}
    ],
    "peer_coverage_months": {
      "min_required": 2,
      "reference_window_size": 3,
      "peer_min": 3,
      "peer_max": 3
    },
    "household_recent_mean_kwh": 285.1,
    "peer_p25_kwh": 191.0,
    "peer_median_kwh": 255.7,
    "peer_p75_kwh": 313.8,
    "difference_from_median_pct": 11.5,
    "relative_position": "above_median"
  },

  "savings_target": {
    "status": "available",
    "target_percentage": 3.4,
    "basis": "data_driven_estimate",
    "explanation": "Your consumption is 11.5% above similar households. An estimated 3.4% reduction may be achievable (estimate based on peer comparison).",
    "disclaimer": "This is a statistical estimate based on available data. Actual savings will depend on your specific usage patterns and actions taken."
  }
}
```

### Field reference

**Top-level**

| Field | Values | Notes |
|---|---|---|
| `cold_start_stage` | 1-4 | 1=no data, 2=<3 records, 3=<20 households, 4=mature |
| `data_status` | `new_user`, `limited`, `sufficient` | |

**`consumption_profile`** — `null` if stage < 3 or no artifacts

| Field | Values |
|---|---|
| `profile` | `low_consumption`, `high_baseline`, `summer_sensitive`, `increasing_trend`, `consistent_consumption`, `moderate_cluster_N` |

**`trend`**

| Field | Values |
|---|---|
| `status` | `ok`, `insufficient_data` |
| `direction` | `increasing`, `decreasing`, `stable`, `null` |

**`anomaly`**

| Field | Values |
|---|---|
| `anomaly_status` | `possible_anomaly`, `normal`, `insufficient_data` |
| `confidence` | `low`, `none`, `insufficient_data` |
| `severity` | `none`, `low`, `moderate`, `high` |
| `anomaly_direction` | `high`, `low`, `none` |

**`benchmark`**

| Field | Values |
|---|---|
| `status` | `available`, `insufficient_data`, `household_not_found`, `no_consumption_data` |
| `match_tier` | 1 (state+type+residents), 2 (type+residents), 3 (residents only) |
| `match_confidence` | `high`, `medium`, `low` |
| `peer_coverage_months` | object: `min_required`, `reference_window_size`, `peer_min`, `peer_max` — present when `status=available` |

**`savings_target`**

| Field | Values |
|---|---|
| `status` | `available`, `no_target` |
| `basis` | `data_driven_estimate`, `insufficient_signals` |
| `target_percentage` | float or `null` |

---

## Cold-Start Stages

| Stage | Condition | Behaviour |
|---|---|---|
| 1 | 0 consumption records | Returns `new_user` message only |
| 2 | 1-2 records | Trend only; anomaly suppressed |
| 3 | >=3 records but <20 households total | Full pipeline; benchmark may be insufficient |
| 4 | >=3 records and >=20 households | Full pipeline |

---

## Limitations

- **Anomaly detection scope: sudden deviations only.** `detect_anomalies()` detects sudden, isolated statistical deviations from a household's own historical baseline (spikes and drops) using a MAD-based robust Z-score. It does NOT detect gradual consumption drift. Gradual increases or decreases over multiple months are assessed separately by `trend_analysis.analyse_trend()` using linear regression. The two modules are complementary and both contribute to savings recommendations.
- **Synthetic data only.** All training data is procedurally generated. No real household data has been used. Real-world performance is unknown.
- **Anomaly detection precision ~40%.** At threshold=3.0, approximately 60% of flagged months are false positives on synthetic data. All anomaly results carry `confidence="low"` and `anomaly_status="possible_anomaly"`.
- **Clustering stability.** Best K varies between 5 and 6 across random seeds (ARI 0.70-1.0). Up to 30% of household cluster assignments may differ between training runs. Profile labels are indicative only.
- **Seasonal assumptions are uniform.** The Indian summer peak (Mar-Jun) multiplier is applied identically across all 8 states. No state-specific or monsoon-coastal adjustment is modelled.
- **Tier-3 peer matches are low-confidence.** When only resident count can be matched (no home type or state alignment), the benchmark is shown with `match_confidence="low"` and does not generate a savings target.
- **Savings targets are estimates.** Targets are derived from statistical signals (peer gap, trend, anomaly spikes). They are not energy audits. The minimum reportable target is 1.0%; targets below this threshold return `status="no_target"`.
- **Tariff range is approximate.** Bill amounts use 8-12 INR/kWh based on Telangana/AP domestic slab tariffs (TSSPDCL/APEPDCL 2023-24). This range is not used in any savings calculation.

---

## Running Tests

```bash
cd household-intelligence
pytest tests/test_m2.py -v
```

78 tests, all passing. Run with `-W error::FutureWarning` to verify no pandas deprecation warnings.

```bash
pytest tests/test_m2.py -v -W error::FutureWarning
```

To run the audit validation script (diagnostic output, not pytest):

```bash
python tests/audit_validation.py
```
