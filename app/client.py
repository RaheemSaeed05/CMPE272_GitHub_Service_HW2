# James 
import httpx

from app.config import (
    GITHUB_TOKEN, 
    GITHUB_OWNER, 
    GITHUB_REPO, 
)

BASE_URL = "https://api.github.com"

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}", 
    "Accept": "application/vnd.github.v3+json", 
    "X-GitHub-Api-Version": "2022-11-28", 
}

async def create_issue(title: str, body: str, labels: list[str]):
    url = f"{BASE_URL}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/issues"
    payload = {
        "title": title, 
        "body": body, 
        "labels": labels, 
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=HEADERS, json=payload)
        
    return response.json()

