# GitHub Actions: CI/CD Workflows and GCP Integration

## Metadata
- **Last verified:** 2026-10-16
- **Official sources:**
  - https://docs.github.com/en/actions
  - https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions
  - https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/configuring-openid-connect-in-google-cloud-platform
  - https://github.com/google-github-actions/auth
  - https://cloud.google.com/iam/docs/workload-identity-federation-with-deployment-pipelines
- **Action versions used in examples:** Verified against latest major versions as of 2026-10-16

---

## Core Concepts

| Term | Description |
|---|---|
| **Workflow** | A configurable automated process defined in a YAML file. Triggered by events. |
| **Job** | A set of steps that run sequentially on the same runner. Jobs run in parallel by default. |
| **Step** | A single task within a job. Either runs a shell command or uses an Action. |
| **Runner** | The VM that executes a job (`ubuntu-latest`, `windows-latest`, `macos-latest`, or self-hosted). |
| **Action** | A reusable unit of code (a step using `uses:`). Published to the GitHub Marketplace. |
| **Trigger (`on:`)** | The event(s) that start a workflow (e.g., `push`, `pull_request`, `schedule`). |
| **Artifact** | Files saved from a job and made available to other jobs or for download. |
| **Secret** | Encrypted environment variable stored in repository or organisation settings. |

---

## Workflow File Placement

Workflows must be placed in:
```
YOUR_REPO/
└── .github/
    └── workflows/
        ├── python-ci.yml
        └── deploy.yml
```

YAML files in `.github/workflows/` are automatically discovered and registered as workflows.

---

## YAML Syntax Essentials

```yaml
name: Workflow Name             # Display name in GitHub UI

on:                             # Trigger conditions
  push:
    branches: ["main"]
  pull_request:
    branches: ["main"]

jobs:
  job-name:                     # Job ID (alphanumeric and hyphens)
    runs-on: ubuntu-latest      # Runner

    steps:
    - name: Step name           # Human-readable step name
      uses: actions/checkout@v4 # Use an action from the Marketplace

    - name: Run a command
      run: echo "Hello, World!"

    - name: Multi-line command
      run: |
        echo "Line 1"
        echo "Line 2"
```

---

## Minimal Python CI Workflow

This workflow checks out code, installs dependencies, and runs tests with `pytest`:

```yaml
name: Python CI

on:
  push:
    branches: ["main"]
  pull_request:
    branches: ["main"]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: "3.12"
        cache: "pip"           # Caches pip dependencies for faster runs

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
        pip install pytest

    - name: Run tests
      run: pytest --tb=short
```

---

## Secrets and Variables

### Repository secrets
Stored in **Settings → Secrets and variables → Actions**.
- Secrets are masked in logs.
- Access in workflows: `${{ secrets.SECRET_NAME }}`

```yaml
- name: Use a secret
  run: echo "Project: ${{ secrets.GCP_PROJECT_ID }}"
  env:
    TOKEN: ${{ secrets.MY_TOKEN }}
```

### Environment variables
```yaml
env:
  PYTHONDONTWRITEBYTECODE: "1"    # Workflow-level env var (available to all jobs)

jobs:
  build:
    env:
      MY_VAR: "value"             # Job-level env var
    steps:
    - run: echo "$MY_VAR"
      env:
        STEP_VAR: "step-only"     # Step-level env var
```

---

## Authenticating to Google Cloud: Workload Identity Federation

**Workload Identity Federation (WIF)** allows GitHub Actions to authenticate to GCP without long-lived service account JSON key files. This is the **recommended approach**.

### One-time GCP Setup (run once — these commands create resources)

```bash
# 1. Enable required APIs
gcloud services enable \
    iam.googleapis.com \
    iamcredentials.googleapis.com \
    sts.googleapis.com

# 2. Create a Workload Identity Pool
gcloud iam workload-identity-pools create "github-pool" \
    --location="global" \
    --display-name="GitHub Actions Pool"

# 3. Create an OIDC provider for GitHub
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
    --location="global" \
    --workload-identity-pool="github-pool" \
    --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
    --issuer-uri="https://token.actions.githubusercontent.com"

# 4. Create a service account for GitHub Actions to impersonate
gcloud iam service-accounts create "github-actions-sa" \
    --display-name="GitHub Actions Service Account"

# 5. Get your project NUMBER (not ID)
gcloud projects describe PROJECT_ID --format="value(projectNumber)"
# Note the number for step 6

# 6. Allow GitHub repository to impersonate the service account
gcloud iam service-accounts add-iam-policy-binding \
    "github-actions-sa@PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/iam.workloadIdentityUser" \
    --member="principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/attribute.repository/YOUR_GITHUB_ORG/YOUR_REPO_NAME"
```

### GitHub Actions Workflow with WIF Authentication

```yaml
name: Python CI with GCP Auth

on:
  push:
    branches: ["main"]

# REQUIRED for WIF — enables GitHub to generate OIDC token
permissions:
  contents: read
  id-token: write

jobs:
  build-test:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: "3.12"
        cache: "pip"

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
        pip install pytest

    - name: Authenticate to Google Cloud (Workload Identity Federation)
      uses: google-github-actions/auth@v2
      with:
        project_id: ${{ secrets.GCP_PROJECT_ID }}
        workload_identity_provider: "projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/providers/github-provider"
        service_account: "github-actions-sa@${{ secrets.GCP_PROJECT_ID }}.iam.gserviceaccount.com"
        # This action sets GOOGLE_APPLICATION_CREDENTIALS automatically

    - name: Set up Cloud SDK (optional — for gcloud CLI in steps)
      uses: google-github-actions/setup-gcloud@v2

    - name: Run tests
      run: pytest --tb=short
      env:
        GOOGLE_CLOUD_PROJECT: ${{ secrets.GCP_PROJECT_ID }}
```

**Required GitHub Secrets** (Settings → Secrets and variables → Actions):
- `GCP_PROJECT_ID` — your GCP project ID (not secret, but convenient to store here)

**Replace placeholders:**
- `PROJECT_NUMBER` — the numeric project number from step 5 above
- `YOUR_GITHUB_ORG/YOUR_REPO_NAME` — your GitHub repository path

---

## Cloud Run Deployment Workflow Concept

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: ["main"]

permissions:
  contents: read
  id-token: write

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Authenticate to Google Cloud
      uses: google-github-actions/auth@v2
      with:
        workload_identity_provider: "projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/providers/github-provider"
        service_account: "github-actions-sa@${{ secrets.GCP_PROJECT_ID }}.iam.gserviceaccount.com"

    - name: Set up Cloud SDK
      uses: google-github-actions/setup-gcloud@v2

    - name: Deploy to Cloud Run
      run: |
        gcloud run deploy my-service \
          --source . \
          --region us-central1 \
          --project ${{ secrets.GCP_PROJECT_ID }} \
          --allow-unauthenticated
```

---

## Dependency Pinning (Security Best Practice)

Pin Action versions to a specific commit SHA (not just a tag) to prevent supply chain attacks:
```yaml
# Less secure: tag can be moved
uses: actions/checkout@v4

# More secure: pinned to a specific commit SHA
uses: actions/checkout@692973ef543e21a9b9d5f1d3be7fdc0deec0bb5  # v4
```

For Actions from trusted first-party sources (`actions/`, `google-github-actions/`), pinning to a major version tag (`@v4`) is a common acceptable practice.

---

## Permissions and Least Privilege

```yaml
# Restrict permissions at workflow level
permissions:
  contents: read          # Read repository contents (default is write — restrict it)
  id-token: write         # Required for WIF OIDC authentication
  pull-requests: write    # Only if the workflow needs to comment on PRs
```

Always grant the minimum permissions necessary.

---

## Troubleshooting

| Error | Likely Cause | Fix |
|---|---|---|
| `missing permission id-token: write` | Permissions not set | Add `permissions: id-token: write` to the workflow |
| `Error creating token: sts/exchange_token` | Incorrect WIF configuration | Verify pool, provider, and attribute mapping |
| `OIDC: not found` | Wrong provider or issuer URI | Confirm `issuer-uri` is `https://token.actions.githubusercontent.com` |
| Tests fail | Wrong Python version or missing deps | Check `python-version` and `requirements.txt` |
| `gcloud: command not found` | Cloud SDK not installed in step | Add `google-github-actions/setup-gcloud@v2` step before using `gcloud` |

---

## Official References
- GitHub Actions documentation: https://docs.github.com/en/actions
- Workflow syntax: https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions
- Configuring OIDC for GCP: https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/configuring-openid-connect-in-google-cloud-platform
- `google-github-actions/auth` action: https://github.com/google-github-actions/auth
- Workload Identity Federation: https://cloud.google.com/iam/docs/workload-identity-federation-with-deployment-pipelines
