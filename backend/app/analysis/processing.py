from datetime import date, datetime, time, timedelta, timezone

from app import config

UTC = timezone.utc


def parse_utc(text: str) -> datetime:
    """Turn an Elexon timestamp such as 2026-01-01T00:30:00Z into a UTC datetime."""
    parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"Timestamp has no timezone: {text}")
    return parsed.astimezone(UTC)


def format_utc(value: datetime) -> str:
    """Format a datetime as an Elexon-style UTC string."""
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def decision_cutoff(
    delivery_day: date,
    cutoff_time: time = config.DEFAULT_CUTOFF_TIME,
    days_before: int = config.CUTOFF_DAYS_BEFORE_DELIVERY,
) -> datetime:
    """The moment the day-ahead decision for a delivery day is made.

    Example: delivery day 2026-01-01 gives 2025-12-31 09:50 UTC.
    In January UK time equals UTC, so no daylight-saving conversion is needed.
    """
    cutoff_date = delivery_day - timedelta(days=days_before)
    return datetime.combine(cutoff_date, cutoff_time, tzinfo=UTC)


def build_hourly_actuals(actual_records: list) -> dict:
    """Turn half-hourly actual records into hourly values.

    Returns {hour_start: {"actual_mw": float or None, "complete": bool}}.
    - Duplicate records for the same half-hour: the latest publishTime wins.
    - An hour is complete only when both :00 and :30 exist. Then its value is
      the mean of the two. Incomplete hours get actual_mw None (never guessed).
    """
    latest = {}
    for record in actual_records:
        generation = record.get("generation")
        if generation is None:
            continue
        start = parse_utc(record["startTime"])
        publish_text = record.get("publishTime")
        publish = parse_utc(publish_text) if publish_text else datetime.min.replace(tzinfo=UTC)
        existing = latest.get(start)
        if existing is None or publish > existing[0]:
            latest[start] = (publish, float(generation))

    halves_by_hour = {}
    for start, (_, generation) in latest.items():
        hour = start.replace(minute=0, second=0, microsecond=0)
        halves_by_hour.setdefault(hour, {})[start.minute] = generation

    hourly = {}
    for hour, halves in halves_by_hour.items():
        if 0 in halves and 30 in halves:
            hourly[hour] = {"actual_mw": (halves[0] + halves[30]) / 2, "complete": True}
        else:
            hourly[hour] = {"actual_mw": None, "complete": False}
    return hourly


def select_eligible_forecasts(
    forecast_records: list,
    cutoff_time: time = config.DEFAULT_CUTOFF_TIME,
) -> dict:
    """For every delivery hour, pick the latest forecast published at or before the cutoff.

    Returns {delivery_hour: {"forecast_mw": float, "publish_time": datetime}}.
    Forecasts published after the cutoff are ignored. If nothing is eligible,
    the delivery hour is simply absent (missing, never filled from a later forecast).
    """
    selected = {}
    for record in forecast_records:
        generation = record.get("generation")
        if generation is None:
            continue
        delivery = parse_utc(record["startTime"])
        publish = parse_utc(record["publishTime"])
        cutoff = decision_cutoff(delivery.date(), cutoff_time)
        if publish > cutoff:
            continue
        current = selected.get(delivery)
        if current is None or publish > current["publish_time"]:
            selected[delivery] = {"forecast_mw": float(generation), "publish_time": publish}
    return selected


def _status(actual, forecast) -> str:
    actual_ok = actual is not None and actual["actual_mw"] is not None
    forecast_ok = forecast is not None
    if actual_ok and forecast_ok:
        return "ok"
    if not forecast_ok and not actual_ok:
        return "missing_forecast_and_actual"
    if not forecast_ok:
        return "missing_forecast"
    if actual is not None:
        return "incomplete_actual"
    return "missing_actual"


def build_hourly_table(
    actual_records: list,
    forecast_records: list,
    start: datetime = config.ANALYSIS_START,
    end: datetime = config.ANALYSIS_END,
    cutoff_time: time = config.DEFAULT_CUTOFF_TIME,
) -> list:
    """One row for every delivery hour from start (included) to end (excluded).

    Forecast error = forecast - actual (positive means overforecast).
    Hours with missing data stay in the table with a status and None values.
    """
    if start.tzinfo is None or end.tzinfo is None:
        raise ValueError("start and end must be timezone-aware datetimes.")

    actuals = build_hourly_actuals(actual_records)
    forecasts = select_eligible_forecasts(forecast_records, cutoff_time)

    rows = []
    hour = start.astimezone(UTC)
    last = end.astimezone(UTC)
    while hour < last:
        actual = actuals.get(hour)
        forecast = forecasts.get(hour)
        actual_mw = actual["actual_mw"] if actual else None
        forecast_mw = forecast["forecast_mw"] if forecast else None
        error_mw = None
        if actual_mw is not None and forecast_mw is not None:
            error_mw = forecast_mw - actual_mw
        rows.append(
            {
                "delivery_time": format_utc(hour),
                "date": hour.date().isoformat(),
                "hour": hour.hour,
                "forecast_mw": forecast_mw,
                "forecast_publish_time": format_utc(forecast["publish_time"]) if forecast else None,
                "actual_mw": actual_mw,
                "error_mw": error_mw,
                "status": _status(actual, forecast),
            }
        )
        hour += timedelta(hours=1)
    return rows