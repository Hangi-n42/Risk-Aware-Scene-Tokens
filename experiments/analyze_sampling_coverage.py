"""Sampled evaluation coverage report CLI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rast.evaluation.sampling_coverage import write_sampling_coverage_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze sampled evaluation axis coverage")
    parser.add_argument("--results", required=True, help="aggregate_results.csv path")
    parser.add_argument("--metadata", default=None, help="optional suite_metadata.json path")
    parser.add_argument("--output", required=True, help="Markdown output path")
    parser.add_argument("--json-output", default=None, help="optional JSON summary output path")
    args = parser.parse_args()

    summary = write_sampling_coverage_report(
        results_path=args.results,
        metadata_path=args.metadata,
        output_path=args.output,
        json_output_path=args.json_output,
    )
    print(f"sampling_coverage_report: {Path(args.output).resolve()}")
    print(f"analyzed_rows={summary['row_count']}")
    print(f"suite_run_id={summary.get('suite_run_id', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
