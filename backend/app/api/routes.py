import logging
from datetime import date, timedelta

from fastapi import APIRouter, HTTPException, Query

from app import config
from app.analysis.metrics import compute_metrics, daily_summaries
from app.analysis.processing import build_hourly_table, decision_cutoff, format_utc
from app.services import data_cache
from app.services.elexon_client import ElexonAPIError

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)

FIRST_DAY = config.ANALYSIS_START.date()
LAST_DAY = (config.ANALYSIS_END - timedelta(days=1)).date()


def _load_rows() -> list:
    """Hourly forecast-versus-actual rows for the whole analysis period.

    Elexon problems are re-raised so main.py answers with HTTP 502. Any other unexpected
    problem becomes a clear HTTP 500 message. The message is raised as an HTTPException
    so that the response still carries the CORS headers and the browser can read it.
    """
    try:
        actuals, forecasts = data_cache.get_raw_records()
        return build_hourly_table(actuals, forecasts)
    except ElexonAPIError:
        raise
    except Exception as exc:
        logger.exception("Unexpected error while processing Elexon data")
        raise HTTPException(
            status_code=500,
            detail="Unexpected error while processing the data. See the backend log for details.",
        ) from exc


def _assumption() -> dict:
    cutoff = config.DEFAULT_CUTOFF_TIME.strftime("%H:%M")
    return {
        "cutoff_time_utc": cutoff,
        "days_before_delivery": config.CUTOFF_DAYS_BEFORE_DELIVERY,
        "summary": (
            f"For each delivery hour, the forecast used is the latest one published at or before "
            f"{cutoff} UTC on the day before delivery. Forecasts published later are not used."
        ),
        "note": (
            "This cutoff is an assumption. 09:50 UK time is when the N2EX day-ahead auction closes; "
            "the EPEX day-ahead auction closes earlier, at 09:20. In January UK time equals UTC."
        ),
        "mape_min_actual_mw": config.MAPE_MIN_ACTUAL_MW,
    }


@router.get("/overview")
def overview():
    """Monthly summary: accuracy metrics, data coverage and the cutoff assumption."""
    rows = _load_rows()
    return {
        "period": {"start": FIRST_DAY.isoformat(), "end": LAST_DAY.isoformat()},
        "assumption": _assumption(),
        "metrics": compute_metrics(rows),
    }


@router.get("/day")
def day(delivery_date: date = Query(..., alias="date", description="Delivery date, e.g. 2026-01-01")):
    """Hourly forecast versus actual for one delivery date, with that day's metrics."""
    if not FIRST_DAY <= delivery_date <= LAST_DAY:
        raise HTTPException(
            status_code=400,
            detail=f"Date must be between {FIRST_DAY.isoformat()} and {LAST_DAY.isoformat()}.",
        )
    rows = [row for row in _load_rows() if row["date"] == delivery_date.isoformat()]
    return {
        "date": delivery_date.isoformat(),
        "cutoff_utc": format_utc(decision_cutoff(delivery_date)),
        "metrics": compute_metrics(rows),
        "rows": rows,
    }


@router.get("/accuracy")
def accuracy():
    """Monthly metrics plus metrics for every delivery date."""
    rows = _load_rows()
    return {"metrics": compute_metrics(rows), "daily": daily_summaries(rows)}