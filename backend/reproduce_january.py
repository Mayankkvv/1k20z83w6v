"""Reproduce the preliminary January 2026 results with the production analysis code.

Run from the backend folder (uses the real internet, takes a minute or two):
    python reproduce_january.py
"""
from datetime import time

from app import config
from app.analysis.metrics import compute_metrics, daily_summaries
from app.analysis.processing import build_hourly_table
from app.services.elexon_client import (
    ElexonAPIError,
    fetch_actual_wind_records,
    fetch_forecast_records,
)

# Results printed by the exploratory scripts in Step 1.
PRELIMINARY_MONTH = {
    "matched_periods": 744,
    "mae_mw": 2122.81,
    "rmse_mw": 2616.69,
    "mean_bias_mw": 1840.30,
    "mape_pct": 22.06,
    "overforecast_periods": 628,
    "underforecast_periods": 116,
    "exact_matches": 0,
}
PRELIMINARY_JAN_1 = {"matched_periods": 24, "mae_mw": 4258.21, "rmse_mw": 4300.92, "mean_bias_mw": 4258.21, "mape_pct": 27.89}


def print_comparison(title: str, new: dict, old: dict) -> None:
    print(f"\n{title}")
    print(f"{'metric':<24}{'production':>14}{'preliminary':>14}  match")
    for key, old_value in old.items():
        new_value = new[key]
        same = new_value is not None and abs(new_value - old_value) <= 0.01
        print(f"{key:<24}{new_value!s:>14}{old_value!s:>14}  {'yes' if same else 'NO'}")


def main() -> None:
    print("Fetching actuals and forecasts from Elexon ...")
    actuals = fetch_actual_wind_records(config.ACTUALS_PUBLISH_FROM, config.ACTUALS_PUBLISH_TO)
    forecasts = fetch_forecast_records(config.FORECAST_PUBLISH_FROM, config.FORECAST_PUBLISH_TO)
    print(f"Raw WIND actual records: {len(actuals)}   Raw forecast records: {len(forecasts)}")

    rows = build_hourly_table(actuals, forecasts)
    month = compute_metrics(rows)
    print(f"Hourly rows: {month['total_periods']}   Matched: {month['matched_periods']}   "
          f"Coverage: {month['coverage_pct']}%")
    print(f"Status counts: {month['status_counts']}")
    print_comparison("Full January 2026 (cutoff 09:50 UTC the day before)", month, PRELIMINARY_MONTH)

    jan_1 = daily_summaries(rows)[0]
    print_comparison("January 1 only", jan_1, PRELIMINARY_JAN_1)

    print("\nSensitivity: same month with the earlier EPEX cutoff of 09:20 UTC")
    early_rows = build_hourly_table(actuals, forecasts, cutoff_time=time(9, 20))
    early = compute_metrics(early_rows)
    print(f"MAE {early['mae_mw']} MW   RMSE {early['rmse_mw']} MW   bias {early['mean_bias_mw']} MW   "
          f"matched {early['matched_periods']}")

    worst = sorted((d for d in daily_summaries(rows) if d["mae_mw"] is not None),
                   key=lambda d: d["mae_mw"], reverse=True)[:3]
    print("\nThree days with the highest MAE:")
    for day in worst:
        print(f"  {day['date']}: MAE {day['mae_mw']} MW, bias {day['mean_bias_mw']} MW")


if __name__ == "__main__":
    try:
        main()
    except ElexonAPIError as error:
        print(f"Elexon API problem: {error}")