# Google Agent Development Kit (ADK): Python Reference

## Metadata
- **Last verified:** 2026-10-16
- **Official sources:**
  - https://google.github.io/adk-docs/
  - https://adk.dev/
  - https://googleapis.github.io/python-genai/
- **Versions verified (in this project's venv):**
  - `google-adk` **2.12.0** (installed 2026-10-16)
  - `google-genai` **2.31.0** (installed 2026-10-16)
  - Python: **3.12**
  - gcloud CLI: **576.0.0**
- **This project:** `d:\cloud-raft`, GCP project `project-garden-505118`

---

## What Is ADK?

Google Agent Development Kit (ADK) is an open-source Python framework for building, running, and evaluating AI agents. It provides:
- `LlmAgent` — an LLM-powered reasoning agent.
- A CLI (`adk`) with a local web UI (`adk web`) for interactive development.
- Tool integration (Python functions, built-in tools, MCP servers).
- Session management, event tracing, and multi-agent support.

ADK is not the same as the Gen AI SDK (`google-genai`). ADK uses `google-genai` internally to call Gemini models.

---

## Installation

```bash
# Install into a virtual environment (recommended)
pip install google-adk>=2.12.0

# Verify installation
adk --version
# Expected: adk, version 2.12.0

# Verify the Python import
python -c "import google.adk; print(google.adk.__version__)"
```

---

## ADK App Discovery and File Structure

`adk web` discovers agents by looking for subdirectories containing `agent.py` and `__init__.py`.

```
cloud-raft/               ← Run `adk web .` from here
├── base_agent/
│   ├── __init__.py       ← Required: marks as a Python package; imports agent module
│   └── agent.py          ← Required: defines `root_agent`
├── rag_agent/
│   ├── __init__.py
│   └── agent.py
└── ...
```

### `__init__.py` (minimum content)
```python
from . import agent
```

### `agent.py` (minimum content)
```python
from google.adk.agents import LlmAgent

root_agent = LlmAgent(
    name="my_agent",
    model="gemini-2.5-flash",  # Or use the Gemini wrapper; see below
    instruction="You are a helpful assistant.",
)
```

> **ADK web discovers `root_agent`** — the variable must be named exactly `root_agent`.

---

## Creating a Minimal LlmAgent

### Option A: Pass model ID as a string (simpler)
```python
from google.adk.agents import LlmAgent

root_agent = LlmAgent(
    name="base_cloud_agent",
    model="gemini-3.5-flash",  # ADK resolves via environment or ADC
    instruction="Answer cloud engineering questions clearly.",
)
```

### Option B: Use the Gemini client wrapper (our existing base_agent approach)
```python
from google import genai
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini

# Build the Vertex AI client (uses ADC — no API key)
client = genai.Client(
    enterprise=True,              # Project-specific parameter — verify against your SDK
    project="project-garden-505118",
    location="global",
)

# Wrap in ADK's Gemini adapter
vertex_model = Gemini(
    model="gemini-3.5-flash",
    client=client,
)

# Create the agent
root_agent = LlmAgent(
    name="base_cloud_agent",
    model=vertex_model,
    instruction=(
        "You are a helpful cloud engineering assistant. "
        "Answer cloud-related questions clearly and accurately. "
        "Do not invent APIs or parameters. "
        "If you are unsure, clearly say so."
    ),
)
```

> **Note:** The `enterprise=True` parameter and `global` location are used in this project's `base_agent/agent.py`. Verify against the `google-genai==2.31.0` API. The standard Vertex AI configuration uses `vertexai=True` — check which parameter is supported in your installed version.

---

## Running ADK Web

```bash
# From the project root (where agent subdirectories are)
adk web .

# Or specify the path explicitly
adk web path/to/agents/dir

# With a specific port
adk web . --port 8080

# With verbose logging
adk web . --verbose
```

**Access the UI:** Open http://127.0.0.1:8000 in your browser.

**What you can do in ADK Web:**
- Switch between different agent apps (base_agent, rag_agent, etc.).
- Send messages to the agent and see responses.
- Inspect events, tool calls, and model requests in the trace panel.
- Measure latency from the UI or from event timestamps.

---

## Tools: Adding Functions to an Agent

ADK automatically converts Python functions into tools using their type hints and docstrings.

```python
from google.adk.agents import LlmAgent

def search_documentation(query: str) -> str:
    """
    Search the local cloud documentation knowledge base for relevant information.

    Args:
        query: The search query from the user.

    Returns:
        Relevant documentation excerpt as a string.
    """
    # Placeholder — replace with actual retrieval logic
    return f"[Search result for '{query}']: No documents indexed yet."


root_agent = LlmAgent(
    name="rag_cloud_agent",
    model="gemini-3.5-flash",
    instruction=(
        "You are a cloud engineering assistant. "
        "Use the search_documentation tool to find relevant documentation "
        "before answering questions about cloud services, APIs, or Terraform. "
        "Ground your answers in the retrieved evidence."
    ),
    tools=[search_documentation],  # Pass the function directly
)
```

ADK generates the JSON schema for `search_documentation` automatically from the type hints and docstring. The agent decides when to call it.

---

## Sessions and State

ADK manages conversation state within a **session**. Sessions are handled by the `Runner` and a session service.

```python
import asyncio
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

root_agent = LlmAgent(
    name="base_cloud_agent",
    model="gemini-3.5-flash",
    instruction="You are a helpful cloud engineering assistant.",
)

session_service = InMemorySessionService()
runner = Runner(
    agent=root_agent,
    app_name="base_agent",
    session_service=session_service,
)

async def run_agent(user_message: str, session_id: str = "session-001"):
    from google.genai import types as genai_types
    content = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=user_message)]
    )
    events = runner.run_async(
        user_id="user-001",
        session_id=session_id,
        new_message=content,
    )
    async for event in events:
        if event.is_final_response():
            print(event.content.parts[0].text)

if __name__ == "__main__":
    asyncio.run(run_agent("What is Cloud Run?"))
```

> **Note:** The `Runner` and `InMemorySessionService` API may differ across ADK versions. Always verify against the installed `google-adk==2.12.0` source or documentation.

---

## Events and Traces

Every interaction in ADK produces **events** — a structured log of what happened:
- `LlmRequestEvent`: The request sent to the model.
- `LlmResponseEvent`: The raw model response.
- `FunctionCallEvent`: A tool was called by the model.
- `FunctionResponseEvent`: The tool returned a result.
- `FinalResponseEvent`: The agent's final reply to the user.

In `adk web`, events appear in the trace panel for each conversation turn. You can inspect:
- Which model was called and with what parameters.
- What tool(s) were triggered and their inputs/outputs.
- Timestamps for latency measurement.

---

## Measuring Latency

For batch evaluation scripts (outside ADK web), wrap each agent call with timing:

```python
import time

start = time.perf_counter()
# ... run_agent(message)
end = time.perf_counter()
latency_ms = (end - start) * 1000
print(f"Latency: {latency_ms:.1f} ms")
```

In ADK web, latency is visible in event timestamps in the trace panel.

---

## Authentication and SDK Compatibility Problems

### Common issue: `UNAUTHENTICATED` or `PERMISSION_DENIED`
1. Verify ADC is set up: `gcloud auth application-default print-access-token`
2. Verify the project has the Vertex AI API enabled: `gcloud services list --enabled --filter="aiplatform"`
3. Verify the model ID is correct and available in your project/region.

### Common issue: `AttributeError: module 'google.adk' has no attribute ...`
- The ADK API changes across versions. Verify the import path against the installed version:
  ```bash
  python -c "import google.adk; help(google.adk)"
  ```

### Common issue: `No module named 'root_agent'` in `adk web`
- Ensure `__init__.py` exists in each agent directory and contains `from . import agent`.
- Ensure the variable in `agent.py` is named exactly `root_agent`.

### Common issue: Model not available
- The model string (e.g., `gemini-3.5-flash`) must be available in your project and region.
- Try a different region or verified model ID.
- This is project-dependent; access cannot be guaranteed from documentation alone.

---

## Adding a Retrieval Tool (for RAG agent)

A simple retrieval tool for the RAG agent uses keyword search over local Markdown files:

```python
import os
from google.adk.agents import LlmAgent

DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")

def retrieve_documentation(query: str) -> str:
    """
    Search local cloud documentation files for content relevant to the query.

    Args:
        query: A question or keyword to search for in the documentation.

    Returns:
        Concatenated excerpts from matching documentation files.
    """
    results = []
    query_lower = query.lower()

    if not os.path.isdir(DOCS_DIR):
        return "Documentation directory not found."

    for filename in os.listdir(DOCS_DIR):
        if not filename.endswith(".md"):
            continue
        filepath = os.path.join(DOCS_DIR, filename)
        with open(filepath, encoding="utf-8") as f:
            content = f.read()
        # Simple keyword matching — replace with embedding-based retrieval later
        if query_lower in content.lower():
            # Return first 500 characters of the matching file as an excerpt
            excerpt = content[:500]
            results.append(f"[Source: {filename}]\n{excerpt}\n")

    if not results:
        return "No relevant documentation found for this query."
    return "\n---\n".join(results[:3])  # Return top 3 matches


root_agent = LlmAgent(
    name="rag_cloud_agent",
    model="gemini-3.5-flash",
    instruction=(
        "You are a cloud engineering assistant. "
        "Always call the retrieve_documentation tool first when answering questions "
        "about cloud services, APIs, Terraform, Kubernetes, or GitHub Actions. "
        "Ground your answers in the retrieved evidence. "
        "If the retrieved documentation does not contain the answer, say so clearly."
    ),
    tools=[retrieve_documentation],
)
```

> This is a simple keyword-based retrieval. For the research experiment, replace with an embedding-based retriever (e.g., ChromaDB) when the benchmark dataset warrants it.

---

## Do Not Modify the Working Base Agent

The `base_agent/agent.py` is working and running via `adk web`. The RAG agent should be implemented independently in `rag_agent/agent.py`. Do not edit `base_agent/agent.py` to add retrieval.

---

## Official References
- ADK documentation: https://google.github.io/adk-docs/
- ADK on adk.dev: https://adk.dev/
- Google Gen AI SDK (Python): https://googleapis.github.io/python-genai/
- ADK on PyPI: https://pypi.org/project/google-adk/
