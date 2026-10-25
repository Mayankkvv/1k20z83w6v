from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.services.elexon_client import ElexonAPIError

app = FastAPI(
    title="WindSight API",
    description="UK wind forecast intelligence: Elexon WINDFOR forecasts vs FUELHH actuals.",
    version="0.2.0",
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