# Idea2Product

**Turn natural language into a runnable web app.** A 4-stage pipeline with 10+ AI agents turns your plain-text idea into a working Flask application—requirements, planning, code generation, and validation in one flow.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Quick Start (3 steps)

**Prerequisites:** Python 3.9+, one LLM API key (OpenAI / Anthropic / Google), and optionally Git (for Code Mining).

1. **Install** (≈2 min)

   ```bash
   git clone https://github.com/yourusername/idea2product.git
   cd idea2product
   python -m venv venv
   # Linux/Mac: source venv/bin/activate
   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -e .
   ```

   For pinned dependencies, use `requirements-pinned.txt`. See [docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md).

2. **Configure** (≈1 min)

   ```bash
   cp .env.example .env
   ```

   Edit `.env`: set `PRIMARY_LLM_PROVIDER` to `openai`, `anthropic`, or `google`, and set the matching API key (e.g. `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GOOGLE_API_KEY`). Other options are in [.env.example](.env.example) and [CLAUDE.md](CLAUDE.md#environment-variables).

3. **Run** (≈1–5 min, depends on LLM)

   ```bash
   python -m src.cli create "Build a todo list app"
   ```

   **Output:** Project under `data/projects/<project_id>/generated/`. Run it with `python app.py` in that directory.

---

## What It Does

Idea2Product runs a 4-stage pipeline: **Requirements → Planning → Code Generation → Validation.**

| Stage | Purpose | Agents |
|-------|---------|--------|
| **1** | Requirements | Interaction Agent |
| **2** | Technical planning | Flow Simulation, Task Division, Algorithm Analysis, Scheme Planning |
| **3** | Code generation | Code Generation, Code Memory, Code Mining |
| **4** | Validation | Full-cycle testing, Fine-tuning, optional Visual Verification |

1. **Requirements** — Interaction Agent clarifies your idea (or skip with non-interactive mode).
2. **Planning** — Flow simulation, task breakdown, algorithm analysis, and scheme planning (file structure, API specs, `.pyi` stubs).
3. **Code generation** — Interface-first: stubs → dependency graph → implementations (LangChain-based).
4. **Validation** — Run generated app, run-fix loop, optional BDD tests and vision-based UI checks.

Details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## Usage

### CLI

```bash
# Create (non-interactive)
python -m src.cli create "Build a todo app with add, delete, complete"

# Create (interactive — asks clarifying questions)
python -m src.cli create -i "Build a todo app"

# List projects / check status
python -m src.cli list
python -m src.cli status <project_id>
```

### Web UI (Build Studio)

**Production:** build frontend, then start the server:

```bash
cd frontend && npm run build && cd ..
python -m src.web.app
```

Open `http://localhost:5000` for the chat-based Build Studio (left: chat, right: code + live preview).

**Development:** run frontend dev server (proxies to Flask on 8080):

```bash
cd frontend && npm run dev
```

Main API: `POST /api/projects` (create), `POST /api/projects/<id>/chat` (send message, triggers generation), `GET /api/projects/<id>/status`, `GET /api/projects/<id>/preview-url`. Full list: [docs/refs/WEB_FLOW_REF.md](docs/refs/WEB_FLOW_REF.md).

### Python API

```python
from config.settings import get_settings
from src.core.orchestrator import Orchestrator

settings = get_settings()
orchestrator = Orchestrator(settings)
result = orchestrator.run("Build a blog with posts and comments", interactive=False)
print(f"Deployable: {result.is_deployable}, Files: {len(result.repository.files)}")
```

---

## Output and Running Generated Apps

Each project is saved under `data/projects/<project_id>/`:

```
data/projects/<project_id>/
├── artifacts/          # requirements, plan, context JSON
├── generated/          # Runnable Flask app (app.py, app/, templates/, etc.)
└── logs/
```

To run the generated app:

```bash
cd data/projects/<project_id>/generated
pip install -r requirements.txt
python app.py
```

App usually listens on `http://localhost:5000`.

---

## Configuration (minimal)

| Variable | Description |
|----------|-------------|
| `PRIMARY_LLM_PROVIDER` | `openai` \| `anthropic` \| `google` |
| `OPENAI_API_KEY` | Required when provider is `openai` |
| `ANTHROPIC_API_KEY` | Required when provider is `anthropic` |
| `GOOGLE_API_KEY` | Required when provider is `google` |
| `OPENAI_BASE_URL` | Optional; custom endpoint (OpenRouter, Azure, local). |

Full list of env vars and feature flags: [CLAUDE.md](CLAUDE.md#environment-variables) and [.env.example](.env.example).

---

## Development

```bash
pytest tests/ -v                                    # Unit tests (no API key)
python -m src.benchmarks.run_small_suite            # Benchmarks (needs API key)
black src/ tests/ && ruff check src/ && mypy src/   # Format, lint, type-check
```

---

## Deploy (Build Studio as a public site)

- **Render:** New Web Service → connect repo → set `OPENAI_API_KEY` (or chosen provider key). See `render.yaml`. Free tier may sleep after idle.
- **Railway:** Deploy from GitHub → add env vars → use `Procfile`. Use `gunicorn --timeout 300` for long runs.

Never commit API keys. Generated projects on free tiers may be ephemeral (lost on restart).

---

## Troubleshooting

| Issue | Action |
|-------|--------|
| **401 Unauthorized** | Check `.env`: correct `PRIMARY_LLM_PROVIDER` and matching `*_API_KEY`. |
| **`ModuleNotFoundError: No module named 'src'`** | Run `pip install -e .` from project root. |
| **Empty or minimal generated code** | Use a clearer requirement (e.g. "todo app with add, delete, complete"). |
| **Web UI not loading** | Run `cd frontend && npm run build` before `python -m src.web.app`. |
| **Import errors in generated app** | In `data/projects/<id>/generated/`, run `pip install -r requirements.txt`. |

More: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

---

## More documentation

| Doc | Purpose |
|-----|---------|
| [docs/CONTEXT_INDEX.md](docs/CONTEXT_INDEX.md) | Doc index and task → doc mapping |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 4-stage pipeline, data flow, components |
| [docs/refs/AGENTS_REF.md](docs/refs/AGENTS_REF.md) | Agent list, I/O, key methods |
| [docs/refs/WEB_FLOW_REF.md](docs/refs/WEB_FLOW_REF.md) | REST API, chat/preview/task services |
| [CLAUDE.md](CLAUDE.md) | Commands, env vars, key patterns |

---

## License

MIT License
