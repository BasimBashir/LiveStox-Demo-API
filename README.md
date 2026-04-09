# ArkAI Demo API

Mock server that mirrors the real ArkAI API exactly — same endpoints, same request/response shapes, no ML models required. Built so frontend and backend developers can integrate against a live API while the production models are still in development.

> **When the real API is ready:** change the base URL. Nothing else changes.

---

## What It Does

| Feature | Detail |
|---------|--------|
| Endpoints | Full ArkAI surface: tracking, counting, weight, cameras, ROI, processing |
| Mock data | Randomised but realistic (8–20 chickens, 900–1500 g, 21–35 days) |
| State | Cameras, ROI configs, and jobs persist for the session |
| Jobs | Created as `processing`, auto-complete to `completed` in ~3 s |
| No dependencies | No CUDA, no YOLO, no GBDT — starts in under 2 seconds |
| FE stack | Tested against React (`fetch`) and .NET (`HttpClient`) |

---

## Quick Start

### Docker (recommended)

```bash
docker compose up --build
```

### Bare Python

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

API: **http://localhost:8000**  
Swagger UI: **http://localhost:8000/docs**  
ReDoc: **http://localhost:8000/redoc**

---

## Endpoints at a Glance

| Group | Base Path | Key Operations |
|-------|-----------|----------------|
| Camera Management | `/api/v1/cameras` | Register, set RTSP, snapshot, stream start/stop |
| ROI Management | `/api/v1/roi` | Upload sample image, define zones and lines |
| Tracking | `/api/v1/tracking` | Per-frame tracking, active tracks, reset |
| Counting | `/api/v1/counting` | Zone counts, line crossings, event history |
| Weight Estimation | `/api/v1/weight` | Bbox and segmentation analysis on images/videos |
| Processing | `/api/v1` | Batch jobs, live stream, job polling |
| Global | `/`, `/health`, `/stats` | API info, health check, system stats |

---

## FE Developer Guide

Full integration guide with JavaScript (React) and C# (.NET) code examples for every endpoint:

**[docs/FE_DEVELOPER_GUIDE.md](docs/FE_DEVELOPER_GUIDE.md)**

Covers:
- Both delivery options (Docker / bare Python)
- Mock behaviour explained
- Typical FE workflow (register → ROI → stream → poll)
- Code examples for every major endpoint in React and C# .NET
- Error reference and polling intervals

---

## Project Structure

```
Demo-Livestox-API/
├── api/
│   ├── main.py              # FastAPI app, CORS, global endpoints
│   ├── schemas.py           # Pydantic models (identical to production)
│   ├── mock_state.py        # In-memory state singleton
│   ├── mock_generators.py   # Randomised data generators (Pillow, no OpenCV)
│   └── routers/
│       ├── tracking.py
│       ├── counting.py
│       ├── weight.py
│       ├── cameras.py
│       ├── roi.py
│       └── processing.py
├── tests/                   # 78 pytest tests, all passing
├── docs/
│   └── FE_DEVELOPER_GUIDE.md
├── Dockerfile
├── docker-compose.yml
└── requirements.txt         # fastapi, uvicorn, pillow, pytest only
```

---

## Running Tests

```bash
.venv\Scripts\activate
pytest -v
```

Expected: **78 passed**

---

## Mock Data Ranges

| Field | Range |
|-------|-------|
| Chickens per frame | 8–20 |
| GBDT weight | 900–1500 g |
| YOLO weight | GBDT ± 30 g |
| Age | 21–35 days |
| Confidence | 0.72–0.96 |
| Zone count delta | +0–3 per call |
| Line in/out delta | +0–2 per call |
| Job completion | ~3 seconds after creation |

---

## Switching to Production

```js
// Demo
const BASE_URL = 'http://localhost:8000';

// Production
const BASE_URL = 'https://api.arkai.io'; // actual URL TBD
```

All paths, parameters, and response shapes are identical to the real ArkAI API.
