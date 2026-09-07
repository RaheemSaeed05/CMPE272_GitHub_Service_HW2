#Raheem, webhook handling

import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, HTTPException, Request, Response

from app import config
from app.event_store import get_events, save_event

webhook_router = APIRouter()
logger = logging.getLogger(__name__)

ALLOWED_ACTIONS = {
    "issues": {
        "opened", "edited", "closed", "reopened",
        "assigned", "unassigned", "labeled", "unlabeled",
        "locked", "unlocked", "deleted"
    },
    "issue_comment": {"created", "edited", "deleted"}
}


def valid_signature(body: bytes, signature: str | None):
    if not signature:
        return False

    secret = config.read_config()["webhook_secret"]

    if not secret:
        return False

    expected = "sha256=" + hmac.new(
        secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


@webhook_router.post("/webhook")
async def webhook(request: Request):
    body = await request.body()

    signature = request.headers.get("X-Hub-Signature-256")

    if not valid_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    event = request.headers.get("X-GitHub-Event")
    delivery_id = request.headers.get("X-GitHub-Delivery")

    if event not in {"issues", "issue_comment", "ping"}:
        raise HTTPException(status_code=400, detail="Unsupported webhook event")

    payload = json.loads(body)

    if event == "ping":
        action = "ping"
        issue_number = None
    else:
        action = payload.get("action")

        if action not in ALLOWED_ACTIONS[event]:
            raise HTTPException(status_code=400, detail="Unsupported webhook action")

        issue_number = payload.get("issue", {}).get("number")

    saved = save_event(delivery_id, event, action, issue_number)

    logger.info(
        "delivery_id=%s event=%s action=%s issue_number=%s stored=%s",
        delivery_id,
        event,
        action,
        issue_number,
        saved
    )

    return Response(status_code=204)


@webhook_router.get("/events")
def events():
    return get_events()
