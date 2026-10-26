# Step Log

## Step 1: Data investigation (DONE)
- FUELHH (actuals) is half-hourly. WINDFOR (forecasts) is hourly.
- Working parameters: publishDateTimeFrom / publishDateTimeTo (not from / to).
- Filter actuals by fuelType == "WIND".
- Provisional January 2026 results (to be re-verified by backend tests):
  MAE 2122.81 MW, RMSE 2616.69 MW, mean bias +1840.30 MW, MAPE 22.06%,
  744 matched hourly periods.

## Step 2: Git/GitHub setup (DONE)
- Added .gitignore, context/ folder, pushed research scripts to a public anonymous repo.

## Step 3: FastAPI backend (DONE)
- backend/app/main.py with GET /health; backend/requirements.txt.

## Step 4: Elexon fetching service (DONE)
- app/config.py, app/services/elexon_client.py, tests/test_elexon_client.py (11 mocked tests),
  live_check_elexon.py, pytest.ini. Retry on 5xx/429/network errors, no retry on other 4xx.

## Step 5: Cutoff verification and analysis module (IN PROGRESS)
- Verified 09:50 UK time = Nord Pool N2EX GB day-ahead gate closure (Nord Pool support page,
  Ofgem access rules). EPEX GB day-ahead closes earlier at 09:20. Sources date from 2020-2023;
  no 2026 confirmation found, so it stays an ASSUMPTION.
- Created app/analysis/processing.py, app/analysis/metrics.py, tests/test_processing.py,
  tests/test_metrics.py (30 tests), reproduce_january.py. Replaced config.py with cutoff and MAPE settings.
- Verify: python -m pytest -v (41 passed); python reproduce_january.py (compare with preliminary).