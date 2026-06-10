"""Aggregate 결과에서 docs/result_report.md를 생성하는 CLI입니다."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rast.evaluation.report import write_result_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate RAST MVP-0 Markdown result report")
    parser.add_argument("--results", required=True, help="aggregate_results.csv 또는 aggregate_results.json 경로")
    parser.add_argument("--summary", default=None, help="선택적 aggregate_summary.csv 또는 aggregate_summary.json 경로")
    parser.add_argument("--output", default=str(ROOT / "docs" / "result_report.md"))
    args = parser.parse_args()

    write_result_report(
        results_path=args.results,
        summary_path=args.summary,
        output_path=args.output,
    )
    print(f"result_report: {Path(args.output).resolve()}")
    print(
        "report_sections: baseline comparison, EventToken Summary, "
        "Incremental Update Summary, Decision Trace Summary, limitations"
    )
    print(
        "one-line example: python experiments\\generate_result_report.py "
        "--results runs\\windows_eval_suite\\<RUN_ID>\\aggregate_results.csv "
        "--summary runs\\windows_eval_suite\\<RUN_ID>\\aggregate_summary.csv "
        "--output docs\\result_report.md"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
