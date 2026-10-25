import math
from collections import Counter

from app import config


def _round(value, digits: int = 2):
    return None if value is None else round(value, digits)


def compute_metrics(rows: list, mape_min_actual_mw: float = config.MAPE_MIN_ACTUAL_MW) -> dict:
    """Accuracy metrics for rows produced by build_hourly_table.

    Only rows with both a forecast and a complete actual (error_mw is not None)
    are matched. Error = forecast - actual, so a positive error is overforecasting.
    """
    total = len(rows)
    matched = [row for row in rows if row["error_mw"] is not None]
    count = len(matched)

    result = {
        "total_periods": total,
        "matched_periods": count,
        "coverage_pct": _round(100 * count / total) if total else None,
        "status_counts": dict(Counter(row["status"] for row in rows)),
        "mae_mw": None,
        "rmse_mw": None,
        "mean_bias_mw": None,
        "mape_pct": None,
        "mape_periods": 0,
        "overforecast_periods": 0,
        "underforecast_periods": 0,
        "exact_matches": 0,
    }
    if count == 0:
        return result

    errors = [row["error_mw"] for row in matched]
    result["mae_mw"] = _round(sum(abs(e) for e in errors) / count)
    result["rmse_mw"] = _round(math.sqrt(sum(e * e for e in errors) / count))
    result["mean_bias_mw"] = _round(sum(errors) / count)
    result["overforecast_periods"] = sum(1 for e in errors if e > 0)
    result["underforecast_periods"] = sum(1 for e in errors if e < 0)
    result["exact_matches"] = sum(1 for e in errors if e == 0)

    # MAPE divides by the actual value, so near-zero actuals are left out.
    mape_rows = [row for row in matched if row["actual_mw"] >= mape_min_actual_mw]
    if mape_rows:
        pct_errors = [abs(row["error_mw"]) / row["actual_mw"] * 100 for row in mape_rows]
        result["mape_pct"] = _round(sum(pct_errors) / len(pct_errors))
        result["mape_periods"] = len(mape_rows)
    return result


def daily_summaries(rows: list) -> list:
    """Metrics for each delivery date, in date order."""
    by_date = {}
    for row in rows:
        by_date.setdefault(row["date"], []).append(row)
    return [{"date": day, **compute_metrics(day_rows)} for day, day_rows in sorted(by_date.items())]