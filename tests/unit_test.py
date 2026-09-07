from fastapi.testclient import TestClient
import asyncio
import app.main as main
from app import client as github_client
import hashlib
import hmac
import json
from fastapi import FastAPI
from app import webhook as webhook_module
import pytest
from datetime import datetime
from app import event_store


from tests.mocks import MockIssue, MockRepo

api_client = TestClient(main.app)

def test_healthz():
    response = api_client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_createIssue(): 
    response = api_client.post(
        "/issues",
        json={
            "body": "Issue has no title", 
            "labels": []
        }
    )
    assert response.status_code == 400

def test_create_issue(httpx_mock):
    expected_url = (
        f"https://api.github.com/repos/"
        f"{github_client.GITHUB_OWNER}/{github_client.GITHUB_REPO}/issues"
    )
    httpx_mock.add_response(
        method="POST",
        url=expected_url,
        status_code=201,
        json={
            "number": 10,
            "title": "Test Issue",
            "body": "This is a test issue",
            "state": "open",
            "labels": [
                {"name": "bug"}
            ]
        }
    )
    result = asyncio.run(
        github_client.create_issue(
            title="Test Issue",
            body="This is a test issue",
            labels=["bug"]
        )
    )
    assert result["number"] == 10
    assert result["title"] == "Test Issue"
    assert result["body"] == "This is a test issue"
    assert result["state"] == "open"

def test_create_issue_sends_correct_request(httpx_mock):
    expected_url = (
        f"https://api.github.com/repos/"
        f"{github_client.GITHUB_OWNER}/{github_client.GITHUB_REPO}/issues"
    )
    httpx_mock.add_response(
        method="POST",
        url=expected_url,
        status_code=201,
        json={
            "number": 10,
            "title": "Test Issue"
        }
    )
    asyncio.run(
        github_client.create_issue(
            title="Test Issue",
            body="Test body",
            labels=["bug", "urgent"]
        )
    )
    request = httpx_mock.get_request()
    assert request.method == "POST"
    assert str(request.url) == expected_url
    request_data = request.content.decode()
    assert '"title":"Test Issue"' in request_data
    assert '"body":"Test body"' in request_data
    assert '"labels":["bug","urgent"]' in request_data
    assert (
        request.headers["Accept"]
        == "application/vnd.github+json"
    )

def test_updateIssue():
    response = api_client.patch(
        "/issues/1",
        json={
            "state": "InvalidState"
        }
    )
    assert response.status_code == 400

def test_getIssue_success(monkeypatch):
    mock_issue = MockIssue(
        number=3,
        title="Test Issue",
        body="This is a test issue.",
        labels=["bug"]
    )
    mock_repo = MockRepo(mock_issue)
    monkeypatch.setattr(main, "repo", mock_repo)
    response = api_client.get("/issues/3")
    assert response.status_code == 200
    assert response.json()["number"] == 3
    assert response.json()["title"] == "Test Issue"
    assert response.json()["body"] == "This is a test issue."
    assert response.json()["labels"] == ["bug"]
    assert response.json()["state"] == "open"

def test_createIssue_success(monkeypatch):
    mock_repo = MockRepo()
    monkeypatch.setattr(main, "repo", mock_repo)
    response = api_client.post(
        "/issues",
        json={
            "title": "Test Issue",
            "body": "Testing creation",
            "labels": ["bug"]
        }
    )
    assert response.status_code == 201
    assert response.json()["title"] == "Test Issue"
    assert response.json()["body"] == "Testing creation"
    assert response.json()["labels"] == ["bug"]
    assert response.headers["Location"] == "/issues/5"

def test_updateIssue_success(monkeypatch):
    mock_issue = MockIssue(
        number=3,
        title="Old Title",
        body="Old body",
        labels=[]
    )
    mock_repo = MockRepo(mock_issue)
    monkeypatch.setattr(main, "repo", mock_repo)
    response = api_client.patch(
        "/issues/3",
        json={
            "title": "New Title",
            "body": "New body",
            "state": "closed"
        }
    )
    assert response.status_code == 200
    assert response.json()["title"] == "New Title"
    assert response.json()["body"] == "New body"
    assert response.json()["state"] == "closed"

def test_updateIssue_state_only(monkeypatch):
    mock_issue = MockIssue(
        number=3,
        title="Test Issue",
        body="Test body"
    )
    mock_repo = MockRepo(mock_issue)
    monkeypatch.setattr(main, "repo", mock_repo)
    response = api_client.patch(
        "/issues/3",
        json={
            "state": "closed"
        }
    )
    assert response.status_code == 200
    assert response.json()["state"] == "closed"
    assert response.json()["title"] == "Test Issue"

def test_addComment_success(monkeypatch):
    mock_issue = MockIssue(number=3)
    mock_repo = MockRepo(mock_issue)
    monkeypatch.setattr(main, "repo", mock_repo)
    response = api_client.post(
        "/issues/3/comments",
        json={
            "body": "This is a test comment"
        }
    )
    assert response.status_code == 201
    assert response.json()["body"] == "This is a test comment"
    assert "id" in response.json()
    assert "user" in response.json()
    assert "html_url" in response.json()

def test_invalid_per_page():
    response = api_client.get(
        "/issues?page=1&per_page=101"
    )
    assert response.status_code == 400

def test_invalid_page():
    response = api_client.get(
        "/issues?page=0&per_page=30"
    )
    assert response.status_code == 400

def test_getIssues_pagination(monkeypatch):
    issues = [
        MockIssue(number=4, title="Issue 4"),
        MockIssue(number=3, title="Issue 3"),
        MockIssue(number=2, title="Issue 2"),
        MockIssue(number=1, title="Issue 1"),
    ]
    mock_repo = MockRepo(issues=issues)
    class MockGithubFactory:
        def __init__(self, auth=None, per_page=30):
            self.per_page = per_page

        def get_repo(self, name):
            mock_repo.per_page = self.per_page
            return mock_repo
    monkeypatch.setattr(main, "Github", MockGithubFactory)
    response = api_client.get("/issues?page=1&per_page=2")
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["number"] == 4
    assert response.json()[1]["number"] == 3
    assert "Link" in response.headers

def test_getIssues_second_page(monkeypatch):
    issues = [
        MockIssue(number=4, title="Issue 4"),
        MockIssue(number=3, title="Issue 3"),
        MockIssue(number=2, title="Issue 2"),
        MockIssue(number=1, title="Issue 1"),
    ]
    mock_repo = MockRepo(issues=issues)
    class MockGithubFactory:
        def __init__(self, auth=None, per_page=30):
            self.per_page = per_page

        def get_repo(self, name):
            mock_repo.per_page = self.per_page
            return mock_repo
    monkeypatch.setattr(main, "Github", MockGithubFactory)
    response = api_client.get("/issues?page=2&per_page=2")
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["number"] == 2
    assert response.json()[1]["number"] == 1

def test_getIssues_label_filter(monkeypatch):
    issues = [
        MockIssue(
            number=1,
            title="Bug issue",
            labels=["bug"]
        ),
        MockIssue(
            number=2,
            title="Documentation issue",
            labels=["documentation"]
        )
    ]

    mock_repo = MockRepo(issues=issues)

    class MockGithubFactory:
        def __init__(self, auth=None, per_page=30):
            self.per_page = per_page

        def get_repo(self, name):
            mock_repo.per_page = self.per_page
            return mock_repo
    monkeypatch.setattr(main,"Github", MockGithubFactory)
    response = api_client.get("/issues?labels=bug")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Bug issue"
    assert response.json()[0]["labels"] == ["bug"]


#event_store
@pytest.fixture(autouse=True)
def reset_event_store():
    event_store.events.clear()
    event_store.processed_deliveries.clear()

    yield

    event_store.events.clear()
    event_store.processed_deliveries.clear()

def test_save_event_success():
    result = event_store.save_event(
        delivery_id="abc123",
        event="issues",
        action="opened",
        issue_number=5
    )
    assert result is True
    assert len(event_store.events) == 1
    saved = event_store.events[0]
    assert saved["id"] == "abc123"
    assert saved["event"] == "issues"
    assert saved["action"] == "opened"
    assert saved["issue_number"] == 5

def test_duplicate_event_is_ignored():
    first = event_store.save_event(
        delivery_id="abc123",
        event="issues",
        action="opened",
        issue_number=5
    )
    second = event_store.save_event(
        delivery_id="abc123",
        event="issues",
        action="opened",
        issue_number=5
    )
    assert first is True
    assert second is False
    assert len(event_store.events) == 1

def test_same_delivery_different_action_is_allowed():
    first = event_store.save_event(
        delivery_id="abc123",
        event="issues",
        action="opened",
        issue_number=5
    )
    second = event_store.save_event(
        delivery_id="abc123",
        event="issues",
        action="closed",
        issue_number=5
    )
    assert first is True
    assert second is True
    assert len(event_store.events) == 2

def test_get_events_returns_saved_events():
    event_store.save_event(
        delivery_id="abc123",
        event="issues",
        action="opened",
        issue_number=5
    )
    event_store.save_event(
        delivery_id="xyz789",
        event="issue_comment",
        action="created",
        issue_number=5
    )
    events = event_store.get_events()
    assert len(events) == 2
    assert events[0]["id"] == "abc123"
    assert events[1]["id"] == "xyz789"

def test_event_has_valid_timestamp():
    event_store.save_event(
        delivery_id="abc123",
        event="issues",
        action="opened",
        issue_number=5
    )
    timestamp = event_store.events[0]["timestamp"]
    parsed = datetime.fromisoformat(timestamp)
    assert parsed.tzinfo is not None

#webhook
app = FastAPI()
app.include_router(webhook_module.webhook_router)

client = TestClient(app)

TEST_SECRET = "test-webhook-secret"

@pytest.fixture(autouse=True)
def setup_webhook_tests(monkeypatch):
    event_store.events.clear()
    event_store.processed_deliveries.clear()
    monkeypatch.setattr(
        webhook_module.config,
        "read_config",
        lambda: {
            "webhook_secret": TEST_SECRET
        }
    )
    yield
    event_store.events.clear()
    event_store.processed_deliveries.clear()

def make_signature(body: bytes):
    digest = hmac.new(
        TEST_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    return f"sha256={digest}"

def test_valid_signature():
    body = b'{"action":"opened"}'
    signature = make_signature(body)
    assert webhook_module.valid_signature(
        body,
        signature
    ) is True

def test_invalid_signature():
    body = b'{"action":"opened"}'
    assert webhook_module.valid_signature(
        body,
        "sha256=wrong"
    ) is False

def test_missing_signature():
    body = b'{"action":"opened"}'
    assert webhook_module.valid_signature(
        body,
        None
    ) is False

def test_tampered_body():
    original_body = b'{"action":"opened"}'
    signature = make_signature(original_body)
    tampered_body = b'{"action":"closed"}'
    assert webhook_module.valid_signature(
        tampered_body,
        signature
    ) is False

def test_issues_webhook_success():
    payload = {
        "action": "opened",
        "issue": {
            "number": 5
        }
    }
    body = json.dumps(
        payload,
        separators=(",", ":")
    ).encode()
    response = client.post(
        "/webhook",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": make_signature(body),
            "X-GitHub-Event": "issues",
            "X-GitHub-Delivery": "delivery-123"
        }
    )
    assert response.status_code == 204
    assert len(event_store.events) == 1
    saved = event_store.events[0]
    assert saved["id"] == "delivery-123"
    assert saved["event"] == "issues"
    assert saved["action"] == "opened"
    assert saved["issue_number"] == 5

def test_issue_comment_webhook_success():
    payload = {
        "action": "created",
        "issue": {
            "number": 7
        }
    }
    body = json.dumps(
        payload,
        separators=(",", ":")
    ).encode()
    response = client.post(
        "/webhook",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": make_signature(body),
            "X-GitHub-Event": "issue_comment",
            "X-GitHub-Delivery": "delivery-456"
        }
    )
    assert response.status_code == 204
    saved = event_store.events[0]
    assert saved["event"] == "issue_comment"
    assert saved["action"] == "created"
    assert saved["issue_number"] == 7

def test_ping_webhook():
    payload = {
        "zen": "Keep it logically awesome."
    }
    body = json.dumps(
        payload,
        separators=(",", ":")
    ).encode()
    response = client.post(
        "/webhook",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": make_signature(body),
            "X-GitHub-Event": "ping",
            "X-GitHub-Delivery": "ping-123"
        }
    )
    assert response.status_code == 204
    saved = event_store.events[0]
    assert saved["event"] == "ping"
    assert saved["action"] == "ping"
    assert saved["issue_number"] is None

def test_webhook_invalid_signature():
    payload = {
        "action": "opened",
        "issue": {
            "number": 5
        }
    }
    body = json.dumps(
        payload,
        separators=(",", ":")
    ).encode()
    response = client.post(
        "/webhook",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": "sha256=wrong",
            "X-GitHub-Event": "issues",
            "X-GitHub-Delivery": "delivery-123"
        }
    )
    assert response.status_code == 401

def test_unknown_event():
    payload = {
        "action": "created"
    }
    body = json.dumps(
        payload,
        separators=(",", ":")
    ).encode()
    response = client.post(
        "/webhook",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": make_signature(body),
            "X-GitHub-Event": "push",
            "X-GitHub-Delivery": "delivery-123"
        }
    )
    assert response.status_code == 400

def test_unknown_action():
    payload = {
        "action": "something_weird",
        "issue": {
            "number": 5
        }
    }
    body = json.dumps(
        payload,
        separators=(",", ":")
    ).encode()
    response = client.post(
        "/webhook",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": make_signature(body),
            "X-GitHub-Event": "issues",
            "X-GitHub-Delivery": "delivery-123"
        }
    )
    assert response.status_code == 400

def test_duplicate_webhook_is_not_stored_twice():
    payload = {
        "action": "opened",
        "issue": {
            "number": 5
        }
    }
    body = json.dumps(
        payload,
        separators=(",", ":")
    ).encode()
    headers = {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": make_signature(body),
        "X-GitHub-Event": "issues",
        "X-GitHub-Delivery": "duplicate-123"
    }
    first = client.post(
        "/webhook",
        content=body,
        headers=headers
    )
    second = client.post(
        "/webhook",
        content=body,
        headers=headers
    )
    assert first.status_code == 204
    assert second.status_code == 204
    assert len(event_store.events) == 1

def test_get_events():
    event_store.save_event(
        "delivery-123",
        "issues",
        "opened",
        5
    )
    response = client.get("/events")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "delivery-123"
    assert data[0]["event"] == "issues"
    assert data[0]["action"] == "opened"
    assert data[0]["issue_number"] == 5