# Step Log

## Step 1: Data investigation (DONE)
- FUELHH (actuals) is half-hourly. WINDFOR (forecasts) is hourly.
- Working parameters: publishDateTimeFrom / publishDateTimeTo (not from / to).
- Filter actuals by fuelType == "WIND".
- Provisional January 2026 results (to be re-verified by backend tests):
  MAE 2122.81 MW, RMSE 2616.69 MW, mean bias +1840.30 MW, MAPE 22.06%,
  744 matched hourly periods.

## Step 2: Git/GitHub setup (IN PROGRESS)
- Added .gitignore and context/ folder.