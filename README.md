# CMPE 272 GitHub Issues Service

A FastAPI service that acts as a gateway to the GitHub Issues API. 

---

## 1. How to Run Locally

### Docker

#### Windows

If Docker Desktop is not installed, open PowerShell and run:

```powershell
winget install --id Docker.DockerDesktop -e
```

After Docker Desktop is installed, run:

```powershell
.\run.bat
```

#### Linux/macOS

Make the Docker script executable:

```bash
chmod +x run.sh
```

Then run:

```bash
./run.sh
```

---

### Non-Docker

Python must be installed before using the non-Docker scripts.

#### Windows

Run:

```powershell
.\run-local.bat
```

#### Linux/macOS

Make the script executable:

```bash
chmod +x run-local.sh
```

Then run:

```bash
./run-local.sh
```
---

## 2. Environment Variable Setup and Scopes Used

Create a `.env` file in the root directory of the project.

Example:

```env
APP_GITHUB_TOKEN=your_github_token
APP_GITHUB_OWNER=your_github_owner
APP_GITHUB_REPO=your_repository_name
WEBHOOK_SECRET=your_webhook_secret
PORT=8000

# Optional ngrok configuration
NGROK_AUTH_TOKEN=
NGROK_DOMAIN=
```

The `.env` file contains private credentials and should not be committed to GitHub.

### Environment Variables

| Variable | Purpose |
|---|---|
| `APP_GITHUB_TOKEN` | GitHub Personal Access Token used to access the GitHub API |
| `APP_GITHUB_OWNER` | Owner of the GitHub repository |
| `APP_GITHUB_REPO` | Name of the GitHub repository |
| `WEBHOOK_SECRET` | Secret used to verify incoming GitHub webhook requests |
| `PORT` | Port used by the FastAPI application |
| `NGROK_AUTH_TOKEN` | Optional ngrok authentication token |
| `NGROK_DOMAIN` | Optional ngrok public domain |

## 3. API Examples

The examples below assume the service is running at:

```text
http://localhost:8000
```

### Health Check

#### `GET /healthz`

curl:

```bash
curl http://localhost:8000/healthz
```

HTTPie:

```bash
http GET http://localhost:8000/healthz
```

Example response:

```json
{
  "status": "ok"
}
```

---

### Create an Issue

#### `POST /issues`

curl:

```bash
curl -X POST http://localhost:8000/issues \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test issue",
    "body": "Created through the GitHub Issues service",
    "labels": ["bug"]
  }'
```

HTTPie:

```bash
http POST http://localhost:8000/issues \
  title="Test issue" \
  body="Created through the GitHub Issues service" \
  labels:='["bug"]'
```

A successful request returns:

```text
201 Created
```

The response also contains a `Location` header such as:

```text
Location: /issues/5
```

---

### List Issues

#### `GET /issues`

curl:

```bash
curl "http://localhost:8000/issues"
```

HTTPie:

```bash
http GET http://localhost:8000/issues
```

Filter by state:

```bash
curl "http://localhost:8000/issues?state=open"
```

```bash
http GET http://localhost:8000/issues state==open
```

Supported state values:

```text
open
closed
all
```

Filter by label:

```bash
curl "http://localhost:8000/issues?labels=bug"
```

```bash
http GET http://localhost:8000/issues labels==bug
```

Use pagination:

```bash
curl "http://localhost:8000/issues?page=1&per_page=10"
```

```bash
http GET http://localhost:8000/issues page==1 per_page==10
```

Combine filters and pagination:

```bash
curl "http://localhost:8000/issues?state=open&labels=bug&page=1&per_page=10"
```

The `page` value starts at `1`.

The maximum value for `per_page` is `100`.

The response also includes a `Link` header containing pagination links when applicable.

---

### Get One Issue

#### `GET /issues/{number}`

Example for issue number 5.

curl:

```bash
curl http://localhost:8000/issues/5
```

HTTPie:

```bash
http GET http://localhost:8000/issues/5
```

A successful request returns:

```text
200 OK
```

If the issue does not exist:

```text
404 Not Found
```

---

### Update an Issue

#### `PATCH /issues/{number}`

Update the title and body.

curl:

```bash
curl -X PATCH http://localhost:8000/issues/5 \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated issue title",
    "body": "Updated issue body"
  }'
```

HTTPie:

```bash
http PATCH http://localhost:8000/issues/5 \
  title="Updated issue title" \
  body="Updated issue body"
```

Close an issue:

```bash
curl -X PATCH http://localhost:8000/issues/5 \
  -H "Content-Type: application/json" \
  -d '{
    "state": "closed"
  }'
```

HTTPie:

```bash
http PATCH http://localhost:8000/issues/5 \
  state="closed"
```

Reopen an issue:

```bash
curl -X PATCH http://localhost:8000/issues/5 \
  -H "Content-Type: application/json" \
  -d '{
    "state": "open"
  }'
```

HTTPie:

```bash
http PATCH http://localhost:8000/issues/5 \
  state="open"
```

GitHub Issues cannot be permanently deleted through the Issues API. Closing an issue is used instead.

---

### Add a Comment

#### `POST /issues/{number}/comments`

curl:

```bash
curl -X POST http://localhost:8000/issues/5/comments \
  -H "Content-Type: application/json" \
  -d '{
    "body": "This is a test comment."
  }'
```

HTTPie:

```bash
http POST http://localhost:8000/issues/5/comments \
  body="This is a test comment."
```

A successful request returns:

```text
201 Created
```

---

### View Stored Webhook Events

#### `GET /events`

curl:

```bash
curl http://localhost:8000/events
```

HTTPie:

```bash
http GET http://localhost:8000/events
```

Webhook events are currently stored in memory. Stored events are cleared when the application restarts.

---

### Webhook Endpoint

#### `POST /webhook`

This endpoint is normally called automatically by GitHub.

The request uses the following GitHub headers:

```text
X-Hub-Signature-256
X-GitHub-Event
X-GitHub-Delivery
```

Supported webhook events:

```text
issues
issue_comment
ping
```

A valid webhook returns:

```text
204 No Content
```

An invalid webhook signature returns:

```text
401 Unauthorized
```

An unsupported webhook event or action returns:

```text
400 Bad Request
```

---

## 4. Webhook Setup Steps and Redelivery Instructions

GitHub must be able to reach the `/webhook` endpoint through a public URL.

For local development, ngrok can be used to provide a public URL.

### Set Up ngrok

Create an ngrok account and obtain:

- an ngrok authentication token
- an ngrok domain

Add the values to `.env`:

```env
NGROK_AUTH_TOKEN=your_ngrok_auth_token
NGROK_DOMAIN=your-domain.ngrok-free.app
```

Do not include `https://` in `NGROK_DOMAIN`.

Correct:

```env
NGROK_DOMAIN=example.ngrok-free.app
```

Incorrect:

```env
NGROK_DOMAIN=https://example.ngrok-free.app
```

When ngrok is configured, the webhook endpoint will look like:

```text
https://example.ngrok-free.app/webhook
```

ngrok is optional for normal API use. The API can still run without ngrok, but GitHub will not be able to send webhooks directly to localhost.

---

### Add the Webhook on GitHub

Open the configured repository on GitHub.

Go to:

```text
Settings
→ Webhooks
→ Add webhook
```

Set the **Payload URL** to:

```text
https://your-domain.ngrok-free.app/webhook
```

Set **Content type** to:

```text
application/json
```

For **Secret**, enter the same value that is stored in:

```env
WEBHOOK_SECRET=your_webhook_secret
```

Select the following events:

- Issues
- Issue comments

Save the webhook.

GitHub normally sends a `ping` event after the webhook is created.

---

### Webhook Signature Verification

GitHub sends a signature using the following header:

```text
X-Hub-Signature-256
```

The service verifies the signature using HMAC-SHA256 and the configured `WEBHOOK_SECRET`.

If the signature is valid:

```text
204 No Content
```

If the signature is invalid:

```text
401 Unauthorized
```

---

### Redeliver a Webhook

GitHub allows previous webhook deliveries to be sent again.

To redeliver a webhook:

1. Open the GitHub repository.
2. Go to **Settings → Webhooks**.
3. Select the configured webhook.
4. Open **Recent Deliveries**.
5. Select the delivery you want to resend.
6. Click **Redeliver**.
7. Confirm the redelivery.

The service uses the GitHub delivery ID and action to prevent duplicate webhook events from being stored multiple times.

If the same delivery is received again, it is ignored but still returns:

```text
204 No Content
```