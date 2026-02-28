# Benchmark and Evaluation

## Current metrics (run_small_suite)

The script `python -m src.benchmarks.run_small_suite` runs a small set of tasks (Todo, Calculator, Weather) and writes `data/benchmark_report.json`.

```bash
python -m src.benchmarks.run_small_suite           # CLI mode (default: small=3 tasks)
python -m src.benchmarks.run_small_suite --tasks full   # Extended 16 tasks
python -m src.benchmarks.run_small_suite chat      # Chat workflow mode
python -m src.benchmarks.run_small_suite --pass-at-k 3  # Pass@k (run each task 3x)
python -m src.benchmarks.run_small_suite --config no_code_memory  # Ablation
python -m src.benchmarks.run_small_suite --runs 5  # Mean±std statistics
python -m src.benchmarks.run_small_suite --offline # Offline (no LLM)
python -m src.benchmarks.run_baseline              # Baseline (no Code Memory/Mining/BDD/Visual)
```

### Per-task fields

| Field | Description |
|-------|-------------|
| `task_id` | Identifier (e.g. todo, calculator, weather) |
| `requirement` | Input requirement text |
| `success` | Pipeline completed without exception |
| `is_deployable` | ValidatedProject.is_deployable |
| `files_count` | Number of generated files |
| `test_passed` / `logic_passed` | TestResult.logic_passed (syntax + run + BDD) |
| `errors_count` | len(TestResult.errors) |
| `bdd_total` | Number of BDD test cases generated |
| `bdd_passed` | BDD cases with status "passed" (when tracked) |
| `fix_attempts` | ValidatedProject.fix_attempts (run-fix + FineTuning iterations) |
| `code_quality_score` | Ruff (E,F,B) score 0–1 |
| `security_score` | Bandit security scan score 0–1 |
| `alignment_score` | Visual-semantic alignment (when enabled) |
| `env_install_success` | Dependency install success |
| `env_start_success` | Service start success |
| `duration_seconds` | Wall-clock time for the run |
| `errors` | Exception messages if pipeline failed |
| `pass_at_k_value` | Pass@k rate (when `--pass-at-k N` used) |

### Summary fields in JSON

- `success`, `deployable`, `test_passed`, `total`
- `total_errors`, `total_fix_attempts`
- `avg_code_quality_score`, `avg_security_score`
- `avg_alignment_score`
- `env_install_success_count`, `env_start_success_count`
- `pass_at_k`, `avg_pass_at_k_value` (when Pass@k mode)

## Mapping to plan.txt "three dimensions"

The research plan (plan.txt) describes a three-dimensional evaluation. Current implementation status:

| Dimension | Plan expectation | Status | Implementation |
|-----------|------------------|--------|----------------|
| **1. Code quality** | Syntax, style, security | Done | `code_quality_score` (ruff E,F,B), `security_score` (bandit) |
| **2. Environment & run** | Install, build, start success | Done | `env_install_success`, `env_start_success` in TestResult and report |
| **3. Requirements & front-end** | Pass@k, BDD, visual alignment | Done | `--pass-at-k N`, `bdd_passed`, `alignment_score` |

### Future extensions

- **Docker:** Optional containerized evaluation path
- **Build success:** Explicit build step tracking if needed

## Paper evaluation

For paper submission, see [docs/paper/](paper/):

- [EVALUATION.md](paper/EVALUATION.md): Task set, metrics, baselines, commands
- [ABLATION.md](paper/ABLATION.md): Ablation presets and interpretation
- [EXAMPLES.md](paper/EXAMPLES.md): Success/failure case templates

```bash
# Ablation with config presets
python -m src.benchmarks.run_small_suite --config no_code_memory --tasks small
# Multiple runs for mean±std
python -m src.benchmarks.run_small_suite --runs 5
# Baseline
python -m src.benchmarks.run_baseline --tasks small
# Aggregate ablation reports
python -m src.benchmarks.aggregate_ablation
```

## CI note

`run_small_suite` requires `OPENAI_API_KEY` and calls the real LLM; it is not suitable as a default CI step. Use for manual or scheduled evaluation, or add a mock/dry-run mode that skips LLM calls.
