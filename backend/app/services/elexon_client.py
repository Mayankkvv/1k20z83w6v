import logging
import time
from datetime import datetime, timedelta, timezone

import requests

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
REQUEST_TIMEOUT_SECONDS = 60
MAX_ATTEMPTS = 3
RETRY_WAIT_SECONDS = 2
DEFAULT_CHUNK_DAYS = 7

logger = logging.getLogger(__name__)


class ElexonAPIError(Exception):
    """Raised when data cannot be retrieved from the Elexon API."""


def _to_utc_string(value: datetime) -> str:
    """Format a timezone-aware datetime as an Elexon-style UTC string."""
    if value.tzinfo is None:
        raise ValueError("Datetimes must be timezone-aware (for example tzinfo=timezone.utc).")
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _get_json(url: str, params: dict):
    """GET a URL and return parsed JSON, retrying on temporary failures."""
    last_error = "unknown error"

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        except requests.RequestException as exc:
            last_error = f"network error: {exc}"
        else:
            status = response.status_code
            if status == 200:
                try:
                    return response.json()
                except ValueError as exc:
                    raise ElexonAPIError("Elexon returned a response that is not valid JSON.") from exc
            if status < 500 and status != 429:
                raise ElexonAPIError(
                    f"Elexon rejected the request (HTTP {status}): {response.text[:200]}"
                )
            last_error = f"temporary server problem (HTTP {status})"

        logger.warning("Elexon request attempt %s/%s failed: %s", attempt, MAX_ATTEMPTS, last_error)
        if attempt < MAX_ATTEMPTS:
            time.sleep(RETRY_WAIT_SECONDS)

    raise ElexonAPIError(f"Elexon request failed after {MAX_ATTEMPTS} attempts: {last_error}")


def _extract_records(payload) -> list:
    """The stream endpoints return a JSON list; also accept {"data": [...]}."""
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("data"), list):
        return payload["data"]
    raise ElexonAPIError("Elexon returned data in an unexpected format.")


def fetch_dataset(
    dataset: str,
    publish_from: datetime,
    publish_to: datetime,
    chunk_days: int = DEFAULT_CHUNK_DAYS,
) -> list:
    """Fetch all raw records of a dataset published between two times.

    The range is split into windows of chunk_days to keep each request small.
    Records exactly on a window boundary could appear twice; the analysis
    step is responsible for removing duplicates.
    """
    start = publish_from.astimezone(timezone.utc)
    end = publish_to.astimezone(timezone.utc)
    if start >= end:
        raise ValueError("publish_from must be earlier than publish_to.")

    url = f"{BASE_URL}/{dataset}/stream"
    records = []
    window_start = start

    while window_start < end:
        window_end = min(window_start + timedelta(days=chunk_days), end)
        params = {
            "publishDateTimeFrom": _to_utc_string(window_start),
            "publishDateTimeTo": _to_utc_string(window_end),
        }
        payload = _get_json(url, params)
        records.extend(_extract_records(payload))
        window_start = window_end

    return records


def fetch_actual_wind_records(publish_from: datetime, publish_to: datetime) -> list:
    """Actual generation (FUELHH), keeping only fuelType == WIND."""
    records = fetch_dataset("FUELHH", publish_from, publish_to)
    return [record for record in records if record.get("fuelType") == "WIND"]


def fetch_forecast_records(publish_from: datetime, publish_to: datetime) -> list:
    """Wind generation forecasts (WINDFOR), all published versions."""
    return fetch_dataset("WINDFOR", publish_from, publish_to)