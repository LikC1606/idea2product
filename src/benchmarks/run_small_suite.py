"""Run a small benchmark suite and output metrics for pipeline evaluation.

Supports two modes:
  - CLI (default): runs the full 4-stage pipeline via Orchestrator.run()
  - Chat: simulates the chat-first web workflow end-to-end

Flags:
  - --pass-at-k N: run each task N times, report Pass@k (BDD/logic pass rate)
  - --tasks small|full: small=3 tasks (todo, calculator, weather), full=16 tasks (default: small for backward compat)
  - --config full|no_code_memory|no_code_mining|no_visual|no_bdd: ablation preset (default: full)
  - --runs N: run each task N times for mean±std statistics
"""

import json
import os
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from config.settings import get_settings
from src.core.orchestrator import Orchestrator

# Ablation presets: which features to disable
ABLATION_PRESETS = {
    "full": {},
    "baseline": {
        "enable_code_memory": False,
        "enable_code_mining": False,
        "enable_visual_verification": False,
        "enable_bdd_testing": False,
    },
    "no_code_memory": {"enable_code_memory": False},
    "no_code_mining": {"enable_code_mining": False},
    "no_visual": {"enable_visual_verification": False},
    "no_bdd": {"enable_bdd_testing": False},
}


def get_settings_for_config(preset: str = "full"):
    """Return settings with ablation preset applied. Creates a new instance for isolation."""
    base = get_settings()
    overrides = ABLATION_PRESETS.get(preset.lower(), ABLATION_PRESETS["full"])
    if not overrides:
        return base
    return base.model_copy(update=overrides)


BENCHMARK_TASKS_SMALL = [
    {
        "id": "todo",
        "requirement": "Build a todo list app with add, delete, and complete functionality",
    },
    {
        "id": "calculator",
        "requirement": "Build a calculator app with add, subtract, multiply, and divide",
    },
    {
        "id": "weather",
        "requirement": "A weather widget showing current temperature for a city",
    },
]

BENCHMARK_TASKS_EXTENDED = [
    {
        "id": "blog",
        "requirement": "Build a blog app with posts, add/edit/delete, and author display",
    },
    {
        "id": "notes",
        "requirement": "Build a notes app with create, list, edit, and delete notes",
    },
    {
        "id": "auth",
        "requirement": "Build a simple app with user login and logout, protected dashboard page",
    },
    {
        "id": "contacts",
        "requirement": "Build a contacts app with add, search, edit, and delete contacts",
    },
    {
        "id": "inventory",
        "requirement": "Build an inventory tracker with add item, list items, update quantity",
    },
    {
        "id": "expenses",
        "requirement": "Build an expense tracker with add expense, list by category, total sum",
    },
    {
        "id": "bookmarks",
        "requirement": "Build a bookmark manager with add URL, list, and delete bookmarks",
    },
    {
        "id": "recipes",
        "requirement": "Build a recipe app with add recipe, list recipes, view details",
    },
    {
        "id": "tasks",
        "requirement": "Build a task manager with create task, assign priority, filter by status",
    },
    {
        "id": "timer",
        "requirement": "Build a simple timer app with start, stop, and reset",
    },
    {
        "id": "counter",
        "requirement": "Build a counter app with increment, decrement, and reset",
    },
    {
        "id": "quotes",
        "requirement": "Build a random quote display app with next quote button",
    },
    {
        "id": "form_demo",
        "requirement": "Build a multi-step registration form with name, email, and submit",
    },
    {
        "id": "api_demo",
        "requirement": "Build a REST API for a simple product catalog with CRUD endpoints",
    },
]

BENCHMARK_TASKS = BENCHMARK_TASKS_SMALL + BENCHMARK_TASKS_EXTENDED


def _collect_task_eval_metrics(settings, project_id: str = "") -> dict:
    """Try to load engineering plan artifact and compute task-division quality metrics."""
    from src.benchmarks.task_eval import evaluate_task_division
    from src.core.data_models import (
        Task,
        TaskType,
        TaskComplexity,
        Requirements,
        Feature,
    )

    try:
        projects_dir = settings.projects_dir
        if project_id:
            plan_path = (
                projects_dir / project_id / "artifacts" / "02_engineering_plan.json"
            )
        else:
            candidates = sorted(
                projects_dir.glob("*/artifacts/02_engineering_plan.json"), reverse=True
            )
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
            tasks.append(
                Task(
                    id=td["id"],
                    name=td["name"],
                    description=td.get("description", ""),
                    type=TaskType(td.get("type", "frontend")),
                    dependencies=td.get("dependencies", []),
                    priority=td.get("priority", 3),
                    estimated_complexity=TaskComplexity(complexity),
                )
            )

        req_path = plan_path.parent / "01_requirements.json"
        if req_path.exists():
            with open(req_path, "r", encoding="utf-8") as f:
                req_data = json.load(f)
            features = [
                Feature(
                    id=ft.get("id", ""),
                    name=ft.get("name", ""),
                    description=ft.get("description", ""),
                    priority=ft.get("priority", 1),
                )
                for ft in req_data.get("features", [])
            ]
            requirements = Requirements(
                title=req_data.get("title", ""),
                description=req_data.get("description", ""),
                features=features,
            )
        else:
            requirements = Requirements(title="", description="", features=[])

        return evaluate_task_division(tasks, requirements)
    except Exception:
        return {}


def _compute_code_quality(settings, project_id: str = "") -> dict:
    """Compute ruff and bandit scores for generated code. Returns {ruff_score, security_score}."""
    try:
        projects_dir = settings.projects_dir
        if project_id:
            gen_path = projects_dir / project_id / "generated"
        else:
            candidates = sorted(projects_dir.glob("*/generated"), reverse=True)
            gen_path = candidates[0] if candidates else None
        if not gen_path or not gen_path.exists():
            return {"ruff_score": None, "security_score": None}
        return _compute_code_quality_impl(gen_path)
    except Exception:
        return {"ruff_score": None, "security_score": None}


def _compute_code_quality_impl(gen_path: Path) -> dict:
    """Compute code quality (ruff: E,F,B) and security (bandit) scores. Returns {ruff_score, security_score}."""
    import subprocess

    out = {"ruff_score": None, "security_score": None}
    try:
        py_files = list(gen_path.rglob("*.py"))
        if not py_files:
            return out
        total_lines = sum(
            1 for f in py_files for _ in open(f, encoding="utf-8", errors="ignore")
        )
        if total_lines == 0:
            return {"ruff_score": 1.0, "security_score": 1.0}

        # Ruff: E,F,B (pycodestyle, pyflakes, bugbear - Plan: extend rules)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "ruff",
                "check",
                "--select",
                "E,F,B",
                "--quiet",
                str(gen_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        issue_count = (
            len(result.stdout.strip().splitlines()) if result.stdout.strip() else 0
        )
        out["ruff_score"] = round(
            max(0.0, 1.0 - (issue_count / max(total_lines, 1))), 3
        )

        # Bandit: security scan (Plan: code quality dimension)
        try:
            b = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "bandit",
                    "-r",
                    str(gen_path),
                    "-f",
                    "json",
                    "-q",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            # Bandit exits 1 when issues found, 0 when clean
            data = json.loads(b.stdout) if (b.stdout and b.stdout.strip()) else {}
            issues = data.get("results", [])
            if not issues:
                out["security_score"] = 1.0
            else:
                sev_high = sum(1 for i in issues if i.get("issue_severity") == "HIGH")
                sev_med = sum(1 for i in issues if i.get("issue_severity") == "MEDIUM")
                penalty = min(
                    1.0, (sev_high * 0.15 + sev_med * 0.05) / max(len(py_files), 1)
                )
                out["security_score"] = round(max(0.0, 1.0 - penalty), 3)
        except Exception as ex:
            import logging
            logging.getLogger(__name__).debug("Bandit/security score calc failed: %s", ex)
        return out
    except Exception:
        return out


def _aggregate_runs_mean_std(runs_list: list) -> dict:
    """Aggregate multiple runs into one result with mean and std for numeric metrics."""
    if not runs_list:
        return {}
    numeric_keys = [
        "duration_seconds",
        "bdd_passed",
        "bdd_total",
        "errors_count",
        "fix_attempts",
        "alignment_score",
        "code_quality_score",
        "security_score",
    ]
    r0 = runs_list[0].copy()
    r0["runs"] = len(runs_list)
    for k in numeric_keys:
        vals = [rr.get(k) for rr in runs_list if rr.get(k) is not None]
        if vals:
            r0[f"{k}_mean"] = round(statistics.mean(vals), 3)
            r0[f"{k}_std"] = round(statistics.stdev(vals), 3) if len(vals) > 1 else 0.0
    success_vals = [1 if rr.get("success") else 0 for rr in runs_list]
    r0["success_rate_mean"] = round(statistics.mean(success_vals), 3)
    r0["success_rate_std"] = (
        round(statistics.stdev(success_vals), 3) if len(success_vals) > 1 else 0.0
    )
    logic_vals = [1 if rr.get("logic_passed") else 0 for rr in runs_list]
    r0["logic_pass_rate_mean"] = round(statistics.mean(logic_vals), 3)
    r0["logic_pass_rate_std"] = (
        round(statistics.stdev(logic_vals), 3) if len(logic_vals) > 1 else 0.0
    )
    return r0


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
        "env_install_success": None,
        "env_start_success": None,
        "security_score": None,
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
        result["bdd_passed"] = sum(
            1
            for t in vp.test_results.bdd_test_cases
            if getattr(t, "status", "") == "passed"
        )
        result["fix_attempts"] = getattr(vp, "fix_attempts", 0)
        result["task_division_eval"] = _collect_task_eval_metrics(settings)
        # Visual alignment score (from VisualVerificationAgent if enabled)
        vf = getattr(vp.test_results, "visual_feedback", None)
        result["alignment_score"] = vf.get("alignment_score", 0.0) if vf else None
        # Code quality (ruff) and security (bandit) - Plan benchmark dimension 1
        q = _compute_code_quality(settings)
        result["code_quality_score"] = q.get("ruff_score")
        result["security_score"] = q.get("security_score")
        # Environment dimension (Plan benchmark)
        result["env_install_success"] = getattr(
            vp.test_results, "env_install_success", None
        )
        result["env_start_success"] = getattr(
            vp.test_results, "env_start_success", None
        )
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
        "env_install_success": None,
        "env_start_success": None,
        "security_score": None,
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
        result["bdd_passed"] = sum(
            1
            for t in vp.test_results.bdd_test_cases
            if getattr(t, "status", "") == "passed"
        )
        result["fix_attempts"] = getattr(vp, "fix_attempts", 0)
        result["task_division_eval"] = _collect_task_eval_metrics(settings, project_id)
        vf = getattr(vp.test_results, "visual_feedback", None)
        result["alignment_score"] = vf.get("alignment_score", 0.0) if vf else None
        q = _compute_code_quality(settings, project_id)
        result["code_quality_score"] = q.get("ruff_score")
        result["security_score"] = q.get("security_score")
        result["env_install_success"] = getattr(
            vp.test_results, "env_install_success", None
        )
        result["env_start_success"] = getattr(
            vp.test_results, "env_start_success", None
        )
    except Exception as e:
        result["errors"].append(str(e)[:200])
    result["duration_seconds"] = round(time.time() - overall_start, 2)
    return result


def run_offline(_settings, tasks_list=None) -> list:
    """Run offline evaluation using golden artifacts in data/benchmark/. No LLM calls."""
    from src.core.data_models import (
        Task,
        TaskType,
        TaskComplexity,
        Requirements,
        Feature,
    )

    if tasks_list is None:
        tasks_list = BENCHMARK_TASKS_SMALL
    benchmark_dir = Path(__file__).parent.parent.parent / "data" / "benchmark"
    results = []
    for task in tasks_list:
        task_id = task["id"]
        task_dir = benchmark_dir / task_id
        result = {
            "task_id": task_id,
            "requirement": task["requirement"][:80] + "..."
            if len(task["requirement"]) > 80
            else task["requirement"],
            "mode": "offline",
            "success": False,
            "task_division_eval": {},
            "code_quality_score": None,
            "security_score": None,
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
                tasks.append(
                    Task(
                        id=td["id"],
                        name=td["name"],
                        description=td.get("description", ""),
                        type=TaskType(td.get("type", "frontend")),
                        dependencies=td.get("dependencies", []),
                        priority=td.get("priority", 3),
                        estimated_complexity=TaskComplexity(c),
                    )
                )
            requirements = Requirements(title="", description="", features=[])
            if req_path.exists():
                with open(req_path, "r", encoding="utf-8") as f:
                    req_data = json.load(f)
                requirements = Requirements(
                    title=req_data.get("title", ""),
                    description=req_data.get("description", ""),
                    features=[
                        Feature(
                            id=ft.get("id", ""),
                            name=ft.get("name", ""),
                            description=ft.get("description", ""),
                            priority=ft.get("priority", 1),
                        )
                        for ft in req_data.get("features", [])
                    ],
                    constraints=req_data.get("constraints", []),
                )
            from src.benchmarks.task_eval import evaluate_task_division

            result["task_division_eval"] = evaluate_task_division(tasks, requirements)
            result["success"] = True
            gen_path = task_dir / "generated"
            if gen_path.exists():
                q = _compute_code_quality_impl(gen_path)
                result["code_quality_score"] = q.get("ruff_score")
                result["security_score"] = q.get("security_score")
        except Exception as e:
            result["errors"] = [str(e)[:200]]
        results.append(result)
    return results


def main():
    """Run benchmark suite and print summary."""
    mode = "cli"
    offline = False
    pass_at_k = 1
    tasks_list = BENCHMARK_TASKS_SMALL  # default small for backward compat
    config_preset = "full"
    runs = 1
    args = sys.argv[1:] or []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ("chat", "--chat"):
            mode = "chat"
        elif arg in ("--offline", "-o"):
            offline = True
        elif arg in ("--pass-at-k", "-k") and i + 1 < len(args):
            try:
                pass_at_k = max(1, int(args[i + 1]))
            except ValueError:
                pass_at_k = 1
            i += 1
        elif arg in ("--tasks", "-t") and i + 1 < len(args):
            t = (args[i + 1] or "").lower()
            tasks_list = BENCHMARK_TASKS if t == "full" else BENCHMARK_TASKS_SMALL
            i += 1
        elif arg in ("--config", "-c") and i + 1 < len(args):
            config_preset = (args[i + 1] or "full").lower()
            i += 1
        elif arg in ("--runs", "-r") and i + 1 < len(args):
            try:
                runs = max(1, int(args[i + 1]))
            except ValueError:
                runs = 1
            i += 1
        i += 1

    if offline:
        print("=" * 60)
        print("Idea2Product Benchmark Suite (offline mode, no LLM)")
        print("=" * 60)
        settings = get_settings()
        results = run_offline(settings, tasks_list)
        for r in results:
            ev = r.get("task_division_eval", {})
            fc = ev.get("feature_coverage", 0)
            dv = ev.get("dependency_validity", False)
            q = r.get("code_quality_score", "N/A")
            print(
                f"  {r['task_id']} | feature_coverage={fc} | dep_valid={dv} | code_quality={q}"
            )
        eval_results = [
            r.get("task_division_eval", {})
            for r in results
            if r.get("task_division_eval")
        ]
        avg_fc = (
            sum(e.get("feature_coverage", 0) for e in eval_results) / len(eval_results)
            if eval_results
            else 0
        )
        dep_ok = sum(1 for e in eval_results if e.get("dependency_validity", False))
        quality_scores = [
            r["code_quality_score"]
            for r in results
            if r.get("code_quality_score") is not None
        ]
        avg_q = (
            round(sum(quality_scores) / len(quality_scores), 3)
            if quality_scores
            else None
        )
        report_path = (
            Path(__file__).parent.parent.parent / "data" / "benchmark_report.json"
        )
        report_path.parent.mkdir(parents=True, exist_ok=True)
        summary = {
            "mode": "offline",
            "avg_feature_coverage": round(avg_fc, 3),
            "dependency_valid_count": dep_ok,
            "avg_code_quality_score": avg_q,
        }
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(
                {"results": results, "summary": summary},
                f,
                indent=2,
                ensure_ascii=False,
            )
        print(f"\nReport: {report_path}")
        return

    if not os.getenv("OPENAI_API_KEY"):
        print(
            "ERROR: OPENAI_API_KEY not set. Benchmark requires real LLM. Use --offline for no-API eval."
        )
        sys.exit(1)

    settings = get_settings_for_config(config_preset)
    results = []
    tasks_count = len(tasks_list)

    print("=" * 60)
    print(
        f"Idea2Product Benchmark Suite (mode={mode}, tasks={tasks_count}, config={config_preset}, "
        f"pass_at_k={pass_at_k}, runs={runs})"
    )
    print("=" * 60)

    run_fn = run_single_chat if mode == "chat" else run_single

    for task in tasks_list:
        task_runs = []
        num_runs = runs if runs > 1 else pass_at_k
        for k in range(num_runs):
            suffix = f" ({k+1}/{num_runs})" if num_runs > 1 else ""
            print(f"\nRunning: {task['id']}{suffix} ...")
            r = run_fn(task, settings)
            task_runs.append(r)
            status = "OK" if r["success"] else "FAIL"
            timing = ""
            if r.get("stage_times"):
                timing = " | stages=" + ", ".join(
                    f"{sk}={sv}s" for sk, sv in r["stage_times"].items()
                )
            print(
                f"  {status} | deployable={r['is_deployable']} | test_ok={r['test_passed']} | {r['duration_seconds']}s{timing}"
            )

        if runs > 1:
            r_agg = _aggregate_runs_mean_std(task_runs)
            r_agg["task_id"] = task["id"]
            r_agg["requirement"] = task["requirement"][:80] + (
                "..." if len(task["requirement"]) > 80 else ""
            )
            r_agg["mode"] = mode
            results.append(r_agg)
            dm = r_agg.get("duration_seconds_mean")
            ds = r_agg.get("duration_seconds_std", 0)
            print(f"  Mean±Std: duration={dm}±{ds}s" if dm is not None else "")
        elif pass_at_k > 1:
            passed = sum(1 for rr in task_runs if rr.get("logic_passed"))
            pass_at_k_val = passed / pass_at_k
            r_agg = {
                "task_id": task["id"],
                "requirement": task["requirement"][:80] + "..."
                if len(task["requirement"]) > 80
                else task["requirement"],
                "mode": mode,
                "pass_at_k": pass_at_k,
                "pass_at_k_value": round(pass_at_k_val, 3),
                "runs_passed": passed,
                "runs_total": pass_at_k,
                "logic_passed": passed == pass_at_k,
                "success": all(rr.get("success") for rr in task_runs),
                "is_deployable": any(rr.get("is_deployable") for rr in task_runs),
                "files_count": task_runs[0].get("files_count", 0) if task_runs else 0,
                "bdd_total": task_runs[0].get("bdd_total", 0) if task_runs else 0,
                "bdd_passed": sum(rr.get("bdd_passed", 0) for rr in task_runs)
                // pass_at_k
                if task_runs
                else 0,
                "duration_seconds": round(
                    sum(rr["duration_seconds"] for rr in task_runs) / pass_at_k, 2
                ),
                "task_division_eval": task_runs[0].get("task_division_eval", {})
                if task_runs
                else {},
                "code_quality_score": task_runs[0].get("code_quality_score")
                if task_runs
                else None,
                "security_score": task_runs[0].get("security_score")
                if task_runs
                else None,
                "alignment_score": task_runs[0].get("alignment_score")
                if task_runs
                else None,
                "env_install_success": task_runs[0].get("env_install_success")
                if task_runs
                else None,
                "env_start_success": task_runs[0].get("env_start_success")
                if task_runs
                else None,
                "errors": [e for rr in task_runs for e in rr.get("errors", [])],
            }
            results.append(r_agg)
            print(f"  Pass@{pass_at_k}: {passed}/{pass_at_k} = {pass_at_k_val:.2%}")
        else:
            results.append(task_runs[0])

    if not results:
        print("No tasks to run. Exiting.")
        return

    success_count = sum(1 for r in results if r["success"])
    deployable_count = sum(1 for r in results if r["is_deployable"])
    test_pass_count = sum(1 for r in results if r["test_passed"])
    denom = len(results)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Mode: {mode}")
    print(
        f"Tasks: {denom} total, {success_count} succeeded, {deployable_count} deployable, {test_pass_count} tests passed"
    )
    print(f"Success rate: {success_count / denom * 100:.0f}%")
    print(f"Deployable rate: {deployable_count / denom * 100:.0f}%")
    print(f"Test pass rate: {test_pass_count / denom * 100:.0f}%")

    avg_duration = sum(r["duration_seconds"] for r in results) / denom
    env_install_ok = sum(1 for r in results if r.get("env_install_success") is True)
    env_start_ok = sum(1 for r in results if r.get("env_start_success") is True)
    print(f"Average duration: {avg_duration:.1f}s")
    print(
        f"Env: install_ok={env_install_ok}/{denom}, start_ok={env_start_ok}/{denom}"
    )
    if pass_at_k > 1:
        avg_pak = (
            sum(r.get("pass_at_k_value", 0) for r in results) / denom
            if results
            else 0
        )
        print(f"Pass@{pass_at_k}: avg={avg_pak:.2%}")

    report_name = (
        f"benchmark_report_{config_preset}.json"
        if config_preset != "full"
        else "benchmark_report.json"
    )
    report_path = Path(__file__).parent.parent.parent / "data" / report_name
    report_path.parent.mkdir(parents=True, exist_ok=True)
    # Aggregate task division eval metrics
    eval_results = [
        r.get("task_division_eval", {}) for r in results if r.get("task_division_eval")
    ]
    avg_feature_coverage = 0.0
    dep_valid_count = 0
    if eval_results:
        avg_feature_coverage = sum(
            e.get("feature_coverage", 0) for e in eval_results
        ) / len(eval_results)
        dep_valid_count = sum(
            1 for e in eval_results if e.get("dependency_validity", False)
        )

    # Aggregate visual alignment scores
    align_scores = [
        r["alignment_score"] for r in results if r.get("alignment_score") is not None
    ]
    avg_alignment = (
        round(sum(align_scores) / len(align_scores), 3) if align_scores else None
    )

    # Aggregate code quality and security scores
    quality_scores = [
        r["code_quality_score"]
        for r in results
        if r.get("code_quality_score") is not None
    ]
    avg_code_quality = (
        round(sum(quality_scores) / len(quality_scores), 3) if quality_scores else None
    )
    security_scores = [
        r["security_score"] for r in results if r.get("security_score") is not None
    ]
    avg_security = (
        round(sum(security_scores) / len(security_scores), 3)
        if security_scores
        else None
    )

    # When runs>1, add mean±std to summary
    summary_extras = {}
    if runs > 1 and results:
        dur_means = [
            r.get("duration_seconds_mean")
            for r in results
            if r.get("duration_seconds_mean") is not None
        ]
        if dur_means:
            summary_extras["duration_mean"] = round(statistics.mean(dur_means), 3)
            summary_extras["duration_std"] = (
                round(statistics.stdev(dur_means), 3) if len(dur_means) > 1 else 0.0
            )
        success_means = [
            r.get("success_rate_mean")
            for r in results
            if r.get("success_rate_mean") is not None
        ]
        if success_means:
            summary_extras["success_rate_mean"] = round(
                statistics.mean(success_means), 3
            )
            summary_extras["success_rate_std"] = (
                round(statistics.stdev(success_means), 3)
                if len(success_means) > 1
                else 0.0
            )
        logic_means = [
            r.get("logic_pass_rate_mean")
            for r in results
            if r.get("logic_pass_rate_mean") is not None
        ]
        if logic_means:
            summary_extras["logic_pass_rate_mean"] = round(
                statistics.mean(logic_means), 3
            )
            summary_extras["logic_pass_rate_std"] = (
                round(statistics.stdev(logic_means), 3) if len(logic_means) > 1 else 0.0
            )

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
        "avg_security_score": avg_security,
        "env_install_success_count": env_install_ok,
        "env_start_success_count": env_start_ok,
        "pass_at_k": pass_at_k if pass_at_k > 1 else None,
        "avg_pass_at_k_value": round(
            sum(r.get("pass_at_k_value", 0) for r in results) / len(results), 3
        )
        if pass_at_k > 1 and results
        else None,
        "runs": runs if runs > 1 else None,
        "config_preset": config_preset,
        **summary_extras,
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(
            {"results": results, "summary": summary}, f, indent=2, ensure_ascii=False
        )
    print(f"\nReport written to: {report_path}")


if __name__ == "__main__":
    main()
