# Example Cases (Paper)

This document provides templates for documenting success and failure cases.

## Success Case Template

### Task

- **ID**: todo
- **Requirement**: Build a todo list app with add, delete, and complete functionality

### Generated Structure

```
generated/
├── app.py
├── app/
│   ├── __init__.py
│   ├── models/
│   │   └── todo.py
│   └── routes/
│       └── todos.py
├── templates/
│   └── index.html
└── static/
    └── css/
```

### Metrics

- alignment_score: 0.85
- code_quality_score: 0.92
- BDD passed: 3/3

### Screenshot

*(Add rendered UI screenshot here)*

---

## Failure Case Template

### Task

- **ID**: auth
- **Requirement**: Build a simple app with user login and logout, protected dashboard page

### Issue

- logic_passed: False
- alignment_score: 0.45
- Error: Session not persisted across requests

### Analysis

*(Categorize: syntax, import, logic, frontend missing, etc.)*

---

## How to Capture Examples

1. Run benchmark: `python -m src.benchmarks.run_small_suite --tasks small`
2. Inspect `data/projects/<latest>/generated/`
3. Take screenshots of rendered apps
4. Record metrics from `data/benchmark_report.json`
5. Fill in this template for 2–3 success and 1–2 failure cases
