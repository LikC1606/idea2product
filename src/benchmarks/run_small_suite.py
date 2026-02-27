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


def _collect_task_eval_metrics(settings, project_id: str = "") -> dict:
    """Try to load engineering plan artifact and compute task-division quality metrics."""
    from src.benchmarks.task_eval import evaluate_task_division
    from src.core.data_models import Task, TaskType, TaskComplexity, Requirements, Feature

    try:
        projects_dir = settings.projects_dir
        if project_id:
            plan_path = projects_dir / project_id / "artifacts" / "02_engineering_plan.json"
        else:
            candidates = sorted(projects_dir.glob("*/artifacts/02_engineering_plan.json"), reverse=True)
            if not candidates:
                return {}
            plan_path = candidates[0]

        if not plan_path.exists():
            return {}

        with open(plan_path, "r", encoding="utf-8") as f:
            plan_data = json.load(f)

        tasks = []
        for td in plan_data.get("tasks", []):
            complexity = td.get("estimated_complexity", "medium")
            if complexity not in ("low", "medium", "high"):
                complexity = "medium"
            tasks.append(Task(
                id=td["id"],
                name=td["name"],
                description=td.get("description", ""),
                type=TaskType(td.get("type", "frontend")),
                dependencies=td.get("dependencies", []),
                priority=td.get("priority", 3),
                estimated_complexity=TaskComplexity(complexity),
            ))

        req_path = plan_path.parent / "01_requirements.json"
        if req_path.exists():
            with open(req_path, "r", encoding="utf-8") as f:
                req_data = json.load(f)
            features = [Feature(id=ft.get("id", ""), name=ft.get("name", ""), description=ft.get("description", ""), priority=ft.get("priority", 1)) for ft in req_data.get("features", [])]
            requirements = Requirements(title=req_data.get("title", ""), description=req_data.get("description", ""), features=features)
        else:
            requirements = Requirements(title="", description="", features=[])

        return evaluate_task_division(tasks, requirements)
    except Exception:
        return {}


def _compute_code_quality(settings, project_id: str = "") -> float:
    """Compute a code quality score by running ruff on the generated code (0.0-1.0)."""
    import subprocess
    try:
        projects_dir = settings.projects_dir
        if project_id:
            gen_path = projects_dir / project_id / "generated"
        else:
            candidates = sorted(projects_dir.glob("*/generated"), reverse=True)
            gen_path = candidates[0] if candidates else None
        if not gen_path or not gen_path.exists():
            return None
        return _compute_code_quality_impl(gen_path)
    except Exception:
        return None


def _compute_code_quality_impl(gen_path: Path) -> float:
    """Internal: compute ruff score for a path."""
    import subprocess
    try:
        py_files = list(gen_path.rglob("*.py"))
        if not py_files:
            return None

        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "--select", "E,F", "--quiet", str(gen_path)],
            capture_output=True, text=True, timeout=30,
        )
        issue_count = len(result.stdout.strip().splitlines()) if result.stdout.strip() else 0
        total_lines = sum(1 for f in py_files for _ in open(f, encoding="utf-8", errors="ignore"))
        if total_lines == 0:
            return 1.0
        score = max(0.0, 1.0 - (issue_count / max(total_lines, 1)))
        return round(score, 3)
    except Exception:
        return None


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
        "task_division_eval": {},
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
        result["task_division_eval"] = _collect_task_eval_metrics(settings)
        # Visual alignment score (from VisualVerificationAgent if enabled)
        vf = getattr(vp.test_results, "visual_feedback", None)
        result["alignment_score"] = vf.get("alignment_score", 0.0) if vf else None
        # Code quality score via ruff (if available)
        result["code_quality_score"] = _compute_code_quality(settings)
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
        "task_division_eval": {},
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
        result["task_division_eval"] = _collect_task_eval_metrics(settings, project_id)
        vf = getattr(vp.test_results, "visual_feedback", None)
        result["alignment_score"] = vf.get("alignment_score", 0.0) if vf else None
        result["code_quality_score"] = _compute_code_quality(settings, project_id)
    except Exception as e:
        result["errors"].append(str(e)[:200])
    result["duration_seconds"] = round(time.time() - overall_start, 2)
    return result


def run_offline(_settings) -> list:
    """Run offline evaluation using golden artifacts in data/benchmark/. No LLM calls."""
    from src.core.data_models import Task, TaskType, TaskComplexity, Requirements, Feature

    benchmark_dir = Path(__file__).parent.parent.parent / "data" / "benchmark"
    results = []
    for task in BENCHMARK_TASKS:
        task_id = task["id"]
        task_dir = benchmark_dir / task_id
        result = {
            "task_id": task_id,
            "requirement": task["requirement"][:80] + "..." if len(task["requirement"]) > 80 else task["requirement"],
            "mode": "offline",
            "success": False,
            "task_division_eval": {},
            "code_quality_score": None,
        }
        try:
            req_path = task_dir / "01_requirements.json"
            plan_path = task_dir / "02_engineering_plan.json"
            if not plan_path.exists():
                result["errors"] = [f"Missing {plan_path}"]
                results.append(result)
                continue
            with open(plan_path, "r", encoding="utf-8") as f:
                plan_data = json.load(f)
            tasks = []
            for td in plan_data.get("tasks", []):
                c = td.get("estimated_complexity", "medium")
                if c not in ("low", "medium", "high"):
                    c = "medium"
                tasks.append(Task(
                    id=td["id"], name=td["name"], description=td.get("description", ""),
                    type=TaskType(td.get("type", "frontend")), dependencies=td.get("dependencies", []),
                    priority=td.get("priority", 3), estimated_complexity=TaskComplexity(c),
                ))
            requirements = Requirements(title="", description="", features=[])
            if req_path.exists():
                with open(req_path, "r", encoding="utf-8") as f:
                    req_data = json.load(f)
                requirements = Requirements(
                    title=req_data.get("title", ""),
                    description=req_data.get("description", ""),
                    features=[Feature(id=ft.get("id", ""), name=ft.get("name", ""), description=ft.get("description", ""), priority=ft.get("priority", 1)) for ft in req_data.get("features", [])],
                    constraints=req_data.get("constraints", []),
                )
            from src.benchmarks.task_eval import evaluate_task_division
            result["task_division_eval"] = evaluate_task_division(tasks, requirements)
            result["success"] = True
            gen_path = task_dir / "generated"
            if gen_path.exists():
                result["code_quality_score"] = _compute_code_quality_impl(gen_path)
        except Exception as e:
            result["errors"] = [str(e)[:200]]
        results.append(result)
    return results


def _compute_code_quality_impl(gen_path: Path) -> float:
    """Compute ruff-based quality score for a generated code directory."""
    import subprocess
    try:
        py_files = list(gen_path.rglob("*.py"))
        if not py_files:
            return None
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "--select", "E,F", "--quiet", str(gen_path)],
            capture_output=True, text=True, timeout=30,
        )
        issue_count = len(result.stdout.strip().splitlines()) if result.stdout.strip() else 0
        total_lines = sum(1 for f in py_files for _ in open(f, encoding="utf-8", errors="ignore"))
        if total_lines == 0:
            return 1.0
        return round(max(0.0, 1.0 - (issue_count / max(total_lines, 1))), 3)
    except Exception:
        return None


def main():
    """Run benchmark suite and print summary."""
    mode = "cli"
    offline = False
    for arg in (sys.argv[1:] or []):
        if arg in ("chat", "--chat"):
            mode = "chat"
        elif arg in ("--offline", "-o"):
            offline = True

    if offline:
        print("=" * 60)
        print("Idea2Product Benchmark Suite (offline mode, no LLM)")
        print("=" * 60)
        settings = get_settings()
        results = run_offline(settings)
        for r in results:
            ev = r.get("task_division_eval", {})
            fc = ev.get("feature_coverage", 0)
            dv = ev.get("dependency_validity", False)
            q = r.get("code_quality_score", "N/A")
            print(f"  {r['task_id']} | feature_coverage={fc} | dep_valid={dv} | code_quality={q}")
        eval_results = [r.get("task_division_eval", {}) for r in results if r.get("task_division_eval")]
        avg_fc = sum(e.get("feature_coverage", 0) for e in eval_results) / len(eval_results) if eval_results else 0
        dep_ok = sum(1 for e in eval_results if e.get("dependency_validity", False))
        quality_scores = [r["code_quality_score"] for r in results if r.get("code_quality_score") is not None]
        avg_q = round(sum(quality_scores) / len(quality_scores), 3) if quality_scores else None
        report_path = Path(__file__).parent.parent.parent / "data" / "benchmark_report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        summary = {"mode": "offline", "avg_feature_coverage": round(avg_fc, 3), "dependency_valid_count": dep_ok, "avg_code_quality_score": avg_q}
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump({"results": results, "summary": summary}, f, indent=2, ensure_ascii=False)
        print(f"\nReport: {report_path}")
        return

    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not set. Benchmark requires real LLM. Use --offline for no-API eval.")
        sys.exit(1)

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
    # Aggregate task division eval metrics
    eval_results = [r.get("task_division_eval", {}) for r in results if r.get("task_division_eval")]
    avg_feature_coverage = 0.0
    dep_valid_count = 0
    if eval_results:
        avg_feature_coverage = sum(e.get("feature_coverage", 0) for e in eval_results) / len(eval_results)
        dep_valid_count = sum(1 for e in eval_results if e.get("dependency_validity", False))

    # Aggregate visual alignment scores
    align_scores = [r["alignment_score"] for r in results if r.get("alignment_score") is not None]
    avg_alignment = round(sum(align_scores) / len(align_scores), 3) if align_scores else None

    # Aggregate code quality scores
    quality_scores = [r["code_quality_score"] for r in results if r.get("code_quality_score") is not None]
    avg_code_quality = round(sum(quality_scores) / len(quality_scores), 3) if quality_scores else None

    summary = {
        "mode": mode,
        "success": success_count,
        "deployable": deployable_count,
        "test_passed": test_pass_count,
        "total": len(results),
        "total_errors": sum(r.get("errors_count", 0) for r in results),
        "total_fix_attempts": sum(r.get("fix_attempts", 0) for r in results),
        "avg_duration_seconds": round(avg_duration, 2),
        "avg_feature_coverage": round(avg_feature_coverage, 3),
        "dependency_valid_count": dep_valid_count,
        "avg_alignment_score": avg_alignment,
        "avg_code_quality_score": avg_code_quality,
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({"results": results, "summary": summary}, f, indent=2, ensure_ascii=False)
    print(f"\nReport written to: {report_path}")


if __name__ == "__main__":
    main()
