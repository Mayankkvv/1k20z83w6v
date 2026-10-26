
import requests
from datetime import datetime, timezone
from collections import defaultdict
from math import sqrt

actuals_url = "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream"
forecasts_url = "https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream"

actual_params = {
    "publishDateTimeFrom": "2026-01-01T00:00:00Z",
    "publishDateTimeTo": "2026-01-02T00:00:00Z",
}

forecast_params = {
    "publishDateTimeFrom": "2025-12-31T00:00:00Z",
    "publishDateTimeTo": "2026-01-01T00:00:00Z",
}

start = datetime(2026, 1, 1, tzinfo=timezone.utc)
end = datetime(2026, 1, 2, tzinfo=timezone.utc)

cutoff = datetime(
    2025, 12, 31, 9, 50, tzinfo=timezone.utc
)


def parse_time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


try:
    actual_response = requests.get(
        actuals_url, params=actual_params, timeout=60
    )
    actual_response.raise_for_status()
    actual_data = actual_response.json()

    forecast_response = requests.get(
        forecasts_url, params=forecast_params, timeout=60
    )
    forecast_response.raise_for_status()
    forecast_data = forecast_response.json()

    if not isinstance(actual_data, list):
        raise ValueError("Unexpected actuals response format")

    if not isinstance(forecast_data, list):
        raise ValueError("Unexpected forecasts response format")

    actuals_by_hour = defaultdict(list)

    for record in actual_data:
        if record.get("fuelType") != "WIND":
            continue

        if record.get("generation") is None:
            continue

        delivery_time = parse_time(record["startTime"])

        if not start <= delivery_time < end:
            continue

        hour = delivery_time.replace(
            minute=0, second=0, microsecond=0
        )

        actuals_by_hour[hour].append(float(record["generation"]))

    forecasts_by_hour = {}

    for record in forecast_data:
        if record.get("generation") is None:
            continue

        delivery_time = parse_time(record["startTime"])
        publish_time = parse_time(record["publishTime"])

        if not start <= delivery_time < end:
            continue

        if publish_time > cutoff:
            continue

        hour = delivery_time.replace(
            minute=0, second=0, microsecond=0
        )

        previous = forecasts_by_hour.get(hour)

        if previous is None or publish_time > previous["publish_time"]:
            forecasts_by_hour[hour] = {
                "generation": float(record["generation"]),
                "publish_time": publish_time,
            }

    matched = []

    for hour in sorted(forecasts_by_hour):
        actual_values = actuals_by_hour.get(hour, [])

        if len(actual_values) != 2:
            continue

        forecast = forecasts_by_hour[hour]["generation"]
        actual = sum(actual_values) / 2
        error = forecast - actual

        matched.append({
            "hour": hour,
            "publish_time": forecasts_by_hour[hour]["publish_time"],
            "forecast": forecast,
            "actual": actual,
            "error": error,
        })

    print("Actual hourly periods:", len(actuals_by_hour))
    print("Eligible hourly forecasts:", len(forecasts_by_hour))
    print("Matched complete hours:", len(matched))
    print("Selected publication times:", sorted({
        row["publish_time"].isoformat() for row in matched
    }))

    if not matched:
        print("No complete matching forecast and actual periods found.")
        raise SystemExit

    errors = [row["error"] for row in matched]
    over = sum(error > 0 for error in errors)
    under = sum(error < 0 for error in errors)
    exact = sum(error == 0 for error in errors)

    forecasts = [row["forecast"] for row in matched]
    actuals = [row["actual"] for row in matched]

    print("\nData sanity check")
    print(f"Overforecast periods: {over}")
    print(f"Underforecast periods: {under}")
    print(f"Exact matches: {exact}")

    print(
        f"Forecast range: {min(forecasts):.1f} to "
        f"{max(forecasts):.1f} MW"
    )
    print(
        f"Actual range: {min(actuals):.1f} to "
        f"{max(actuals):.1f} MW"
    )
    print(
        f"Error range: {min(errors):+.1f} to "
        f"{max(errors):+.1f} MW"
    )
    actual_values = [row["actual"] for row in matched]

    mae = sum(abs(error) for error in errors) / len(errors)
    rmse = sqrt(sum(error ** 2 for error in errors) / len(errors))
    bias = sum(errors) / len(errors)

    percentage_errors = [
        abs(row["error"]) / abs(row["actual"]) * 100
        for row in matched
        if row["actual"] != 0
    ]

    print("\nAccuracy metrics")
    print(f"MAE: {mae:.2f} MW")
    print(f"RMSE: {rmse:.2f} MW")
    print(f"Mean bias error: {bias:.2f} MW")

    if percentage_errors:
        mape = sum(percentage_errors) / len(percentage_errors)
        print(f"MAPE: {mape:.2f}%")
    else:
        print("MAPE: unavailable because actual generation is zero")

    print("\nFirst 5 matched hours")

    for row in matched[:5]:
        print(
            f"{row['hour'].isoformat()} | "
            f"Published: {row['publish_time'].isoformat()} | "
            f"Forecast: {row['forecast']:.1f} MW | "
            f"Actual: {row['actual']:.1f} MW | "
            f"Error: {row['error']:+.1f} MW"
        )

except (requests.RequestException, ValueError, KeyError) as error:
    print("Error:", error)
