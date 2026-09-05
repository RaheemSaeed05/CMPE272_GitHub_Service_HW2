# Raheem

import logging
import uuid

from fastapi import FastAPI, Request

app = FastAPI(title="CMPE 272 GitHub Issues Service")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())

    response = await call_next(request)

    logger.info(
        "request_id=%s method=%s path=%s status=%s",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
    )

    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/healthz")
def healthz():
    return {"status": "ok"}
