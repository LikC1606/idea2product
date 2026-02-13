# Idea2Product

A multi-agent system that transforms user requirements into production-ready web applications.

## Overview

Idea2Product is an end-to-end automated software generation framework that bridges the gap between AI model capabilities and deployable applications. The system uses 10 specialized agents across 4 stages to automatically handle requirement clarification, technical planning, code generation, and validation.

## Architecture

The system consists of 4 stages:

1. **Stage 1 - Requirements**: Interaction Agent clarifies user requirements through multi-turn dialogue
2. **Stage 2 - Planning**: Task Division, Algorithm Analysis, and Scheme Planning agents create a comprehensive engineering plan
3. **Stage 3 - Code Generation**: Code Generation, Code Memory, and Code Mining agents produce working code
4. **Stage 4 - Validation**: Black-box Testing and Fine-tuning agents validate and fix the generated code

## Installation

### Prerequisites

- Python 3.9 or higher
- Anthropic API key (Claude)
- Git (optional, for code mining features)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd idea2product
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

Or install in development mode:
```bash
pip install -e .
```

3. Configure environment variables:
```bash
cp .env.example .env
```

Edit `.env` and add your `ANTHROPIC_API_KEY`.

## Usage

### Command Line Interface

Create a new web application from a requirement:

```bash
python -m src.cli create "Build a todo list app with add, delete, and complete functionality"
```

Check project status:

```bash
python -m src.cli status proj_20260213_001
```

List all projects:

```bash
python -m src.cli list
```

### Example Output

```
[Stage 1] Interaction: Clarifying requirements...
[Stage 1] Interaction: Requirements finalized
[Stage 2] Planning: Dividing into tasks...
[Stage 2] Planning: Analyzing algorithms...
[Stage 2] Planning: Engineering plan created
[Stage 3] Generation: Generating code...
[Stage 3] Generation: 8 files generated
[Stage 4] Validation: Running tests...
[Stage 4] Validation: Tests passed!

✓ Project generated successfully!
Location: data/projects/proj_20260213_001/generated/
Run: cd data/projects/proj_20260213_001/generated && python backend/app.py
```

## Project Structure

```
idea2product/
├── src/                    # Source code
│   ├── core/              # Core infrastructure
│   ├── agents/            # 10 specialized agents
│   ├── services/          # Supporting services
│   └── utils/             # Utilities
├── config/                # Configuration and prompts
├── templates/             # Code generation templates
├── data/                  # Generated projects and database
├── tests/                 # Test suite
└── docs/                  # Documentation
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Quality

Format code:
```bash
black src/ tests/
```

Lint code:
```bash
ruff check src/ tests/
```

Type checking:
```bash
mypy src/
```

## Documentation

- [Architecture Documentation](docs/architecture.md)
- [Agent Specifications](docs/agent_specifications.md)
- [Implementation Plan](.claude/plans/wise-strolling-hamster.md)

## Research Context

This project is part of research into bridging the gap between AI model capabilities and production-ready applications. See [plan.txt](plan.txt) for the complete research proposal.

## License

MIT License (or your chosen license)

## Contributing

Contributions are welcome! Please read the contributing guidelines first.

## Citation

If you use this work in your research, please cite:

```bibtex
@software{idea2product2026,
  title={Idea2Product: Multi-Agent System for Automated Application Generation},
  author={Research Team},
  year={2026},
  url={https://github.com/yourusername/idea2product}
}
```
