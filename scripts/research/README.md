# Research scripts

These are the exploratory scripts used before the application was built. They are kept as
evidence of how the Elexon data was investigated. They are **not** part of the application,
and their results were reproduced and tested in `backend/` (see `backend/reproduce_january.py`).

Run them from the project root with the virtual environment active, for example:

    python scripts/research/check_actuals.py

| Script | What it investigated |
|---|---|
| `check_actuals.py` | The FUELHH actual-generation endpoint: working parameters (`publishDateTimeFrom` / `publishDateTimeTo`), WIND filtering, 48 half-hourly periods on 1 January 2026. |
| `check_forecasts.py` | The WINDFOR forecast endpoint: eight forecast versions published on 31 December 2025, each with 24 hourly periods. |
| `compare_one_day.py` | A first forecast-versus-actual comparison for 1 January 2026 using a 09:50 UTC cutoff on the previous day. |
| `check_january.py` | A first full-month analysis (744 hourly periods) with provisional accuracy metrics. |

Known simplifications compared with the application: no retries or error handling, no
tests, and no handling of malformed records.