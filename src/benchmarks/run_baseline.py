"""Run benchmark in baseline mode (no Code Memory, Code Mining, BDD, or Visual Verification).

This provides a zero-shot / simplified pipeline baseline for paper comparison.
Usage: python -m src.benchmarks.run_baseline [--tasks small|full] [--runs N]

Equivalent to: python -m src.benchmarks.run_small_suite --config baseline [same args]
"""

import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Prepend --config baseline and delegate to run_small_suite
sys.argv = [sys.argv[0], "--config", "baseline"] + sys.argv[1:]

from src.benchmarks.run_small_suite import main  # noqa: E402

if __name__ == "__main__":
    main()
