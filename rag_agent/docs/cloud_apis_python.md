# Calling Google Cloud APIs from Python

## Metadata
- **Last verified:** 2026-10-16
- **Official sources:**
  - https://cloud.google.com/apis/docs/client-libraries-explained
  - https://cloud.google.com/docs/authentication/client-libraries
  - https://cloud.google.com/python/docs/reference
  - https://cloud.google.com/storage/docs/reference/libraries#client-libraries-install-python
  - https://cloud.google.com/docs/authentication/application-default-credentials

---

## REST APIs vs Client Libraries

### Google Cloud REST APIs
- Every Google Cloud service exposes a REST API (HTTP/JSON or gRPC).
- You can call them directly using `requests` or `httpx` with an OAuth2 bearer token.
- **Not recommended** for routine use — you must handle token refresh, retries, pagination, and serialisation yourself.

### Google Cloud Python Client Libraries
- Official, open-source Python packages that wrap the REST/gRPC APIs.
- Handle authentication (ADC), token refresh, retries, pagination, and serialisation automatically.
- **Recommended approach** for production and research code.
- Package names follow the pattern: `google-cloud-SERVICENAME`
  - Examples: `google-cloud-storage`, `google-cloud-bigquery`, `google-cloud-aiplatform`
- Full list: https://cloud.google.com/python/docs/reference

---

## HTTP Fundamentals (Background)

| Method | Purpose |
|---|---|
| `GET` | Read a resource |
| `POST` | Create a resource or trigger an action |
| `PUT` | Replace a resource |
| `PATCH` | Partially update a resource |
| `DELETE` | Delete a resource |

| Status Code | Meaning |
|---|---|
| `200 OK` | Success |
| `201 Created` | Resource created |
| `400 Bad Request` | Invalid request (check parameters) |
| `401 Unauthorized` | Missing or invalid credentials |
| `403 Forbidden` | Valid credentials but insufficient permissions |
| `404 Not Found` | Resource does not exist |
| `429 Too Many Requests` | Rate limit or quota exceeded |
| `500 Internal Server Error` | Server-side error |

---

## Prerequisites

1. **GCP project** with billing enabled.
2. **Target API enabled** in your project:
   ```bash
   gcloud services enable storage.googleapis.com
   ```
3. **ADC configured** for local development:
   ```bash
   gcloud auth application-default login
   ```
4. **IAM permissions** — the identity must have the required role for the API being called.
5. **Client library installed:**
   ```bash
   pip install google-cloud-storage
   ```

---

## Authentication with ADC (Application Default Credentials)

Google Cloud client libraries discover credentials in this order (you do not need to configure this in code):

1. `GOOGLE_APPLICATION_CREDENTIALS` environment variable → path to a service account JSON key file.
2. `gcloud auth application-default login` → user credentials stored locally.
3. Attached service account metadata → when running on GCP infrastructure (Cloud Run, GKE, Compute Engine).

```python
# No authentication code needed — the library handles it automatically
from google.cloud import storage

client = storage.Client()  # ADC credentials are discovered and used
```

---

## Minimal Working Example: Google Cloud Storage

```python
"""
Example: List blobs in a GCS bucket using the google-cloud-storage client library.

Prerequisites:
  - gcloud auth application-default login
  - pip install google-cloud-storage
  - storage.googleapis.com API enabled
  - Identity has roles/storage.objectViewer or roles/storage.admin
"""

from google.cloud import storage
from google.api_core import exceptions as gcp_exceptions

BUCKET_NAME = "YOUR_BUCKET_NAME"  # Replace with an actual bucket you have access to
PROJECT_ID  = "PROJECT_ID"        # Replace with your GCP project ID


def list_bucket_contents(bucket_name: str, project_id: str) -> None:
    """List the first 10 objects in a GCS bucket."""
    # Client is authenticated via ADC — no credentials in code
    client = storage.Client(project=project_id)

    try:
        blobs = client.list_blobs(bucket_name, max_results=10)
        print(f"Objects in bucket '{bucket_name}':")
        for blob in blobs:
            print(f"  - {blob.name}  ({blob.size} bytes)")

    except gcp_exceptions.NotFound:
        print(f"Bucket '{bucket_name}' not found or not accessible.")
    except gcp_exceptions.Forbidden:
        print(f"Access denied to bucket '{bucket_name}'. Check IAM permissions.")
    except gcp_exceptions.GoogleAPICallError as e:
        print(f"API call failed: {e}")


if __name__ == "__main__":
    list_bucket_contents(BUCKET_NAME, PROJECT_ID)
```

**Install the library:**
```bash
pip install google-cloud-storage
```

**Enable the API:**
```bash
gcloud services enable storage.googleapis.com
```

**Required IAM role:**
- `roles/storage.objectViewer` (read-only) or `roles/storage.admin`

---

## Error Handling with Client Libraries

```python
from google.api_core import exceptions as gcp_exceptions
from google.api_core import retry

# Standard exception types from google.api_core
try:
    # ... API call
    pass
except gcp_exceptions.Unauthenticated:
    print("Credentials are missing or expired. Check ADC setup.")
except gcp_exceptions.PermissionDenied:
    print("IAM permission denied. Check your role and project.")
except gcp_exceptions.NotFound:
    print("Resource not found. Check the resource name and project.")
except gcp_exceptions.ResourceExhausted:
    print("Quota exceeded. Check quotas in the Cloud Console.")
except gcp_exceptions.ServiceUnavailable:
    print("Service temporarily unavailable. Retry with backoff.")
except gcp_exceptions.GoogleAPICallError as e:
    print(f"API error: {e.message} (code: {e.code})")
```

---

## Retries

Client libraries perform automatic retries with exponential backoff for transient errors (`503 Service Unavailable`, `429 Too Many Requests`) by default. You can customise:

```python
from google.api_core import retry

# Custom retry configuration
custom_retry = retry.Retry(
    initial=1.0,      # Initial delay in seconds
    maximum=60.0,     # Maximum delay
    multiplier=2.0,   # Delay multiplier after each attempt
    deadline=300.0,   # Total time budget in seconds
)

# Use with supported methods
blobs = client.list_blobs(BUCKET_NAME, retry=custom_retry)
```

---

## Pagination

Many list operations return paginated results. Client libraries handle pagination automatically in most cases:

```python
# Automatic pagination — iterates through all pages
for blob in client.list_blobs(BUCKET_NAME):
    print(blob.name)

# Manual pagination with a page token (raw API style)
# Not needed when using high-level client library methods
```

---

## API Enablement and IAM Permissions

Before any API call will succeed:

```bash
# 1. Enable the API
gcloud services enable SERVICENAME.googleapis.com

# 2. Grant the appropriate role
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="user:YOUR_EMAIL" \
    --role="roles/storage.admin"

# 3. Verify the role is granted
gcloud projects get-iam-policy PROJECT_ID \
    --flatten="bindings[].members" \
    --filter="bindings.members:YOUR_EMAIL"
```

---

## Version-Specific API Behaviour

- Client libraries version independently of the API itself. Always check the library's changelog.
- API methods and parameters can change between major library versions.
- Pin client library versions in `requirements.txt`:
  ```
  google-cloud-storage>=2.18.0,<3.0.0
  ```
- For Vertex AI / Gemini API, use `google-genai>=2.31.0` as in this project.

---

## Credentials: What NOT to Do

```python
# DO NOT do any of these:

# Hard-coding credentials in code
client = storage.Client(credentials=SERVICE_ACCOUNT_CREDENTIALS_HARDCODED)

# Loading a key file from a hardcoded path that might be committed
import json
with open("service-account-key.json") as f:
    creds = json.load(f)

# Printing credentials to stdout or logs
print(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))
```

Always use ADC. If you must use a key file, load its path from an environment variable and never commit the file.

---

## Request Quotas and Limits

- Each API has per-project, per-minute, and per-day quotas.
- Check current quotas: **Cloud Console → APIs & Services → Quotas**.
- Request a quota increase through the Cloud Console if needed.
- Use `429 Too Many Requests` or `ResourceExhausted` errors as signals to back off.

---

## Common Errors

| Error | Cause | Fix |
|---|---|---|
| `google.auth.exceptions.DefaultCredentialsError` | ADC not configured | Run `gcloud auth application-default login` |
| `403 PERMISSION_DENIED` | Missing IAM role | Grant the required role to your principal |
| `404 NOT_FOUND` | Wrong resource name or project | Verify the resource exists in the correct project |
| `429 RESOURCE_EXHAUSTED` | API quota exceeded | Reduce request rate; request quota increase |
| `api not enabled` | API not enabled for the project | `gcloud services enable SERVICENAME.googleapis.com` |

---

## Official References
- Client libraries explained: https://cloud.google.com/apis/docs/client-libraries-explained
- Authentication for client libraries: https://cloud.google.com/docs/authentication/client-libraries
- Python client library reference: https://cloud.google.com/python/docs/reference
- Cloud Storage Python client: https://cloud.google.com/storage/docs/reference/libraries#client-libraries-install-python
- ADC documentation: https://cloud.google.com/docs/authentication/application-default-credentials
- API quotas: https://cloud.google.com/docs/quota
