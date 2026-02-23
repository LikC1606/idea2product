"""Run a small benchmark suite and output metrics for pipeline evaluation."""

import json
import os
import sys
import time
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from config.settings import get_settings
from src.core.orchestrator import Orchestrator


BENCHMARK_TASKS = [
    {"id": "todo", "requirement": "Build a todo list app with add, delete, and complete functionality"},
    {"id": "calculator", "requirement": "Build a calculator app with add, subtract, multiply, and divide"},
    {"id": "weather", "requirement": "A weather widget showing current temperature for a city"},
]


def run_single(task: dict, settings) -> dict:
    """Run pipeline for one task, return metrics."""
    req = task["requirement"]
    task_id = task["id"]
    result = {
        "task_id": task_id,
        "requirement": req[:80] + "..." if len(req) > 80 else req,
        "success": False,
        "is_deployable": False,
        "files_count": 0,
        "test_passed": False,
        "logic_passed": False,
        "errors_count": 0,
        "bdd_total": 0,
        "bdd_passed": 0,
        "fix_attempts": 0,
        "duration_seconds": 0.0,
        "errors": [],
    }
    start = time.time()
    try:
        orch = Orchestrator(settings)
        vp = orch.run(req, interactive=False)
        result["success"] = True
        result["is_deployable"] = vp.is_deployable
        result["files_count"] = len(vp.repository.files)
        result["test_passed"] = vp.test_results.logic_passed
        result["logic_passed"] = vp.test_results.logic_passed
        result["errors_count"] = len(vp.test_results.errors)
        result["bdd_total"] = len(vp.test_results.bdd_test_cases)
        result["bdd_passed"] = sum(1 for t in vp.test_results.bdd_test_cases if getattr(t, "status", "") == "passed")
        result["fix_attempts"] = getattr(vp, "fix_attempts", 0)
    except Exception as e:
        result["errors"].append(str(e)[:200])
    result["duration_seconds"] = round(time.time() - start, 2)
    return result


def main():
    """Run benchmark suite and print summary."""
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not set. Benchmark requires real LLM.")
        sys.exit(1)

    settings = get_settings()
    results = []

    print("=" * 60)
    print("Idea2Product Benchmark Suite (small)")
    print("=" * 60)

    for task in BENCHMARK_TASKS:
        print(f"\nRunning: {task['id']} ...")
        r = run_single(task, settings)
        results.append(r)
        status = "OK" if r["success"] else "FAIL"
        print(f"  {status} | deployable={r['is_deployable']} | files={r['files_count']} | test_ok={r['test_passed']} | errors={r['errors_count']} | fix_attempts={r['fix_attempts']} | {r['duration_seconds']}s")

    # Summary
    success_count = sum(1 for r in results if r["success"])
    deployable_count = sum(1 for r in results if r["is_deployable"])
    test_pass_count = sum(1 for r in results if r["test_passed"])

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Tasks: {len(results)} total, {success_count} succeeded, {deployable_count} deployable, {test_pass_count} tests passed")
    print(f"Success rate: {success_count / len(results) * 100:.0f}%")
    print(f"Deployable rate: {deployable_count / len(results) * 100:.0f}%")
    print(f"Test pass rate: {test_pass_count / len(results) * 100:.0f}%")

    # Write JSON report
    report_path = Path(__file__).parent.parent.parent / "data" / "benchmark_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "success": success_count,
        "deployable": deployable_count,
        "test_passed": test_pass_count,
        "total": len(results),
        "total_errors": sum(r.get("errors_count", 0) for r in results),
        "total_fix_attempts": sum(r.get("fix_attempts", 0) for r in results),
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({"results": results, "summary": summary}, f, indent=2, ensure_ascii=False)
    print(f"\nReport written to: {report_path}")


if __name__ == "__main__":
    main()
