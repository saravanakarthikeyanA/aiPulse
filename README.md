# AI Pulse — Hackathon Project Guide
### Live AI News Intelligence Hub | Azure AI Foundry + MCP + React


## 1. Project Overview

**AI Pulse** is a real-time AI news intelligence hub. Users get curated, grounded, and cited summaries of the latest AI developments — and can ask follow-up questions about the news through a conversational chat interface. Powered by **Azure AI Foundry**, **MCP (Model Context Protocol)**, and **Foundry IQ** for grounded, cited answers.

### Core Features
- **Live AI News Feed** — Grounded, cited news summaries from real sources
- **Topic Filters** — LLM Releases, Research, Regulation, Industry, Tools
- **"Ask the News" Chat** — Conversational Q&A powered by the Azure agent
- **News Cards** — Clean cards with title, summary, source citation, and timestamp
- **MCP Integration** — Exposes a news intelligence tool Copilot can call in VS Code

### Hackathon Requirements Satisfied
| Requirement | How |
|---|---|
| GitHub Copilot Usage | React + Python = Copilot's strongest domain |
| Microsoft IQ (Foundry IQ) | Grounded, cited answers via Azure AI Foundry agent |
| Creative Application | "Ask the AI News" — novel conversational news experience |
| MCP Integration | MCP server connected to Foundry agent |

---

## 2. Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    BROWSER (localhost:5173)              │
│   React + Vite + TailwindCSS                            │
│   ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  │
│   │  News Feed  │  │ Topic Filter │  │  Chat Panel  │  │
│   └──────┬──────┘  └──────┬───────┘  └──────┬───────┘  │
└──────────┼────────────────┼─────────────────┼───────────┘
           │                │                 │
           └────────────────┴─────────────────┘
                            │ HTTP REST
                            ▼
┌─────────────────────────────────────────────────────────┐
│                FastAPI Backend (localhost:8000)          │
│   POST /api/news  →  topic filter → agent call          │
│   POST /api/chat  →  user message → agent call          │
│   GET  /api/health → healthcheck                        │
└────────────────────────┬────────────────────────────────┘
                         │ Python SDK
                         ▼
┌─────────────────────────────────────────────────────────┐
│           Azure AI Foundry Agent  (agent.py)            │
│   AIProjectClient + PromptAgentDefinition               │
└────────────────────────┬────────────────────────────────┘
                         │ MCP Protocol
                         ▼
┌─────────────────────────────────────────────────────────┐
│         MCP Server: https://learn.microsoft.com/api/mcp  │
│         (Microsoft Learn Knowledge + Web Search)        │
└─────────────────────────────────────────────────────────┘
                         │ Foundry IQ
                         ▼
┌─────────────────────────────────────────────────────────┐
│         Grounded, Cited AI News Response                │
│         (reduces hallucination, cites sources)          │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Folder Structure

```
ai-pulse/
├── backend/
│   ├── agent.py              ← Azure AI Foundry agent (modified from original)
│   ├── main.py               ← FastAPI server
│   ├── requirements.txt
│   └── .env                  ← NEVER commit this
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── NewsFeed.jsx
│   │   │   ├── NewsCard.jsx
│   │   │   ├── TopicFilter.jsx
│   │   │   ├── ChatPanel.jsx
│   │   │   └── Header.jsx
│   │   ├── api/
│   │   │   └── client.js     ← Axios API calls to backend
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── package.json
├── .gitignore
└── README.md
```

---

---


## 4. Run the Project Locally

### Prerequisites

| Tool | Version | Install |
|---|---|---|
| Python | 3.11+ | python.org |
| Node.js | 20+ | nodejs.org |
| Azure CLI | Latest | `winget install Microsoft.AzureCLI` |

### Step-by-step

```bash
# 1. Clone / create project
mkdir ai-pulse && cd ai-pulse

# 2. Azure login (uses DefaultAzureCredential)
az login

# 3. Backend
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate    # Mac/Linux
pip install -r requirements.txt
# Create your .env file with PROJECT_ENDPOINT and MODEL_DEPLOYMENT_NAME
uvicorn main:app --reload --port 8000

# 4. Frontend (new terminal)
cd ../frontend
npm install
npm run dev

# 5. Open browser
# http://localhost:5173
```

### Verify backend is running

```bash
curl http://localhost:8000/api/health
# Expected: {"status":"ok"}
```

---

*Built with Azure AI Foundry · GitHub Copilot · React · FastAPI*
*AI Pulse — Know AI, as it happens.*
