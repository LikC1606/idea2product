# Idea2Product

A multi-agent AI system that transforms natural language requirements into production-ready web applications through a 4-stage pipeline with 10 specialized agents.

## Overview

Idea2Product bridges the gap between AI capabilities and deployable applications. It automatically handles:
- **Requirements Gathering**: Multi-turn dialogue to clarify user needs
- **Technical Planning**: Task division, algorithm analysis, and engineering specifications
- **Code Generation**: Generates working code with dependency resolution
- **Validation**: BDD testing, visual verification, and automatic bug fixing

## Architecture

| Stage | Purpose | Agents |
|-------|---------|--------|
| **Stage 1** | Requirements Gathering | Interaction Agent |
| **Stage 2** | Technical Planning | Task Division, Algorithm Analysis, Scheme Planning |
| **Stage 3** | Code Generation | Code Generation, Code Memory, Code Mining |
| **Stage 4** | Validation | BDD Testing, Visual Verification, Fine-tuning |

### Key Technical Innovations
- **Interface-First Strategy**: Generates `.pyi` interfaces first, then dependency graph, then implementations
- **Code Memory Agent**: Builds dynamic knowledge graph with AST analysis
- **Code Mining Agent**: Retrieves and adapts external code via GitHub
- **Visual Verification**: Uses GPT-4o Vision for UI rendering verification
- **Automatic Test Execution**: Runs generated pytest tests and fixes failures

## Installation

### Prerequisites

- Python 3.9 or higher
- OpenAI API key (GPT-4o)
- Git (optional, for code mining)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd idea2product
```

2. Install dependencies:
```bash
pip install -r requirements.txt
pip install -e .  # Development mode
```

3. Configure environment variables:
```bash
cp .env.example .env
```

Edit `.env` and configure:
```env
OPENAI_API_KEY=your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1  # Or custom endpoint
OPENAI_MODEL=gpt-4o
```

## Quick Start

### Create a New Project

```bash
python -m src.cli create "Build a todo list app with add, delete, and complete functionality"
```

The system will:
1. Clarify requirements through interactive dialogue
2. Generate technical specifications
3. Produce working code with dependencies
4. Run tests and fix any issues

### CLI Commands

```bash
# Create new project (interactive)
python -m src.cli create "Your app description"

# Create non-interactive (skip clarification)
python -m src.cli create "Your app description" --no-interactive

# Check project status
python -m src.cli status proj_20260214_xxx

# List all projects
python -m src.cli list

# View project details
python -m src.cli details proj_20260214_xxx
```

## Project Output

Generated projects are stored in `data/projects/{project_id}/`:

```
data/projects/proj_20260214_xxx/
├── context.json          # Requirements context
├── plan.json             # Technical specifications
├── generated/            # Generated source code
│   ├── app/
│   ├── models/
│   ├── services/
│   └── tests/
└── logs/                 # Execution logs
```

## Running Generated Apps

After successful generation, run your app:

```bash
cd data/projects/{project_id}/generated
python -m flask run  # For web apps
# or
python app.py        # For standalone apps
```

## Development

### Running Tests

```bash
pytest tests/                          # All tests
pytest tests/test_file.py              # Specific file
pytest tests/test_file.py::test_name   # Specific test
```

### Code Quality

```bash
black src/ tests/      # Format code
ruff check src/ tests/ # Lint code
mypy src/              # Type checking
```

## Configuration

All settings are in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | - | Required API key |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | API endpoint |
| `OPENAI_MODEL` | `gpt-4o` | LLM model |
| `OPENAI_VLM_MODEL` | `gpt-4o` | Vision model for UI verification |
| `MAX_TOKENS` | `4096` | Max response tokens |
| `TEMPERATURE` | `0.7` | LLM creativity |
| `GITHUB_TOKEN` | - | Optional, for code mining |
| `LOG_LEVEL` | `INFO` | Logging level |

## Implementation Status

| Component | Status |
|-----------|--------|
| Stage 1 (Requirements) | ✅ Implemented |
| Stage 2 (Planning) | ✅ Implemented |
| Stage 3 (Code Generation) | ✅ Implemented |
| Stage 4 (Validation) | ✅ Implemented |

Core infrastructure complete. Agent logic handles dependency resolution, test execution, and automatic bug fixing.

## License

MIT License
