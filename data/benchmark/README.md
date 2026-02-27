# Benchmark Data

This directory contains golden/reference artifacts for offline evaluation.

## Structure

Each subdirectory (e.g., `todo/`, `calculator/`) represents one benchmark task:

```
task_name/
  01_requirements.json   # Expected Requirements output
  02_engineering_plan.json  # Expected EngineeringPlan (tasks, etc.)
  generated/             # Optional: reference generated code for quality eval
```

## Offline Evaluation

Run without API calls:

```bash
python -m src.benchmarks.run_small_suite --offline
```

This loads artifacts from `data/benchmark/`, runs `evaluate_task_division()` and optionally `_compute_code_quality()` on any `generated/` code. No LLM calls are made.

## Metrics

- **feature_coverage**: Ratio of features mentioned in task descriptions
- **dependency_validity**: DAG validity (no cycles, no dangling refs)
- **code_quality_score**: Ruff E/F check on generated Python (if available)
