# PLAN.md --- Version-Aware Reliability Evaluation of LLMs for Cloud Engineering

**Project type:** MCA research project + working demonstration\
**Working title:** *Version-Aware Reliability Evaluation of LLMs for
Cloud Engineering: A Comparative Study of Base LLM, RAG, SFT, and RAFT*\
**Initial implementation target:** Working Base LLM and RAG agents in
Google ADK Web\
**Research principle:** Build the demo first, then develop the dataset,
training pipeline, and controlled evaluation. Do not present
placeholders as completed methods or results.

------------------------------------------------------------------------

## 1. Project in Plain Language

We are studying whether giving an AI the right documentation and
training helps it produce more accurate cloud-related answers and
code---especially when documentation is outdated, contradictory, or
contains irrelevant information.

In simple terms, we will ask the same cloud engineering questions to
four versions of an AI and measure which one gets the answer right more
often, follows the correct documentation version, and responds
efficiently.

**We are not claiming to invent RAFT.** Our research contribution will
be our own cloud-focused test set, controlled comparisons, evaluation
method, and analysis of where each approach succeeds or fails.

## 2. Problem Statement

AI models can generate useful cloud guidance and code, but their answers
may: - use an API or parameter that does not exist in the requested
version; - follow outdated documentation; - be distracted by irrelevant
retrieved material; - fail to notice that two documents disagree; -
produce code that looks plausible but does not parse, validate, or meet
the task requirements.

Retrieval-Augmented Generation (RAG) gives a model relevant documents at
answer time. Supervised Fine-Tuning (SFT) trains a model on examples.
Retrieval-Augmented Fine-Tuning (RAFT) trains a model to answer using
relevant documents while learning to ignore distractor documents. The
project tests these approaches under the same tasks and evaluation
conditions.

## 3. Research Questions

**RQ1.** How accurately does a base model answer cloud engineering
questions without supplied documentation?

**RQ2.** Does retrieving relevant documentation improve answer and code
correctness?

**RQ3.** How does irrelevant or contradictory documentation affect each
approach?

**RQ4.** Does fine-tuning improve reliability, and does RAFT reduce the
negative effect of distractor documents compared with ordinary RAG?

**RQ5.** Do the results differ between documentation-grounded questions,
Python cloud SDK code, and Terraform/HCL tasks?

These questions are deliberately testable. The project will report
measured results, including cases where an expected improvement does not
occur.

## 4. Scope

### 4.1 Initial domain

The first benchmark will focus on **Google Cloud (GCP) engineering**,
using version-labelled official documentation and a small set of
well-defined tasks.

Planned task categories:

1.  **Documentation-grounded cloud Q&A** --- explain a cloud feature,
    configuration choice, or API behavior using supplied evidence.
2.  **Python cloud SDK/API code** --- generate small code snippets using
    a specified library/API version.
3.  **Terraform/HCL** --- generate or correct small infrastructure
    configurations using a specified provider/version.

Kubernetes manifests, GitHub Actions, and other cloud platforms may be
added as extensions only after the core benchmark works. Do not attempt
to cover every cloud product and platform in the first experiment.

### 4.2 Out of scope for the first prototype

-   Deploying generated infrastructure to a live cloud project.
-   A large production-ready web application.
-   A complicated multi-agent workflow.
-   Fine-tuning before the initial prototype is demonstrated.
-   Claiming that a response is correct solely because it sounds
    confident or provides a convincing explanation.

All code validation should run locally or in a safe, isolated test
environment. Never run generated infrastructure changes against a real
project as part of the basic evaluation.

## 5. Research Design

The eventual comparison has four experimental arms. They must answer the
same benchmark questions and use the same base model family/checkpoint
wherever technically possible.

  -----------------------------------------------------------------------
  Arm                     Method                  What it receives at
                                                  inference time
  ----------------------- ----------------------- -----------------------
  **A --- Base LLM**      Prompt the model        Task/question and fixed
                          without retrieved       instructions
                          project documents       

  **B --- RAG**           Retrieve relevant       Task/question +
                          documentation and place retrieved evidence
                          it in the prompt        

  **C --- SFT**           Model fine-tuned on     Task/question and fixed
                          curated                 instructions; no
                          instruction/output      retrieval unless
                          examples                explicitly specified in
                                                  a separate experiment

  **D --- RAFT**          Model fine-tuned on     Task/question +
                          examples containing     inference-time evidence
                          relevant evidence and   according to the frozen
                          distractors             protocol
  -----------------------------------------------------------------------

**Fair-comparison rule:** Keep the benchmark questions, task
requirements, model settings, and scoring rules fixed. Record any
unavoidable difference. Do not silently compare different model families
and attribute all differences to RAG, SFT, or RAFT.

**Important terminology:** RAFT training examples use a question,
relevant document(s), distractor document(s), and a target answer
grounded in the relevant evidence. At evaluation time, specify and keep
consistent how retrieved evidence is supplied. The study will
distinguish irrelevant-document robustness from genuine conflict
resolution; they are related but not identical.

## 6. Hypotheses to Test

These are hypotheses, not promised outcomes.

-   **H1:** RAG will improve some correctness measures over the base
    model when the needed information is available in the supplied
    documentation.
-   **H2:** Adding irrelevant retrieved documents may reduce RAG
    performance on at least some tasks.
-   **H3:** RAFT may degrade less than standard RAG as distractor noise
    increases.
-   **H4:** SFT and retrieval-based approaches may show different
    strengths: for example, learned output patterns versus
    version-specific evidence use.
-   **H5:** The size and direction of these effects may differ by task
    type and documentation condition.

A valid finding can be that an approach helps only in certain conditions
or fails to improve performance. Do not invent results or claim
statistical significance without suitable analysis.

## 7. Implementation Strategy: Prototype First

### Stage 0 --- Demonstrate a working skeleton

**Immediate milestone:** Make Base LLM and RAG independently runnable in
ADK Web. Use a tiny sample document set. Keep the code short and easy to
explain.

-   Create a Python virtual environment.
-   Configure Google Cloud authentication.
-   Create a Base agent using `LlmAgent`.
-   Create a RAG agent using `LlmAgent` plus a small local-document
    retrieval function/tool.
-   Run both through the ADK Web interface and switch between the
    available agent apps.
-   Inspect responses, tool events, and traces.
-   Add a basic timing wrapper or event-based measurement for end-to-end
    latency.
-   Create SFT and RAFT app placeholders only if useful for
    demonstrating the planned architecture. Label them **not implemented
    yet** until they actually use tuned models.

This stage is a working prototype, not the completed research
experiment.

### Stage 1 --- Freeze a small pilot benchmark

Create approximately 20--30 manually checked pilot tasks across the
initial task categories. The number is an initial planning target, not a
final sample-size claim.

Each task should record: - stable task ID; - task category; - user
prompt and explicit requirements; - requested product/library/provider
version; - authoritative source URL and version/date; - expected answer
facts or expected code behavior; - known invalid/deprecated patterns
where relevant; - relevant documents; - distractor documents and
condition; - scoring rubric and validator; - notes explaining the
expected result.

Run the Base and RAG agents against the same pilot tasks. Use the pilot
to find broken prompts, retrieval errors, and scoring problems before
scaling up.

### Stage 2 --- Build the research dataset

Expand the pilot into a curated, version-labelled benchmark. The final
size will be decided after a feasibility pilot and documented in the
methodology.

Prepare distinct conditions: 1. **Clean evidence:** relevant
documentation only. 2. **Distractor noise:** relevant documentation plus
controlled irrelevant documents. 3. **Version conflict:** documents
disagree, and the task identifies the target version or the evidence
hierarchy needed to resolve the disagreement. 4. **Deprecation/version
adherence:** an older pattern is present, but the task asks for a
specific newer version, or vice versa. 5. **Missing/insufficient
evidence:** the correct behavior may be to state uncertainty or ask for
clarification rather than invent details.

Do not label an older API as "wrong" merely because it is old. It is
wrong only relative to the requested target version or task
requirements.

### Stage 3 --- Implement evaluation before large-scale training

Build task-specific, reproducible checks. The evaluator---not the
model's own explanation---decides whether the output passes.

-   Python: parse/AST checks, expected imports and API usage, unit tests
    or safe mocked tests where feasible.
-   Terraform/HCL: syntax/format validation and provider/schema
    validation where the required tooling is available; no live apply.
-   Documentation Q&A: predefined expected facts, source support,
    version correctness, and a human-reviewed rubric for ambiguous
    cases.
-   Conflict task: score whether the output selects the correct
    version/evidence or appropriately reports the conflict.

AST similarity alone is not proof of semantic correctness. A
syntactically valid snippet can still use the wrong API or fail the
task.

### Stage 4 --- Prepare SFT and RAFT

After the benchmark and scoring pipeline are stable: - curate
instruction/output examples for SFT; - create RAFT examples with
relevant evidence, realistic distractors, and target answers; - split
train/validation/test by task/source groups to reduce leakage; - check
for near-duplicate questions and documents across splits; - document the
exact training recipe and model revision; - run a small feasibility
pilot before committing to a larger training run.

**Primary model strategy:** Use one compatible model checkpoint for the
four arms if possible. Free Colab GPU is the initial training option,
but feasibility is not assumed. If the chosen model cannot be trained
reliably, reduce model size or use a documented alternative. Do not mix
a Gemini API model in one arm and a separately trained open-weight model
in another and then attribute the difference solely to the method.

Gemini may be used for the initial ADK prototype. Whether the eventual
SFT/RAFT arms can be implemented on the same model family must be
decided before the final comparison. If that is not feasible, define a
narrower fair comparison rather than pretending the arms are equivalent.

### Stage 5 --- Run the controlled experiment

-   Freeze prompts, model identifiers/revisions, retrieval settings,
    dataset, and scoring code.
-   Run all applicable arms on the same test tasks.
-   Save raw outputs, retrieved document IDs, configuration, timestamps,
    latency, token/cost metadata when available, and validator outcomes.
-   Repeat runs when model nondeterminism or service behavior makes a
    single run unreliable; record the number of repetitions and
    generation settings.
-   Analyze overall results and results by task category and evidence
    condition.
-   Manually inspect representative successes and failures.
-   Report limitations and failed hypotheses.

### Stage 6 --- Paper and final demonstration

Deliver: - a working ADK Web prototype; - the benchmark and dataset
documentation; - reproducible evaluation scripts and configuration; -
comparison tables and charts; - failure-case analysis; - a research
paper describing methodology, results, limitations, and conclusions.

## 8. Google ADK and Vertex AI Setup

### 8.1 Role of ADK

ADK is the agent interface and execution framework for the prototype.
ADK Web provides a convenient chat playground for running and inspecting
agents. We will use its app/agent selection workflow to compare the Base
and RAG implementations.

ADK traces and events can help inspect model calls and tool usage. They
do **not** replace the research evaluator. Correctness, version
adherence, distractor robustness, and the final benchmark metrics will
be calculated by our own evaluation code.

### 8.2 Vertex AI authentication

The project already has a Google Cloud project: `project-garden-505118`.

Use Application Default Credentials (ADC) or the supported Google Cloud
authentication method for the installed SDK. A Gemini API key should not
be needed when the client is configured for the appropriate
Vertex/enterprise endpoint and ADC is set up correctly. However, ADC
alone does not guarantee access: the required API must be enabled,
billing/quota must be available, and the signed-in identity must have
appropriate permissions.

Keep credentials out of source control. Do not commit service-account
keys, access tokens, or `.env` secrets.

Example configuration based on the current intended approach (confirm
the exact SDK version and constructor parameters in the installed
environment):

``` python
from google import genai
from google.adk.models.google_llm import Gemini
from google.adk.agents import LlmAgent

client = genai.Client(
    enterprise=True,
    project="project-garden-505118",
    location="global",
)

vertex_model = Gemini(
    model="gemini-3.5-flash",
    client=client,
)

root_agent = LlmAgent(
    name="base_cloud_agent",
    model=vertex_model,
    instruction=(
        "Answer cloud engineering questions clearly. "
        "If you are unsure about a version-specific detail, say so. "
        "Do not invent APIs, parameters, or documentation sources."
    ),
)
```

This is an illustrative starting point, not a guarantee that every SDK
version exposes exactly these imports and arguments. Verify it against
the installed ADK and Google Gen AI SDK versions.

### 8.3 Model selection

Potential Gemini model IDs to test in the environment: -
`gemini-3.5-flash` - `gemini-3.8-flash`

Both model IDs appear in current Google documentation. Choose one for
the prototype based on actual access, latency, cost/quota, and observed
performance. For a fair comparison of prompting versus retrieval in the
prototype, keep the same Gemini model and generation settings in both
agents.

**Research limitation:** Gemini API access and model choice do not
automatically provide a matching trainable SFT/RAFT checkpoint. The
final fine-tuning plan must be checked separately. Do not assume the
Gemini model used for the demo can be fine-tuned using the same
LoRA/QLoRA workflow as an open-weight model.

### 8.4 ADK Web execution

Use the ADK Web command supported by the installed package (commonly
`adk web`) from the project root or its parent directory as required by
the app-discovery setup. Confirm the current command and app-folder
layout from the installed ADK version. The interface is for interactive
demonstration; evaluation should also be runnable in a repeatable batch
mode.

## 9. Proposed Simple Folder Structure

Prefer separate, discoverable ADK app folders so the Web interface can
list/switch between apps. Keep the first version small.

``` text
cloud-raft/
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
├── PLAN.md
├── base_agent/
│   ├── __init__.py
│   └── agent.py
├── rag_agent/
│   ├── __init__.py
│   ├── agent.py
│   ├── retrieval.py
│   └── docs/
│       └── sample_gcp_docs.md
├── sft_agent/
│   ├── __init__.py
│   └── agent.py
├── raft_agent/
│   ├── __init__.py
│   └── agent.py
├── data/
│   ├── pilot_tasks.jsonl
│   └── README.md
├── evaluation/
│   ├── run_eval.py
│   ├── metrics.py
│   └── validators.py
├── results/
│   └── .gitkeep
└── training/
    ├── prepare_sft_data.py
    ├── prepare_raft_data.py
    └── train_lora.py
```

Notes: - `sft_agent/` and `raft_agent/` may initially contain clearly
labelled placeholders, not fake tuned behavior. -
`rag_agent/retrieval.py` can start with simple local retrieval for the
demo. Replace it with a vector index (e.g., ChromaDB) only when the
dataset warrants it. - A database is not required for the first demo.
JSONL is enough for pilot tasks and results. Add SQLite later if
structured result querying becomes useful. - No separate custom backend
or frontend is required for the initial prototype; ADK Web provides the
interactive interface. - The evaluation scripts are still needed even
though there is no custom web backend.

## 10. RAG Method for the Prototype

Initial prototype: 1. Store a small number of sample GCP documentation
excerpts in local files. 2. Implement a simple retrieval function that
returns the most relevant excerpt(s) for a query. 3. Pass the retrieved
excerpts, with source labels, to the RAG agent. 4. Instruct the model to
ground version-specific answers in the supplied evidence and admit when
evidence is insufficient. 5. Show the response and inspect
retrieval/tool events in ADK Web.

Later research version: - use official, version-labelled sources; -
choose and document chunking, embedding model, retrieval method, top-k,
and filtering; - preserve source URL, product/version, date, and chunk
ID; - measure retrieval quality separately where possible; - freeze
retrieval settings before the test set is scored.

The Base agent must not receive the RAG documents invisibly. The
difference between arms must be explicit and recorded.

## 11. Evaluation Metrics

Use the same definitions for all arms where a metric applies. Report
denominators and missing/invalid outputs clearly.

  -----------------------------------------------------------------------
  Metric                  What it measures        Evaluation method
  ----------------------- ----------------------- -----------------------
  **Task success /        Percentage of tasks     Task-specific rubric
  correctness rate**      satisfying predefined   and validators
                          requirements            

  **Syntax/parse          Whether generated       Python parser;
  success**               code/configuration      HCL/Terraform
                          parses                  parser/formatter where
                                                  available

  **API/schema validity** Whether the required    Version-aware rules,
                          API names, parameters,  mocks, schemas, or safe
                          or provider schema are  tests
                          valid for the target    
                          version                 

  **Version adherence**   Whether output follows  Version-specific
                          the requested version   expected checks
                          and avoids incompatible 
                          deprecated patterns     

  **Evidence support**    Whether factual claims  Citation/source
                          are supported by the    matching and human
                          supplied authoritative  audit for ambiguous
                          evidence                cases

  **Hallucinated API      Frequency of            Predefined invalid-API
  rate**                  unsupported or          rules; report exact
                          nonexistent API usage   denominator

  **Distractor            Change in performance   Compare clean-evidence
  degradation**           as irrelevant material  score with
                          is added                noisy-evidence score

  **Conflict handling**   Whether output resolves Labelled conflict cases
                          or explicitly reports a and precision/recall/F1
                          true documentation      if outputs include a
                          conflict appropriately  conflict decision

  **Latency**             End-to-end time for     Consistent timer around
                          each response           the run; report median
                                                  and spread

  **Cost/token usage**    Resource use when       Provider usage metadata
                          available               and pricing
                                                  snapshot/date
  -----------------------------------------------------------------------

Do not collapse all metrics into one score without a justified weighting
scheme. Present primary correctness metrics separately from supporting
metrics such as latency.

## 12. Experimental Controls and Data Quality

To make the research defensible: - Use a fixed test set that is not used
to train the SFT/RAFT models. - Keep train, validation, and test data
separated by source/task groups where possible. - Prevent near-duplicate
question/document leakage across splits. - Record source URLs, retrieval
settings, document versions, model IDs, prompts, and run timestamps. -
Use the same task instructions and comparable output limits across
arms. - Use a fixed set of test conditions and document how distractors
were selected. - Make expected answers and scoring rules before
inspecting model outputs where possible. - Keep raw model outputs so the
results can be audited. - Track failures rather than silently discarding
them. - If human scoring is used, define the rubric and preserve
reviewer decisions. - Report uncertainty and variation. Do not claim
statistical significance without an appropriate test and sufficient
observations.

## 13. What Counts as the Research Contribution?

The contribution is **not** "we invented RAFT." RAFT is an existing
method. Our intended contribution is to: 1. Build a documented,
version-aware benchmark for selected cloud engineering tasks. 2. Compare
Base, RAG, SFT, and RAFT under controlled evidence conditions. 3.
Measure correctness, version adherence, API hallucinations, distractor
degradation, conflict handling, and latency. 4. Analyze concrete failure
cases and identify which method helps under which conditions. 5. Provide
reproducible task data, evaluation code, and a transparent methodology.

A literature review is required before claiming that this exact
benchmark or comparison is novel. The paper should describe the
contribution precisely and acknowledge related RAFT and
infrastructure-as-code research.

## 14. Expected Deliverables

### Prototype deliverables

-   [ ] ADK Web launches successfully.
-   [ ] Base agent answers cloud questions.
-   [ ] RAG agent retrieves sample documentation and uses it in its
    answer.
-   [ ] User can switch between the Base and RAG app entries in ADK Web.
-   [ ] Agent events/tool calls can be inspected.
-   [ ] Latency is recorded for test runs.
-   [ ] SFT and RAFT are clearly marked as future work until genuinely
    implemented.

### Research deliverables

-   [ ] Literature review and refined research gap.
-   [ ] Version-labelled pilot and final benchmark.
-   [ ] Reproducible dataset split and run configuration.
-   [ ] SFT and RAFT training data and training record, if feasible.
-   [ ] Task-specific evaluation scripts.
-   [ ] Results tables, plots, and failure analysis.
-   [ ] Final paper with limitations and reproducibility details.

## 15. Risks and Mitigations

  -----------------------------------------------------------------------
  Risk                                Mitigation
  ----------------------------------- -----------------------------------
  Fine-tuning is too expensive or     Run a small feasibility test early;
  unreliable on free Colab            reduce model size or revise scope
                                      transparently

  Gemini model is not available to    Verify access and quota before
  the project/region/endpoint         building around it; keep the model
                                      ID configurable

  Gemini cannot be trained in the     Use Gemini for the demo and select
  desired way                         a compatible open-weight model for
                                      a separate, clearly defined
                                      training experiment; do not claim a
                                      direct same-model four-arm
                                      comparison

  Prototype is mistaken for completed Label sample data, placeholders,
  research                            and preliminary observations
                                      clearly

  Too many cloud technologies make    Start with GCP Q&A, Python SDK/API,
  the study unmanageable              and small Terraform/HCL tasks; add
                                      Kubernetes/GitHub only if time
                                      permits

  LLM judge scores are inconsistent   Prefer deterministic checks for
                                      syntax/schema; use a documented
                                      human rubric for ambiguous semantic
                                      cases

  Retrieved documents are outdated or Preserve source URL, version/date,
  mislabeled                          and benchmark metadata

  Conflicting documents have no clear Define target-version and
  resolution rule                     source-authority rules before
                                      evaluation
  -----------------------------------------------------------------------

## 16. Immediate Build Order

1.  Create the virtual environment and install compatible ADK + Google
    Gen AI packages.
2.  Verify ADC, project access, API enablement, billing/quota, and one
    model call.
3.  Implement the Base `LlmAgent`.
4.  Implement the RAG `LlmAgent` with a tiny local sample-document
    retrieval tool.
5.  Launch ADK Web and verify app selection/switching.
6.  Capture sample runs and latency.
7.  Add a small JSONL pilot task set and a repeatable evaluation script.
8.  Only after the prototype is stable, expand the dataset and decide
    the compatible SFT/RAFT training model.
9.  Run the full controlled experiment and write the paper from actual
    results.

## 17. Definition of "Done"

The project is complete when it has: - a reproducible demonstration of
the selected approaches; - a documented and version-aware benchmark; - a
fair experimental comparison with task-specific evaluation; - recorded
outputs and measurable results; - a transparent discussion of failures,
limitations, and the research contribution; - a paper whose claims are
supported by the experiments.

**The prototype proves that the system can run. The benchmark and
experiments provide the research evidence. Both are necessary, and they
are not the same thing.**

## 18. Technical References to Verify During Implementation

-   ADK documentation: https://google.github.io/adk-docs/
-   ADK manual workflow / Web playground:
    https://google.github.io/agents-cli/guide/hands-on-tutorial/
-   Gemini 3.5 Flash documentation:
    https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/guides/gemini-3-5-flash
-   Gemini 3.8 Flash documentation:
    https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/guides/gemini-3-8-flash
-   Vertex AI / Gemini quickstart:
    https://docs.cloud.google.com/vertex-ai/generative-ai/docs/start/quickstart

These references confirm documented product/model names at the time this
plan was prepared; actual project access, SDK signatures, quota,
billing, and availability must still be tested in the user's
environment.
