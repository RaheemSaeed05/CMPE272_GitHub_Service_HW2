from datetime import datetime, timezone


class MockLabel:
    def __init__(self, name):
        self.name = name

class MockUser:
    def __init__(self, login):
        self.login = login

class MockComment:
    def __init__(self):
        self.id = 12345
        self.body = "Test comment"
        self.user = MockUser("testuser")
        self.created_at = datetime.now(timezone.utc)
        self.html_url = ("https://example.com/comments/12345")

class MockIssue:
    def __init__(self, number=1, title="test issue", body="test body", state="open", labels=None):
        self.number = number
        self.html_url = f"https://example.com/issues/{number}"
        self.state = state
        self.title = title
        self.body = body
        self.labels = [
            MockLabel(label)
            for label in (labels or [])
        ]
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        self.last_edit = None
        self.last_comment = None

    def edit(self, **updates):
        self.last_edit = updates
        if "title" in updates:
            self.title = updates["title"]
        if "body" in updates:
            self.body = updates["body"]
        if "state" in updates:
            self.state = updates["state"]

    def create_comment(self, body):
        self.last_comment = body
        comment = MockComment()
        comment.body = body
        return comment

class MockRepo:
    def __init__(self, issue=None, issues=None, per_page=30):
        self.issue = issue or MockIssue()

        if issues is None:
            self.issues = [self.issue]
        else:
            self.issues = issues

        self.per_page = per_page

    def get_issue(self, number):
        return self.issue

    def create_issue(self, title, body=None, labels=None):
        self.issue = MockIssue(
            number=5,
            title=title,
            body=body,
            labels=labels or []
        )

        return self.issue

    def get_label(self, name):
        return MockLabel(name)

    def get_issues(self, state="open", labels=None):
        results = [
            issue
            for issue in self.issues
            if state == "all" or issue.state == state
        ]

        if labels:
            wanted = {label.name for label in labels}

            results = [
                issue
                for issue in results
                if wanted.issubset(
                    {label.name for label in issue.labels}
                )
            ]

        return MockPaginatedIssues(
            results,
            self.per_page
        )

class MockPaginatedIssues:
    def __init__(self, issues, per_page=30):
        self.issues = issues
        self.per_page = per_page
        self.totalCount = len(issues)

    def get_page(self, page_number):
        start = page_number * self.per_page
        end = start + self.per_page

        return self.issues[start:end]

class MockGithub:
    def __init__(self, repo, per_page=30):
        self.repo = repo
        self.per_page = per_page

    def get_repo(self, name):
        self.repo.per_page = self.per_page
        return self.repo