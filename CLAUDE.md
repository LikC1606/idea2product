# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Idea2Product is a **multi-agent AI system for automated web application generation** that transforms natural language requirements into production-ready web applications through a 4-stage pipeline with 10 specialized agents.

## Common Commands

### Setup
```bash
pip install -r requirements.txt
pip install -e .  # Development mode
```

### Environment Variables
Copy `.env.example` to `.env` and configure:
- `OPENAI_API_KEY` - Required for LLM calls (uses GPT-4o by default)
- `OPENAI_BASE_URL` - Custom API endpoint (e.g., OpenRouter, Azure OpenAI)
- `GITHUB_TOKEN` - Optional, for code mining features
- `OPENAI_MODEL` - Default: `gpt-4o`
- `OPENAI_VLM_MODEL` - For visual verification, default: `gpt-4o`
- `MAX_TOKENS` - Default: `4096`
- `TEMPERATURE` - Default: `0.7`
- `LOG_LEVEL` - Default: `INFO`

**Feature flags** (all default to `true`):
- `ENABLE_CODE_MINING` - Enable external code retrieval from GitHub
- `ENABLE_VISUAL_VERIFICATION` - Enable GPT-4o Vision UI verification
- `ENABLE_BDD_TESTING` - Enable BDD test generation and execution

**Note**: `.env` file takes priority over environment variables. Settings in [config/settings.py](config/settings.py) ensures .env is loaded first.

### Running the CLI
```bash
python -m src.cli create "Build a todo list app"           # Create new project
python -m src.cli create "Build a todo app" --no-interactive  # Skip clarification
python -m src.cli status proj_xxx                          # Check project status
python -m src.cli list                                     # List all projects
python -m src.cli details proj_xxx                        # View project details
```

### Testing
```bash
pytest tests/                                       # Run all tests
pytest tests/path/to/test_file.py                  # Run specific test file
pytest tests/path/to/test_file.py::test_function_name  # Run specific test
```

### Code Quality
```bash
black src/ tests/    # Format code
ruff check src/ tests/  # Lint code
mypy src/            # Type checking
```

## Architecture

### 4-Stage Pipeline
| Stage | Purpose | Key Agents |
|-------|---------|------------|
| **Stage 1** | Requirements Gathering | Interaction Agent (multi-turn dialogue) |
| **Stage 2** | Technical Planning | Task Division, Algorithm Analysis, Scheme Planning |
| **Stage 3** | Code Generation | Code Generation, Code Memory, Code Mining |
| **Stage 4** | Validation | BDD Testing, Visual Verification, Fine-tuning |

### The 10 Agents
Located in [src/agents/](src/agents/):
- **Stage 1**: [interaction_agent.py](src/agents/stage1_requirements/interaction_agent.py) - Clarifies requirements via dialogue
- **Stage 2**: [planning_agents.py](src/agents/stage2_planning/planning_agents.py) - TaskDivision, AlgorithmAnalysis, SchemePlanning
- **Stage 3**: [code_generation_agents.py](src/agents/stage3_generation/code_generation_agents.py) - CodeGeneration, CodeMemory, CodeMining
- **Stage 4**: [validation_agents.py](src/agents/stage4_validation/validation_agents.py) - FullCycleTesting, FineTuning, VisualVerification

### Key Technical Innovations
- **Interface-First Strategy**: Generates `.pyi` interfaces first, then dependency graph, then implementations
- **Code Memory Agent**: Builds dynamic knowledge graph with AST and global symbol table (SQLite-based)
- **Code Mining Agent**: Retrieves and adapts external code from GitHub to current project architecture
- **Visual Verification**: Uses GPT-4o Vision for UI rendering verification
- **BDD Testing**: Generates Gherkin-style Given-When-Then test cases

### Core Components
- **Orchestrator** ([src/core/orchestrator.py](src/core/orchestrator.py)): Coordinates the 4-stage workflow, manages ExecutionContext
- **LLMService** ([src/services/llm_service.py](src/services/llm_service.py)): Manages OpenAI API calls (GPT-4o)
- **CodeMemoryService** ([src/services/code_memory_service.py](src/services/code_memory_service.py)): SQLite-based code knowledge graph at `data/code_memory.db`
- **CodeMiningService** ([src/services/code_mining_service.py](src/services/code_mining_service.py)): External code retrieval via GitHub
- **ExecutionService** ([src/services/execution_service.py](src/services/execution_service.py)): Runs generated applications in sandbox
- **Data Models** ([src/core/data_models.py](src/core/data_models.py)): Requirements, EngineeringPlan, CodeRepository, ValidatedProject
- **Settings** ([config/settings.py](config/settings.py)): Centralized configuration with pydantic, loads from `.env`

### Base Classes
- **AgentBase** ([src/core/agent_base.py](src/core/agent_base.py)): Abstract base class for all agents, provides LLM access and context management
- **ExecutionContext** ([src/core/context.py](src/core/context.py)): Carries state through the pipeline, stores requirements, plans, generated code, and validation results

### Key Paths
- `config/prompts/` - Agent prompt templates (created at runtime if missing)
- `templates/` - Code generation templates
- `data/code_memory.db` - SQLite database for code knowledge graph

### Data Flow
1. Project created in `data/projects/{project_id}/`
2. Stage 1 stores requirements in `artifacts/01_requirements.json`
3. Stage 2 generates `artifacts/02_engineering_plan.json` with engineering specifications
4. Stage 3 outputs code to `generated/` directory
5. Stage 4 runs BDD tests and visual verification, saves `artifacts/04_validated_project.json`

### Project Directory Structure
```
data/projects/{project_id}/
├── artifacts/          # JSON artifacts from each stage
│   ├── 01_requirements.json
│   ├── 02_engineering_plan.json
│   ├── 03_code_repository.json
│   ├── 04_validated_project.json
│   └── context.json    # Full execution context
├── generated/          # Final generated code
├── logs/               # Execution logs
└── orchestrator.log
```

### Implementation Status
- **Stage 1**: Fully implemented - Interaction Agent handles both interactive and non-interactive modes
- **Stage 2**: Implemented - TaskDivision, AlgorithmAnalysis, SchemePlanning agents work
- **Stage 3**: Implemented - CodeGeneration with dependency resolution, generates missing stubs for config/models/controllers/services, cleans markdown code blocks
- **Stage 4**: Implemented - Runs actual pytest tests, FineTuningAgent fixes syntax/import errors, generates __init__.py files

### Documentation
- [README.md](README.md) - Project overview and quick reference
- [TUTORIAL.md](TUTORIAL.md) - Step-by-step usage guide with examples
