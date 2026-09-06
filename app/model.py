# James
from pydantic import BaseModel 

class NewIssue(BaseModel):
    title: str
    body: str
    labels: list[str]

class NewComment(BaseModel):
    body: str

class Comment(BaseModel):
    id: int
    body: str
    user: str
    created_at: str
    html_url: str

class Issue(BaseModel):
    id: int
    title: str
    body: str
    state: str
    labels: list[str]
    created_at: str
    updated_at: str
    comments: list[Comment] = []
    html_url: str