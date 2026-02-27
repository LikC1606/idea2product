# Reproducibility Guide

This document describes how to reproduce Idea2Product results for research and evaluation.

## Environment

- **Python**: 3.9, 3.10, 3.11, or 3.12
- **OS**: Linux, macOS, or Windows
- **Dependencies**: See `requirements-pinned.txt` for exact versions

## Installation (Exact Versions)

For maximum reproducibility, use the pinned requirements:

```bash
git clone https://github.com/yourusername/idea2product.git
cd idea2product
python -m venv venv
# Linux/Mac: source venv/bin/activate
# Windows: venv\Scripts\activate
pip install -r requirements-pinned.txt
pip install -e .
```

If `requirements-pinned.txt` is outdated, regenerate it:

```bash
pip install -r requirements.txt
pip freeze | grep -E "^(openai|pydantic|langchain|flask|click|rich|...)" > requirements-pinned.txt
```

## Configuration

```bash
cp .env.example .env
# Set OPENAI_API_KEY=sk-...
```

Optional: Set `RANDOM_SEED=42` in `.env` for more deterministic behavior where applicable (LLM outputs remain non-deterministic).

## Expected Output

### CLI Mode

```bash
python -m src.cli create "Build a todo list app"
```

- Project saved to `data/projects/<project_id>/generated/`
- Artifacts in `data/projects/<project_id>/artifacts/`:
  - `01_requirements.json`
  - `02_engineering_plan.json`
  - `03_code_repository.json`
  - `chat.json`, `context.json`, `task_status.json`

### Benchmark Suite

```bash
python -m src.benchmarks.run_small_suite
```

- Output: `data/benchmark_report.json`
- Metrics: success_rate, deployable_rate, duration, fix_attempts, BDD pass rate

### Offline Evaluation

For evaluation without API calls, see `docs/paper/EVALUATION.md` (if available) or run unit tests:

```bash
pytest tests/ -v
```

## Version Information

Record your environment when reporting results:

```bash
python --version
pip list
```

## Citations

If you use Idea2Product in research, please cite the repository and include:
- Python version
- Dependency versions (from `pip freeze` or `requirements-pinned.txt`)
- Model used (e.g., gpt-4o, gpt-4o-mini)
- Any custom configuration
