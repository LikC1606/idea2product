# Ablation Study (Paper)

## Configurations

| Preset | Code Memory | Code Mining | Visual Verification | BDD Testing |
|--------|-------------|-------------|---------------------|-------------|
| **full** | ✓ | ✓ | ✓ | ✓ |
| **baseline** | ✗ | ✗ | ✗ | ✗ |
| **no_code_memory** | ✗ | ✓ | ✓ | ✓ |
| **no_code_mining** | ✓ | ✗ | ✓ | ✓ |
| **no_visual** | ✓ | ✓ | ✗ | ✓ |
| **no_bdd** | ✓ | ✓ | ✓ | ✗ |

## Running Ablation

1. Run each configuration on the same task set:

```bash
python -m src.benchmarks.run_small_suite --config full --tasks small
python -m src.benchmarks.run_small_suite --config baseline --tasks small
python -m src.benchmarks.run_small_suite --config no_code_memory --tasks small
python -m src.benchmarks.run_small_suite --config no_code_mining --tasks small
python -m src.benchmarks.run_small_suite --config no_visual --tasks small
python -m src.benchmarks.run_small_suite --config no_bdd --tasks small
```

2. Aggregate results:

```bash
python -m src.benchmarks.aggregate_ablation
```

3. Output: `data/ablation_summary.md` with Markdown and LaTeX tables

## Interpreting Results

- **full vs baseline**: Overall benefit of Idea2Product features
- **no_code_memory**: Impact of dynamic symbol table and snippet retrieval
- **no_code_mining**: Impact of GitHub code retrieval and adaptation
- **no_visual**: Impact of visual-semantic alignment verification
- **no_bdd**: Impact of BDD test-driven generation
