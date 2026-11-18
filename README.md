<!-- README_SYNC: source=8e9c0125f75c21c72dcd7be5d76646e42a6f44ce; updated=2026-11-18 -->
<p align="center">English · <a href="./README_CN.md" lang="zh-CN">简体中文</a></p>

# Idea2Product

Idea2Product turns a plain-language brief into a Flask app you can inspect and run locally. It saves the requirements, engineering plan, generated source, and validation logs along the way so you can see where a result came from and what still needs work.

[Star the repository](https://github.com/LikC1606/idea2product) to find the pipeline and evaluation references again.

<a href="https://github.com/LikC1606/idea2product"><img alt="GitHub stars" src="https://img.shields.io/github/stars/LikC1606/idea2product"></a>
<a href="./pyproject.toml"><img alt="Project version 0.1.0" src="https://img.shields.io/badge/version-0.1.0-blue"></a>
<a href="./.github/workflows/ci.yml"><img alt="CI configuration" src="https://img.shields.io/badge/checks-CI_workflow-2f855a"></a>
<a href="./frontend/package.json"><img alt="Frontend: Vue 3" src="https://img.shields.io/badge/frontend-Vue_3-42b883"></a>

Use the Python CLI for a single brief, or open Build Studio for a chat workflow with source and preview panels. Generated code is prototype output: review the code, dependencies, and validation results before deploying it.

## Quick start

Use Python 3.12 and Git. The commands below are for a Unix shell; [requirements.txt](./requirements.txt) lists the dependencies. Start with this file: the older [pinned list](./requirements-pinned.txt) predates the current `langchain.agents.create_agent` import.

```bash
git clone https://github.com/LikC1606/idea2product.git
cd idea2product
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m src.cli --help
cp .env.example .env
```

Use [.env.example](./.env.example) as a reference when editing `.env`. Set `PRIMARY_LLM_PROVIDER` to `openai`, `anthropic`, or `google`, and fill in the matching API key. Non-OpenAI settings use a compatible endpoint configured with the provider's base URL. Keep secrets out of Git. Generation calls your configured model service and may incur usage charges.

```bash
python -m src.cli create "Build a todo app that can add, complete, and delete tasks"
```

When generation succeeds, the CLI reports the project location and entry point. Review `generated/` and its local run instructions, plus the validation output. The CLI's `-i` option lets it ask clarifying questions first. Replace `PROJECT_ID` below with the ID printed by the CLI.

```bash
python -m src.cli create --help
python -m src.cli list
python -m src.cli status PROJECT_ID
python -m src.cli from-paper --help
```

## Build Studio in the browser

Use Node.js 20.19+ on the 20.x line or 22.12+ for the Vite frontend. From the project root with the Python environment active:

```bash
npm ci --prefix frontend
npm run build --prefix frontend
HOST=127.0.0.1 PORT=8080 python -m src.web.app
```

Open `http://127.0.0.1:8080`. Flask serves the built Vue interface and API. Build Studio keeps the conversation, generated files, and preview together. For the development proxy, REST endpoints, and preview subprocesses, see the [Web flow reference](./docs/refs/WEB_FLOW_REF.md).

## What the pipeline saves

| Stage | Result |
| --- | --- |
| Requirements | A structured brief with features and constraints |
| Planning | User flows, tasks, APIs, file layout and interface stubs |
| Generation | Source files, generated in dependency order from the planned interfaces |
| Validation | Test and startup results, with repair attempts or optional BDD and visual checks |

```text
data/projects/<project_id>/
  artifacts/
    01_requirements.json
    02_engineering_plan.json
    03_code_repository.json
    context.json
  generated/
  logs/
```

The [architecture guide](./docs/ARCHITECTURE.md) explains the agents and handoffs. The [artifact and data model reference](./docs/refs/DATA_MODELS_REF.md) describes what those records contain.

## Development and evaluation

- The [documentation index](./docs/CONTEXT_INDEX.md) links to agent, provider, and configuration references. See [troubleshooting](./docs/TROUBLESHOOTING.md) for dependency, provider, or preview failures.
- The [benchmark guide](./docs/BENCHMARK.md) and [research evaluation protocol](./docs/paper/EVALUATION.md) cover task definitions and metrics. Live benchmark modes call the model provider. Record the model, dependency versions, and feature flags for reproducible comparisons.
- The [CI workflow](./.github/workflows/ci.yml) lists test and lint commands. Check that the agent reference still matches the source with:

```bash
python scripts/check_docs.py
```

The repository does not currently include a license file. No MIT or other reuse license is asserted here.

[Report reproducible issues](https://github.com/LikC1606/idea2product/issues) with the failing stage and relevant logs. [Star Idea2Product](https://github.com/LikC1606/idea2product) to keep the reference handy.
