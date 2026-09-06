# James
from pydantic import BaseModel 
from enum import StrEnum

class IssueState(StrEnum):
    OPEN = "open"
    CLOSED = "closed"

class NewIssue(BaseModel):
    title: str
    body: str
    labels: list[str]

class UpdateIssue(BaseModel):
    title: str
    body: str
    state: IssueState 

class NewComment(BaseModel):
    body: str

class Comment(BaseModel):
    id: int
    body: str
    user: str
    created_at: str
    html_url: str

class Issue(BaseModel):
    number: int
    html_url: str
    state: IssueState
    title: str 
    body: str
    labels: list[str]
    created_at: str
    updated_at: str
