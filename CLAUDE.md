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
python -m src.cli create "Build a todo app" --no-interactive
python -m src.cli list
python -m src.cli status <project_id>

# Web backend
python -m src.web.app --port 5000

# Testing & code quality
pytest tests/ -v
black src/ tests/
ruff check src/
mypy src/
```

## Architecture

A 4-stage pipeline with 10 specialized agents that transform natural language requirements into production-ready applications.

### Pipeline Flow
1. **Stage 1** (Requirements) - Interaction Agent clarifies requirements via dialogue
2. **Stage 2** (Planning) - TaskDivision, AlgorithmAnalysis, SchemePlanning agents create specs
3. **Stage 3** (Code Generation) - Generates code with interface-first strategy, dependency resolution
4. **Stage 4** (Validation) - BDD testing, visual verification, automatic bug fixing

### Key Files
- [orchestrator.py](src/core/orchestrator.py) - Coordinates all stages
- [context.py](src/core/context.py) - ExecutionContext carries state through pipeline
- [agent_base.py](src/core/agent_base.py) - Abstract base for all agents
- [data_models.py](src/core/data_models.py) - Requirements, EngineeringPlan, CodeRepository, ValidatedProject

### Agent Locations
- [stage1_requirements/](src/agents/stage1_requirements/) - Interaction Agent
- [stage2_planning/](src/agents/stage2_planning/) - Planning agents
- [stage3_generation/](src/agents/stage3_generation/) - Code generation with memory/mining
- [stage4_validation/](src/agents/stage4_validation/) - Testing and verification

### Services
- [llm_service.py](src/services/llm_service.py) - OpenAI API calls
- [code_memory_service.py](src/services/code_memory_service.py) - SQLite knowledge graph (`data/code_memory.db`)
- [code_mining_service.py](src/services/code_mining_service.py) - GitHub code retrieval

## Project Structure

```
data/projects/{project_id}/
├── artifacts/
│   ├── 01_requirements.json
│   ├── 02_engineering_plan.json
│   ├── 03_code_repository.json
│   ├── 04_validated_project.json
│   └── context.json
├── generated/          # Final application code
└── logs/
```

## Environment Variables

Key settings in `.env`:
- `OPENAI_API_KEY` - Required
- `OPENAI_MODEL` - Default: gpt-4o
- `OPENAI_BASE_URL` - Custom endpoint (OpenRouter, Azure, etc.)
- `ENABLE_CODE_MINING`, `ENABLE_VISUAL_VERIFICATION`, `ENABLE_BDD_TESTING` - Feature flags

## Key Patterns

- Agents inherit from `AgentBase` and implement `execute(context)` returning typed results
- Stage execution happens in `Orchestrator.run()` with run-fix loop in Stage 4
- Code generation uses interface-first: generates `.pyi` files, then dependency graph, then implementations
- Generated apps can be run directly from `data/projects/{id}/generated/`

## Documentation
- [README.md](README.md) - Full overview
- [TUTORIAL.md](TUTORIAL.md) - Step-by-step guide
