from datetime import datetime, timedelta, timezone

# Delivery periods analysed by the app: January 2026 (UK local time is GMT = UTC in January).
ANALYSIS_START = datetime(2026, 1, 1, tzinfo=timezone.utc)
ANALYSIS_END = datetime(2026, 2, 1, tzinfo=timezone.utc)  # exclusive

# Actuals (FUELHH) are published about 30 minutes after their period ends,
# so the last January period (23:30 on Jan 31) is published on Feb 1.
ACTUALS_PUBLISH_FROM = ANALYSIS_START
ACTUALS_PUBLISH_TO = ANALYSIS_END + timedelta(hours=1)

# Forecasts (WINDFOR) for a delivery day are published before that day.
# Start 2 days early for a safety margin. The last day-ahead decision for
# Jan 31 happens on Jan 30, so we do not need forecasts published after Jan 31 00:00.
FORECAST_PUBLISH_FROM = ANALYSIS_START - timedelta(days=2)
FORECAST_PUBLISH_TO = ANALYSIS_END - timedelta(days=1)