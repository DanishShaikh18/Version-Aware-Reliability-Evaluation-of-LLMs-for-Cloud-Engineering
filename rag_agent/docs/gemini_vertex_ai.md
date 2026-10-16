# Gemini on Vertex AI: Models, SDK, and Agent Integration

## Metadata
- **Last verified:** 2026-10-16
- **Official sources:**
  - https://cloud.google.com/vertex-ai/generative-ai/docs/overview
  - https://googleapis.github.io/python-genai/
  - https://pypi.org/project/google-genai/
  - https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/gemini
  - https://google.github.io/adk-docs/
- **SDK versions verified (in this project's venv):**
  - `google-genai` **2.31.0** (installed: 2026-10-16)
  - `google-adk` **2.12.0** (installed: 2026-10-16)

---

## Concepts and Terminology

| Term | Meaning |
|---|---|
| **Gemini** | Family of Google multimodal language models (text, image, audio, code). |
| **Vertex AI** | Google Cloud's managed ML platform that hosts Gemini and other models. |
| **Gemini API (Vertex AI)** | The REST and gRPC API endpoint for Gemini on Vertex AI, accessed via the `google-genai` SDK. |
| **Gemini API (AI Studio)** | A separate endpoint using API keys; not Vertex AI; not used in this project. |
| **`google-genai` SDK** | The unified Python library for Gemini, supporting both Vertex AI and AI Studio endpoints. |
| **`google-adk` SDK** | Agent Development Kit — builds agents that can use Gemini via `LlmAgent`. |
| **Model ID** | A specific string identifying a model version (e.g., `gemini-2.5-flash`). Must be verified for your project and region. |

**This project uses Vertex AI via ADC (Application Default Credentials), not API keys.**

---

## Prerequisites

1. **Google Cloud project** with billing enabled.
2. **Vertex AI API enabled:**
   ```bash
   gcloud services enable aiplatform.googleapis.com
   ```
3. **ADC configured:**
   ```bash
   gcloud auth application-default login
   gcloud config set project PROJECT_ID
   ```
4. **IAM permissions** — your principal needs at minimum:
   - `roles/aiplatform.user` (to call models)
5. **SDK installed:**
   ```bash
   pip install google-genai>=2.31.0
   ```

---

## Model IDs and Availability

> **Important:** Model availability depends on your GCP project, region, billing status, and quota. Never assume a model is available because its ID appears in documentation or code examples. Always verify against your own project.

### Model IDs referenced in this project's PLAN.md
- `gemini-3.5-flash` — referenced in PLAN.md and used in `base_agent/agent.py`.
- `gemini-3.8-flash` — referenced in PLAN.md as an alternative.

### How to verify available models (from official docs, untested on this machine)
```bash
# List available models in your project and region via gcloud (if supported)
gcloud ai models list --region=REGION

# Or via the Gen AI SDK (Python):
# client.models.list() — refer to SDK docs for current method signature
```

Access and availability are **project-dependent**. If a model call returns a `404` or `403`, verify:
- The API is enabled.
- The project has the required quota.
- The model ID is correct and available in the selected `location`.

---

## Making a Basic Request with the Google Gen AI SDK

### Vertex AI client configuration (using ADC)

```python
from google import genai
from google.genai import types

# Configure for Vertex AI — uses ADC automatically
client = genai.Client(
    vertexai=True,
    project="PROJECT_ID",   # Replace with your GCP project ID
    location="us-central1", # Or the region where the model is available
)

# Generate content
response = client.models.generate_content(
    model="gemini-3.5-flash",  # Verify this model ID is available in your project
    contents="What is Cloud Run and when should I use it?",
    config=types.GenerateContentConfig(
        temperature=0.2,
        max_output_tokens=512,
    ),
)

print(response.text)
```

> **Note on `enterprise=True` vs `vertexai=True`:** Our `base_agent/agent.py` uses `enterprise=True`. The parameter accepted by `genai.Client` depends on the installed SDK version. As of `google-genai==2.31.0`, `vertexai=True` is the documented approach. If your agent uses a project-specific `enterprise=True`, verify it against the version you have installed.

### Alternative: Configure via environment variables (no code change needed)
```bash
export GOOGLE_GENAI_USE_VERTEXAI=true
export GOOGLE_CLOUD_PROJECT="PROJECT_ID"
export GOOGLE_CLOUD_LOCATION="us-central1"
```
Then in Python:
```python
from google import genai
client = genai.Client()  # ADC and Vertex AI are picked up from environment
response = client.models.generate_content(
    model="gemini-3.5-flash",
    contents="Hello from Vertex AI!",
)
print(response.text)
```

---

## Generation Configuration

```python
from google.genai import types

config = types.GenerateContentConfig(
    temperature=0.2,          # 0.0 = deterministic, 1.0 = more creative
    max_output_tokens=1024,   # Maximum tokens in the response
    top_p=0.95,               # Nucleus sampling parameter
    top_k=40,                 # Top-k sampling parameter
    # candidate_count=1,      # Number of response candidates
)
```

**Latency considerations:**
- Larger `max_output_tokens` increases latency and cost.
- Thinking/reasoning controls (if supported by the model version) increase latency significantly.
- Measure end-to-end latency in your evaluation scripts; do not rely on estimated values.

---

## Error Handling

```python
from google.api_core import exceptions as google_exceptions

try:
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents="Explain VPC firewall rules.",
    )
    print(response.text)
except google_exceptions.PermissionDenied as e:
    print(f"Permission denied: {e}. Check IAM roles and API enablement.")
except google_exceptions.NotFound as e:
    print(f"Model or resource not found: {e}. Verify model ID and region.")
except google_exceptions.ResourceExhausted as e:
    print(f"Quota exceeded: {e}. Check your Vertex AI quota.")
except Exception as e:
    print(f"Unexpected error: {e}")
```

---

## Safety and Responsible API Usage

- Gemini responses may be blocked by safety filters. Check `response.prompt_feedback` if the response is empty.
- Do not attempt to bypass safety filters in production systems.
- For research tasks, log all prompts and responses to enable auditing.
- Safety settings can be adjusted within the limits documented at:
  https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/configure-safety-attributes

---

## Using Gemini from a Google ADK `LlmAgent`

The `base_agent/agent.py` in this project uses ADK's `Gemini` model wrapper:

```python
from google import genai
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini

# Build the Vertex AI client
client = genai.Client(
    enterprise=True,          # Project-specific parameter — verify against your SDK version
    project="project-garden-505118",
    location="global",
)

# Wrap in the ADK Gemini adapter
vertex_model = Gemini(
    model="gemini-3.5-flash",
    client=client,
)

# Create the agent
root_agent = LlmAgent(
    name="base_cloud_agent",
    model=vertex_model,
    instruction=(
        "Answer cloud engineering questions clearly and accurately. "
        "Do not invent APIs or parameters. "
        "If you are unsure, clearly say so."
    ),
)
```

### Alternative: Pass model ID directly (if your ADK version supports it)
```python
root_agent = LlmAgent(
    name="base_cloud_agent",
    model="gemini-3.5-flash",  # ADK resolves via environment or ADC
    instruction="Answer cloud engineering questions clearly.",
)
```

Always verify the constructor signature against your installed ADK version (`google-adk==2.12.0`).

---

## Token Usage and Cost Awareness

- Vertex AI bills per **input token** and **output token** (pricing varies by model).
- Use `response.usage_metadata` (if available) to log token counts in your evaluation scripts.
- Keep prompts concise. Unnecessary context in RAG documents increases token cost.
- Check current pricing at: https://cloud.google.com/vertex-ai/generative-ai/docs/pricing

---

## Version-Specific Notes

- **Model IDs change over time.** `gemini-3.5-flash` and `gemini-3.8-flash` are the model IDs referenced in PLAN.md (2026-10). Verify these IDs are still current when running experiments.
- **`enterprise=True` vs `vertexai=True`:** These client constructor parameters may differ across SDK versions. Always check the SDK changelog and installed version.
- **Deprecated:** The `google-cloud-aiplatform` library's older Generative AI client (`vertexai.generative_models`) is the previous approach; the unified `google-genai` library is now preferred for new projects.

---

## Official References
- Vertex AI Generative AI overview: https://cloud.google.com/vertex-ai/generative-ai/docs/overview
- Google Gen AI SDK (Python): https://googleapis.github.io/python-genai/
- Gen AI SDK on PyPI: https://pypi.org/project/google-genai/
- Gemini model reference: https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/gemini
- ADK documentation: https://google.github.io/adk-docs/
- Safety attributes: https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/configure-safety-attributes
