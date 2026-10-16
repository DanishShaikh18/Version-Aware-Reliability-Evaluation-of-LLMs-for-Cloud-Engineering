
from google import genai
from google.genai import types
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini

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
        "You are a helpful cloud engineering assistant. "
        "Answer clearly and concisely. "
        "Do not invent APIs or parameters. "
        "If unsure, say so."
    ),
    generate_content_config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(
            thinking_level="MINIMAL"
        ),
        max_output_tokens=512,
    ),
)
