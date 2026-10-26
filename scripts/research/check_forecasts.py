
import requests
from collections import defaultdict
from datetime import datetime, timezone

url = "https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream"

params = {
    "publishDateTimeFrom": "2025-12-31T00:00:00Z",
    "publishDateTimeTo": "2026-01-01T00:00:00Z",
}

try:
    response = requests.get(url, params=params, timeout=60)
    print("Status code:", response.status_code)
    response.raise_for_status()

    data = response.json()

    if not isinstance(data, list):
        print("Unexpected response:", data)
        raise SystemExit

    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end = datetime(2026, 1, 2, tzinfo=timezone.utc)

    forecasts = []

    for record in data:
        if not record.get("startTime") or not record.get("publishTime"):
            continue

        delivery_time = datetime.fromisoformat(
            record["startTime"].replace("Z", "+00:00")
        )

        if start <= delivery_time < end:
            forecasts.append(record)

    grouped = defaultdict(list)

    for record in forecasts:
        grouped[record["publishTime"]].append(record)

    print("Forecast publication versions:", len(grouped))

    for publish_time in sorted(grouped):
        records = grouped[publish_time]

        times = sorted({
            datetime.fromisoformat(
                record["startTime"].replace("Z", "+00:00")
            )
            for record in records
        })

        intervals = sorted({
            int((times[i] - times[i - 1]).total_seconds() / 60)
            for i in range(1, len(times))
        })

        print("\nPublication time:", publish_time)
        print("Record count:", len(records))
        print("Unique delivery periods:", len(times))
        print("First delivery period:", times[0].isoformat())
        print("Last delivery period:", times[-1].isoformat())
        print("Intervals between periods (minutes):", intervals)

except (requests.RequestException, ValueError, KeyError) as error:
    print("Error:", error)
