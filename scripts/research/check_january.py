
import requests
from collections import defaultdict
from datetime import datetime, timedelta, timezone, time
from math import sqrt

ACTUALS_URL = (
    "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream"
)
FORECASTS_URL = (
    "https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream"
)

START = datetime(2026, 1, 1, tzinfo=timezone.utc)
END = datetime(2026, 2, 1, tzinfo=timezone.utc)

CUTOFF_HOUR = 9
CUTOFF_MINUTE = 50


def parse_time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def fetch_data(url, params):
    response = requests.get(url, params=params, timeout=120)
    print("Fetched:", url.split("/")[-2])
    print("Status code:", response.status_code)
    response.raise_for_status()

    data = response.json()

    if not isinstance(data, list):
        raise ValueError("Unexpected API response format")

    print("Records received:", len(data))
    return data


def main():
    actual_params = {
        "publishDateTimeFrom": "2026-01-01T00:00:00Z",
        "publishDateTimeTo": "2026-02-01T01:00:00Z",
    }

    forecast_params = {
        "publishDateTimeFrom": "2025-12-31T00:00:00Z",
        "publishDateTimeTo": "2026-01-31T00:00:00Z",
    }

    actual_data = fetch_data(ACTUALS_URL, actual_params)
    forecast_data = fetch_data(FORECASTS_URL, forecast_params)

    print("\nProcessing actual generation...")

    actual_by_period = {}

    for record in actual_data:
        if record.get("fuelType") != "WIND":
            continue

        if record.get("generation") is None:
            continue

        if not record.get("startTime") or not record.get("publishTime"):
            continue

        delivery_time = parse_time(record["startTime"])

        if not START <= delivery_time < END:
            continue

        existing = actual_by_period.get(delivery_time)

        if (
            existing is None
            or parse_time(record["publishTime"])
            > parse_time(existing["publishTime"])
        ):
            actual_by_period[delivery_time] = record

    actuals_by_hour = defaultdict(list)

    for delivery_time, record in actual_by_period.items():
        hour = delivery_time.replace(
            minute=0, second=0, microsecond=0
        )

        actuals_by_hour[hour].append(
            float(record["generation"])
        )

    print("Unique half-hourly actual periods:", len(actual_by_period))
    print("Hourly groups with actual data:", len(actuals_by_hour))

    print("\nSelecting day-ahead forecasts...")

    forecasts_by_hour = {}

    for record in forecast_data:
        if record.get("generation") is None:
            continue

        if not record.get("startTime") or not record.get("publishTime"):
            continue

        delivery_time = parse_time(record["startTime"])
        publish_time = parse_time(record["publishTime"])

        if not START <= delivery_time < END:
            continue

        cutoff_date = delivery_time.date() - timedelta(days=1)

        cutoff = datetime.combine(
            cutoff_date,
            time(CUTOFF_HOUR, CUTOFF_MINUTE),
            tzinfo=timezone.utc,
        )

        if publish_time > cutoff:
            continue

        hour = delivery_time.replace(
            minute=0, second=0, microsecond=0
        )

        existing = forecasts_by_hour.get(hour)

        if (
            existing is None
            or publish_time > existing["publish_time"]
        ):
            forecasts_by_hour[hour] = {
                "generation": float(record["generation"]),
                "publish_time": publish_time,
            }

    print("Eligible hourly forecasts:", len(forecasts_by_hour))

    matched = []

    for hour in sorted(forecasts_by_hour):
        values = actuals_by_hour.get(hour, [])

        if len(values) != 2:
            continue

        forecast = forecasts_by_hour[hour]["generation"]
        actual = sum(values) / 2

        matched.append({
            "hour": hour,
            "publish_time": forecasts_by_hour[hour]["publish_time"],
            "forecast": forecast,
            "actual": actual,
            "error": forecast - actual,
        })

    expected_hours = 31 * 24

    print("\nData coverage")
    print("Expected hourly periods:", expected_hours)
    print("Matched hourly periods:", len(matched))
    print(
        f"Coverage: {len(matched) / expected_hours * 100:.2f}%"
    )

    if not matched:
        print("No matching data. Check the API responses.")
        return

    errors = [row["error"] for row in matched]

    mae = sum(abs(error) for error in errors) / len(errors)

    rmse = sqrt(
        sum(error ** 2 for error in errors) / len(errors)
    )

    bias = sum(errors) / len(errors)

    percentage_errors = [
        abs(row["error"]) / abs(row["actual"]) * 100
        for row in matched
        if row["actual"] != 0
    ]

    print("\nJanuary 2026 accuracy metrics")
    print(f"MAE: {mae:.2f} MW")
    print(f"RMSE: {rmse:.2f} MW")
    print(f"Mean bias error: {bias:.2f} MW")

    if percentage_errors:
        mape = sum(percentage_errors) / len(percentage_errors)
        print(f"MAPE: {mape:.2f}%")
        print("Periods included in MAPE:", len(percentage_errors))
    else:
        print("MAPE unavailable: no non-zero actual values")

    over = sum(error > 0 for error in errors)
    under = sum(error < 0 for error in errors)
    exact = sum(error == 0 for error in errors)

    print("\nForecast error direction")
    print("Overforecast periods:", over)
    print("Underforecast periods:", under)
    print("Exact matches:", exact)

    daily_errors = defaultdict(list)

    for row in matched:
        daily_errors[row["hour"].date()].append(row["error"])

    print("\nDaily mean absolute error")

    for day in sorted(daily_errors):
        daily_mae = sum(
            abs(error) for error in daily_errors[day]
        ) / len(daily_errors[day])

        print(f"{day}: {daily_mae:.2f} MW")

    print("\nFirst 5 matched periods")

    for row in matched[:5]:
        print(
            f"{row['hour'].isoformat()} | "
            f"Published: {row['publish_time'].isoformat()} | "
            f"Forecast: {row['forecast']:.1f} MW | "
            f"Actual: {row['actual']:.1f} MW | "
            f"Error: {row['error']:+.1f} MW"
        )


if __name__ == "__main__":
    try:
        main()
    except (requests.RequestException, ValueError, KeyError) as error:
        print("Error:", error)
