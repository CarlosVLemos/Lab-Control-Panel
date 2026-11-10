from fastapi import FastAPI

app = FastAPI(title="Lab Control Panel", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "lab-control-panel"}
