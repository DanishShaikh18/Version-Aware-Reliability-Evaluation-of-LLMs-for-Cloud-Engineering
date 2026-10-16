
from google import genai
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini

from .retrieval import search_cloud_docs


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
    name="rag_cloud_agent",
    model=vertex_model,
    instruction="""
You are a cloud engineering assistant using local documentation.

For questions about cloud services, APIs, installation, commands,
configuration, or versions, use the search_cloud_docs tool first.

Base documentation-dependent claims on the retrieved passages.
Include source filenames and section headings in your answer.
If the evidence is insufficient, say so instead of inventing details.
Do not claim a version or API is current unless the evidence supports it.

Answer clearly and concisely. Include practical commands or code
when the retrieved documentation supports them.
""",
    tools=[search_cloud_docs],
)
