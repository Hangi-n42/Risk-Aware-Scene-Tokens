"""Sample-size convergence report 생성 CLI입니다."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rast.evaluation.sample_size_convergence import write_sample_size_convergence_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze sample-size convergence for sampled RAST evaluation runs")
    parser.add_argument("--sample-size-sweep-index", required=True)
    parser.add_argument("--output", default=str(ROOT / "docs" / "sample_size_convergence_report.md"))
    parser.add_argument("--json-output", default=None)
    args = parser.parse_args()

    write_sample_size_convergence_report(
        sample_size_sweep_index_path=args.sample_size_sweep_index,
        output_path=args.output,
        json_output_path=args.json_output,
    )
    print(f"sample_size_convergence_report: {Path(args.output).resolve()}")
    if args.json_output:
        print(f"sample_size_convergence_json: {Path(args.json_output).resolve()}")
    else:
        print(f"sample_size_convergence_json: {Path(args.output).with_suffix('.json').resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
