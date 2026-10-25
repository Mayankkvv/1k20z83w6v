import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import data_cache, elexon_client
from app.services.elexon_client import ElexonAPIError

client = TestClient(app)


def make_fake_records():
    """January 1 only. Actual hour = mean(100, 200) = 150. Eligible forecast = 160 (error +10).

    A later forecast (999, published after the cutoff) must be ignored.
    """
    actuals = []
    forecasts = []
    for hour in range(24):
        for minute, value in ((0, 100), (30, 200)):
            start = f"2026-01-01T{hour:02d}:{minute:02d}:00Z"
            actuals.append(
                {"startTime": start, "publishTime": start, "fuelType": "WIND", "generation": value}
            )
        delivery = f"2026-01-01T{hour:02d}:00:00Z"
        forecasts.append(
            {"startTime": delivery, "publishTime": "2025-12-31T09:30:00Z", "generation": 160}
        )
        forecasts.append(
            {"startTime": delivery, "publishTime": "2025-12-31T11:30:00Z", "generation": 999}
        )
    return actuals, forecasts


def install_fake_elexon(monkeypatch, actuals, forecasts):
    calls = {"actuals": 0, "forecasts": 0}

    def fake_actuals(publish_from, publish_to):
        calls["actuals"] += 1
        return actuals

    def fake_forecasts(publish_from, publish_to):
        calls["forecasts"] += 1
        return forecasts

    monkeypatch.setattr(elexon_client, "fetch_actual_wind_records", fake_actuals)
    monkeypatch.setattr(elexon_client, "fetch_forecast_records", fake_forecasts)
    return calls


@pytest.fixture(autouse=True)
def fresh_cache():
    data_cache.clear_cache()
    yield
    data_cache.clear_cache()


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_overview_returns_metrics_and_assumption(monkeypatch):
    install_fake_elexon(monkeypatch, *make_fake_records())

    body = client.get("/api/overview").json()

    assert body["period"] == {"start": "2026-01-01", "end": "2026-01-31"}
    assert body["assumption"]["cutoff_time_utc"] == "09:50"
    assert "09:50" in body["assumption"]["summary"]
    metrics = body["metrics"]
    assert metrics["total_periods"] == 744
    assert metrics["matched_periods"] == 24
    assert metrics["coverage_pct"] == pytest.approx(3.23)
    assert metrics["mae_mw"] == pytest.approx(10.0)
    assert metrics["mean_bias_mw"] == pytest.approx(10.0)


def test_day_returns_hourly_rows_and_ignores_late_forecast(monkeypatch):
    install_fake_elexon(monkeypatch, *make_fake_records())

    body = client.get("/api/day", params={"date": "2026-01-01"}).json()

    assert body["date"] == "2026-01-01"
    assert body["cutoff_utc"] == "2025-12-31T09:50:00Z"
    assert len(body["rows"]) == 24
    first = body["rows"][0]
    assert first["delivery_time"] == "2026-01-01T00:00:00Z"
    assert first["forecast_mw"] == 160
    assert first["actual_mw"] == 150
    assert first["error_mw"] == 10
    assert first["forecast_publish_time"] == "2025-12-31T09:30:00Z"
    assert first["status"] == "ok"
    assert all(row["forecast_mw"] == 160 for row in body["rows"])
    assert body["metrics"]["mae_mw"] == pytest.approx(10.0)
    assert body["metrics"]["rmse_mw"] == pytest.approx(10.0)
    assert body["metrics"]["mape_pct"] == pytest.approx(6.67)


def test_day_without_data_returns_missing_rows_not_an_error(monkeypatch):
    install_fake_elexon(monkeypatch, *make_fake_records())

    response = client.get("/api/day", params={"date": "2026-01-02"})

    assert response.status_code == 200
    body = response.json()
    assert len(body["rows"]) == 24
    assert all(row["status"] == "missing_forecast_and_actual" for row in body["rows"])
    assert body["metrics"]["matched_periods"] == 0
    assert body["metrics"]["mae_mw"] is None


def test_day_outside_january_2026_is_rejected():
    assert client.get("/api/day", params={"date": "2025-12-31"}).status_code == 400
    assert client.get("/api/day", params={"date": "2026-02-01"}).status_code == 400


def test_day_with_invalid_date_format_is_rejected():
    assert client.get("/api/day", params={"date": "not-a-date"}).status_code == 422
    assert client.get("/api/day").status_code == 422


def test_accuracy_returns_monthly_and_daily_metrics(monkeypatch):
    install_fake_elexon(monkeypatch, *make_fake_records())

    body = client.get("/api/accuracy").json()

    assert body["metrics"]["matched_periods"] == 24
    assert len(body["daily"]) == 31
    assert body["daily"][0]["date"] == "2026-01-01"
    assert body["daily"][0]["mae_mw"] == pytest.approx(10.0)
    assert body["daily"][1]["matched_periods"] == 0
    assert body["daily"][1]["mae_mw"] is None


def test_elexon_failure_returns_502_with_message(monkeypatch):
    def failing(publish_from, publish_to):
        raise ElexonAPIError("boom")

    monkeypatch.setattr(elexon_client, "fetch_actual_wind_records", failing)
    monkeypatch.setattr(elexon_client, "fetch_forecast_records", lambda a, b: [])

    response = client.get("/api/overview")

    assert response.status_code == 502
    assert "boom" in response.json()["detail"]


def test_failed_fetch_is_not_cached(monkeypatch):
    def failing(publish_from, publish_to):
        raise ElexonAPIError("boom")

    monkeypatch.setattr(elexon_client, "fetch_actual_wind_records", failing)
    monkeypatch.setattr(elexon_client, "fetch_forecast_records", lambda a, b: [])
    assert client.get("/api/overview").status_code == 502

    install_fake_elexon(monkeypatch, *make_fake_records())
    assert client.get("/api/overview").status_code == 200


def test_elexon_is_fetched_once_and_then_cached(monkeypatch):
    calls = install_fake_elexon(monkeypatch, *make_fake_records())

    client.get("/api/overview")
    client.get("/api/accuracy")
    client.get("/api/day", params={"date": "2026-01-01"})

    assert calls == {"actuals": 1, "forecasts": 1}