# Paper Appendix Materials

This directory contains materials for paper submission and reproducibility.

## Contents

- **EVALUATION.md** - Evaluation setup and metrics
- **PROMPTS/** - (Optional) Prompt templates for reference

## Environment

- **OS**: Linux (Ubuntu 22.04) or macOS
- **Python**: 3.9+
- **Model**: GPT-4o (primary), gpt-4o-mini (Stage 1/2 light steps)

## Key Hyperparameters

| Parameter | Value |
|-----------|-------|
| OPENAI_MODEL | gpt-4o |
| max_tokens | 4096 |
| temperature | 0.7 |
| max_fix_attempts | 2 |
| use_fast_model_for_light_stages | true |

## Evaluation Metrics

- **success_rate**: Pipeline completes without exception
- **deployable_rate**: Generated app runs (`python app.py`)
- **feature_coverage**: Features mentioned in task descriptions
- **dependency_validity**: Task DAG has no cycles
- **fix_attempts**: Number of run-fix iterations in Stage 4

See `docs/REPRODUCIBILITY.md` for reproduction steps.
