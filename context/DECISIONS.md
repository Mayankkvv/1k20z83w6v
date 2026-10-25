# Decisions

1. Forecast error = forecast - actual. Positive means overforecast.
2. Compare at hourly resolution: average the two half-hourly actuals in each hour.
3. Decision cutoff: 09:50 UTC on the day before delivery. This is an ASSUMPTION
   (based on the N2EX day-ahead auction), not stated by the assessment.
   It is not yet verified against authoritative documentation. It must be configurable.
4. Only forecasts with publishTime <= cutoff are eligible. Use the latest eligible one.
   If none exists, mark the hour as missing.
5. Preliminary scripts are not production code. Their results must be reproduced with tests.
6. Metrics are always calculated by the Python backend, never hardcoded in React.