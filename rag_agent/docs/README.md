# RAG Agent Documentation Knowledge Base

**Project:** Version-Aware Reliability Evaluation of LLMs for Cloud Engineering  
**Purpose:** Local documentation knowledge base for the RAG agent retrieval pipeline.  
**Last updated:** 2026-10-16  

---

## Overview

This directory contains the knowledge base used by the RAG agent (`rag_agent/`). Each Markdown file covers one cloud engineering topic, sourced from official documentation. These files will be indexed and retrieved during research experiments.

All documents are written for **accurate retrieval** — they use descriptive headings, exact commands, version numbers, and source URLs. They are designed to support the research conditions described in PLAN.md, including clean evidence, distractor noise, and version-conflict experiments (planned for a later stage).

---

## Document Index

| File | Topic | When to retrieve |
|---|---|---|
| [`gcp_fundamentals.md`](gcp_fundamentals.md) | GCP resource hierarchy, IAM, service accounts, ADC, gcloud CLI | Questions about GCP structure, authentication, project setup, enabling APIs, gcloud commands |
| [`cloud_run.md`](cloud_run.md) | Cloud Run services, deploying Python from source, IAM, env vars, revisions | Questions about deploying applications to Cloud Run, `gcloud run deploy`, serverless compute |
| [`gemini_vertex_ai.md`](gemini_vertex_ai.md) | Gemini models on Vertex AI, Gen AI SDK, model IDs, generation config, error handling | Questions about Gemini API, model IDs, `google-genai` SDK usage, Vertex AI configuration |
| [`cloud_networking.md`](cloud_networking.md) | VPC, subnets, firewall rules, Cloud NAT, Private Google Access, DNS, load balancing | Questions about GCP networking, VPC configuration, firewall rules, subnet CIDRs, connectivity |
| [`terraform_gcp.md`](terraform_gcp.md) | Terraform IaC, Google provider, init/plan/apply workflow, state, ADC auth | Questions about Terraform, HCL configuration, Google provider, infrastructure provisioning |
| [`kubernetes.md`](kubernetes.md) | Kubernetes pods, deployments, services, kubectl, ConfigMaps, GKE | Questions about Kubernetes concepts, YAML manifests, kubectl commands, GKE-specific features |
| [`github_actions.md`](github_actions.md) | GitHub Actions workflows, Python CI, Workload Identity Federation, GCP auth | Questions about GitHub Actions, CI/CD pipelines, GCP authentication from GitHub, workflow syntax |
| [`cloud_apis_python.md`](cloud_apis_python.md) | Google Cloud client libraries, ADC, error handling, retries, pagination | Questions about calling GCP APIs from Python, authentication, IAM permissions, API errors |
| [`adk_python.md`](adk_python.md) | Google ADK, LlmAgent, adk web, tools, sessions, retrieval, latency | Questions about ADK, agent creation, tool integration, running agents, debugging |

---

## Retrieval Guidance for the RAG Agent

- **Retrieve by topic:** Match the user's question to the most relevant document using keyword or embedding similarity.
- **Retrieve by service name:** `Cloud Run`, `Vertex AI`, `Gemini`, `Terraform`, `Kubernetes`, `GitHub Actions`, `VPC`, `IAM`, `ADK`, `gcloud`.
- **Retrieve by task type:**
  - *Deploy an app* → `cloud_run.md`
  - *Call Gemini from Python* → `gemini_vertex_ai.md`, `adk_python.md`
  - *Terraform resource* → `terraform_gcp.md`
  - *Kubernetes manifest* → `kubernetes.md`
  - *CI/CD pipeline* → `github_actions.md`
  - *Networking / firewall* → `cloud_networking.md`
  - *Authenticate / IAM* → `gcp_fundamentals.md`, `cloud_apis_python.md`

---

## Version Tracking

Each document records a **last verified date** and the SDK/CLI versions verified at that time. When documentation is updated after a version change, update the `last verified` date and record the old version in a version note section.

Future research experiments will introduce **controlled version-conflict documents** as separate files — they will not replace the current accurate documentation.

---

## Not in This Knowledge Base

- Complete API references (link to official docs instead).
- Kubernetes and GitHub Actions are in scope for extension only — focus is on GCP/Gemini for the initial benchmark.
- No personal credentials, project-specific secrets, or access tokens.
- No invented or unverified commands.
