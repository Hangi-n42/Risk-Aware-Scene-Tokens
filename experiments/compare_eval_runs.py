"""두 RAST evaluation run을 비교하는 Markdown report CLI입니다."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rast.evaluation.compare_runs import write_eval_comparison_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare two RAST evaluation aggregate runs")
    parser.add_argument("--baseline-results", required=True)
    parser.add_argument("--baseline-summary", default=None)
    parser.add_argument("--candidate-results", required=True)
    parser.add_argument("--candidate-summary", default=None)
    parser.add_argument("--baseline-metadata", default=None)
    parser.add_argument("--candidate-metadata", default=None)
    parser.add_argument("--candidate-coverage", default=None)
    parser.add_argument("--candidate-seed-stability", default=None)
    parser.add_argument("--candidate-sample-size-convergence", default=None)
    parser.add_argument("--output", default=str(ROOT / "docs" / "eval_comparison_report.md"))
    args = parser.parse_args()

    write_eval_comparison_report(
        baseline_results=args.baseline_results,
        baseline_summary=args.baseline_summary,
        candidate_results=args.candidate_results,
        candidate_summary=args.candidate_summary,
        baseline_metadata=args.baseline_metadata,
        candidate_metadata=args.candidate_metadata,
        candidate_coverage=args.candidate_coverage,
        candidate_seed_stability=args.candidate_seed_stability,
        candidate_sample_size_convergence=args.candidate_sample_size_convergence,
        output=args.output,
    )
    print(f"eval_comparison_report: {Path(args.output).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
