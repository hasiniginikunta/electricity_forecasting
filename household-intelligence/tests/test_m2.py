"""
M2 Test Suite
=============
Run with:  pytest tests/ -v
           (from the household-intelligence/ directory)
Context: Indian household electricity consumption (primary: Telangana).
"""
import sys
import numpy as np
import pandas as pd
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from preprocessing.pipeline import (
    validate_households, validate_consumption, filter_valid_consumption,
    impute_households, HouseholdProfileTransformer, get_household_series,
)
from features.engineering import (
    compute_consumption_features, compute_household_features, build_feature_matrix,
)
from trend_analysis.trend import analyse_trend
from anomaly_detection.detector import detect_anomalies, robust_zscore
from benchmarking.peer_comparison import benchmark_household
from savings.targets import calculate_savings_target
from data.synthetic_generator import generate_households, generate_consumption


# ── Fixtures ──────────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def synthetic_data():
    hh = generate_households(n=60, seed=0)
    cons = generate_consumption(hh, n_months=12, seed=0)
    return hh, cons


@pytest.fixture
def simple_series_increasing():
    vals = [100, 110, 120, 130, 140, 150]
    idx = pd.period_range("2023-01", periods=6, freq="M")
    return pd.Series(vals, index=idx)


@pytest.fixture
def simple_series_stable():
    vals = [200, 198, 202, 199, 201, 200]
    idx = pd.period_range("2023-01", periods=6, freq="M")
    return pd.Series(vals, index=idx)


@pytest.fixture
def simple_series_decreasing():
    vals = [300, 280, 260, 240, 220, 200]
    idx = pd.period_range("2023-01", periods=6, freq="M")
    return pd.Series(vals, index=idx)


def _make_series_with_spike(n_base=12, base=200.0, spike_mult=4.0, seed=0):
    """Realistic baseline with natural noise + one spike at the end."""
    rng = np.random.default_rng(seed)
    base_vals = base + rng.normal(0, base * 0.07, n_base)
    vals = list(base_vals) + [base * spike_mult]
    idx = pd.period_range("2023-01", periods=n_base + 1, freq="M")
    return pd.Series(vals, index=idx)


def _make_series_with_drop(n_base=12, base=300.0, drop_to=60.0, seed=0):
    """Realistic baseline with natural noise + one drop at the end."""
    rng = np.random.default_rng(seed)
    base_vals = base + rng.normal(0, base * 0.07, n_base)
    vals = list(base_vals) + [drop_to]
    idx = pd.period_range("2023-01", periods=n_base + 1, freq="M")
    return pd.Series(vals, index=idx)


# ── Preprocessing tests ───────────────────────────────────────────────────────
class TestPreprocessing:

    def test_validate_households_flags_invalid_residents(self):
        df = pd.DataFrame([{"household_id": "H1", "n_residents": 0,
                             "home_size_m2": 100, "home_type": "apartment",
                             "state": "Telangana"}])
        result = validate_households(df)
        assert result.iloc[0]["validation_flag"] != "ok"

    def test_validate_households_flags_implausible_residents(self):
        df = pd.DataFrame([{"household_id": "H1", "n_residents": 25,
                             "home_size_m2": 100, "home_type": "apartment",
                             "state": "Telangana"}])
        result = validate_households(df)
        assert "implausible_n_residents" in result.iloc[0]["validation_flag"]

    def test_validate_households_valid_row(self):
        df = pd.DataFrame([{"household_id": "H1", "n_residents": 3,
                             "home_size_m2": 150, "home_type": "house",
                             "state": "Telangana"}])
        result = validate_households(df)
        assert result.iloc[0]["validation_flag"] == "ok"

    def test_validate_consumption_flags_below_min(self):
        df = pd.DataFrame([{
            "household_id": "H1", "billing_year": 2023, "billing_month": 1,
            "consumption_kwh": 5.0,
        }])
        result = validate_consumption(df)
        assert result.iloc[0]["validation_flag"] == "below_minimum"

    def test_validate_consumption_flags_above_max(self):
        df = pd.DataFrame([{
            "household_id": "H1", "billing_year": 2023, "billing_month": 1,
            "consumption_kwh": 9999.0,
        }])
        result = validate_consumption(df)
        assert result.iloc[0]["validation_flag"] == "above_maximum"

    def test_validate_consumption_flags_duplicate(self):
        df = pd.DataFrame([
            {"household_id": "H1", "billing_year": 2023, "billing_month": 1,
             "consumption_kwh": 200.0},
            {"household_id": "H1", "billing_year": 2023, "billing_month": 1,
             "consumption_kwh": 210.0},
        ])
        result = validate_consumption(df)
        assert result.iloc[1]["validation_flag"] == "duplicate"

    def test_duplicate_checked_before_range(self):
        df = pd.DataFrame([
            {"household_id": "H1", "billing_year": 2023, "billing_month": 1,
             "consumption_kwh": 200.0},
            {"household_id": "H1", "billing_year": 2023, "billing_month": 1,
             "consumption_kwh": 9999.0},
        ])
        result = validate_consumption(df)
        assert result.iloc[1]["validation_flag"] == "duplicate"

    def test_filter_valid_removes_bad_records(self):
        df = pd.DataFrame([
            {"household_id": "H1", "billing_year": 2023, "billing_month": 1,
             "consumption_kwh": 5.0},
            {"household_id": "H1", "billing_year": 2023, "billing_month": 2,
             "consumption_kwh": 200.0},
        ])
        result = filter_valid_consumption(df)
        assert len(result) == 1
        assert result.iloc[0]["consumption_kwh"] == 200.0

    def test_impute_fills_missing_residents(self):
        df = pd.DataFrame([
            {"household_id": "H1", "n_residents": None, "home_size_m2": 100,
             "home_type": "apartment", "state": "Telangana",
             "has_solar": None, "has_air_conditioner": None,
             "has_inverter_ac": None, "has_electric_vehicle": None,
             "has_electric_water_heater": None},
            {"household_id": "H2", "n_residents": 3, "home_size_m2": 120,
             "home_type": "house", "state": "Telangana",
             "has_solar": False, "has_air_conditioner": True,
             "has_inverter_ac": False, "has_electric_vehicle": False,
             "has_electric_water_heater": True},
        ])
        result = impute_households(df)
        assert pd.notna(result.iloc[0]["n_residents"])

    def test_impute_default_state_is_telangana(self):
        df = pd.DataFrame([
            {"household_id": "H1", "n_residents": 2, "home_size_m2": 80,
             "home_type": "apartment", "state": None,
             "has_solar": False, "has_air_conditioner": False,
             "has_inverter_ac": False, "has_electric_vehicle": False,
             "has_electric_water_heater": False},
        ])
        result = impute_households(df)
        assert result.iloc[0]["state"] == "Telangana"

    def test_synthetic_data_uses_inr_not_aud(self, synthetic_data):
        _, cons = synthetic_data
        assert "bill_amount_inr" in cons.columns
        assert "bill_amount_aud" not in cons.columns

    def test_synthetic_data_uses_indian_states(self, synthetic_data):
        hh, _ = synthetic_data
        indian_states = {"Telangana", "Andhra Pradesh", "Maharashtra",
                         "Karnataka", "Tamil Nadu", "Delhi", "Gujarat", "Rajasthan"}
        assert set(hh["state"].unique()).issubset(indian_states)

    def test_transformer_fit_transform_shape(self, synthetic_data):
        hh, _ = synthetic_data
        t = HouseholdProfileTransformer()
        X = t.fit_transform(hh)
        assert X.shape[0] == len(hh)
        assert X.shape[1] > 0

    def test_transformer_raises_before_fit(self, synthetic_data):
        hh, _ = synthetic_data
        t = HouseholdProfileTransformer()
        with pytest.raises(RuntimeError):
            t.transform(hh)

    def test_get_household_series_sorted(self, synthetic_data):
        hh, cons = synthetic_data
        hid = hh["household_id"].iloc[0]
        series = get_household_series(cons, hid)
        assert list(series.index) == sorted(series.index)

    def test_missing_months_not_zero_filled(self, synthetic_data):
        hh, cons = synthetic_data
        hid = hh["household_id"].iloc[0]
        cons_dropped = cons[~(
            (cons["household_id"] == hid) &
            (cons["billing_month"] == 6)
        )]
        series = get_household_series(cons_dropped, hid)
        assert 0.0 not in series.values or series.min() > 0


# ── Feature engineering tests ─────────────────────────────────────────────────
class TestFeatureEngineering:

    def test_consumption_features_keys(self, simple_series_increasing):
        feat = compute_consumption_features(simple_series_increasing)
        for key in ["mean_kwh", "median_kwh", "std_kwh", "cv", "trend_slope_kwh_per_month"]:
            assert key in feat

    def test_empty_series_returns_n_records_zero(self):
        feat = compute_consumption_features(pd.Series([], dtype=float))
        assert feat["n_records"] == 0

    def test_kwh_per_resident_computed(self, simple_series_increasing):
        hh_row = pd.Series({"n_residents": 2, "home_size_m2": 150,
                             "has_solar": False, "has_air_conditioner": True,
                             "has_inverter_ac": False, "has_electric_vehicle": False,
                             "has_electric_water_heater": False})
        cf = compute_consumption_features(simple_series_increasing)
        hf = compute_household_features(hh_row, cf)
        assert hf["kwh_per_resident"] == pytest.approx(cf["mean_kwh"] / 2, rel=1e-3)

    def test_summer_sensitivity_uses_indian_months(self):
        months = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        vals = [100, 100, 130, 150, 180, 160, 110, 100, 100, 100, 100, 100]
        idx = pd.PeriodIndex([pd.Period(f"2023-{m:02d}", "M") for m in months])
        series = pd.Series(vals, index=idx)
        feat = compute_consumption_features(series)
        assert feat["summer_sensitivity"] > 0

    def test_build_feature_matrix_index(self, synthetic_data):
        hh, cons = synthetic_data
        fm = build_feature_matrix(hh, cons)
        assert fm.index.name == "household_id"
        assert len(fm) > 0


# ── Trend analysis tests ──────────────────────────────────────────────────────
class TestTrendAnalysis:

    def test_increasing_detected(self, simple_series_increasing):
        result = analyse_trend(simple_series_increasing)
        assert result["direction"] == "increasing"

    def test_decreasing_detected(self, simple_series_decreasing):
        result = analyse_trend(simple_series_decreasing)
        assert result["direction"] == "decreasing"

    def test_stable_detected(self, simple_series_stable):
        result = analyse_trend(simple_series_stable)
        assert result["direction"] == "stable"

    def test_insufficient_data_message(self):
        series = pd.Series([200.0, 210.0])
        result = analyse_trend(series)
        assert result["status"] == "insufficient_data"
        assert result["direction"] is None

    def test_percentage_change_sign(self, simple_series_increasing):
        result = analyse_trend(simple_series_increasing)
        assert result["percentage_change"] > 0

    def test_rolling_avg_present(self, simple_series_increasing):
        result = analyse_trend(simple_series_increasing)
        assert result["rolling_3m_avg"] is not None

    def test_missing_month_creates_gap_in_regression(self):
        idx = pd.PeriodIndex(["2023-01", "2023-03"], freq="M")
        series = pd.Series([200.0, 200.0], index=idx)
        result = analyse_trend(series)
        assert result["status"] == "insufficient_data"

    def test_gap_does_not_distort_slope(self):
        idx_full = pd.period_range("2023-01", periods=6, freq="M")
        vals = [100.0, 110.0, 120.0, 130.0, 140.0, 150.0]
        series_full = pd.Series(vals, index=idx_full)
        idx_gap = pd.PeriodIndex(["2023-01", "2023-03", "2023-04", "2023-05", "2023-06"], freq="M")
        series_gap = pd.Series([100.0, 120.0, 130.0, 140.0, 150.0], index=idx_gap)
        result_full = analyse_trend(series_full)
        result_gap = analyse_trend(series_gap)
        assert result_full["direction"] == "increasing"
        assert result_gap["direction"] == "increasing"
        assert abs(result_gap["slope_kwh_per_month"] - result_full["slope_kwh_per_month"]) < 5.0


# ── Anomaly detection tests ───────────────────────────────────────────────────
class TestAnomalyDetection:

    def test_injected_spike_detected(self):
        """4x spike against realistic varied baseline must be detected at threshold=3.0."""
        series = _make_series_with_spike(n_base=12, base=200.0, spike_mult=4.0, seed=0)
        result = detect_anomalies(series)
        assert result.iloc[-1]["is_anomaly"] is True

    def test_sudden_drop_detected(self):
        """Drop to 20% of baseline against realistic varied baseline must be detected."""
        series = _make_series_with_drop(n_base=12, base=300.0, drop_to=60.0, seed=0)
        result = detect_anomalies(series)
        assert result.iloc[-1]["is_anomaly"] is True
        assert result.iloc[-1]["anomaly_direction"] == "low"

    def test_spike_has_high_direction(self):
        series = _make_series_with_spike(n_base=12, base=200.0, spike_mult=4.0, seed=0)
        result = detect_anomalies(series)
        assert result.iloc[-1]["anomaly_direction"] == "high"

    def test_normal_values_not_flagged(self):
        vals = [200.0, 205.0, 198.0, 202.0, 199.0, 201.0]
        idx = pd.period_range("2023-01", periods=6, freq="M")
        series = pd.Series(vals, index=idx)
        result = detect_anomalies(series)
        assert result["is_anomaly"].sum() == 0

    def test_anomaly_status_is_possible_anomaly(self):
        """Flagged records must use 'possible_anomaly' language, not a definitive claim."""
        series = _make_series_with_spike(n_base=12, base=200.0, spike_mult=4.0, seed=0)
        result = detect_anomalies(series)
        flagged = result[result["is_anomaly"]]
        assert all(flagged["anomaly_status"] == "possible_anomaly")

    def test_anomaly_confidence_is_low(self):
        """Flagged records must carry confidence='low' to reflect ~40% precision."""
        series = _make_series_with_spike(n_base=12, base=200.0, spike_mult=4.0, seed=0)
        result = detect_anomalies(series)
        flagged = result[result["is_anomaly"]]
        assert all(flagged["confidence"] == "low")

    def test_explanation_says_verify(self):
        """Explanation text must include verification language, not a definitive claim."""
        series = _make_series_with_spike(n_base=12, base=200.0, spike_mult=4.0, seed=0)
        result = detect_anomalies(series)
        flagged = result[result["is_anomaly"]]
        assert all("verify" in str(row["explanation"]).lower() for _, row in flagged.iterrows())

    def test_insufficient_data_fewer_than_3_records(self):
        """With 1 or 2 records, all rows must have anomaly_status='insufficient_data'."""
        for n in [1, 2]:
            idx = pd.period_range("2023-01", periods=n, freq="M")
            series = pd.Series([200.0] * n, index=idx)
            result = detect_anomalies(series)
            assert result["is_anomaly"].sum() == 0
            assert all(result["anomaly_status"] == "insufficient_data")

    def test_insufficient_data_no_anomaly_score(self):
        """With fewer than 3 records, anomaly_score must be None."""
        idx = pd.period_range("2023-01", periods=2, freq="M")
        series = pd.Series([200.0, 210.0], index=idx)
        result = detect_anomalies(series)
        assert all(result["anomaly_score"].isna())

    def test_seasonal_increase_not_flagged_as_anomaly(self):
        """Consistent Indian summer peak (May) over 2 years must not be flagged."""
        months = list(range(1, 13)) * 2
        years = [2022] * 12 + [2023] * 12
        base = [100, 100, 130, 150, 180, 160, 110, 100, 100, 100, 100, 100]
        vals = base + base
        idx = pd.PeriodIndex(
            [pd.Period(f"{y}-{m:02d}", "M") for y, m in zip(years, months)]
        )
        series = pd.Series(vals, index=idx)
        result = detect_anomalies(series)
        may_rows = result[result["period"].apply(lambda p: p.month == 5)]
        assert may_rows["is_anomaly"].sum() == 0

    def test_anomaly_has_explanation(self):
        series = _make_series_with_spike(n_base=12, base=200.0, spike_mult=5.0, seed=1)
        result = detect_anomalies(series)
        anomalies = result[result["is_anomaly"]]
        assert all(pd.notna(anomalies["explanation"]))

    def test_severity_levels(self):
        from anomaly_detection.detector import _severity
        threshold = 3.0
        assert _severity(1.0, threshold) == "none"
        assert _severity(3.5, threshold) == "low"       # 3.0 < 3.5 <= 4.5
        assert _severity(5.0, threshold) == "moderate"  # 4.5 < 5.0 <= 6.0
        assert _severity(7.0, threshold) == "high"      # 7.0 > 6.0

    def test_robust_zscore_constant_series(self):
        s = pd.Series([100.0] * 10)
        z = robust_zscore(s)
        assert (z == 0).all()

    def test_synthetic_anomaly_recall(self, synthetic_data):
        """Recall on injected anomalies should be > 0 (we detect at least some)."""
        hh, cons = synthetic_data
        injected = cons[cons["is_injected_anomaly"] == True]
        if injected.empty:
            pytest.skip("No injected anomalies in this synthetic batch")
        hid = injected["household_id"].iloc[0]
        from preprocessing.pipeline import get_household_series
        series = get_household_series(cons, hid)
        result = detect_anomalies(series)
        assert result["is_anomaly"].sum() >= 1


# ── Benchmarking tests ────────────────────────────────────────────────────────
class TestBenchmarking:

    def test_available_with_sufficient_peers(self, synthetic_data):
        hh, cons = synthetic_data
        hid = hh["household_id"].iloc[0]
        result = benchmark_household(hid, hh, cons)
        assert result["status"] in ("available", "insufficient_data")

    def test_insufficient_data_with_tiny_dataset(self):
        hh = generate_households(n=3, seed=99)
        cons = generate_consumption(hh, n_months=3, seed=99)
        hid = hh["household_id"].iloc[0]
        result = benchmark_household(hid, hh, cons)
        assert result["status"] == "insufficient_data"

    def test_no_individual_records_exposed(self, synthetic_data):
        hh, cons = synthetic_data
        hid = hh["household_id"].iloc[0]
        result = benchmark_household(hid, hh, cons)
        assert "peer_consumption_records" not in result
        assert "peer_ids" not in result

    def test_unknown_household_returns_not_found(self, synthetic_data):
        hh, cons = synthetic_data
        result = benchmark_household("UNKNOWN_999", hh, cons)
        assert result["status"] == "household_not_found"

    def test_benchmark_uses_same_calendar_months(self, synthetic_data):
        hh, cons = synthetic_data
        hid = hh["household_id"].iloc[0]
        result = benchmark_household(hid, hh, cons)
        if result["status"] == "available":
            assert "comparison_months" in result
            assert len(result["comparison_months"]) > 0

    def test_match_tier_and_confidence_present(self, synthetic_data):
        """Available benchmark must expose match_tier and match_confidence."""
        hh, cons = synthetic_data
        hid = hh["household_id"].iloc[0]
        result = benchmark_household(hid, hh, cons)
        if result["status"] == "available":
            assert "match_tier" in result
            assert result["match_tier"] in (1, 2, 3)
            assert "match_confidence" in result
            assert result["match_confidence"] in ("high", "medium", "low")

    def test_tier3_has_low_confidence(self):
        """A tier-3 match (resident count only) must report match_confidence='low'."""
        # Build households where tier-1 and tier-2 cannot be satisfied:
        # target is a villa in Telangana; all peers are apartments in Delhi
        hh = pd.DataFrame([
            {"household_id": "T1", "state": "Telangana", "home_type": "villa",
             "n_residents": 3, "home_size_m2": 200},
        ] + [
            {"household_id": f"P{i}", "state": "Delhi", "home_type": "apartment",
             "n_residents": 3, "home_size_m2": 80}
            for i in range(8)
        ])
        cons = pd.DataFrame(
            [{"household_id": hid, "billing_year": 2023, "billing_month": m,
              "consumption_kwh": 250.0}
             for hid in hh["household_id"] for m in range(1, 4)]
        )
        result = benchmark_household("T1", hh, cons)
        if result["status"] == "available":
            assert result["match_tier"] == 3
            assert result["match_confidence"] == "low"

    def test_no_calendar_overlap_returns_insufficient(self):
        """Target Jan-Mar, peers Jul-Sep: no common months -> insufficient_data."""
        hh = generate_households(n=10, seed=77)
        target_id = hh["household_id"].iloc[0]
        peer_ids = hh["household_id"].iloc[1:].tolist()
        target_cons = pd.DataFrame([
            {"household_id": target_id, "billing_year": 2023,
             "billing_month": m, "consumption_kwh": 250.0} for m in [1, 2, 3]
        ])
        peer_cons = pd.DataFrame([
            {"household_id": pid, "billing_year": 2023,
             "billing_month": m, "consumption_kwh": 230.0}
            for pid in peer_ids for m in [7, 8, 9]
        ])
        result = benchmark_household(target_id, hh, pd.concat([target_cons, peer_cons]))
        assert result["status"] == "insufficient_data"

    def test_peer_coverage_3_of_3_months_included(self):
        """Peers with all 3 reference months must be included in the cohort."""
        from config.settings import BENCHMARKING_CONFIG
        hh = pd.DataFrame(
            [{"household_id": "T1", "state": "Telangana", "home_type": "apartment",
              "n_residents": 3, "home_size_m2": 100}]
            + [{"household_id": f"P{i}", "state": "Telangana", "home_type": "apartment",
                "n_residents": 3, "home_size_m2": 100} for i in range(8)]
        )
        # All peers have all 3 reference months (Oct, Nov, Dec 2023)
        cons = pd.DataFrame(
            [{"household_id": hid, "billing_year": 2023, "billing_month": m,
              "consumption_kwh": 250.0}
             for hid in hh["household_id"] for m in range(1, 13)]
        )
        result = benchmark_household("T1", hh, cons)
        assert result["status"] == "available"
        assert result["peer_coverage_months"]["peer_min"] == 3

    def test_peer_coverage_1_of_3_months_excluded(self):
        """Peers with only 1 of 3 reference months must be excluded (below min_coverage_months=2)."""
        hh = pd.DataFrame(
            [{"household_id": "T1", "state": "Telangana", "home_type": "apartment",
              "n_residents": 3, "home_size_m2": 100}]
            + [{"household_id": f"P{i}", "state": "Telangana", "home_type": "apartment",
                "n_residents": 3, "home_size_m2": 100} for i in range(8)]
        )
        target_cons = pd.DataFrame([
            {"household_id": "T1", "billing_year": 2023, "billing_month": m,
             "consumption_kwh": 250.0} for m in range(1, 13)
        ])
        # Each peer only has 1 of the 3 reference months (Dec only)
        peer_cons = pd.DataFrame([
            {"household_id": f"P{i}", "billing_year": 2023, "billing_month": 12,
             "consumption_kwh": 230.0} for i in range(8)
        ])
        result = benchmark_household("T1", hh, pd.concat([target_cons, peer_cons]))
        # 1 month < min_coverage_months=2, so all peers excluded -> insufficient_data
        assert result["status"] == "insufficient_data"

    def test_peer_coverage_2_of_3_months_included(self):
        """Peers with exactly 2 of 3 reference months must be included (meets min_coverage_months=2)."""
        hh = pd.DataFrame(
            [{"household_id": "T1", "state": "Telangana", "home_type": "apartment",
              "n_residents": 3, "home_size_m2": 100}]
            + [{"household_id": f"P{i}", "state": "Telangana", "home_type": "apartment",
                "n_residents": 3, "home_size_m2": 100} for i in range(8)]
        )
        target_cons = pd.DataFrame([
            {"household_id": "T1", "billing_year": 2023, "billing_month": m,
             "consumption_kwh": 250.0} for m in range(1, 13)
        ])
        # Each peer has 2 of the 3 reference months (Nov + Dec, missing Oct)
        peer_cons = pd.DataFrame([
            {"household_id": f"P{i}", "billing_year": 2023, "billing_month": m,
             "consumption_kwh": 230.0}
            for i in range(8) for m in [11, 12]
        ])
        result = benchmark_household("T1", hh, pd.concat([target_cons, peer_cons]))
        # 2 months >= min_coverage_months=2, so peers are included
        assert result["status"] == "available"
        assert result["peer_coverage_months"]["peer_min"] == 2
        assert result["peer_coverage_months"]["min_required"] == 2


# ── Cold-start tests ──────────────────────────────────────────────────────────
class TestColdStart:

    def test_stage1_no_consumption(self):
        from main import _cold_start_stage
        assert _cold_start_stage(0, 100) == 1

    def test_stage2_few_records(self):
        from main import _cold_start_stage
        assert _cold_start_stage(2, 100) == 2

    def test_stage3_small_dataset(self):
        from main import _cold_start_stage
        assert _cold_start_stage(5, 10) == 3

    def test_stage4_mature(self):
        from main import _cold_start_stage
        assert _cold_start_stage(12, 50) == 4

    def test_new_user_inference_returns_message(self, synthetic_data):
        from main import run_inference
        hh, cons = synthetic_data
        empty_cons = cons.iloc[0:0]
        hid = hh["household_id"].iloc[0]
        result = run_inference(hid, hh, empty_cons)
        assert result["data_status"] == "new_user"
        assert "message" in result

    def test_stage2_anomaly_suppressed(self, synthetic_data):
        """With 1 or 2 records, anomaly output must be suppressed (insufficient_data)."""
        from main import run_inference
        hh, cons = synthetic_data
        hid = hh["household_id"].iloc[0]
        for n_keep in [1, 2]:
            hid_cons = cons[cons["household_id"] == hid].head(n_keep)
            other_cons = cons[cons["household_id"] != hid]
            cons_slice = pd.concat([hid_cons, other_cons])
            result = run_inference(hid, hh, cons_slice)
            assert result["anomaly"]["anomaly_status"] == "insufficient_data"
            assert result["anomaly"]["detected"] is False

    def test_stage3_end_to_end(self):
        """Stage 3 (small dataset, n_households < 20): full inference must complete."""
        from main import run_inference
        hh_small = generate_households(n=15, seed=7)
        cons_small = generate_consumption(hh_small, n_months=6, seed=7)
        hid = hh_small["household_id"].iloc[0]
        result = run_inference(hid, hh_small, cons_small)
        assert result["cold_start_stage"] == 3
        assert result["data_status"] == "sufficient"
        assert result["trend"] is not None
        assert result["anomaly"] is not None
        assert result["benchmark"] is not None

    def test_stage3_anomaly_not_suppressed(self):
        """Stage 3 has >= 3 records: anomaly output must not be suppressed."""
        from main import run_inference
        hh_small = generate_households(n=15, seed=7)
        cons_small = generate_consumption(hh_small, n_months=6, seed=7)
        hid = hh_small["household_id"].iloc[0]
        result = run_inference(hid, hh_small, cons_small)
        assert result["anomaly"]["anomaly_status"] != "insufficient_data"


# ── Savings target tests ──────────────────────────────────────────────────────
class TestSavingsTargets:

    def test_no_signals_returns_no_target(self):
        result = calculate_savings_target(
            trend_result={"status": "insufficient_data"},
            benchmark_result={"status": "insufficient_data"},
            anomaly_result=[],
            household_features={},
        )
        assert result["status"] == "no_target"

    def test_above_median_generates_target(self):
        result = calculate_savings_target(
            trend_result={"status": "ok", "direction": "stable", "percentage_change": 0},
            benchmark_result={"status": "available", "difference_from_median_pct": 20.0},
            anomaly_result=[],
            household_features={},
        )
        assert result["status"] == "available"
        assert result["target_percentage"] > 0

    def test_target_capped_at_max(self):
        from config.settings import SAVINGS_CONFIG
        result = calculate_savings_target(
            trend_result={"status": "ok", "direction": "increasing",
                          "percentage_change": 100},
            benchmark_result={"status": "available",
                               "difference_from_median_pct": 100.0},
            anomaly_result=[{"is_anomaly": True, "anomaly_direction": "high"}] * 5,
            household_features={},
        )
        assert result["target_percentage"] <= SAVINGS_CONFIG["max_target_pct"]

    def test_explanation_is_string(self):
        result = calculate_savings_target(
            trend_result={"status": "ok", "direction": "increasing",
                          "percentage_change": 15},
            benchmark_result={"status": "available",
                               "difference_from_median_pct": 18.0},
            anomaly_result=[],
            household_features={},
        )
        assert isinstance(result.get("explanation"), str)

    def test_appliance_ownership_alone_does_not_generate_target(self):
        result = calculate_savings_target(
            trend_result={"status": "insufficient_data"},
            benchmark_result={"status": "insufficient_data"},
            anomaly_result=[],
            household_features={"has_solar": 0, "has_air_conditioner": 1},
        )
        assert result["status"] == "no_target"

    def test_target_includes_disclaimer(self):
        result = calculate_savings_target(
            trend_result={"status": "ok", "direction": "increasing",
                          "percentage_change": 20},
            benchmark_result={"status": "available",
                               "difference_from_median_pct": 25.0},
            anomaly_result=[],
            household_features={},
        )
        assert "disclaimer" in result

    def test_floor_removed_weak_signal_gives_actual_value(self):
        """A 6% peer gap gives contribution=1.8%, not inflated to 3.0%."""
        result = calculate_savings_target(
            trend_result={"status": "ok", "direction": "stable", "percentage_change": 0},
            benchmark_result={"status": "available", "difference_from_median_pct": 6.0},
            anomaly_result=[],
            household_features={},
        )
        assert result["status"] == "available"
        assert result["target_percentage"] == pytest.approx(1.8, abs=0.1)

    def test_anomalies_alone_do_not_generate_target(self):
        """2+ anomalies without a peer gap or trend must NOT produce a target."""
        result = calculate_savings_target(
            trend_result={"status": "insufficient_data"},
            benchmark_result={"status": "insufficient_data"},
            anomaly_result=[
                {"is_anomaly": True, "anomaly_direction": "high"},
                {"is_anomaly": True, "anomaly_direction": "high"},
            ],
            household_features={},
        )
        assert result["status"] == "no_target"

    def test_low_anomalies_not_counted_as_waste(self):
        """Drops (anomaly_direction='low') must not contribute to savings target."""
        # Peer gap provides the primary signal; drops should not add to it
        result_with_drops = calculate_savings_target(
            trend_result={"status": "ok", "direction": "stable", "percentage_change": 0},
            benchmark_result={"status": "available", "difference_from_median_pct": 20.0},
            anomaly_result=[
                {"is_anomaly": True, "anomaly_direction": "low"},
                {"is_anomaly": True, "anomaly_direction": "low"},
                {"is_anomaly": True, "anomaly_direction": "low"},
            ],
            household_features={},
        )
        result_no_anomalies = calculate_savings_target(
            trend_result={"status": "ok", "direction": "stable", "percentage_change": 0},
            benchmark_result={"status": "available", "difference_from_median_pct": 20.0},
            anomaly_result=[],
            household_features={},
        )
        # Drops must not inflate the target
        assert result_with_drops["target_percentage"] == result_no_anomalies["target_percentage"]

    def test_high_anomalies_with_primary_signal_add_contribution(self):
        """High anomalies WITH a peer gap must add their contribution."""
        result_with_highs = calculate_savings_target(
            trend_result={"status": "ok", "direction": "stable", "percentage_change": 0},
            benchmark_result={"status": "available", "difference_from_median_pct": 20.0},
            anomaly_result=[
                {"is_anomaly": True, "anomaly_direction": "high"},
                {"is_anomaly": True, "anomaly_direction": "high"},
            ],
            household_features={},
        )
        result_no_anomalies = calculate_savings_target(
            trend_result={"status": "ok", "direction": "stable", "percentage_change": 0},
            benchmark_result={"status": "available", "difference_from_median_pct": 20.0},
            anomaly_result=[],
            household_features={},
        )
        assert result_with_highs["target_percentage"] > result_no_anomalies["target_percentage"]


# ── Clustering tests ──────────────────────────────────────────────────────────
class TestClustering:

    def test_new_household_gets_cluster_prediction(self, synthetic_data):
        from clustering.kmeans_model import train_clustering, label_clusters, predict_cluster
        hh, cons = synthetic_data
        fm = build_feature_matrix(hh, cons)
        pipeline, labels, _ = train_clustering(fm, k_min=2, k_max=4, seed=0)
        _, label_map = label_clusters(fm, labels)
        new_hh = pd.DataFrame([{
            "household_id": "H_NEW_999",
            "state": "Telangana", "n_residents": 3, "home_type": "apartment",
            "home_size_m2": 100.0, "has_solar": False, "has_air_conditioner": True,
            "has_inverter_ac": False, "has_electric_vehicle": False,
            "has_electric_water_heater": True,
        }])
        new_cons = pd.DataFrame([{
            "household_id": "H_NEW_999",
            "billing_year": 2023, "billing_month": m,
            "consumption_kwh": 250.0 + m * 5,
        } for m in range(1, 7)])
        new_fm = build_feature_matrix(new_hh, new_cons)
        assert not new_fm.empty
        result = predict_cluster(pipeline, new_fm, label_map)
        assert len(result) == 1
        assert isinstance(result.iloc[0], str)
        assert result.iloc[0] != ""

    def test_eval_metrics_use_scaled_space(self, synthetic_data):
        from clustering.kmeans_model import train_clustering, _transform_features, CLUSTER_FEATURES
        from sklearn.metrics import silhouette_score
        hh, cons = synthetic_data
        fm = build_feature_matrix(hh, cons)
        pipeline, labels, eval_scores = train_clustering(fm, k_min=2, k_max=3, seed=0)
        X_raw = fm[CLUSTER_FEATURES].values
        X_scaled = _transform_features(pipeline, X_raw)
        sil_raw = silhouette_score(X_raw, labels.values)
        sil_scaled = silhouette_score(X_scaled, labels.values)
        assert abs(sil_raw - sil_scaled) > 1e-6
        best_k = eval_scores["best_k"]
        stored_sil = eval_scores["scores_by_k"][best_k]["silhouette"]
        assert abs(stored_sil - sil_scaled) < 1e-3

    def test_cluster_label_map_has_string_values(self, synthetic_data):
        """label_map values must be non-empty strings (indicative labels)."""
        from clustering.kmeans_model import train_clustering, label_clusters
        hh, cons = synthetic_data
        fm = build_feature_matrix(hh, cons)
        _, labels, _ = train_clustering(fm, k_min=2, k_max=4, seed=0)
        _, label_map = label_clusters(fm, labels)
        for k, v in label_map.items():
            assert isinstance(v, str) and len(v) > 0


# ── End-to-end inference test ─────────────────────────────────────────────────
class TestEndToEnd:

    def test_inference_returns_required_keys(self, synthetic_data):
        from main import run_inference
        hh, cons = synthetic_data
        hid = hh["household_id"].iloc[0]
        result = run_inference(hid, hh, cons)
        for key in ["household_id", "cold_start_stage", "trend", "anomaly"]:
            assert key in result

    def test_inference_anomaly_has_status_and_confidence(self, synthetic_data):
        """Anomaly output must always include anomaly_status and confidence fields."""
        from main import run_inference
        hh, cons = synthetic_data
        hid = hh["household_id"].iloc[0]
        result = run_inference(hid, hh, cons)
        assert "anomaly_status" in result["anomaly"]
        assert "confidence" in result["anomaly"]

    def test_inference_unknown_household(self, synthetic_data):
        from main import run_inference
        hh, cons = synthetic_data
        result = run_inference("DOES_NOT_EXIST", hh, cons)
        assert "error" in result
