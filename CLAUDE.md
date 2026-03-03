# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Quick Start

```bash
pip install -r requirements.txt
pip install -e .
cp .env.example .env  # Configure API key for your primary provider (OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY)
```

## Common Commands

```bash
# CLI
python -m src.cli create "Build a todo app"
python -m src.cli create -i "Build a todo app"   # interactive Q&A mode
python -m src.cli from-paper paper.pdf            # analyze paper and get app ideas (optional: --generate, --context)
python -m src.cli list
python -m src.cli status <project_id>

# Web backend (serves frontend from frontend/dist after build)
cd frontend && npm run build && cd ..
python -m src.web.app

# Frontend dev (Vite dev server with proxy to Flask on 8080)
cd frontend && npm run dev

# Testing & code quality
pytest tests/ -v
python -m src.benchmarks.run_small_suite  # requires OPENAI_API_KEY
python scripts/check_bugs.py markdown
black src/ tests/
ruff check src/
mypy src/
```

## Architecture

4-stage pipeline: Requirements → Planning → Code Generation → Validation.

### Key Files

- `src/core/orchestrator.py` — Coordinates all stages
- `src/core/context.py` — ExecutionContext
- `src/core/data_models.py` — Requirements, EngineeringPlan, CodeRepository, ValidatedProject
- `config/settings.py` — Configuration, feature flags

### Agent Locations

- `src/agents/stage1_requirements/` — InteractionAgent, PaperToProjectAgent
- `src/agents/stage2_planning/` — FlowSimulation, TaskDivision, AlgorithmAnalysis, SchemePlanning
- `src/agents/stage3_generation/` — CodeGeneration, CodeMemory, CodeMining
- `src/agents/stage4_validation/` — FullCycleTesting, FineTuning, VisualVerification

### Services

- `src/services/llm_service.py` — OpenAI API (use `LLMService.from_settings(settings)`)
- `src/web/services/chat_service.py` — Chat persistence
- `src/web/services/preview_service.py` — Live preview
- `src/web/services/task_service.py` — Background generation

## Environment Variables

- **Primary LLM** — `PRIMARY_LLM_PROVIDER` = `openai` | `anthropic` | `google`. At least the selected provider's key must be set.
- **OpenAI** — `OPENAI_API_KEY` (required when primary=openai), `OPENAI_MODEL`, `OPENAI_BASE_URL`, `OPENAI_VLM_MODEL`
- **Anthropic (Claude)** — `ANTHROPIC_API_KEY` (when primary=anthropic), `ANTHROPIC_BASE_URL` (default OpenRouter), `ANTHROPIC_MODEL`
- **Google (Gemini)** — `GOOGLE_API_KEY` (when primary=google), `GOOGLE_BASE_URL`, `GOOGLE_MODEL`
- `ENABLE_CODE_MEMORY`, `ENABLE_CODE_MINING`, `ENABLE_VISUAL_VERIFICATION`, `ENABLE_BDD_TESTING` — Feature flags
- `ENABLE_CODE_MEMORY`, `ENABLE_CODE_MINING`, `ENABLE_VISUAL_VERIFICATION`, `ENABLE_BDD_TESTING` — Feature flags
- `VALIDATION_PORT` — Port for FullCycleTesting/FrontendTesting/VisualVerification/CodeFix (default 5555)
- `WARN_UNUSED_FILES`, `BDD_TEST_TIMEOUT_SECONDS` — FullCycleTesting Agent (unused file warnings, pytest timeout)
- `FINE_TUNING_MAX_CONTEXT_CHARS`, `USE_FAST_MODEL_FOR_FINE_TUNING_SYNTAX` — FineTuning Agent (LLM context limit, fast model for syntax fix)
- `CODE_MEMORY_PREFETCH_MAX_QUERIES`, `CODE_MEMORY_CONTEXT_MAX_CHARS` — Code Memory Agent prefetch limits
- `SKIP_FLOW_EXTRACTION`, `USE_FAST_MODEL_FOR_TASK_REVIEW`, `FAST_MODEL_FOR_REVIEW` — Task Division Agent
- `SKIP_HF_FOR_SIMPLE_TASKS`, `SKIP_FLOW_IN_ALGORITHM`, `ENABLE_HF_CACHE` — Algorithm Analysis Agent
- `SKIP_API_REVIEW_WHEN_SIMPLE`, `USE_FAST_MODEL_FOR_API_REVIEW`, `SKIP_FLOW_IN_SCHEME_PLANNING` — Scheme Planning Agent
- `USE_FAST_MODEL_FOR_SIMPLE_CODE_TASKS`, `FAST_MODEL_FOR_CODE_GEN`, `SKIP_MINING_FOR_SIMPLE_TASKS`, `ENABLE_STAGE3_SYNTAX_CHECK`, `ENABLE_STAGE3_IMPORT_SANITY_CHECK` — Code Generation Agent
- `CODE_MINING_PARALLEL_WORKERS`, `CODE_MINING_MAX_CONTEXT_CHARS`, `CODE_MINING_DEDUPLICATE_QUERIES` — Code Mining Agent
- `ENABLE_PARALLEL_STAGE3_PREFETCH` — When True (default), run CodeMemory pre_execute and CodeMining execute in parallel in Stage 3
- `MAX_SYSTEM_PROMPT_CHARS`, `USE_FAST_MODEL_FOR_SYNTAX_FIX`, `CODE_GEN_SYNTAX_FIX_RETRIES` — Code Generation Agent
- `ENABLE_IMAGE_GENERATION`, `IMAGE_GENERATION_PROVIDER` — Image generation (openai | generic_http); when True, Stage 3 runs asset generation (hero/placeholder images to generated/static/images/)
- `IMAGE_GENERATION_OPENAI_MODEL`, `IMAGE_GENERATION_BASE_URL`, `IMAGE_GENERATION_API_KEY` — OpenAI DALL-E or generic HTTP provider; `IMAGE_GENERATION_RESPONSE_IMAGE_PATH`, `IMAGE_GENERATION_EXTRA_HEADERS`, `IMAGE_GENERATION_TIMEOUT` for generic_http
- `ENABLE_VIDEO_GENERATION`, `VIDEO_GENERATION_PROVIDER`, `VIDEO_GENERATION_BASE_URL`, `VIDEO_GENERATION_API_KEY` — Optional video generation service（text/script → mp4），用于教程/演示视频等
- `ENABLE_PPT_GENERATION`, `PPT_GENERATION_PROVIDER`, `PPT_GENERATION_BASE_URL`, `PPT_GENERATION_API_KEY` — Optional PPT 生成服务（结构化大纲 → pptx）
- `ENABLE_LATEX_GENERATION`, `LATEX_GENERATION_PROVIDER`, `LATEX_GENERATION_BASE_URL`, `LATEX_GENERATION_API_KEY` — Optional LaTeX/PDF 生成服务（文档导出）
- `ENABLE_AUDIO_GENERATION`, `AUDIO_GENERATION_PROVIDER`, `AUDIO_GENERATION_BASE_URL`, `AUDIO_GENERATION_API_KEY` — Optional 音频生成服务（TTS/音乐）
- `ENABLE_STAGE2_WEB_SEARCH`, `WEB_SEARCH_PROVIDER`, `WEB_SEARCH_API_KEY` — Stage 2 model discovery: when True, ModelIntegrationPlanningAgent searches web for external APIs and writes plan.external_model_specs; Serper uses WEB_SEARCH_API_KEY or SERPER_API_KEY
- `EXPOSE_ERROR_DETAILS` — When True, 500 API responses may include error details; when False (default), return generic "Internal server error" only; server always logs full exception

## Key Patterns

- Agents are standalone classes taking `LLMService`; they do **not** inherit from AgentBase
- Interface-first: .pyi stubs → dependency graph → implementations
- CodeSkeleton built via `src/utils/skeleton_builder.py`
- Generated apps in `data/projects/{id}/generated/`

## Further Documentation

Detailed architecture, Agent I/O, data models, Web flow, and code-gen specs: **docs/CONTEXT_INDEX.md**
