from fastapi import FastAPI

app = FastAPI(
    title="WindSight API",
    description="UK wind forecast intelligence: Elexon WINDFOR forecasts vs FUELHH actuals.",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    """Simple check that the backend is running."""
    return {"status": "ok", "service": "windsight-backend"}