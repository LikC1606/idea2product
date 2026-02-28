"""Aggregate ablation results from multiple benchmark_report_*.json files.

Reads all benchmark_report*.json in data/, merges summaries by config, outputs
Markdown and LaTeX tables for paper writing.

Usage:
  python -m src.benchmarks.aggregate_ablation [data_dir]
  Default data_dir: data/

Output: prints Markdown table to stdout, writes data/ablation_summary.md
"""

import json
import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


def load_reports(data_dir: Path) -> list:
    """Load all benchmark_report*.json files."""
    reports = []
    for f in sorted(data_dir.glob("benchmark_report*.json")):
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            config = data.get("summary", {}).get("config_preset")
            if config is None:
                config = (
                    f.stem.replace("benchmark_report_", "") if "_" in f.stem else "full"
                )
            reports.append({"path": f, "config": config, "data": data})
        except Exception as e:
            print(f"Warning: skip {f}: {e}", file=sys.stderr)
    return reports


def build_table(reports: list) -> tuple[str, str]:
    """Build Markdown and LaTeX tables from reports."""
    rows = []
    for r in reports:
        s = r["data"].get("summary", {})
        config = r["config"]
        total = s.get("total", 0)
        success = s.get("success", 0)
        deployable = s.get("deployable", 0)
        test_passed = s.get("test_passed", 0)
        success_rate = (success / total * 100) if total else 0
        deploy_rate = (deployable / total * 100) if total else 0
        test_rate = (test_passed / total * 100) if total else 0
        align = s.get("avg_alignment_score")
        align_str = f"{align:.2f}" if align is not None else "-"
        code_q = s.get("avg_code_quality_score")
        code_str = f"{code_q:.2f}" if code_q is not None else "-"
        sec = s.get("avg_security_score")
        sec_str = f"{sec:.2f}" if sec is not None else "-"
        dur = s.get("avg_duration_seconds")
        dur_str = f"{dur:.0f}s" if dur is not None else "-"
        # Mean±std if available
        sr_mean = s.get("success_rate_mean")
        sr_std = s.get("success_rate_std")
        if sr_mean is not None and sr_std is not None:
            success_str = f"{sr_mean*100:.0f}±{sr_std*100:.0f}%"
        else:
            success_str = f"{success_rate:.0f}%"
        rows.append(
            {
                "config": config,
                "success": success_str,
                "deploy": f"{deploy_rate:.0f}%",
                "test": f"{test_rate:.0f}%",
                "align": align_str,
                "code": code_str,
                "sec": sec_str,
                "dur": dur_str,
                "n": total,
            }
        )

    # Markdown
    md_lines = [
        "| Config | Success | Deploy | Test Pass | Align | Code Q | Security | Duration | N |",
        "|--------|---------|--------|-----------|-------|--------|----------|----------|---|",
    ]
    for row in rows:
        md_lines.append(
            f"| {row['config']} | {row['success']} | {row['deploy']} | {row['test']} | "
            f"{row['align']} | {row['code']} | {row['sec']} | {row['dur']} | {row['n']} |"
        )

    # LaTeX
    latex_lines = [
        "\\begin{tabular}{lccccccc}",
        "\\toprule",
        "Config & Success & Deploy & Test & Align & CodeQ & Sec & Dur \\\\",
        "\\midrule",
    ]
    for row in rows:
        latex_lines.append(
            f"{row['config']} & {row['success']} & {row['deploy']} & {row['test']} & "
            f"{row['align']} & {row['code']} & {row['sec']} & {row['dur']} \\\\"
        )
    latex_lines.extend(["\\bottomrule", "\\end{tabular}"])

    return "\n".join(md_lines), "\n".join(latex_lines)


def main():
    data_dir = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path(__file__).parent.parent.parent / "data"
    )
    if not data_dir.exists():
        print(f"Error: {data_dir} not found", file=sys.stderr)
        sys.exit(1)

    reports = load_reports(data_dir)
    if not reports:
        print("No benchmark_report*.json found.", file=sys.stderr)
        sys.exit(0)

    md_table, latex_table = build_table(reports)

    print("## Ablation Summary (Markdown)\n")
    print(md_table)
    print("\n## LaTeX\n")
    print(latex_table)

    out_path = data_dir / "ablation_summary.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# Ablation Study Summary\n\n")
        f.write("Generated from benchmark_report_*.json\n\n")
        f.write(md_table)
        f.write("\n\n## LaTeX\n\n```\n")
        f.write(latex_table)
        f.write("\n```\n")
    print(f"\nWrote: {out_path}")


if __name__ == "__main__":
    main()
