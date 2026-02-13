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

### Running the CLI
```bash
python -m src.cli create "Build a todo list app with add, delete, and complete functionality"
python -m src.cli status proj_20260213_001
python -m src.cli list
```

### Testing
```bash
pytest tests/                          # Run all tests
pytest tests/path/to/test_file.py      # Run specific test file
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
| **Stage 4** | Validation | BDD Testing, Visual Verification (GPT-4o), Fine-tuning |

### Key Technical Innovations
- **Interface-First Strategy**: Generates `.pyi` interfaces first, then dependency graph, then implementations
- **Code Memory Agent**: Builds dynamic knowledge graph with AST and global symbol table
- **Code Mining Agent**: Retrieves and adapts external code to current project architecture
- **Visual Verification**: Uses GPT-4o Vision for UI rendering verification
- **BDD Testing**: Generates Gherkin-style Given-When-Then test cases

### Directory Structure
```
src/
├── core/           # Orchestrator, data models, context management
├── agents/         # Stage 1-4 agent implementations (mostly stub)
├── services/       # LLM, code memory, code mining, execution services
├── utils/          # Utilities
└── cli.py          # Command-line interface

config/
├── settings.py     # Pydantic settings
└── prompts/        # Agent prompt templates

templates/          # Web app code generation templates
data/               # Generated projects and SQLite code memory
tests/              # Test suite (pytest + pytest-bdd)
```

### Core Components
- **Orchestrator** ([src/core/orchestrator.py](src/core/orchestrator.py)): Coordinates the 4-stage workflow
- **LLMService** ([src/services/llm_service.py](src/services/llm_service.py)): Manages OpenAI API calls
- **CodeMemoryService** ([src/services/code_memory_service.py](src/services/code_memory_service.py)): SQLite-based code knowledge graph
- **CodeMiningService** ([src/services/code_mining_service.py](src/services/code_mining_service.py)): External code retrieval

### Implementation Status
The core infrastructure is complete. Agent logic in `src/agents/` is in early MVP phase - most `execute_stage_X()` methods raise `NotImplementedError`.
