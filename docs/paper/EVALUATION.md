# Evaluation Setup (Paper)

This document describes the experimental setup for paper evaluation.

## Task Set

### Small Set (3 tasks)

- **todo**: Build a todo list app with add, delete, and complete functionality
- **calculator**: Build a calculator app with add, subtract, multiply, and divide
- **weather**: A weather widget showing current temperature for a city

### Extended Set (16 tasks)

The extended set adds CRUD, auth, multi-page, and API-focused tasks:

- **blog**: Blog app with posts, add/edit/delete, author display
- **notes**: Notes app with create, list, edit, delete
- **auth**: Simple app with user login/logout, protected dashboard
- **contacts**: Contacts app with add, search, edit, delete
- **inventory**: Inventory tracker with add item, list, update quantity
- **expenses**: Expense tracker with add expense, list by category, total sum
- **bookmarks**: Bookmark manager with add URL, list, delete
- **recipes**: Recipe app with add recipe, list, view details
- **tasks**: Task manager with create, assign priority, filter by status
- **timer**: Timer app with start, stop, reset
- **counter**: Counter app with increment, decrement, reset
- **quotes**: Random quote display with next quote button
- **form_demo**: Multi-step registration form
- **api_demo**: REST API for product catalog CRUD

## Metrics

| Metric | Description |
|--------|-------------|
| **Success rate** | Pipeline completed without exception |
| **Deployable rate** | ValidatedProject.is_deployable |
| **Test pass rate** | BDD + syntax + run tests passed |
| **alignment_score** | Visual-semantic alignment (0-1) |
| **code_quality_score** | Ruff E,F,B (0-1) |
| **security_score** | Bandit scan (0-1) |
| **env_install_success** | Dependency install success |
| **env_start_success** | Service start success |
| **Pass@k** | Fraction of k runs that pass all tests |

## Baselines

- **baseline**: Pipeline with Code Memory, Code Mining, BDD, and Visual Verification disabled
- Run: `python -m src.benchmarks.run_baseline --tasks small`

## Commands

```bash
# Full pipeline (default: small task set)
python -m src.benchmarks.run_small_suite

# Extended task set
python -m src.benchmarks.run_small_suite --tasks full

# Baseline comparison
python -m src.benchmarks.run_baseline --tasks small

# Ablation: disable specific features
python -m src.benchmarks.run_small_suite --config no_code_memory
python -m src.benchmarks.run_small_suite --config no_code_mining
python -m src.benchmarks.run_small_suite --config no_visual
python -m src.benchmarks.run_small_suite --config no_bdd

# Multiple runs for statistics (mean ± std)
python -m src.benchmarks.run_small_suite --runs 5

# Pass@k
python -m src.benchmarks.run_small_suite --pass-at-k 3
```

## Output

- `data/benchmark_report.json` – full config
- `data/benchmark_report_<config>.json` – ablation configs
- `data/ablation_summary.md` – aggregated table (run `python -m src.benchmarks.aggregate_ablation`)
