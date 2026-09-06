from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_createIssue(): 
    response = client.post(
        "/issues",
        json={
            "body": "Issue has no title", 
            "labels": []
        }
    )

    assert response.status_code == 400

def test_updateIssue():
    response = client.patch(
        "/issues/1",
        json={
            "state": "InvalidState"
        }
    )

    assert response.status_code == 400
