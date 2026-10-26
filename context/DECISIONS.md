# Decisions

1. Forecast error = forecast - actual. Positive means overforecast.
2. Compare at hourly resolution: average the two half-hourly actuals in each hour.
   An hour with only one half-hour is "incomplete_actual" and gets no value.
3. Decision cutoff: 09:50 UTC on the day before delivery, configurable (config.DEFAULT_CUTOFF_TIME
   and the cutoff_time function parameter). This is an ASSUMPTION, not stated by the assessment.
   Verified: 09:50 UK time is the gate closure of the Nord Pool N2EX GB day-ahead auction
   (Nord Pool support page; Ofgem access rules). The EPEX GB day-ahead auction closes earlier
   at 09:20 UK time. Sources are from 2020-2023, so 2026 timings are unconfirmed.
   In January UK time = UTC, so the times are used directly as UTC.
4. Only forecasts with publishTime <= cutoff are eligible (exactly at the cutoff counts).
   Use the latest eligible one. If none exists, the hour is "missing_forecast" (never filled).
5. Preliminary scripts are not production code. Their results are reproduced by reproduce_january.py.
6. Metrics are always calculated by the Python backend, never hardcoded in React.
7. The fetching service returns raw records only. Cleaning, duplicates and cutoff logic live in
   backend/app/analysis/.
8. Fetch windows: actuals published Jan 1 00:00 to Feb 1 01:00 UTC; forecasts published
   Dec 30 00:00 to Jan 31 00:00 UTC.
9. Duplicate actual records for one half-hour: the latest publishTime wins.
10. MAPE = mean of |error| / actual x 100, over matched hours with actual >= 1 MW.
    Hours below that are left out of MAPE only, and the count is reported (mape_periods).