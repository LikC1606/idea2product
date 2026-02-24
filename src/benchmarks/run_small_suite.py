"""Run a small benchmark suite and output metrics for pipeline evaluation.

Supports two modes:
  - CLI (default): runs the full 4-stage pipeline via Orchestrator.run()
  - Chat: simulates the chat-first web workflow end-to-end
"""

import json
import os
import sys
import time
from pathlib import Path

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
        "mode": "cli",
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
        "stage_times": {},
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


def run_single_chat(task: dict, settings) -> dict:
    """Run the chat-first workflow for one task, return metrics with per-stage timing."""
    from src.services.llm_service import LLMService
    from src.agents.stage1_requirements.interaction_agent import InteractionAgent

    req = task["requirement"]
    task_id = task["id"]
    result = {
        "task_id": task_id,
        "requirement": req[:80] + "..." if len(req) > 80 else req,
        "mode": "chat",
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
        "stage_times": {},
        "errors": [],
    }
    overall_start = time.time()
    try:
        llm_service = LLMService.from_settings(settings)
        agent = InteractionAgent(llm_service)

        t0 = time.time()
        messages = [{"role": "user", "content": req}]
        reply = agent.reply_in_chat(messages)
        messages.append({"role": "assistant", "content": reply})
        result["stage_times"]["chat_reply"] = round(time.time() - t0, 2)

        t0 = time.time()
        requirements = agent.conversation_to_requirements(messages)
        result["stage_times"]["requirements"] = round(time.time() - t0, 2)

        orch = Orchestrator(settings)

        import uuid
        from datetime import datetime
        from src.utils.file_utils import ensure_dir, write_json
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_id = f"bench_{ts}_{uuid.uuid4().hex[:6]}"
        project_path = settings.projects_dir / project_id
        ensure_dir(project_path / "artifacts")
        ensure_dir(project_path / "generated")
        ensure_dir(project_path / "logs")

        t0 = time.time()
        vp = orch.run_from_stage_2(project_id, requirements)
        result["stage_times"]["stages_2_to_4"] = round(time.time() - t0, 2)

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
    result["duration_seconds"] = round(time.time() - overall_start, 2)
    return result


def main():
    """Run benchmark suite and print summary."""
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not set. Benchmark requires real LLM.")
        sys.exit(1)

    mode = "cli"
    if len(sys.argv) > 1 and sys.argv[1] in ("chat", "--chat"):
        mode = "chat"

    settings = get_settings()
    results = []

    print("=" * 60)
    print(f"Idea2Product Benchmark Suite (small, mode={mode})")
    print("=" * 60)

    run_fn = run_single_chat if mode == "chat" else run_single

    for task in BENCHMARK_TASKS:
        print(f"\nRunning: {task['id']} ...")
        r = run_fn(task, settings)
        results.append(r)
        status = "OK" if r["success"] else "FAIL"
        timing = ""
        if r.get("stage_times"):
            timing = " | stages=" + ", ".join(f"{k}={v}s" for k, v in r["stage_times"].items())
        print(f"  {status} | deployable={r['is_deployable']} | files={r['files_count']} | test_ok={r['test_passed']} | errors={r['errors_count']} | {r['duration_seconds']}s{timing}")

    success_count = sum(1 for r in results if r["success"])
    deployable_count = sum(1 for r in results if r["is_deployable"])
    test_pass_count = sum(1 for r in results if r["test_passed"])

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Mode: {mode}")
    print(f"Tasks: {len(results)} total, {success_count} succeeded, {deployable_count} deployable, {test_pass_count} tests passed")
    print(f"Success rate: {success_count / len(results) * 100:.0f}%")
    print(f"Deployable rate: {deployable_count / len(results) * 100:.0f}%")
    print(f"Test pass rate: {test_pass_count / len(results) * 100:.0f}%")

    avg_duration = sum(r["duration_seconds"] for r in results) / len(results)
    print(f"Average duration: {avg_duration:.1f}s")

    report_path = Path(__file__).parent.parent.parent / "data" / "benchmark_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "mode": mode,
        "success": success_count,
        "deployable": deployable_count,
        "test_passed": test_pass_count,
        "total": len(results),
        "total_errors": sum(r.get("errors_count", 0) for r in results),
        "total_fix_attempts": sum(r.get("fix_attempts", 0) for r in results),
        "avg_duration_seconds": round(avg_duration, 2),
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({"results": results, "summary": summary}, f, indent=2, ensure_ascii=False)
    print(f"\nReport written to: {report_path}")


if __name__ == "__main__":
    main()
