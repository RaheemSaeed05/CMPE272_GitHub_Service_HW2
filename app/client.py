import httpx

from app import config

conf = config.read_config()

GITHUB_OWNER = conf["app_github_owner"]
GITHUB_REPO = conf["app_github_repo"]
GITHUB_TOKEN = conf["app_github_token"]


BASE_URL = "https://api.github.com"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


async def create_issue(
    title: str,
    body: str,
    labels: list[str]
):
    url = (
        f"{BASE_URL}/repos/"
        f"{GITHUB_OWNER}/{GITHUB_REPO}/issues"
    )

    payload = {
        "title": title,
        "body": body,
        "labels": labels,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            headers=HEADERS,
            json=payload
        )

    return response.json()