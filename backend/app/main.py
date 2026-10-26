import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.services.elexon_client import ElexonAPIError

# Web addresses that are allowed to call this API from a browser.
# Override with the CORS_ORIGINS environment variable (comma-separated), e.g. for deployment.
DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"


def get_cors_origins() -> list:
    raw = os.environ.get("CORS_ORIGINS", DEFAULT_CORS_ORIGINS)
    return [origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()]


app = FastAPI(
    title="WindSight API",
    description="UK wind forecast intelligence: Elexon WINDFOR forecasts vs FUELHH actuals.",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(router)


@app.exception_handler(ElexonAPIError)
async def elexon_error_handler(request: Request, exc: ElexonAPIError):
    """Elexon failed: answer with 502 (bad gateway) and a readable message."""
    return JSONResponse(
        status_code=502,
        content={"detail": f"Could not get data from Elexon: {exc}"},
    )


@app.get("/health")
def health_check():
    """Simple check that the backend is running."""
    return {"status": "ok", "service": "windsight-backend"}