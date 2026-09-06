# Raheem

import logging
import uuid
import requests
from github import Github, Auth
from fastapi import FastAPI, Request
from app import config
from pydantic import BaseModel
import json
from enum import StrEnum

class Issue(BaseModel):
    title: str

class Comment(BaseModel):
    body: str

class IssueState(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


app = FastAPI(title="CMPE 272 GitHub Issues Service")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

conf = config.read_config()
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

@app.post("/issues")
async def createIssue(issue: Issue):
    github_issue = repo.create_issue(issue.title)
    return {
        "number": github_issue.number,
        "html_url": github_issue.html_url,
        "state": github_issue.state,
        "title": github_issue.body,
        "labels": github_issue.labels,
        "created_at": github_issue.created_at,
        "updated_at": github_issue.updated_at
    }


@app.get("/issues")
def getIssues():
    github_issues = repo.get_issues()
    all_issues = list()
    for item in github_issues:
        all_issues.append({
            "id": item.id,
            "title": item.title,
            "number": item.number
        })
    return all_issues

@app.get("/issues/{number}")
def getIssue(number: int):
    github_issue = repo.get_issue(number)
    return {
        "number": github_issue.number,
        "html_url": github_issue.html_url,
        "state": github_issue.state,
        "title": github_issue.title,
        "labels": github_issue.labels,
        "created_at": github_issue.created_at,
        "updated_at": github_issue.updated_at
    }

@app.patch("/issues/{number}")
def updateIssue(number: int, title: str = None, body: str = None, state: IssueState = None):
    github_issue = repo.get_issue(number)
    updates = {}
    if title is not None:
        updates["title"] = title
    if body is not None:
        updates["body"] = body
    if state is not None:
        updates["state"] = state.value
    github_issue.edit(**updates)
    return {"message": f"Issue #{number} updated successfully"}
     

@app.post("/issues/{number}/comments")
def addComment(number: int, comment: Comment):
    github_issue = repo.get_issue(number)
    new_comment = github_issue.create_comment(comment.body)
    return {
        "issue_number": number,
        "body": new_comment.body,
        "created_at": new_comment.created_at
    }

