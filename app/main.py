# Author, Raheem Saee, FastAPI application setup and health-check endpoint.

from fastapi import FastAPI

app = FastAPI(title="CMPE 272 GitHub Issues Service")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}
