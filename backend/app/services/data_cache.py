import threading
import time

from app import config
from app.services import elexon_client

CACHE_TTL_SECONDS = 3600  # keep Elexon data for one hour before fetching again

_lock = threading.Lock()
_cache = {"loaded_at": None, "actuals": None, "forecasts": None}


def clear_cache() -> None:
    """Forget the stored Elexon data (used by tests)."""
    with _lock:
        _cache.update(loaded_at=None, actuals=None, forecasts=None)


def get_raw_records():
    """Return (actual_records, forecast_records) for the analysis period.

    Elexon is called only when nothing is stored yet or the stored data is older
    than CACHE_TTL_SECONDS. If a fetch fails, nothing is stored, so the next
    request tries again. The lock makes simultaneous requests wait for one fetch.
    """
    with _lock:
        loaded_at = _cache["loaded_at"]
        if loaded_at is not None and time.monotonic() - loaded_at < CACHE_TTL_SECONDS:
            return _cache["actuals"], _cache["forecasts"]

        actuals = elexon_client.fetch_actual_wind_records(
            config.ACTUALS_PUBLISH_FROM, config.ACTUALS_PUBLISH_TO
        )
        forecasts = elexon_client.fetch_forecast_records(
            config.FORECAST_PUBLISH_FROM, config.FORECAST_PUBLISH_TO
        )
        _cache.update(loaded_at=time.monotonic(), actuals=actuals, forecasts=forecasts)
        return actuals, forecasts