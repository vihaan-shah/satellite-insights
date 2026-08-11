"""
LangChain agent for satellite data Q&A — LangChain 1.x compatible.

Uses ChatWatsonx (IBM Granite) with tool-calling via bind_tools, running
a manual ReAct loop without requiring LangGraph or the legacy AgentExecutor.
Falls back to direct Granite text generation when no API key is set.
"""
import os
import json
from typing import Optional

from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from app.ingest.eonet import fetch_events
from app.store.db import get_event, list_insights


# ---------------------------------------------------------------------------
# Tool definitions (LangChain 1.x @tool decorator)
# ---------------------------------------------------------------------------

@tool
def get_recent_events(query: str) -> str:
    """Get a list of the most recent open natural events (wildfires, floods, storms, volcanoes).
    Input can be any string."""
    events = fetch_events(limit=5)
    if not events:
        return "No open events found at this time."
    lines = []
    for e in events:
        cats = ", ".join(c.get("title", "") for c in e.get("categories", []))
        geom = e.get("geometry", [])
        coords = geom[-1].get("coordinates", [0, 0]) if geom else [0, 0]
        lines.append(f"• [{e.get('id')}] {e.get('title')} ({cats}) — Lat {coords[1]:.1f}, Lon {coords[0]:.1f}")
    return "\n".join(lines)


@tool
def get_event_detail(event_id: str) -> str:
    """Get details about a specific event by its EONET event ID.
    Input: the event ID string (e.g. EONET_6789)."""
    event = get_event(event_id.strip())
    if not event:
        return f"Event '{event_id}' not found in local database."
    geom = event.get("geometry", [])
    coords = geom[-1].get("coordinates", [0, 0]) if geom else [0, 0]
    date = geom[-1].get("date", "unknown")[:10] if geom else "unknown"
    cats = ", ".join(c.get("title", "") for c in event.get("categories", []))
    return (
        f"Title: {event.get('title')}\n"
        f"Status: {'Closed' if event.get('closed') else 'Open'}\n"
        f"Date: {date}\n"
        f"Location: Lat {coords[1]:.2f}, Lon {coords[0]:.2f}\n"
        f"Categories: {cats}"
    )


@tool
def list_situation_briefs(query: str) -> str:
    """List the most recent AI-generated situation briefs stored in the database.
    Input can be any string."""
    insights = list_insights(limit=5)
    if not insights:
        return "No briefs stored yet. Generate one by visiting /api/insights/{event_id}."
    lines = [
        f"• [{i.get('event_id')}] {i.get('title')} (risk: {i.get('analysis', {}).get('risk_level', 'unknown')}): "
        f"{i.get('brief', '')[:120]}…"
        for i in insights
    ]
    return "\n".join(lines)


TOOLS = [get_recent_events, get_event_detail, list_situation_briefs]


# ---------------------------------------------------------------------------
# Tool executor
# ---------------------------------------------------------------------------

def _execute_tool(tool_name: str, tool_input: dict) -> str:
    """Dispatch a tool call by name and return its string output."""
    registry = {t.name: t for t in TOOLS}
    t = registry.get(tool_name)
    if t is None:
        return f"Unknown tool: {tool_name}"
    try:
        # All our tools accept a single string argument
        first_arg = next(iter(tool_input.values()), "") if tool_input else ""
        return str(t.invoke(first_arg))
    except Exception as exc:
        return f"Tool error: {exc}"


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a satellite intelligence assistant with access to live natural event data and AI-generated situation briefs.

You have tools to:
- get_recent_events: list current open natural events
- get_event_detail: get details about a specific event by ID
- list_situation_briefs: list recent AI-generated situation briefs

Answer the user's question using the tools as needed. Be concise and factual.
Use the following context from past briefs when relevant:

{rag_context}"""


def run_agent(user_message: str, event_id: Optional[str] = None, rag_context: str = "") -> str:
    """
    Run the tool-calling agent and return the final answer.

    Uses ChatWatsonx.bind_tools for structured tool calls with a manual
    ReAct loop (max 4 iterations). Falls back gracefully when offline.
    """
    api_key = os.getenv("WATSONX_API_KEY", "")
    if not api_key:
        return (
            "[Granite offline — set WATSONX_API_KEY in .env] "
            f"You asked: {user_message!r}. In production this would query live satellite "
            "data and IBM Granite to answer your question."
        )

    try:
        from langchain_ibm import ChatWatsonx

        llm = ChatWatsonx(
            model_id=os.getenv("GRANITE_MODEL", "ibm/granite-13b-instruct-v2"),
            url=os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com"),
            project_id=os.getenv("WATSONX_PROJECT_ID", ""),
            apikey=api_key,
            params={"max_new_tokens": 512, "temperature": 0.3},
        )

        llm_with_tools = llm.bind_tools(TOOLS)

        messages = [
            SystemMessage(content=SYSTEM_PROMPT.format(rag_context=rag_context or "None available.")),
            HumanMessage(content=user_message),
        ]

        # Manual tool-calling loop (up to 4 rounds)
        for _ in range(4):
            response = llm_with_tools.invoke(messages)
            messages.append(response)

            tool_calls = getattr(response, "tool_calls", [])
            if not tool_calls:
                # No more tool calls — return final text
                return response.content or "No answer generated."

            # Execute each tool call and append results
            for tc in tool_calls:
                result = _execute_tool(tc["name"], tc.get("args", {}))
                messages.append(
                    ToolMessage(content=result, tool_call_id=tc["id"])
                )

        # If we exhausted iterations, return whatever the last text was
        last = messages[-1]
        return getattr(last, "content", "Agent reached iteration limit.") or "Agent reached iteration limit."

    except Exception as exc:
        return f"Agent encountered an error: {exc}"
