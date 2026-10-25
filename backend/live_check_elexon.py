"""Live check of the Elexon fetching service (uses the real internet).

Run from the backend folder:
    python live_check_elexon.py            # quick check for January 1 only
    python live_check_elexon.py --month    # full January check (slower)
"""
import sys
from collections import Counter
from datetime import datetime, timezone

from app import config
from app.services.elexon_client import (
    ElexonAPIError,
    fetch_actual_wind_records,
    fetch_forecast_records,
)


def utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


def check_january_1() -> None:
    print("--- January 1 check ---")
    actuals = fetch_actual_wind_records(utc(2026, 1, 1), utc(2026, 1, 2, 1))
    periods = {r["startTime"] for r in actuals if r["startTime"].startswith("2026-01-01")}
    print(f"Actual WIND half-hours on Jan 1: {len(periods)} (expected 48)")

    forecasts = fetch_forecast_records(utc(2025, 12, 31), utc(2026, 1, 1))
    rows = [r for r in forecasts if r["startTime"].startswith("2026-01-01")]
    per_version = Counter(r["publishTime"] for r in rows)
    print(f"Forecast versions published on Dec 31 for Jan 1: {len(per_version)} (expected 8)")
    for publish_time, count in sorted(per_version.items()):
        print(f"  {publish_time}: {count} hourly rows (expected 24)")


def check_month() -> None:
    print("--- Full January check ---")
    actuals = fetch_actual_wind_records(config.ACTUALS_PUBLISH_FROM, config.ACTUALS_PUBLISH_TO)
    jan_actuals = [r for r in actuals if r["startTime"].startswith("2026-01")]
    unique_periods = {r["startTime"] for r in jan_actuals}
    print(f"WIND actual records in January: {len(jan_actuals)}")
    print(f"Unique half-hourly periods: {len(unique_periods)} (expected 1488)")

    forecasts = fetch_forecast_records(config.FORECAST_PUBLISH_FROM, config.FORECAST_PUBLISH_TO)
    jan_forecasts = [r for r in forecasts if r["startTime"].startswith("2026-01")]
    unique_delivery = {r["startTime"] for r in jan_forecasts}
    print(f"Forecast records for January delivery: {len(jan_forecasts)}")
    print(f"Unique forecast delivery hours: {len(unique_delivery)} (expected 744)")


if __name__ == "__main__":
    try:
        check_january_1()
        if "--month" in sys.argv:
            check_month()
    except ElexonAPIError as error:
        print(f"Elexon API problem: {error}")