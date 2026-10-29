"""
SYNTHETIC DATA GENERATOR
========================
All data produced here is SYNTHETIC and must never be treated as real observations.
Used exclusively for development, testing and demonstration.
Context: Indian household electricity consumption.
"""
import numpy as np
import pandas as pd
from pathlib import Path
from config.settings import TARIFF_CONFIG


# Indian states — Telangana listed first as primary context
STATES = ["Telangana", "Andhra Pradesh", "Maharashtra", "Karnataka",
          "Tamil Nadu", "Delhi", "Gujarat", "Rajasthan"]
HOME_TYPES = ["house", "apartment", "flat", "villa"]

# Indian seasonal multipliers (Northern Hemisphere, tropical/subtropical)
# Summer (Mar–Jun): peak AC load; Monsoon (Jul–Sep): moderate; Winter (Nov–Feb): low
SEASONAL = {
    1: 0.85,   # Jan — cool/mild
    2: 0.90,   # Feb — warming
    3: 1.10,   # Mar — pre-summer heat
    4: 1.25,   # Apr — hot
    5: 1.35,   # May — peak summer
    6: 1.30,   # Jun — peak summer / early monsoon
    7: 1.05,   # Jul — monsoon, AC reduces
    8: 1.00,   # Aug — monsoon
    9: 1.00,   # Sep — post-monsoon
    10: 0.95,  # Oct — mild
    11: 0.85,  # Nov — cool
    12: 0.80,  # Dec — coolest
}


def _base_consumption(n_residents: int, home_type: str, has_solar: bool,
                      has_ac: bool, has_inverter_ac: bool, has_ev: bool) -> float:
    base = 100 + n_residents * 50  # Indian baseline lower than Australian
    if home_type == "house" or home_type == "villa":
        base += 40
    elif home_type == "flat":
        base -= 20
    if has_ac:
        base += 90   # AC is dominant load in India
    if has_inverter_ac:
        base -= 20   # inverter AC is more efficient
    if has_ev:
        base += 80
    if has_solar:
        base *= 0.72
    return max(base, 50.0)


def generate_households(n: int = 300, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    records = []
    for i in range(n):
        hid = f"H{i+1:04d}"
        state = rng.choice(STATES)
        n_res = int(rng.choice([1, 2, 3, 4, 5, 6], p=[0.10, 0.25, 0.25, 0.20, 0.12, 0.08]))
        home_type = rng.choice(HOME_TYPES, p=[0.40, 0.35, 0.15, 0.10])
        home_size_m2 = float(rng.integers(40, 300))
        has_solar = bool(rng.random() < 0.15)          # lower solar penetration in India
        has_ac = bool(rng.random() < 0.55)             # ~55% AC ownership
        has_inverter_ac = has_ac and bool(rng.random() < 0.50)
        has_ev = bool(rng.random() < 0.05)
        has_electric_water_heater = bool(rng.random() < 0.60)  # geysers common
        records.append({
            "household_id": hid,
            "state": state,
            "n_residents": n_res,
            "home_type": home_type,
            "home_size_m2": home_size_m2,
            "has_solar": has_solar,
            "has_air_conditioner": has_ac,
            "has_inverter_ac": has_inverter_ac,
            "has_electric_vehicle": has_ev,
            "has_electric_water_heater": has_electric_water_heater,
            "data_source": "SYNTHETIC",
        })
    return pd.DataFrame(records)


def generate_consumption(
    households: pd.DataFrame,
    n_months: int = 24,
    start_year: int = 2023,
    start_month: int = 1,
    seed: int = 42,
    anomaly_fraction: float = 0.03,
) -> pd.DataFrame:
    """
    Generate monthly consumption records in kWh with INR bill amounts.
    anomaly_fraction: proportion of records injected with a known anomaly
                      (labelled is_injected_anomaly=True for evaluation).
    """
    rng = np.random.default_rng(seed)
    records = []

    dates = pd.date_range(
        start=f"{start_year}-{start_month:02d}-01", periods=n_months, freq="MS"
    )

    for _, hh in households.iterrows():
        base = _base_consumption(
            hh["n_residents"], hh["home_type"], hh["has_solar"],
            hh["has_air_conditioner"], hh["has_inverter_ac"], hh["has_electric_vehicle"],
        )
        noise_scale = rng.uniform(0.05, 0.15)
        drift = rng.choice([-0.003, 0.0, 0.003, 0.006], p=[0.10, 0.50, 0.30, 0.10])

        for t, dt in enumerate(dates):
            seasonal_mult = SEASONAL[dt.month]
            trend_mult = 1.0 + drift * t
            noise = rng.normal(1.0, noise_scale)
            kwh = round(base * seasonal_mult * trend_mult * noise, 1)
            kwh = max(kwh, 20.0)

            is_anomaly = False
            if rng.random() < anomaly_fraction:
                kwh = round(kwh * rng.uniform(2.0, 3.5), 1)
                is_anomaly = True

            records.append({
                "household_id": hh["household_id"],
                "billing_year": dt.year,
                "billing_month": dt.month,
                "consumption_kwh": kwh,
                "bill_amount_inr": round(kwh * rng.uniform(
                    TARIFF_CONFIG["min_inr_per_kwh"],
                    TARIFF_CONFIG["max_inr_per_kwh"]
                ), 2),
                "is_injected_anomaly": is_anomaly,
                "data_source": "SYNTHETIC",
            })

    return pd.DataFrame(records)


def save_synthetic_data(out_dir: Path, n_households: int = 300,
                        n_months: int = 24, seed: int = 42) -> tuple:
    out_dir.mkdir(parents=True, exist_ok=True)
    hh = generate_households(n=n_households, seed=seed)
    cons = generate_consumption(hh, n_months=n_months, seed=seed)
    hh_path = out_dir / "synthetic_households.csv"
    cons_path = out_dir / "synthetic_consumption.csv"
    hh.to_csv(hh_path, index=False)
    cons.to_csv(cons_path, index=False)
    print(f"[SYNTHETIC] Saved {len(hh)} households -> {hh_path}")
    print(f"[SYNTHETIC] Saved {len(cons)} consumption records -> {cons_path}")
    return hh_path, cons_path


if __name__ == "__main__":
    from config.settings import DATA_DIR
    save_synthetic_data(DATA_DIR)
