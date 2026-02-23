# Benchmark and Evaluation

## Current metrics (run_small_suite)

The script `python -m src.benchmarks.run_small_suite` runs a small set of tasks (Todo, Calculator, Weather) and writes `data/benchmark_report.json`.

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
| `duration_seconds` | Wall-clock time for the run |
| `errors` | Exception messages if pipeline failed |

### Summary fields in JSON

- `success`, `deployable`, `test_passed`, `total`
- `total_errors`, `total_fix_attempts`

## Mapping to plan.txt "three dimensions"

The research plan (plan.txt) describes a three-dimensional evaluation:

1. **Code quality** – syntax, style, security.  
   **Current:** Partially covered by `logic_passed` (syntax check + run) and `errors_count`. No dedicated style or security scan.

2. **Environment and run** – install, build, startup, stability.  
   **Current:** Covered by run-fix loop and `test_passed` (app import/run and BDD smoke tests). No Docker or isolated env yet.

3. **Requirements and front-end** – functional correctness (e.g. Pass@k / BDD), visual–semantic alignment.  
   **Current:** BDD smoke tests and `bdd_total` / `bdd_passed`; visual verification is optional and not yet aggregated into a single alignment score in the report.

## Future extensions

- **Code quality:** Integrate ruff/bandit or similar; add a code_quality score to the report.
- **Environment:** Optional Docker run; report install/build/start success.
- **Pass@k:** Run N samples per task and report pass rate.
- **Visual alignment:** Persist VisualVerificationResult and add alignment_score to the benchmark JSON (when enabled).

## CI note

`run_small_suite` requires `OPENAI_API_KEY` and calls the real LLM; it is not suitable as a default CI step. Use for manual or scheduled evaluation, or add a mock/dry-run mode that skips LLM calls.
