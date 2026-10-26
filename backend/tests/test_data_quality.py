"""Tests for unusual or broken data coming from Elexon, and for the UTC time assumption."""
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from app import config
from app.analysis import processing
from app.main import app
from app.services import data_cache, elexon_client

UTC = timezone.utc
client = TestClient(app, raise_server_exceptions=False)


def dt(day, hour, minute=0, month=1, year=2026):
    return datetime(year, month, day, hour, minute, tzinfo=UTC)


GOOD_FORECAST = {
    "startTime": "2026-01-01T00:00:00Z",
    "publishTime": "2025-12-31T09:30:00Z",
    "generation": 160,
}
GOOD_ACTUALS = [
    {"startTime": "2026-01-01T00:00:00Z", "publishTime": "2026-01-01T00:30:00Z", "generation": 100},
    {"startTime": "2026-01-01T00:30:00Z", "publishTime": "2026-01-01T01:00:00Z", "generation": 200},
]


# ---------- the "UK time equals UTC in January" assumption ----------

def test_uk_time_equals_utc_for_the_whole_analysis_period():
    """If this fails, the period was changed to include British Summer Time and the
    cutoff logic (which treats 09:50 UK time as 09:50 UTC) would be wrong."""
    london = ZoneInfo("Europe/London")
    day = (config.ANALYSIS_START - timedelta(days=config.CUTOFF_DAYS_BEFORE_DELIVERY + 2)).date()
    last_day = config.ANALYSIS_END.date()
    while day <= last_day:
        for hour in (0, 9, 23):
            local = datetime(day.year, day.month, day.day, hour, tzinfo=london)
            assert local.utcoffset() == timedelta(0), f"{day} {hour}:00 is not UTC+0 in London"
        day += timedelta(days=1)


def test_decision_cutoff_in_summer_would_differ_from_utc_in_london():
    """Documents why the assumption matters: in July 09:50 London time is 08:50 UTC."""
    london_cutoff = datetime(2026, 7, 1, 9, 50, tzinfo=ZoneInfo("Europe/London"))
    assert london_cutoff.astimezone(UTC).hour == 8
    assert processing.decision_cutoff(date(2026, 7, 2)).hour == 9  # our code uses UTC directly


# ---------- broken records are skipped, never crash ----------

@pytest.mark.parametrize(
    "bad_record",
    [
        {"fuelType": "WIND", "generation": 5},  # no startTime
        {"startTime": "garbage", "generation": 5},  # invalid timestamp
        {"startTime": "2026-01-01T00:00:00", "generation": 5},  # timestamp without timezone
        {"startTime": 12345, "generation": 5},  # wrong type
        {"startTime": "2026-01-01T00:00:00Z", "generation": "abc"},  # generation not a number
        {"startTime": "2026-01-01T00:00:00Z", "generation": float("nan")},
        {"startTime": "2026-01-01T00:00:00Z", "generation": True},
        "not even a dictionary",
        None,
    ],
)
def test_unusable_actual_records_are_ignored(bad_record):
    hourly = processing.build_hourly_actuals([bad_record] + GOOD_ACTUALS)
    assert hourly[dt(1, 0)] == {"actual_mw": 150.0, "complete": True}


@pytest.mark.parametrize(
    "bad_record",
    [
        {"startTime": "2026-01-01T00:00:00Z", "generation": 5},  # no publishTime
        {"startTime": "2026-01-01T00:00:00Z", "publishTime": "nope", "generation": 5},
        {"publishTime": "2025-12-31T09:30:00Z", "generation": 5},  # no startTime
        {"startTime": "2026-01-01T00:00:00Z", "publishTime": "2025-12-31T09:30:00Z", "generation": "x"},
        42,
        None,
    ],
)
def test_unusable_forecast_records_are_ignored(bad_record):
    selected = processing.select_eligible_forecasts([bad_record, GOOD_FORECAST])
    assert selected[dt(1, 0)]["forecast_mw"] == 160


def test_only_broken_records_gives_missing_rows_not_a_crash():
    rows = processing.build_hourly_table([{"startTime": "garbage"}], [{"generation": 1}], dt(1, 0), dt(1, 3))
    assert [row["status"] for row in rows] == ["missing_forecast_and_actual"] * 3


def test_skipped_records_are_logged(caplog):
    with caplog.at_level("WARNING"):
        processing.build_hourly_actuals([{"startTime": "garbage"}] + GOOD_ACTUALS)
    assert "Ignored 1 actual record" in caplog.text


def test_generation_as_numeric_string_is_accepted():
    records = [dict(GOOD_ACTUALS[0], generation="100"), dict(GOOD_ACTUALS[1], generation="200.0")]
    assert processing.build_hourly_actuals(records)[dt(1, 0)]["actual_mw"] == 150.0


def test_zero_generation_is_a_valid_value():
    records = [dict(GOOD_ACTUALS[0], generation=0), dict(GOOD_ACTUALS[1], generation=0)]
    assert processing.build_hourly_actuals(records)[dt(1, 0)] == {"actual_mw": 0.0, "complete": True}


def test_identical_forecast_versions_do_not_change_the_result():
    selected = processing.select_eligible_forecasts([GOOD_FORECAST, dict(GOOD_FORECAST)])
    assert selected[dt(1, 0)]["forecast_mw"] == 160


# ---------- API behaviour with broken data ----------

@pytest.fixture(autouse=True)
def fresh_cache():
    data_cache.clear_cache()
    yield
    data_cache.clear_cache()


def test_api_survives_broken_records(monkeypatch):
    monkeypatch.setattr(
        elexon_client, "fetch_actual_wind_records", lambda a, b: [{"fuelType": "WIND"}] + GOOD_ACTUALS
    )
    monkeypatch.setattr(elexon_client, "fetch_forecast_records", lambda a, b: [{"startTime": "x"}, GOOD_FORECAST])

    response = client.get("/api/day", params={"date": "2026-01-01"})

    assert response.status_code == 200
    first = response.json()["rows"][0]
    assert (first["forecast_mw"], first["actual_mw"], first["error_mw"]) == (160, 150, 10)


def test_unexpected_processing_error_returns_json_500_with_cors_headers(monkeypatch):
    def explode(actuals, forecasts):
        raise RuntimeError("something unexpected")

    monkeypatch.setattr(elexon_client, "fetch_actual_wind_records", lambda a, b: [])
    monkeypatch.setattr(elexon_client, "fetch_forecast_records", lambda a, b: [])
    monkeypatch.setattr("app.api.routes.build_hourly_table", explode)

    response = client.get("/api/overview", headers={"Origin": "http://localhost:5173"})

    assert response.status_code == 500
    assert "Unexpected error" in response.json()["detail"]
    # Without these headers the browser would hide the message and show "cannot reach backend".
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_elexon_error_response_has_cors_headers(monkeypatch):
    def failing(publish_from, publish_to):
        raise elexon_client.ElexonAPIError("boom")

    monkeypatch.setattr(elexon_client, "fetch_actual_wind_records", failing)
    monkeypatch.setattr(elexon_client, "fetch_forecast_records", lambda a, b: [])

    response = client.get("/api/overview", headers={"Origin": "http://localhost:5173"})

    assert response.status_code == 502
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"