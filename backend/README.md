# SchemaSense AI — Backend API & Generative Engine

**Subtitle**: Natural Language. Precise SQL.  
**Phase**: Phase 8 — Final Engineering Audit, Academic Evidence & Demonstration Readiness  
**Target Environment**: Python 3.10+ / FastAPI / SQLite / Transformers / SQLGlot  

---

## 1. Architecture Overview

```text
backend/
├── app/
│   ├── api/v1/          # REST Endpoints: health, databases, ai, execution, history, analytics
│   ├── core/            # Settings, CORS, structured logging, exception handlers
│   ├── db/              # Seeders (Campus Intelligence demonstration database)
│   ├── schemas/         # Strongly-typed Pydantic v2 schemas
│   ├── services/        # AI provider (Qwen2.5-Coder), SQL validator, execution sandbox,
│   │                    # correction engine, semantic analyzer, history & analytics
│   └── main.py          # FastAPI application entrypoint
├── data/
│   ├── databases/       # SQLite databases (campus_intelligence.db)
│   └── history/         # Durable query history storage
├── docs/                # Academic guide, demonstration runbook, and evidence checklist
├── evaluation/          # Master evidence ledger, benchmark dataset, and execution results
├── notebooks/           # Independent Google Colab notebook (SchemaSense_AI_GenAI_AAT1.ipynb)
├── tests/               # 167 Pytest integration & unit test suite
├── .env.example         # Environment variable template
├── requirements.txt     # Python runtime dependencies
└── pytest.ini           # Pytest configuration pinning cache directory
```

---

## 2. Getting Started

### 2.1 Prerequisites
- Python 3.10 or 3.11 (tested on Python 3.11.9)
- Virtual environment support

### 2.2 Virtual Environment & Dependencies
```powershell
# In backend/
python -m venv .venv

# On Windows PowerShell
.\.venv\Scripts\Activate.ps1
# On Linux / macOS
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install nbformat pandas matplotlib tabulate
```

### 2.3 Configuration
Copy `.env.example` to `.env` if local overrides are needed:
```powershell
cp .env.example .env
```
Default ports: Backend runs on `http://127.0.0.1:8001`. Frontend runs on `http://127.0.0.1:5173`.

### 2.4 Running the Development Server
```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

The API will be available at:
- Interactive Swagger UI: `http://127.0.0.1:8001/docs`
- ReDoc: `http://127.0.0.1:8001/redoc`
- Health check: `http://127.0.0.1:8001/api/health`
- Capabilities discovery: `http://127.0.0.1:8001/api/capabilities`

---

## 3. Running Backend Tests

All 167 automated tests run via `pytest`:
```powershell
pytest
```

---

## 4. Implemented API Endpoints (Phase 8 Production Suite)

| Category | Method | Path | Description |
|---|---|---|---|
| **System** | `GET` | `/` | Root service info and discovery links |
| **System** | `GET` | `/api/health` | Live service health, uptime, version, and environment |
| **System** | `GET` | `/api/capabilities` | Phase 8 capability matrix and active provider info |
| **Databases** | `GET` | `/api/databases` | List all registered SQLite databases |
| **Databases** | `POST` | `/api/databases/upload` | Upload and validate a custom SQLite `.db` file |
| **Databases** | `GET` | `/api/databases/{id}/schema` | Dynamic schema introspection (tables, columns, foreign keys) |
| **Databases** | `GET` | `/api/databases/{id}/tables/{table}/preview` | Paginated live data preview |
| **AI Inference**| `POST` | `/api/ai/generate` | Schema-grounded Text-to-SQL generation (Qwen2.5-Coder) |
| **AI Execution**| `POST` | `/api/ai/query` | End-to-end generate $\to$ validate $\to$ execute $\to$ self-correct |
| **SQL Execution**| `POST` | `/api/sql/execute` | Execute raw validated SQL in read-only sandbox |
| **History** | `GET` | `/api/history` | Paginated query history with search and status filters |
| **History** | `DELETE`| `/api/history/{id}` | Delete a specific recorded query |
| **Analytics** | `GET` | `/api/analytics` | Execution pass rates, average durations, and error taxonomy |

---

## 5. Security & Isolation Controls
- **SQLGlot AST Parsing**: Prohibits mutating statements (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `PRAGMA`).
- **SQLite Engine C-Authorizer**: Uses `conn.set_authorizer` to enforce read-only execution at the SQLite virtual machine level.
- **Instruction Timeout Limit**: Intercepts runaway queries after 500,000 VM instructions using `set_progress_handler`.
- **Bounded Result Sets**: Caps output rows to protect system memory.
- **Explicit CORS**: Restricted to development origins (`localhost:5173`, `127.0.0.1:5173`).
