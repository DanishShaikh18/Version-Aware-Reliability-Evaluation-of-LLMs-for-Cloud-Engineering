# Cloud Run: Deploying Containerised and Source-Based Applications

## Metadata
- **Last verified:** 2026-10-16
- **Official sources:**
  - https://cloud.google.com/run/docs/overview/what-is-cloud-run
  - https://cloud.google.com/run/docs/deploying-source-code
  - https://cloud.google.com/run/docs/quickstarts/build-and-deploy/deploy-python-service
  - https://cloud.google.com/run/docs/triggering/using-scheduler
  - https://cloud.google.com/run/docs/configuring/services/environment-variables
- **gcloud CLI version verified:** Google Cloud SDK 576.0.0

---

## What Is Cloud Run?

Cloud Run is a fully managed serverless compute platform on Google Cloud that runs stateless containers. You deploy code or a container image; Cloud Run handles provisioning, scaling (including scale-to-zero), TLS, and load balancing automatically.

**When to use Cloud Run:**
- HTTP/gRPC APIs, REST services, or web applications.
- Event-driven workloads triggered by Pub/Sub, Eventarc, or Cloud Scheduler.
- Containerised applications you want to run without managing servers.
- Tasks with variable traffic (benefits from scale-to-zero when idle).

**When Cloud Run is not the right choice:**
- Long-running background processes with no HTTP trigger (use Cloud Run Jobs).
- Stateful workloads requiring persistent local disk (use GKE or Compute Engine).

---

## Services vs. Jobs

| Concept | Description |
|---|---|
| **Cloud Run Service** | Runs containers in response to HTTP(S) requests; scales automatically. |
| **Cloud Run Job** | Executes a container to completion (batch/scheduled tasks); not HTTP-triggered. |

This document focuses on **Cloud Run Services**.

---

## Prerequisites

Before deploying to Cloud Run:

1. **Google Cloud project** with billing enabled.
2. **APIs enabled** in your project:
   ```bash
   gcloud services enable \
       run.googleapis.com \
       cloudbuild.googleapis.com \
       artifactregistry.googleapis.com
   ```
3. **gcloud CLI installed** and initialised:
   ```bash
   gcloud init
   gcloud config set project PROJECT_ID
   ```
4. **IAM permissions** — the deploying account needs:
   - `roles/run.admin`
   - `roles/iam.serviceAccountUser`
   - `roles/cloudbuild.builds.editor`
   - `roles/artifactregistry.admin`

---

## Deployment Approaches

| Method | Description |
|---|---|
| `--source .` | Cloud Build compiles your source code into a container image using Buildpacks. No Dockerfile required. |
| Container image | Push a pre-built image to Artifact Registry or Docker Hub, then deploy. |
| Cloud Console | Point-and-click deployment through the Google Cloud web UI. |

---

## Deploying from Source Code (Python)

`gcloud run deploy --source .` builds your Python source using Google Cloud Buildpacks, pushes the image to Artifact Registry, and deploys the service — all in a single command.

### Required project files

**`main.py`** — Application entry point that listens on the `PORT` environment variable (Cloud Run always sets `PORT`, defaulting to `8080`):
```python
import os
from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello from Cloud Run!", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
```

**`requirements.txt`** — All dependencies including a production-grade WSGI server:
```
Flask==3.1.0
gunicorn==23.0.0
```

> **Note:** Buildpacks use `requirements.txt` (or `pyproject.toml`) to install dependencies. If neither is present, the build will fail.

### Deploy command (untested on this machine — command is from official docs)
```bash
# Run from inside your project directory
gcloud run deploy SERVICE_NAME \
    --source . \
    --region REGION \
    --platform managed
```

**Interactive prompts the first time:**
- Choose a region (e.g., `us-central1`).
- Allow/deny unauthenticated (public) invocations.

**Fully non-interactive example:**
```bash
gcloud run deploy my-python-service \
    --source . \
    --region us-central1 \
    --allow-unauthenticated \
    --project PROJECT_ID
```

---

## Revisions, Traffic, and Updates

Each deployment creates a new **revision**. Traffic can be split across revisions.

```bash
# Deploy a new version
gcloud run deploy SERVICE_NAME --source . --region REGION

# List revisions
gcloud run revisions list --service SERVICE_NAME --region REGION

# Route all traffic to a specific revision
gcloud run services update-traffic SERVICE_NAME \
    --to-revisions REVISION_NAME=100 \
    --region REGION
```

---

## Environment Variables

```bash
# Set environment variables at deploy time
gcloud run deploy SERVICE_NAME \
    --source . \
    --region REGION \
    --set-env-vars KEY1=VALUE1,KEY2=VALUE2

# Update environment variables on a running service
gcloud run services update SERVICE_NAME \
    --region REGION \
    --set-env-vars KEY=NEW_VALUE
```

> **Security:** Do not put secrets in environment variables directly. Use Secret Manager:
> ```bash
> gcloud run deploy SERVICE_NAME \
>     --set-secrets SECRET_NAME=projects/PROJECT_ID/secrets/MY_SECRET:latest
> ```

---

## Regions

Cloud Run is a regional service. Common regions:
- `us-central1` (Iowa)
- `us-east1` (South Carolina)
- `europe-west1` (Belgium)
- `asia-south1` (Mumbai)

Choose a region close to your users. For latency-sensitive workloads, check current region availability in the documentation.

---

## Authentication and Access Control

### Public (unauthenticated) access
```bash
gcloud run services add-iam-policy-binding SERVICE_NAME \
    --region REGION \
    --member="allUsers" \
    --role="roles/run.invoker"
```

### Private (authenticated) access
- Remove `allUsers` from the IAM binding.
- Clients must include a Bearer token in the `Authorization` header.
- Service-to-service calls: use a service account with `roles/run.invoker`.

```bash
# Get a token for testing from your authenticated user
TOKEN=$(gcloud auth print-identity-token)
curl -H "Authorization: Bearer $TOKEN" https://SERVICE_URL
```

---

## Viewing Logs

```bash
# Stream logs for a Cloud Run service
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=SERVICE_NAME" \
    --limit=50 \
    --format="table(timestamp,textPayload)"
```

Or use the Cloud Console → Cloud Run → select your service → Logs tab.

---

## Common Errors and Troubleshooting

| Error | Likely Cause | Fix |
|---|---|---|
| `Build failed` | Missing `requirements.txt` or syntax error | Check build logs: `gcloud builds list` |
| `Container failed to start` | App not listening on `PORT` | Use `os.environ.get("PORT", 8080)` |
| `403 Forbidden` | IAM not configured | Add `allUsers` as `roles/run.invoker` for public access |
| `No module named ...` | Dependency missing from `requirements.txt` | Add the package and redeploy |
| `API not enabled` | Cloud Run or Build API not enabled | `gcloud services enable run.googleapis.com cloudbuild.googleapis.com` |

---

## Cost Considerations

- **Pricing model:** Pay only for the CPU and memory used while handling requests plus container instance startup time.
- **Scale-to-zero:** No cost when no requests are being processed (unless min-instances > 0 is set).
- **Free tier:** As of the last check, Cloud Run has a monthly free allowance for requests, compute time, and networking. Always verify current pricing at https://cloud.google.com/run/pricing.
- **Cloud Build and Artifact Registry** also have their own pricing for source deployments.

---

## Security Considerations

- Use service accounts with least-privilege roles for Cloud Run services (not the Compute Engine default service account).
- Store sensitive configuration in **Secret Manager**, not in environment variables or container images.
- Enable **VPC connector** to restrict egress to private networks where needed.
- Use **binary authorization** in production to enforce container image signing.

---

## Official References
- What is Cloud Run: https://cloud.google.com/run/docs/overview/what-is-cloud-run
- Deploying from source: https://cloud.google.com/run/docs/deploying-source-code
- Python quickstart: https://cloud.google.com/run/docs/quickstarts/build-and-deploy/deploy-python-service
- Environment variables: https://cloud.google.com/run/docs/configuring/services/environment-variables
- IAM for Cloud Run: https://cloud.google.com/run/docs/securing/managing-access
- Pricing: https://cloud.google.com/run/pricing
