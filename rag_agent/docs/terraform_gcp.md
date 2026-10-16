# Terraform with GCP: Infrastructure as Code

## Metadata
- **Last verified:** 2026-10-16
- **Official sources:**
  - https://developer.hashicorp.com/terraform/docs
  - https://developer.hashicorp.com/terraform/install
  - https://registry.terraform.io/providers/hashicorp/google/latest/docs
  - https://cloud.google.com/docs/terraform
- **Version context:**
  - Terraform CLI: verify with `terraform version` (see Installation section)
  - Google provider: `hashicorp/google`, pinned to `~> 6.0` in examples below
  - **Always pin provider versions in production**

---

## What Is Terraform?

Terraform is an open-source **Infrastructure as Code (IaC)** tool by HashiCorp. It lets you define cloud infrastructure in declarative HCL (HashiCorp Configuration Language) files, then provision and manage it through a consistent CLI workflow.

**Core principles:**
- **Declarative:** You describe the desired end state, not the steps to reach it.
- **Idempotent:** Running the same configuration repeatedly produces the same result.
- **State-tracked:** Terraform records what it has created in a state file, enabling it to calculate incremental changes.

---

## Installing Terraform

### Windows
1. Download the binary from https://developer.hashicorp.com/terraform/install (select Windows AMD64).
2. Unzip and place `terraform.exe` in a directory on your `PATH` (e.g., `C:\tools\terraform\`).
3. Add that directory to `PATH` in System Properties → Environment Variables.

### macOS (Homebrew)
```bash
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
```

### Linux (apt — Debian/Ubuntu)
```bash
wget -O - https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform
```

### Verify installation (must run after installation)
```bash
terraform version
# Expected output example:
# Terraform v1.10.x
# on windows_amd64
```

> **Note:** Terraform CLI version and Google provider version are independent. You can have Terraform v1.10 with Google provider v5.x or v6.x — do not confuse the two.

---

## Key Concepts

| Concept | Description |
|---|---|
| **Provider** | A plugin that Terraform uses to interact with a cloud or API (e.g., `hashicorp/google`). |
| **Resource** | A specific piece of infrastructure (e.g., a GCS bucket, a Cloud Run service). |
| **Variable** | An input value that parameterises your configuration. |
| **Output** | A value exported from your configuration for use by other modules or for display. |
| **State** | A JSON file (`.tfstate`) recording the real-world resources Terraform manages. |
| **Module** | A reusable group of Terraform files encapsulating a set of resources. |
| **Backend** | Where state is stored (local by default; remote backends: GCS, Terraform Cloud). |

---

## Authentication with ADC

When using the Google provider for local development, Terraform uses **Application Default Credentials**. No explicit credentials block is needed.

```bash
# Authenticate via gcloud for local Terraform use
gcloud auth application-default login

# (Optional) Set a quota project if required
gcloud auth application-default set-quota-project PROJECT_ID
```

If running in CI/CD or from a service account, set:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

> **Security:** Never store service account JSON key files in your Terraform configuration directory or commit them to version control.

---

## Project Structure

A typical GCP Terraform project:
```
terraform-project/
├── providers.tf      # Terraform version and provider configuration
├── variables.tf      # Input variable declarations
├── main.tf           # Resource definitions
├── outputs.tf        # Output value declarations
├── terraform.tfvars  # Variable values (do NOT commit secrets here)
└── .gitignore        # Should ignore .tfstate, .tfstate.backup, .tfvars with secrets
```

---

## Complete Example: GCS Bucket on GCP

### `providers.tf`
```hcl
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"  # Pinned to 6.x; will not auto-upgrade to 7.x
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  # No 'credentials' block needed — uses ADC automatically
}
```

### `variables.tf`
```hcl
variable "project_id" {
  type        = string
  description = "GCP project ID"
}

variable "region" {
  type        = string
  description = "GCP region"
  default     = "us-central1"
}

variable "bucket_name" {
  type        = string
  description = "Globally unique name for the GCS bucket"
}
```

### `main.tf`
```hcl
resource "google_storage_bucket" "research_data" {
  name          = var.bucket_name
  location      = var.region
  force_destroy = false  # Prevents accidental deletion of non-empty buckets

  versioning {
    enabled = true
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 365  # Delete objects older than 365 days
    }
  }
}
```

### `outputs.tf`
```hcl
output "bucket_url" {
  description = "The URL of the created GCS bucket"
  value       = google_storage_bucket.research_data.url
}

output "bucket_name" {
  description = "The name of the created GCS bucket"
  value       = google_storage_bucket.research_data.name
}
```

### `terraform.tfvars` (do not commit if it contains secrets)
```hcl
project_id  = "PROJECT_ID"
region      = "us-central1"
bucket_name = "my-unique-research-bucket-name"
```

---

## The Standard Workflow

### 1. `terraform init`
Downloads the Google provider plugin and initialises the backend. **Run once per new directory or after changing providers.**
```bash
terraform init
# Output: Initializing provider plugins... Installing hashicorp/google v6.x.x
```

### 2. `terraform fmt`
Formats all `.tf` files in the directory to the canonical HCL style.
```bash
terraform fmt
```

### 3. `terraform validate`
Validates the configuration syntax and internal consistency **without** calling GCP APIs. Safe to run at any time.
```bash
terraform validate
# Output: Success! The configuration is valid.
```

### 4. `terraform plan`
Queries GCP APIs (using ADC) and generates an execution plan showing what will be **created, modified, or destroyed**. **No changes are applied.**
```bash
terraform plan
# Review the output carefully before applying
```

> **Safe validation:** Running `terraform plan` is safe. It reads existing state and calls read-only GCP APIs. It does not create, modify, or delete resources.

### 5. `terraform apply`
Executes the plan and provisions resources on GCP.
```bash
terraform apply
# Terraform displays the plan and prompts: Enter a value: yes
```

To apply without the interactive prompt (for CI/CD):
```bash
terraform apply -auto-approve
```

### 6. `terraform destroy`
Destroys all resources managed by the current configuration.
```bash
terraform destroy
# Prompts for confirmation before proceeding
```

> **Caution:** `terraform destroy` is destructive and irreversible for non-versioned data. Always review the plan output.

---

## Provider Version Pinning and Upgrades

```hcl
# Pin to a minor version (allows patch updates)
version = "~> 6.0"    # Allows 6.0.x, 6.1.x, but NOT 7.x

# Pin to an exact version
version = "= 6.12.0"

# Allow major updates (not recommended for production)
version = ">= 6.0"
```

To upgrade the provider:
```bash
terraform init -upgrade
```

---

## State Management

- State is stored in `terraform.tfstate` (local by default).
- For team use, store state remotely in a **GCS bucket backend**:
  ```hcl
  terraform {
    backend "gcs" {
      bucket = "my-tf-state-bucket"
      prefix = "terraform/state"
    }
  }
  ```
- **Never edit `.tfstate` by hand.**
- **Add `.tfstate` and `.tfstate.backup` to `.gitignore`.**

---

## Secrets and Security

- Do not put secrets in `.tf` files or `terraform.tfvars` committed to version control.
- Use the `sensitive = true` attribute on sensitive variables and outputs:
  ```hcl
  variable "db_password" {
    type      = string
    sensitive = true
  }
  ```
- Use environment variables to pass secrets:
  ```bash
  export TF_VAR_db_password="my-secret-password"
  ```
- For GCP, prefer Secret Manager over environment variables for production secrets.

---

## Common Errors and Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `Error: Provider produced inconsistent result` | Race condition or provider bug | Run `terraform apply` again |
| `Error: insufficient permission` | ADC account lacks required IAM role | Grant the required role; re-run `plan` |
| `Error: Resource already exists` | Resource created outside Terraform | Use `terraform import` to bring it under management |
| `Error: Invalid provider version` | Version constraint not satisfied | Update `required_providers` or run `terraform init -upgrade` |
| `State lock timeout` | Another process holds the lock | Wait or manually unlock: `terraform force-unlock LOCK_ID` |

---

## Safely Validating Without Creating Resources

```bash
# 1. Validate syntax only (no API calls)
terraform validate

# 2. Preview changes without applying
terraform plan

# 3. Use -target to plan/apply only specific resources
terraform plan -target=google_storage_bucket.research_data
```

---

## Official References
- Terraform documentation: https://developer.hashicorp.com/terraform/docs
- Terraform install: https://developer.hashicorp.com/terraform/install
- Google provider docs: https://registry.terraform.io/providers/hashicorp/google/latest/docs
- GCS bucket resource: https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/storage_bucket
- Using Terraform with Google Cloud: https://cloud.google.com/docs/terraform
- Remote backend (GCS): https://developer.hashicorp.com/terraform/language/backend/gcs
