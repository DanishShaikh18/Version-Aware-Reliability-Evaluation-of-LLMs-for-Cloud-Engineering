# GCP Fundamentals: Resource Hierarchy, IAM, and CLI

## Metadata
- **Last verified:** 2026-10-16
- **Official sources:**
  - https://cloud.google.com/docs/overview
  - https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy
  - https://cloud.google.com/iam/docs/overview
  - https://cloud.google.com/sdk/docs/install
  - https://cloud.google.com/docs/authentication/application-default-credentials
- **SDK version verified:** Google Cloud SDK 576.0.0 (core 2026.07.10)

---

## What Is Google Cloud?

Google Cloud Platform (GCP) is Google's public cloud infrastructure. It provides compute, storage, networking, machine learning, and data analytics services accessible via APIs, CLI, and the Cloud Console.

---

## Resource Hierarchy

GCP organises all resources in a strict parent-child tree. Every resource (except the root) has exactly one parent. IAM policies and organisation policies assigned at a higher level cascade downward to child resources.

```
Organisation  (root, optional, tied to Google Workspace / Cloud Identity domain)
  └── Folders  (optional grouping by department, environment, team)
       └── Projects  (administrative and billing boundary — where APIs are enabled)
            └── Resources  (VMs, buckets, databases, Cloud Run services, etc.)
```

### Organisation
- Represents a company or domain (e.g., `example.com`).
- Requires a Google Workspace or Cloud Identity account.
- Assets belong to the organisation, not to individual employees.

### Folders
- Optional sub-containers under an Organisation.
- Typical use: group by environment (`production`, `staging`), department, or team.
- Folders can be nested.

### Projects
- The fundamental unit of work in GCP.
- Every resource lives inside exactly one project.
- Projects have a globally unique **Project ID** (immutable once set) and a numeric **Project Number**.
- APIs are enabled per project; billing is linked per project.

### Resources
- Actual cloud components: Compute Engine VMs, Cloud Run services, Cloud Storage buckets, BigQuery datasets, etc.
- Each resource belongs to one project.

---

## IAM: Identity and Access Management

IAM controls who (identity / principal) can do what (role / permissions) on which resource.

### Principals (Identities)
| Type | Description |
|---|---|
| Google Account | A single human user (e.g., `user@gmail.com`) |
| Service Account | A non-human machine identity for applications and workloads |
| Google Group | Collection of Google Accounts or service accounts |
| Cloud Identity / Workspace domain | All users in an org domain |

### Roles
- **Basic roles:** `roles/viewer`, `roles/editor`, `roles/owner` — broad scope, use sparingly.
- **Predefined roles:** Service-specific (e.g., `roles/run.admin`, `roles/storage.objectViewer`).
- **Custom roles:** Fine-grained, user-defined permission sets.

### How to Grant a Role
```bash
# Grant a predefined role to a user on a project
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="user:user@example.com" \
    --role="roles/viewer"

# Grant a role to a service account
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:SA_NAME@PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.invoker"
```

### Service Accounts
- Special accounts used by code, VMs, Cloud Run services, and pipelines.
- Created at project level; granted IAM roles.
- Avoid downloading service account key JSON files where possible; prefer workload identity or ADC instead.

```bash
# Create a service account
gcloud iam service-accounts create SA_NAME \
    --display-name="My Service Account" \
    --project=PROJECT_ID

# List service accounts
gcloud iam service-accounts list --project=PROJECT_ID
```

---

## Application Default Credentials (ADC)

ADC is the recommended authentication approach for applications running on or connecting to GCP.

### How ADC works
The Google client libraries and ADK discover credentials in this order:
1. `GOOGLE_APPLICATION_CREDENTIALS` environment variable (points to a JSON key file).
2. `gcloud auth application-default login` credentials (stored locally).
3. Attached service account (when running on GCP infrastructure: Compute Engine, Cloud Run, GKE, etc.).

### Set up ADC for local development
```bash
# Authenticate your user account for local development
gcloud auth application-default login
# This opens a browser; creates credentials at the default location:
# Windows: %APPDATA%\gcloud\application_default_credentials.json

# Verify ADC is working
gcloud auth application-default print-access-token
```

### Print the ADC credential info
```bash
gcloud auth application-default print-access-token
gcloud config get-value core/account
```

**Security rule:** Never commit ADC credential files or service account JSON keys to source control.

---

## Installing the Google Cloud CLI

### Download and install
- **Windows:** Download the installer from https://cloud.google.com/sdk/docs/install and run it. The installer adds `gcloud` to your PATH.
- **Linux/macOS (package manager or archive):** Follow the platform-specific steps at the same page.

### Verify installed version
```bash
gcloud --version
# Expected output example (versions will differ):
# Google Cloud SDK 576.0.0
# bq 2.1.34
# core 2026.07.10
```

### Update components
```bash
gcloud components update
```

---

## Initialising gcloud

```bash
# Interactive initialisation: logs in, selects project and region
gcloud init
```

This command walks through:
1. Logging in (or selecting an existing account).
2. Selecting a default project.
3. Optionally selecting a default compute region and zone.

---

## Selecting a Project

```bash
# Set default project for all subsequent commands
gcloud config set project PROJECT_ID

# Verify current project
gcloud config get-value project

# List available projects
gcloud projects list
```

---

## Enabling APIs

APIs must be enabled before you can use a service in a project.

```bash
# Enable a single API
gcloud services enable run.googleapis.com

# Enable multiple APIs at once
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    aiplatform.googleapis.com

# List enabled APIs
gcloud services list --enabled --project=PROJECT_ID

# Check if a specific API is enabled
gcloud services list --enabled --filter="name:run.googleapis.com"
```

---

## Common gcloud Commands

```bash
# Check authentication status
gcloud auth list

# Describe a project
gcloud projects describe PROJECT_ID

# Get help on any command
gcloud help
gcloud run --help
gcloud services --help

# View current config
gcloud config list

# Switch between configurations (useful for multiple projects)
gcloud config configurations list
gcloud config configurations activate CONFIG_NAME
```

---

## Regions and Zones

- **Region:** A geographic area (e.g., `us-central1`, `europe-west1`, `asia-south1`).
- **Zone:** An isolated location within a region (e.g., `us-central1-a`). Zonal resources (e.g., VMs) are deployed to a specific zone; regional resources (e.g., Cloud Run) span a region.

```bash
# List available regions
gcloud compute regions list

# List zones in a region
gcloud compute zones list --filter="region:us-central1"
```

---

## Security Best Practices

1. **Principle of least privilege:** Grant only the permissions a principal needs for its specific task.
2. **Prefer predefined roles over basic roles** (`owner`, `editor`).
3. **Use service accounts for workloads**, not personal accounts.
4. **Avoid service account key files** where possible; use ADC, workload identity, or attached service accounts.
5. **Never commit credentials** to source control. Use `.gitignore` to exclude `.env`, `*.json` key files, and `application_default_credentials.json`.
6. **Enable organisation policies** to restrict external IP addresses, allowed regions, etc.
7. **Audit IAM bindings** periodically to remove stale access.

---

## Common Errors and Troubleshooting

| Error | Likely Cause | Fix |
|---|---|---|
| `PERMISSION_DENIED` | Missing IAM role | Grant required role to the principal |
| `API not enabled` | API not enabled in project | `gcloud services enable SERVICE` |
| `UNAUTHENTICATED` | ADC not set up | Run `gcloud auth application-default login` |
| `Project not found` | Wrong project ID or missing access | Verify with `gcloud projects list` |
| `Quota exceeded` | Request quota limit hit | Check quotas in Cloud Console; request increase |

---

## Official References
- Google Cloud overview: https://cloud.google.com/docs/overview
- Resource hierarchy: https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy
- IAM overview: https://cloud.google.com/iam/docs/overview
- Application Default Credentials: https://cloud.google.com/docs/authentication/application-default-credentials
- Google Cloud CLI install: https://cloud.google.com/sdk/docs/install
- Regions and zones: https://cloud.google.com/compute/docs/regions-zones
