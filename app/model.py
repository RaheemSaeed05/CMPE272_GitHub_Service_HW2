# James
from enum import StrEnum

from pydantic import BaseModel


class IssueState(StrEnum):
    OPEN = "open"
    CLOSED = "closed"

class NewIssue(BaseModel):
    title: str
    body: str
    labels: list[str]

class UpdateIssue(BaseModel):
    title: str | None = None
    body: str | None = None
    state: IssueState | None = None

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
