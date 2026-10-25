import math

import pytest

from app.analysis import metrics


def row(date, forecast, actual_value):
    error = None if forecast is None or actual_value is None else forecast - actual_value
    return {
        "date": date,
        "forecast_mw": forecast,
        "actual_mw": actual_value,
        "error_mw": error,
        "status": "ok" if error is not None else "missing_forecast",
    }


# Hand-calculated example:
# forecast: 110, 90, 100, 130   actual: 100, 100, 100, 100
# errors:   +10, -10, 0, +30
# MAE  = (10 + 10 + 0 + 30) / 4          = 12.5
# RMSE = sqrt((100 + 100 + 0 + 900) / 4) = sqrt(275) = 16.5831...
# bias = (10 - 10 + 0 + 30) / 4          = 7.5
# MAPE = (10% + 10% + 0% + 30%) / 4      = 12.5%
EXAMPLE = [
    row("2026-01-01", 110, 100),
    row("2026-01-01", 90, 100),
    row("2026-01-01", 100, 100),
    row("2026-01-01", 130, 100),
]


def test_metrics_match_hand_calculation():
    result = metrics.compute_metrics(EXAMPLE)
    assert result["matched_periods"] == 4
    assert result["mae_mw"] == pytest.approx(12.5)
    assert result["rmse_mw"] == pytest.approx(round(math.sqrt(275), 2))
    assert result["mean_bias_mw"] == pytest.approx(7.5)
    assert result["mape_pct"] == pytest.approx(12.5)
    assert result["overforecast_periods"] == 2
    assert result["underforecast_periods"] == 1
    assert result["exact_matches"] == 1


def test_positive_bias_means_overforecast():
    rows = [row("2026-01-01", 150, 100), row("2026-01-01", 120, 100)]
    assert metrics.compute_metrics(rows)["mean_bias_mw"] > 0


def test_negative_bias_means_underforecast():
    rows = [row("2026-01-01", 50, 100), row("2026-01-01", 80, 100)]
    assert metrics.compute_metrics(rows)["mean_bias_mw"] < 0


def test_rows_with_missing_data_are_not_matched():
    rows = EXAMPLE + [row("2026-01-01", None, 100), row("2026-01-01", 100, None)]
    result = metrics.compute_metrics(rows)
    assert result["total_periods"] == 6
    assert result["matched_periods"] == 4
    assert result["coverage_pct"] == pytest.approx(66.67)
    assert result["mae_mw"] == pytest.approx(12.5)


def test_zero_actual_is_left_out_of_mape_only():
    rows = [row("2026-01-01", 5, 0), row("2026-01-01", 110, 100)]
    result = metrics.compute_metrics(rows)
    assert result["mae_mw"] == pytest.approx(7.5)
    assert result["mape_pct"] == pytest.approx(10.0)
    assert result["mape_periods"] == 1


def test_no_matched_rows_gives_none_not_an_error():
    result = metrics.compute_metrics([row("2026-01-01", None, None)])
    assert result["matched_periods"] == 0
    assert result["mae_mw"] is None
    assert result["rmse_mw"] is None
    assert result["mape_pct"] is None


def test_empty_input_does_not_divide_by_zero():
    result = metrics.compute_metrics([])
    assert result["total_periods"] == 0
    assert result["coverage_pct"] is None
    assert result["mae_mw"] is None


def test_daily_summaries_group_by_date():
    rows = EXAMPLE + [row("2026-01-02", 120, 100), row("2026-01-02", 80, 100)]
    days = metrics.daily_summaries(rows)
    assert [d["date"] for d in days] == ["2026-01-01", "2026-01-02"]
    assert days[0]["mae_mw"] == pytest.approx(12.5)
    assert days[1]["mae_mw"] == pytest.approx(20.0)
    assert days[1]["mean_bias_mw"] == pytest.approx(0.0)