# Current State

## Project
WindSight: UK Wind Forecast Intelligence. A full-stack assessment (React + Python/FastAPI)
that compares Elexon WINDFOR forecasts with FUELHH actual wind generation for January 2026.

## Owner setup
- Windows 11, VS Code, PowerShell
- Project folder: C:\Users\mayank\Desktop\wind-forecast-app
- Python venv: .venv in project root (Conda "base" is also shown in the prompt; this is fine)
- GitHub: public repo with anonymous name, remote "origin", branch main

## Working rules
- One step at a time. Wait for "next" before continuing.
- Explain for an absolute beginner. Give complete files and exact PowerShell commands.
- Every step ends with verification, then git status / add / commit / push.
- Never paste passwords or tokens into chat.
- Time limit: 16 hours total. Prefer a polished MVP.

## Roadmap status
- Step 1: Data investigation. DONE
- Step 2: Git/GitHub setup. DONE
- Step 3: FastAPI backend + /health. DONE
- Step 4: Elexon fetching service + tests. DONE
- Step 5: Cutoff verification + analysis module + tests. DONE (production results match preliminary)
- Step 6: API endpoints, caching, error handling, API tests. DONE (user confirmed)
- Step 7: React frontend with Vite. IN PROGRESS (files created, awaiting verification)
- Steps 8-15: see original roadmap. TODO

## Current structure
- check_actuals.py, check_forecasts.py, compare_one_day.py, check_january.py (root, to move to scripts/research/ later)
- backend/app/main.py (FastAPI app, /health, Elexon error handler -> HTTP 502)
- backend/app/config.py (January 2026 windows, DEFAULT_CUTOFF_TIME 09:50, MAPE_MIN_ACTUAL_MW 1.0)
- backend/app/api/routes.py (GET /api/overview, /api/day?date=, /api/accuracy)
- backend/app/services/elexon_client.py (raw fetching only)
- backend/app/services/data_cache.py (in-memory cache of raw records, 1 hour TTL, failures not cached)
- backend/app/analysis/processing.py (cutoff, forecast selection, hourly actuals, build_hourly_table)
- backend/app/analysis/metrics.py (compute_metrics, daily_summaries)
- backend/tests/ (test_elexon_client.py, test_processing.py, test_metrics.py, test_api.py; 51 tests expected)
- backend/live_check_elexon.py, backend/reproduce_january.py (manual live checks)
- frontend/ (Vite + React, JavaScript, plain CSS, Recharts installed)
  - frontend/index.html, frontend/src/main.jsx, frontend/src/App.jsx
  - frontend/src/pages/Dashboard.jsx (placeholder page for now)
  - frontend/src/index.css (CSS variables incl. --color-forecast blue, --color-actual orange)
- context/

## API summary
- GET /health -> {"status": "ok", ...}
- GET /api/overview -> {period, assumption{cutoff_time_utc, summary, note, mape_min_actual_mw}, metrics}
- GET /api/day?date=YYYY-MM-DD -> {date, cutoff_utc, metrics, rows[24]}; 400 outside Jan 2026, 422 bad format
- GET /api/accuracy -> {metrics, daily[31]}
- Row fields: delivery_time, date, hour, forecast_mw, forecast_publish_time, actual_mw, error_mw, status
- Elexon failure -> 502 {"detail": "Could not get data from Elexon: ..."}
- Metrics fields: total_periods, matched_periods, coverage_pct, status_counts, mae_mw, rmse_mw,
  mean_bias_mw, mape_pct, mape_periods, overforecast_periods, underforecast_periods, exact_matches
- Known January values: month MAE 2122.81, RMSE 2616.69, bias +1840.3, MAPE 22.06, 744 matched hours.
  Jan 1 MAE 4258.21. Highest-MAE day Jan 28 (5374.79).

## How to run
- Backend: cd backend; python -m uvicorn app.main:app --reload  (http://127.0.0.1:8000/docs)
- Backend tests: cd backend; python -m pytest -v
- Frontend: cd frontend; npm run dev  (http://localhost:5173); build check: npm run build
- Live checks: python live_check_elexon.py [--month]; python reproduce_january.py

## Next action
Verify the frontend runs and builds, commit and push Step 7.
Step 8: build the dashboard UI (metric cards, chart, date selector, accuracy section, data table),
first with sample data shape from the API summary above. CORS and real API calls come in Step 9.