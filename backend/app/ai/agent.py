"""
LangChain agent with tools for satellite data Q&A.
Uses IBM Granite as the LLM backbone.
"""
import os
from typing import Optional
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain_core.prompts import PromptTemplate
from langchain_ibm import WatsonxLLM

from app.ingest.eonet import fetch_events
from app.store.db import get_event, list_insights


# ---------------------------------------------------------------------------
# Watsonx LLM (Granite)
# ---------------------------------------------------------------------------

def _build_llm() -> WatsonxLLM:
    return WatsonxLLM(
        model_id=os.getenv("GRANITE_MODEL", "ibm/granite-13b-instruct-v2"),
        url=os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com"),
        project_id=os.getenv("WATSONX_PROJECT_ID", ""),
        apikey=os.getenv("WATSONX_API_KEY", ""),
        params={
            "decoding_method": "sample",
            "max_new_tokens": 512,
            "temperature": 0.4,
        },
    )


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

def _tool_get_recent_events(query: str) -> str:
    """Return a summary of the most recent open natural events."""
    events = fetch_events(limit=5)
    if not events:
        return "No open events found at this time."
    lines = []
    for e in events:
        cats = ", ".join(c.get("title", "") for c in e.get("categories", []))
        lines.append(f"• {e.get('title')} ({cats})")
    return "\n".join(lines)


def _tool_get_event_detail(event_id: str) -> str:
    """Return detail about a specific event by ID."""
    event = get_event(event_id.strip())
    if not event:
        return f"Event {event_id!r} not found in local database."
    geom = event.get("geometry", [])
    coords = geom[-1].get("coordinates", [0, 0]) if geom else [0, 0]
    return (
        f"Title: {event.get('title')}\n"
        f"Status: {event.get('closed') and 'Closed' or 'Open'}\n"
        f"Location: Lat {coords[1]:.2f}, Lon {coords[0]:.2f}\n"
        f"Categories: {', '.join(c.get('title','') for c in event.get('categories',[]))}"
    )


def _tool_list_briefs(query: str) -> str:
    """Return the most recent stored situation briefs."""
    insights = list_insights(limit=5)
    if not insights:
        return "No briefs stored yet."
    lines = [f"• [{i.get('event_id')}] {i.get('title')}: {i.get('brief','')[:120]}…" for i in insights]
    return "\n".join(lines)


TOOLS = [
    Tool(
        name="get_recent_events",
        func=_tool_get_recent_events,
        description="Get a list of the most recent open natural events (wildfires, floods, storms). Input: any string.",
    ),
    Tool(
        name="get_event_detail",
        func=_tool_get_event_detail,
        description="Get details about a specific event by its EONET event ID. Input: event ID string.",
    ),
    Tool(
        name="list_situation_briefs",
        func=_tool_list_briefs,
        description="List recent AI-generated situation briefs from the database. Input: any string.",
    ),
]


# ---------------------------------------------------------------------------
# ReAct prompt
# ---------------------------------------------------------------------------

REACT_TEMPLATE = """You are a satellite intelligence assistant with access to live natural event data and AI-generated situation briefs.

You have access to the following tools:

{tools}

Use the following format:
Question: the input question you must answer
Thought: think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Context from past briefs:
{rag_context}

Question: {input}
{agent_scratchpad}"""


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_agent(user_message: str, event_id: Optional[str] = None, rag_context: str = "") -> str:
    """
    Run the LangChain ReAct agent and return the final answer.

    Falls back to a simple Granite direct call if LangChain is unavailable
    or no API key is set.
    """
    api_key = os.getenv("WATSONX_API_KEY", "")
    if not api_key:
        return (
            "[Granite offline — set WATSONX_API_KEY in .env] "
            f"You asked: {user_message!r}. In production this would query live satellite data and IBM Granite."
        )

    try:
        llm = _build_llm()
        prompt = PromptTemplate.from_template(REACT_TEMPLATE)
        agent = create_react_agent(llm=llm, tools=TOOLS, prompt=prompt)
        executor = AgentExecutor(agent=agent, tools=TOOLS, verbose=False, max_iterations=5, handle_parsing_errors=True)

        result = executor.invoke({
            "input": user_message,
            "rag_context": rag_context or "No prior briefs available.",
        })
        return result.get("output", "No answer generated.")
    except Exception as exc:
        # Graceful degradation
        return f"Agent encountered an error: {exc}"
