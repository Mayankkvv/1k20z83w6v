from datetime import date, datetime, time, timezone

import pytest

from app.analysis import processing

UTC = timezone.utc
JAN_1 = datetime(2026, 1, 1, tzinfo=UTC)


def dt(day, hour, minute=0, month=1, year=2026):
    return datetime(year, month, day, hour, minute, tzinfo=UTC)


def iso(value):
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def actual(start, generation, publish=None):
    return {
        "startTime": iso(start),
        "publishTime": iso(publish or start),
        "fuelType": "WIND",
        "generation": generation,
    }


def forecast(start, publish, generation):
    return {"startTime": iso(start), "publishTime": iso(publish), "generation": generation}


# ---------- timestamps and cutoff ----------

def test_parse_utc_reads_z_suffix():
    assert processing.parse_utc("2026-01-01T00:30:00Z") == dt(1, 0, 30)


def test_parse_utc_rejects_timestamp_without_timezone():
    with pytest.raises(ValueError):
        processing.parse_utc("2026-01-01T00:30:00")


def test_decision_cutoff_is_09_50_on_previous_day():
    assert processing.decision_cutoff(date(2026, 1, 1)) == datetime(2025, 12, 31, 9, 50, tzinfo=UTC)


def test_decision_cutoff_time_is_configurable():
    cutoff = processing.decision_cutoff(date(2026, 1, 1), time(9, 20))
    assert cutoff == datetime(2025, 12, 31, 9, 20, tzinfo=UTC)


# ---------- forecast selection ----------

def test_latest_forecast_before_cutoff_is_selected():
    delivery = dt(1, 0)
    records = [
        forecast(delivery, dt(31, 7, 30, month=12, year=2025), 1000),
        forecast(delivery, dt(31, 9, 30, month=12, year=2025), 2000),
        forecast(delivery, dt(31, 11, 30, month=12, year=2025), 3000),
    ]
    selected = processing.select_eligible_forecasts(records)
    assert selected[delivery]["forecast_mw"] == 2000
    assert selected[delivery]["publish_time"] == dt(31, 9, 30, month=12, year=2025)


def test_forecast_after_cutoff_is_rejected_and_hour_is_missing():
    delivery = dt(1, 0)
    records = [forecast(delivery, dt(31, 11, 30, month=12, year=2025), 3000)]
    assert processing.select_eligible_forecasts(records) == {}


def test_forecast_published_on_delivery_day_is_rejected():
    delivery = dt(1, 5)
    records = [forecast(delivery, dt(1, 0, 30), 3000)]
    assert processing.select_eligible_forecasts(records) == {}


def test_forecast_published_exactly_at_cutoff_is_eligible():
    delivery = dt(1, 0)
    records = [forecast(delivery, dt(31, 9, 50, month=12, year=2025), 1234)]
    assert processing.select_eligible_forecasts(records)[delivery]["forecast_mw"] == 1234


def test_cutoff_applies_to_every_hour_of_the_delivery_day():
    delivery = dt(1, 23)
    records = [
        forecast(delivery, dt(31, 9, 30, month=12, year=2025), 111),
        forecast(delivery, dt(31, 11, 30, month=12, year=2025), 222),
    ]
    assert processing.select_eligible_forecasts(records)[delivery]["forecast_mw"] == 111


def test_different_cutoff_time_selects_a_different_forecast():
    delivery = dt(1, 0)
    records = [
        forecast(delivery, dt(31, 7, 30, month=12, year=2025), 1000),
        forecast(delivery, dt(31, 9, 30, month=12, year=2025), 2000),
    ]
    selected = processing.select_eligible_forecasts(records, cutoff_time=time(9, 20))
    assert selected[delivery]["forecast_mw"] == 1000


def test_forecast_with_null_generation_is_ignored():
    delivery = dt(1, 0)
    records = [forecast(delivery, dt(31, 9, 30, month=12, year=2025), None)]
    assert processing.select_eligible_forecasts(records) == {}


# ---------- hourly actuals ----------

def test_two_half_hours_become_one_hourly_mean():
    records = [actual(dt(1, 0, 0), 100), actual(dt(1, 0, 30), 200)]
    hourly = processing.build_hourly_actuals(records)
    assert hourly[dt(1, 0)] == {"actual_mw": 150.0, "complete": True}


def test_incomplete_hour_has_no_value():
    hourly = processing.build_hourly_actuals([actual(dt(1, 0, 0), 100)])
    assert hourly[dt(1, 0)] == {"actual_mw": None, "complete": False}


def test_duplicate_records_are_not_double_counted():
    records = [
        actual(dt(1, 0, 0), 100),
        actual(dt(1, 0, 0), 100),
        actual(dt(1, 0, 30), 200),
    ]
    assert processing.build_hourly_actuals(records)[dt(1, 0)]["actual_mw"] == 150.0


def test_duplicate_with_newer_publish_time_wins():
    records = [
        actual(dt(1, 0, 0), 100, publish=dt(1, 0, 30)),
        actual(dt(1, 0, 0), 120, publish=dt(1, 6, 0)),
        actual(dt(1, 0, 30), 200, publish=dt(1, 1, 0)),
    ]
    assert processing.build_hourly_actuals(records)[dt(1, 0)]["actual_mw"] == 160.0


def test_actual_with_null_generation_makes_hour_incomplete():
    records = [actual(dt(1, 0, 0), 100), actual(dt(1, 0, 30), None)]
    assert processing.build_hourly_actuals(records)[dt(1, 0)]["complete"] is False


# ---------- hourly table ----------

def make_day_records():
    actuals = [
        actual(dt(1, 0, 0), 100),
        actual(dt(1, 0, 30), 200),
        actual(dt(1, 1, 0), 300),
        actual(dt(1, 1, 30), 500),
    ]
    published = dt(31, 9, 30, month=12, year=2025)
    forecasts = [forecast(dt(1, 0), published, 160), forecast(dt(1, 1), published, 380)]
    return actuals, forecasts


def test_forecast_and_actual_are_matched_on_delivery_hour():
    actuals, forecasts = make_day_records()
    rows = processing.build_hourly_table(actuals, forecasts, dt(1, 0), dt(1, 2))
    assert len(rows) == 2
    first, second = rows
    assert first["delivery_time"] == "2026-01-01T00:00:00Z"
    assert (first["forecast_mw"], first["actual_mw"], first["error_mw"]) == (160, 150, 10)
    assert (second["forecast_mw"], second["actual_mw"], second["error_mw"]) == (380, 400, -20)
    assert first["forecast_publish_time"] == "2025-12-31T09:30:00Z"
    assert first["status"] == "ok"


def test_table_has_one_row_for_every_hour_even_without_data():
    rows = processing.build_hourly_table([], [], dt(1, 0), dt(4, 0))
    assert len(rows) == 72
    assert all(row["status"] == "missing_forecast_and_actual" for row in rows)


def test_missing_forecast_is_reported_not_filled():
    actuals, _ = make_day_records()
    late = [forecast(dt(1, 0), dt(31, 11, 30, month=12, year=2025), 999)]
    rows = processing.build_hourly_table(actuals, late, dt(1, 0), dt(1, 1))
    assert rows[0]["forecast_mw"] is None
    assert rows[0]["error_mw"] is None
    assert rows[0]["status"] == "missing_forecast"


def test_missing_actual_is_reported():
    _, forecasts = make_day_records()
    rows = processing.build_hourly_table([], forecasts, dt(1, 0), dt(1, 1))
    assert rows[0]["status"] == "missing_actual"
    assert rows[0]["error_mw"] is None


def test_incomplete_actual_hour_is_reported():
    _, forecasts = make_day_records()
    rows = processing.build_hourly_table([actual(dt(1, 0, 0), 100)], forecasts, dt(1, 0), dt(1, 1))
    assert rows[0]["status"] == "incomplete_actual"
    assert rows[0]["actual_mw"] is None
    assert rows[0]["error_mw"] is None


def test_naive_start_is_rejected():
    with pytest.raises(ValueError):
        processing.build_hourly_table([], [], datetime(2026, 1, 1), dt(1, 2))