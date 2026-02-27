# Evaluation Guide

## Offline Evaluation (No API)

Run without OPENAI_API_KEY:

```bash
python -m src.benchmarks.run_small_suite --offline
```

Uses golden artifacts from `data/benchmark/`. Output: `data/benchmark_report.json`.

## Full Benchmark (Requires API Key)

```bash
export OPENAI_API_KEY=sk-...
python -m src.benchmarks.run_small_suite        # CLI mode
python -m src.benchmarks.run_small_suite chat   # Chat workflow mode
```

## Metrics

| Metric | Description |
|--------|-------------|
| success_rate | % of tasks where pipeline completes |
| deployable_rate | % where generated app runs |
| avg_feature_coverage | Features covered in task division |
| dependency_valid_count | Tasks with valid DAG |
| avg_code_quality_score | Ruff E/F check (0-1) |
| avg_duration_seconds | Mean pipeline duration |

## Benchmark Tasks

1. **todo** - Todo list with add, delete, complete
2. **calculator** - Add, subtract, multiply, divide
3. **weather** - Weather widget for city
