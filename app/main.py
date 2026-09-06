# Raheem

import logging
import uuid
from github import Github, Auth
from fastapi import FastAPI, Request, Response, Query
from app import config
import json
from app.model import NewIssue, UpdateIssue, NewComment, IssueState
from contextlib import asynccontextmanager
import ngrok

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
conf = config.read_config()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Setting up ngrok Endpoint")
    ngrok.set_auth_token(conf['ngrok_auth_token'])
    ngrok.forward(
        addr=conf['port'],
        domain=conf['ngrok_domain']
    )
    yield
    logger.info("Tearing Down ngrok Endpoint")
    ngrok.disconnect()

app = FastAPI(title="CMPE 272 GitHub Issues Service", lifespan=lifespan)


username = conf['github_owner']
repository = conf['github_repo']
token = conf['github_token']

auth = Auth.Token(token)
g = Github(auth=auth)
user = g.get_user(username)
repo = user.get_repo(repository)

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

'''
1) POST /issues
   Body: { title: string, body?: string, labels?: string[] }
   Behavior: Creates a GitHub issue in the configured repo.
   Responses:
     201 Created → { number, html_url, state, title, body, labels, created_at, updated_at }
     400 if invalid payload; 401 if missing/invalid token (propagate useful error info)
   Notes:
     - Return Location header: /issues/{number}
     - Map external validation errors into clear messages.
'''
@app.post("/issues", status_code=201)
async def createIssue(issue: NewIssue, response: Response):
    github_issue = repo.create_issue(title=issue.title, body=issue.body, labels=issue.labels)
    response.headers["Location"] = f"/issues/{github_issue.number}"
    return {
        "number": github_issue.number,
        "html_url": github_issue.html_url,
        "state": github_issue.state,
        "title": github_issue.title,
        "body": github_issue.body,
        "labels": [
            label.name for label in github_issue.labels
        ],
        "created_at": github_issue.created_at,
        "updated_at": github_issue.updated_at
    }

'''
2) GET /issues
   Query: state=open|closed|all (default=open), labels?, page?, per_page? (<=100)
   Behavior: Lists issues for the repo; preserve GitHub pagination semantics.
   Responses:
     200 OK → [{ number, title, state, labels, ... }], plus pagination headers.
'''
@app.get("/issues")
def getIssues(state: str = "open", labels: str = None, page: int = Query(default=1, ge=1), per_page: int = Query(default=30, ge=1, le=100)):
    github_page = Github(auth=auth, per_page=per_page)

    repo_page = github_page.get_repo(f"{username}/{repository}")

    label_objects = []
    if labels:
        label_names = [
            label.strip() 
            for label in labels.split(",")
            if label.strip()
        ]
        for label_name in label_names:
            label_objects.append(repo_page.get_label(label_name))

    if label_objects:
        github_issues = repo_page.get_issues(state=state, labels=label_objects)
    else:
        github_issues = repo_page.get_issues(state=state)

    issues_page = github_issues.get_page(page - 1)

    all_issues = list()

    for item in issues_page:
        all_issues.append({
            "number": item.number,
            "html_url": item.html_url,
            "state": item.state,
            "title": item.title,
            "body": item.body,
            "labels": [
                label.name for label in item.labels
            ],
            "created_at": item.created_at,
            "updated_at": item.updated_at
        })
    return all_issues

'''
3) GET /issues/{number}
   Behavior: Returns a single issue.
   Responses: 200 OK, 404 if not found.
'''
@app.get("/issues/{number}")
def getIssue(number: int):

    github_issue = repo.get_issue(number)
    
    return {
        "number": github_issue.number,
        "html_url": github_issue.html_url,
        "state": github_issue.state,
        "title": github_issue.title,
        "body": github_issue.body,
        "labels": [
            label.name for label in github_issue.labels
        ],
        "created_at": github_issue.created_at,
        "updated_at": github_issue.updated_at
    }

'''
4) PATCH /issues/{number}
   Body: { title?, body?, state? }   # state may be "open" or "closed"
   Behavior: Updates the issue (rename, edit body, close/open).
   Responses: 200 OK; 400/404 on errors.
'''
@app.patch("/issues/{number}")
def updateIssue(number: int, issue: IssueState = None):
    github_issue = repo.get_issue(number)
    updates = {}
    if issue.title is not None:
        updates["title"] = issue.title
    if issue.body is not None:
        updates["body"] = issue.body
    if issue.state is not None:
        updates["state"] = issue.state.value
    github_issue.edit(**updates)
    github_issue = repo.get_issue(number)
    return {"message": f"Issue #{number} updated successfully"}
     
'''
5) POST /issues/{number}/comments
   Body: { body: string }
   Behavior: Adds a comment to the issue.
   Responses: 201 Created → { id, body, user, created_at, html_url }
'''
@app.post("/issues/{number}/comments", status_code=201)
def addComment(number: int, comment: NewComment):
    github_issue = repo.get_issue(number)
    new_comment = github_issue.create_comment(comment.body)
    return {
        "id": new_comment.id,
        "body": new_comment.body,
        "user": new_comment.user.login,
        "created_at": new_comment.created_at,
        "html_url": new_comment.html_url, 
    }


'''
6) POST /webhook
   Behavior:
     - Verify HMAC SHA-256 signature using WEBHOOK_SECRET.
     - Accept events: "issues", "issue_comment" (and "ping").
     - On valid signature + known event: persist event to a local store (file/SQLite/in-memory ok), log summary.
     - Respond 2xx quickly (ack), never block on long work. Use retry-safe handling.
   Responses:
     204 No Content on success; 401 if signature invalid; 400 for unknown event/action.
'''


'''
7) GET /events (optional but recommended)
   Behavior: Returns the last N processed webhook deliveries for debugging.
   Response: 200 OK → array of { id, event, action, issue_number, timestamp }
'''