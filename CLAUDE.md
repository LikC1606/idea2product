# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start

```bash
pip install -r requirements.txt
pip install -e .
cp .env.example .env  # Configure OPENAI_API_KEY
```

## Common Commands

```bash
# CLI
python -m src.cli create "Build a todo app"
python -m src.cli create -i "Build a todo app"   # interactive Q&A mode
python -m src.cli list
python -m src.cli status <project_id>

# Web backend
python -m src.web.app

# Testing & code quality
pytest tests/ -v
python -m src.benchmarks.run_small_suite  # requires OPENAI_API_KEY
black src/ tests/
ruff check src/
mypy src/
```

## Architecture

A 4-stage pipeline with 10 specialized agents that transform natural language requirements into production-ready applications.

### Pipeline Flow
1. **Stage 1** (Requirements) - InteractionAgent clarifies requirements via dialogue
2. **Stage 2** (Planning) - FlowSimulation, TaskDivision, AlgorithmAnalysis, SchemePlanning agents create specs
3. **Stage 3** (Code Generation) - Generates code with interface-first strategy, dependency resolution
4. **Stage 4** (Validation) - BDD testing, optional visual verification, automatic bug fixing (run-fix loop + FineTuningAgent)

### Key Files
- `src/core/orchestrator.py` - Coordinates all stages
- `src/core/context.py` - ExecutionContext carries state through pipeline
- `src/core/data_models.py` - Requirements, EngineeringPlan, CodeRepository, ValidatedProject, etc.
- `config/settings.py` - Application configuration with feature flags

### Agent Locations
- `src/agents/stage1_requirements/` - InteractionAgent
- `src/agents/stage2_planning/` - FlowSimulation, TaskDivision, AlgorithmAnalysis, SchemePlanning
- `src/agents/stage3_generation/` - CodeGeneration (LangChain), CodeMemory, CodeMining
- `src/agents/stage4_validation/` - FullCycleTesting, FineTuning, VisualVerification

### Services
- `src/services/llm_service.py` - OpenAI API calls (use `LLMService.from_settings(settings)`)
- `src/services/code_memory_service.py` - SQLite knowledge graph (`data/code_memory.db`)
- `src/services/code_mining_service.py` - GitHub code retrieval
- `src/services/execution_service.py` - Reserved (not used in pipeline)
- `src/web/services/chat_service.py` - Per-project chat persistence (`artifacts/chat.json`)
- `src/web/services/preview_service.py` - Manages subprocesses for live preview of generated apps
- `src/web/services/task_service.py` - Background generation with per-project serialization

## Project Structure

```
config/settings.py                  # Pydantic-settings configuration
src/core/orchestrator.py            # Main pipeline coordinator
src/cli.py                          # Click CLI
src/web/app.py                      # Flask web backend
src/web/api/projects.py             # REST API endpoints
src/web/services/chat_service.py    # Chat persistence (artifacts/chat.json)
src/web/services/preview_service.py # Live preview subprocess manager
src/web/services/task_service.py    # Background generation tasks
templates/flask_base/               # Flask app template for code generation
templates/index.html                # Build Studio UI (chat + code + preview)
data/projects/{id}/                 # Generated project artifacts
tests/                              # Unit tests (mocked, no API key needed)
```

## Environment Variables

Key settings in `.env`:
- `OPENAI_API_KEY` - Required
- `OPENAI_MODEL` - Default: gpt-4o
- `OPENAI_BASE_URL` - Custom endpoint (OpenRouter, Azure, etc.)
- `ENABLE_CODE_MEMORY`, `ENABLE_CODE_MINING` - Off by default
- `ENABLE_VISUAL_VERIFICATION`, `ENABLE_BDD_TESTING` - Feature flags

## Key Patterns

- Agents are standalone classes taking `LLMService` in constructor; they do **not** inherit from `AgentBase`
- Stage execution happens in `Orchestrator.run()` with run-fix loop in Stage 4
- Code generation uses interface-first: generates `.pyi` files, then dependency graph, then implementations
- `CodeSkeleton` is built from pyi stubs via `src/utils/skeleton_builder.py` and injected into the LLM prompt
- Generated apps are saved to `data/projects/{id}/generated/`

## Web Flow (Chat-first)

1. `POST /api/projects {"start_chat": true}` → creates project dirs, returns `project_id`
2. `POST /api/projects/<id>/chat {"message": "..."}` → appends user msg, gets AI reply, auto-triggers generation
3. First generation: `conversation_to_requirements()` → `orchestrator.run_from_stage_2()`
4. Incremental: `merge_requirements(existing, new_msg)` → `orchestrator.run_from_stage_2()`
5. After generation completes, `preview_service.start_preview()` launches the app on a dynamic port
6. `GET /api/projects/<id>/preview-url` returns the live URL for iframe embedding
7. Per-project serialization: only one generation runs per project; subsequent requests queue and re-run
