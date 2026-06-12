# backend/agent.py
import os
import json
import asyncio
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition, MCPTool


# Load env files deterministically: prefer backend/.env then fallback to repo root .env
_here = os.path.dirname(__file__)
_repo_root = os.path.dirname(_here)
load_dotenv(os.path.join(_here, ".env"))
load_dotenv(os.path.join(_repo_root, ".env"))
# Also attempt the default lookup (cwd) as a final fallback
load_dotenv()

# Read values after loading .env files so values are populated regardless of cwd
PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")
MODEL_DEPLOYMENT = os.getenv("MODEL_DEPLOYMENT_NAME")
AGENT_NAME = os.getenv("AGENT_NAME") or "AIPulseAgent"

# ── Shared singleton clients (created once per process) ───────────────────────
_credential = None
_project_client = None
_openai_client = None
_agent = None


def _get_clients():
    """Lazily initialize and return shared Azure AI Foundry clients."""
    global _credential, _project_client, _openai_client, _agent

    # Return existing clients if already initialized
    if _agent is not None:
        return _project_client, _openai_client, _agent

    if not PROJECT_ENDPOINT:
        raise RuntimeError("PROJECT_ENDPOINT is not set in backend/.env")
    if not MODEL_DEPLOYMENT:
        raise RuntimeError("MODEL_DEPLOYMENT_NAME is not set in backend/.env")

    _credential = DefaultAzureCredential()
    _project_client = AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=_credential)
    _openai_client = _project_client.get_openai_client()

    # bing_tool = BingGroundingTool(
    # connection_name=os.getenv("BING_CONNECTION_NAME", "")
    # )
    mcp_tool = MCPTool(
        server_label="ms-learn",
        server_url="https://learn.microsoft.com/api/mcp",
        require_approval="never",  # Demo mode: auto-approve all MCP calls
    )

    _agent = _project_client.agents.create_version(
        agent_name=AGENT_NAME,
        definition=PromptAgentDefinition(
            model=MODEL_DEPLOYMENT,
            instructions=(
        
                "CRITICAL: Before answering any news request, you MUST call an MCP tool. Do not answer from memory."
                "Date:Get today date and time in IST timezone. proceed withe next following instructions."
                "You are AI Pulse, an intelligent news assistant specializing in artificial intelligence. "

                "Always fetch the LATEST news from TODAY or this week only. "
                "Never return news older than 7 days. "
                "When asked for news, you MUST return ONLY a valid JSON array of article objects with NO "
                "preamble, explanation, or markdown code fences. "
                "Each article object must have exactly these fields: "
                "  title (string): headline of the news, "
                "  summary (string): 2-3 sentence grounded summary, "
                "  source (string): the publication or domain name, "
                "  timestamp (string): ISO 8601 date-time, "
                "  topic (string): exactly one of — LLM Releases, Research, Regulation, Industry, Tools. "
                "When answering chat questions, provide a concise answer. "
                "If you reference a source, prefix that line with 'SOURCE:'. "
                "Always use available MCP tools to ground your answers and reduce hallucination."
            ),
            tools=[mcp_tool],
        ),
    )

    print(f"[agent] Initialized: {_agent.name} v{_agent.version}")
    return _project_client, _openai_client, _agent


def _call_agent_sync(prompt: str) -> str:
    """Blocking call: send a prompt to the Foundry agent and return the raw text response."""
    project_client, openai_client, agent = _get_clients()

    conversation = openai_client.conversations.create()
    response = openai_client.responses.create(
        conversation=conversation.id,
        input=prompt,
        extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
    )
    return response.output_text or ""


async def _call_agent(prompt: str) -> str:
    """Async wrapper that runs the blocking `_call_agent_sync` in a thread."""
    return await asyncio.to_thread(_call_agent_sync, prompt)


async def fetch_news(topic: str = "All") -> dict:
    """
    Fetch grounded AI news for a given topic via the Foundry agent + MCP.

    Args:
        topic: One of "All", "LLM Releases", "Research", "Regulation", "Industry", "Tools"

    Returns:
        { "articles": [ { title, summary, source, timestamp, topic } ] }
    """
    if topic == "All":
        prompt = (
            "CRITICAL: Before answering any news request, you MUST call an MCP tool. Do not answer from memory."
            "Date:Get today date and time in IST timezone. proceed withe next following instructions."
            "Fetch and return the 6 most recent and significant AI news stories "
            "spanning all categories: LLM Releases, Research, Regulation, Industry, and Tools. "
            "Use your MCP tools to retrieve real, grounded news. "
            "Return ONLY a JSON array of article objects. No preamble, no code fences."
        )
    else:
        prompt = (
            f"Fetch and return the 4 most recent AI news stories specifically about: {topic}. "
            "Use your MCP tools to retrieve real, grounded news. "
            "Return ONLY a JSON array of article objects. No preamble, no code fences."
        )

    try:
        raw = await _call_agent(prompt)
    except Exception as exc:
        # If the live agent call fails, optionally return a dynamic development fallback
        use_mock = os.getenv("AI_PULSE_USE_MOCK", "true").lower() in ("1", "true", "yes")
        if not use_mock:
            raise

        # Build dynamic mock articles with current timestamps so UI shows fresh content
        now = datetime.now(timezone.utc)
        def mk_article(i, tpc):
            return {
                "title": f"{tpc} — Sample update {i} (dev)",
                "summary": f"This is a dynamic development article for topic {tpc}. Generated at {now.isoformat()}.",
                "source": "dev.local",
                "timestamp": now.isoformat(),
                "topic": tpc if tpc != "All" else "LLM Releases",
            }

        items = []
        count = 6 if topic == "All" else 4
        for i in range(count):
            items.append(mk_article(i + 1, topic))

        return {"articles": items}

    # Strip markdown code fences if model wraps response in ```json ... ```
    clean = (
        raw.strip()
        .removeprefix("```json")
        .removeprefix("```")
        .removesuffix("```")
        .strip()
    )

    try:
        articles = json.loads(clean)
        if isinstance(articles, dict) and "articles" in articles:
            articles = articles["articles"]

        if not isinstance(articles, list):
            return {"articles": []}

        # Normalize and filter by recency (last 7 days) and sort newest first.
        def _parse_iso_datetime(s: str):
            if not s:
                return None
            try:
                # datetime.fromisoformat handles offsets like +00:00
                dt = datetime.fromisoformat(s)
                # If naive, assume UTC
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except Exception:
                # Try common fallback formats
                try:
                    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S%z").astimezone(timezone.utc)
                except Exception:
                    return None

        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=7)

        normalized = []
        for a in articles:
            if not isinstance(a, dict):
                continue
            ts = a.get("timestamp") or a.get("time") or a.get("date")
            parsed_ts = _parse_iso_datetime(ts) if ts else None
            # If timestamp missing or unparsable, skip the article to avoid showing stale/ambiguous items
            if parsed_ts is None:
                continue
            # Only include articles within the last 7 days
            if parsed_ts < cutoff:
                continue
            # attach parsed timestamp for sorting
            a["_parsed_ts"] = parsed_ts
            normalized.append(a)

        # sort newest first
        normalized.sort(key=lambda x: x["_parsed_ts"], reverse=True)

        # Trim to requested count: 6 for All, 4 for topic-specific
        limit = 6 if topic == "All" else 4
        trimmed = normalized[:limit]

        # If no recent articles (strict cutoff), relax: return newest available articles from agent
        if len(trimmed) == 0:
            # Try to build candidate list from original articles, using parsed timestamps when available
            candidates = []
            for a in articles:
                if not isinstance(a, dict):
                    continue
                ts = a.get("timestamp") or a.get("time") or a.get("date")
                parsed_ts = _parse_iso_datetime(ts) if ts else None
                a["_parsed_ts"] = parsed_ts
                candidates.append(a)

            # Sort candidates: items with parsed timestamps first (newest), then others in original order
            candidates.sort(key=lambda x: (x.get("_parsed_ts") is None, x.get("_parsed_ts") or datetime.min), reverse=True)
            trimmed = candidates[:limit]

        # Remove helper field and ensure required keys exist
        out = []
        for art in trimmed:
            if isinstance(art, dict):
                art.pop("_parsed_ts", None)
                out.append(
                    {
                        "title": art.get("title", "Untitled"),
                        "summary": art.get("summary", ""),
                        "source": art.get("source", ""),
                        "timestamp": art.get("timestamp"),
                        "topic": art.get("topic", topic if topic != "All" else art.get("topic", "")),
                    }
                )

        return {"articles": out}
    except json.JSONDecodeError:
        # Removed development fallback: in production we must surface parsing errors
        # so they are handled by the API layer rather than returning static data.
        raise


async def chat_with_news(message: str, history: list) -> dict:
    """
    Answer a user's question about AI news, with citations.

    Args:
        message: The user's current question
        history: List of { "role": "user"|"assistant", "content": str }

    Returns:
        { "reply": str, "citations": [ str ] }
    """
    # Include last 3 conversation turns (6 messages) for context
    recent = history[-6:] if len(history) > 6 else history
    context = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in recent
    )

    prompt = (
        f"Previous conversation:\n{context}\n\n"
        f"User question: {message}\n\n"
        "CRITICAL: Before answering any news request, you MUST call an MCP tool. Do not answer from memory."
        "Date:Get today date and time in IST timezone. proceed withe next following instructions."
        "Use your MCP tools to find grounded information. "
        "Answer concisely in 2-4 sentences. "
        "For every source you reference, add a new line starting with 'SOURCE:' followed by the URL or publication name."
    )

    raw = await _call_agent(prompt)

    # Clean possible markdown code fences
    clean = (
        raw.strip()
        .removeprefix("```json")
        .removeprefix("```")
        .removesuffix("```")
        .strip()
    )

    # If we got an empty response, optionally fallback to dynamic dev reply
    if not clean:
        use_mock = os.getenv("AI_PULSE_USE_MOCK", "true").lower() in ("1", "true", "yes")
        if use_mock:
            now = datetime.now(timezone.utc)
            reply_text = f"No direct answer; generated dev reply at {now.isoformat()}"
            return {"reply": reply_text, "citations": ["dev.local"]}

    # If the agent returned a JSON array/dict (e.g., list of articles), normalize
    try:
        parsed = json.loads(clean)
    except json.JSONDecodeError:
        parsed = None

    if isinstance(parsed, list):
        # Build a concise human-readable reply from up to 3 articles
        top = parsed[:3]
        reply_parts = []
        citations = []
        for art in top:
            title = art.get("title") if isinstance(art, dict) else None
            summary = art.get("summary") if isinstance(art, dict) else None
            source = art.get("source") if isinstance(art, dict) else None
            if title and summary:
                reply_parts.append(f"{title} — {summary}")
            elif title:
                reply_parts.append(title)
            if source:
                citations.append(source)

        reply_text = "\n\n".join(reply_parts).strip()
        return {"reply": reply_text or "No concise reply available.", "citations": citations}

    # Fallback: treat as plain-text reply and extract SOURCE: lines
    lines = clean.split("\n")
    reply_lines = []
    citations = []

    for line in lines:
        stripped = line.strip()
        if stripped.upper().startswith("SOURCE:"):
            citation = stripped[7:].strip()  # Remove "SOURCE:" prefix
            if citation:
                citations.append(citation)
        else:
            reply_lines.append(line)

    return {
        "reply": "\n".join(reply_lines).strip(),
        "citations": citations,
    }


def cleanup():
    """Delete the agent version from Foundry on server shutdown."""
    global _agent, _project_client
    if _agent and _project_client:
        try:
            _project_client.agents.delete_version(
                agent_name=_agent.name, agent_version=_agent.version
            )
            print(f"[agent] Cleaned up: {_agent.name} v{_agent.version}")
        except Exception as e:
            print(f"[agent] Cleanup warning: {e}")