# 🛰 Satellite-Insights

> Turn live satellite data into plain-English, mission-ready situation briefs — powered by IBM Granite and NASA open data.

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688)](https://fastapi.tiangolo.com)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org)
[![IBM Granite](https://img.shields.io/badge/IBM-Granite-blue)](https://www.ibm.com/granite)

---

## Problem

Natural disasters — wildfires, floods, volcanic eruptions — generate enormous amounts of satellite data every day. That data sits in raw imagery tiles and CSV hotspot files. Field responders and operations teams need concise, actionable summaries, not raw pixels.

## Solution

**Satellite Insights** is an AI-native platform that:

1. **Ingests** live natural event feeds (NASA EONET), active fire hotspots (NASA FIRMS), and satellite imagery (NASA GIBS/MODIS)
2. **Analyzes** the data with lightweight ML — hotspot clustering, burn-area estimation, fire radiative power
3. **Generates** a 3–5 sentence plain-English **situation brief** using IBM Granite via watsonx.ai
4. **Lets users interrogate** the data via a chat panel backed by a LangChain ReAct agent + Chroma RAG store

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  INGESTION (daily cron / on-demand)                 │
│  NASA EONET events · NASA FIRMS · NASA GIBS imagery │
└──────────────────────┬──────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│  ANALYSIS (Python)                                  │
│  cloud detection · NDVI proxy · FRP clustering      │
│  burn/flood area estimate · anomaly detection       │
└──────────────────────┬──────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│  AI INSIGHT LAYER — IBM Granite (watsonx.ai)        │
│  Situation brief generator (summarizer.py)          │
│  LangChain ReAct agent + tool definitions (agent.py)│
│  Chroma vector store — RAG over past briefs         │
└──────────────────────┬──────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│  PRESENTATION  Next.js 14 + FastAPI                 │
│  Dashboard · Event cards · Leaflet map · Chat panel │
│  /api/events  /api/events/{id}  /api/insights  /api/chat │
└─────────────────────────────────────────────────────┘
```

---

## AI Approach

| Component | Role |
|---|---|
| **IBM Granite** (via watsonx.ai) | LLM that writes situation briefs, event summaries, and chat answers |
| **LangChain ReAct agent** | Orchestrates tool calls: get events → fetch imagery → run analysis → generate brief |
| **Chroma RAG** | Grounds chat answers in real stored briefs; enables "what happened near X last week?" queries |
| **Classical ML** | Deterministic FRP thresholding, hotspot clustering, burn-area pixel estimates — keeps the demo reliable while LLM adds the insight layer |

IBM Bob was the **primary development tool** throughout — used for code generation, refactoring, debugging, and documentation.

---

## Data Sources

| Source | What you get | Key needed? |
|---|---|---|
| [NASA EONET](https://eonet.gsfc.nasa.gov) | Live natural events feed | ❌ None |
| [NASA GIBS](https://earthdata.nasa.gov/eosdis/science-system-description/eosdis-components/gibs) | Global MODIS/VIIRS imagery tiles | ❌ None |
| [NASA FIRMS](https://firms.modaps.eosdis.nasa.gov) | Active fire hotspot CSVs | ✅ Free |
| [IBM watsonx.ai](https://cloud.ibm.com) | Granite LLM inference | ✅ Free tier |

---

## Project Structure

```
satellite-insights/
├── .env.example               # Template for secrets
├── docker-compose.yml         # One-command deployment
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── app/
│       ├── main.py            # FastAPI entry point
│       ├── api/routes.py      # /events /insights /chat
│       ├── ingest/
│       │   ├── eonet.py       # NASA EONET feed
│       │   ├── firms.py       # NASA FIRMS hotspots
│       │   └── gibs.py        # NASA GIBS imagery URLs
│       ├── analysis/
│       │   ├── indices.py     # FRP, burn area, NDVI proxy
│       │   ├── cloud_detection.py
│       │   └── event_detector.py
│       ├── ai/
│       │   ├── granite_client.py  # watsonx.ai wrapper
│       │   ├── summarizer.py      # Granite brief generator
│       │   └── agent.py           # LangChain ReAct agent
│       ├── store/
│       │   ├── db.py          # SQLite event + insight cache
│       │   └── vectorstore.py # Chroma RAG store
│       └── schemas/insight.py
├── frontend/
│   ├── Dockerfile
│   ├── app/
│   │   ├── page.tsx           # Dashboard
│   │   └── events/[id]/page.tsx  # Event detail + brief + chat
│   └── components/
│       ├── SatelliteMap.tsx   # Leaflet + GIBS overlay
│       ├── InsightCard.tsx    # Brief summary card
│       └── ChatPanel.tsx      # Chat UI
└── notebooks/
    └── explore_data.ipynb     # End-to-end demo for judges
```

---

## Installation & Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- An IBM Cloud account ([free tier](https://cloud.ibm.com/registration))
- A NASA FIRMS MAP key ([free registration](https://firms.modaps.eosdis.nasa.gov/api/area/))

---

### Step 1 — Clone or download the project

```bash
cd "IBM Hackathon/satellite-insights"
```

---

### Step 2 — Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials:

```env
WATSONX_API_KEY=your_ibm_cloud_api_key
WATSONX_PROJECT_ID=your_watsonx_project_id
FIRMS_MAP_KEY=your_firms_key
```

**Getting watsonx.ai credentials:**
1. Go to [cloud.ibm.com](https://cloud.ibm.com) → create a free account
2. Create a **watsonx.ai** instance
3. Open the project → **Manage** → copy the Project ID
4. Go to **Manage → Access (IAM)** → **API Keys** → create one

---

### Step 3 — Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Start the API server:

```bash
uvicorn app.main:app --reload --port 8000
```

The API is now live at `http://localhost:8000`. Open `http://localhost:8000/docs` for the auto-generated Swagger UI.

---

### Step 4 — Run the daily ingestion job (optional but recommended)

```bash
# From backend/ with venv active
python scripts/daily_job.py
```

This fetches current events, runs analysis, and pre-populates the database with situation briefs.

---

### Step 5 — Frontend setup

```bash
cd ../frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

---

### Step 6 — Run tests

```bash
cd backend
pytest tests/ -v
```

---

### Optional: Docker (one command)

```bash
# From satellite-insights/
docker compose up --build
```

Frontend → `http://localhost:3000`  
Backend → `http://localhost:8000`

---

## Demo Flow

1. Open the dashboard → see live active events (wildfires, floods, storms)
2. Click an event card — e.g. *"Wildfire, California"*
3. Backend fetches the latest GIBS imagery tile + FIRMS hotspot data
4. ML computes burn area estimate and fire radiative power
5. IBM Granite generates a 3–4 sentence brief: *"Fire active, ~2,400 ha affected, smoke extending east, risk level HIGH…"*
6. Use the chat panel to ask follow-up questions: *"What caused this fire?"* or *"Are there similar events nearby?"*
7. The LangChain agent uses RAG over past stored briefs to answer grounded questions

---

## Pushing to GitHub

```bash
# 1. Initialize git (from satellite-insights/)
cd satellite-insights
git init
git add .
git commit -m "feat: initial Satellite-to-Insights platform"

# 2. Create a new repo on GitHub (github.com/new)
#    Name it: satellite-insights
#    DO NOT add README/license (we already have them)

# 3. Add the remote and push
git remote add origin https://github.com/YOUR_USERNAME/satellite-insights.git
git branch -M main
git push -u origin main
```

> **Note:** `.env` is in `.gitignore` — your API keys are never pushed.

---

## License

MIT — see [LICENSE](LICENSE).
