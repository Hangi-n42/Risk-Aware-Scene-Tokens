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
    parser.add_argument("--replay-index", default=None, help="선택적 replay_index.json 경로")
    parser.add_argument("--suite-metadata", default=None, help="선택적 suite_metadata.json 경로")
    parser.add_argument("--sampling-coverage", default=None, help="선택적 sampling coverage report 경로")
    parser.add_argument("--seed-stability", default=None, help="선택적 seed stability report 경로")
    parser.add_argument("--sample-size-convergence", default=None, help="선택적 sample-size convergence report 경로")
    parser.add_argument("--output", default=str(ROOT / "docs" / "result_report.md"))
    args = parser.parse_args()

    write_result_report(
        results_path=args.results,
        summary_path=args.summary,
        replay_index_path=args.replay_index,
        suite_metadata_path=args.suite_metadata,
        sampling_coverage_path=args.sampling_coverage,
        seed_stability_path=args.seed_stability,
        sample_size_convergence_path=args.sample_size_convergence,
        output_path=args.output,
    )
    print(f"result_report: {Path(args.output).resolve()}")
    print(
        "report_sections: suite metadata, baseline comparison, EventToken Summary, "
        "UncertaintyToken Summary, EvidenceToken Summary, AffordanceToken Summary, Replay Trace Summary, "
        "Replay Artifact Summary, Representative Decision Trace Summary, "
        "Sampling Coverage and Stability Artifacts, Sample-size Convergence Artifact, "
        "Incremental Update Summary, Decision Trace Summary, "
        "Scene Graph vs RAST Differentiation Summary, Event-aware Planner Summary, "
        "Uncertainty-aware Planner Summary, Affordance-aware Planner Summary, "
        "Event-aware Ablation Summary, Threshold and Noise Sensitivity Summary, limitations"
    )
    print(
        "one-line example: python experiments\\generate_result_report.py "
        "--results runs\\windows_eval_suite\\<RUN_ID>\\aggregate_results.csv "
        "--summary runs\\windows_eval_suite\\<RUN_ID>\\aggregate_summary.csv "
        "--suite-metadata runs\\windows_eval_suite\\<RUN_ID>\\suite_metadata.json "
        "--replay-index runs\\windows_eval_suite\\<RUN_ID>\\replays\\replay_index.json "
        "--sampling-coverage docs\\sampling_coverage_report.md "
        "--seed-stability docs\\seed_stability_report.md "
        "--sample-size-convergence docs\\sample_size_convergence_report.md "
        "--output docs\\result_report.md"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
