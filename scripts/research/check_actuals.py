
import requests
from datetime import datetime

url = "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream"

params = {
    "publishDateTimeFrom": "2026-01-01T00:00:00Z",
    "publishDateTimeTo": "2026-01-02T00:00:00Z",
}

try:
    response = requests.get(url, params=params, timeout=30)
    print("Status code:", response.status_code)
    response.raise_for_status()

    data = response.json()

    start = datetime.fromisoformat("2026-01-01T00:00:00+00:00")
    end = datetime.fromisoformat("2026-01-02T00:00:00+00:00")

    wind_records = []

    for record in data:
        if record.get("fuelType") != "WIND":
            continue

        start_time = datetime.fromisoformat(
            record["startTime"].replace("Z", "+00:00")
        )

        if start <= start_time < end:
            wind_records.append(record)

    wind_records.sort(key=lambda record: record["startTime"])

    print("Total API records:", len(data))
    print("Wind records for January 1:", len(wind_records))

    if wind_records:
        print("First delivery period:", wind_records[0]["startTime"])
        print("Last delivery period:", wind_records[-1]["startTime"])
        print("\nFirst 3 filtered records:")

        for record in wind_records[:3]:
            print(record)

except (requests.RequestException, ValueError, KeyError) as error:
    print("Error:", error)
