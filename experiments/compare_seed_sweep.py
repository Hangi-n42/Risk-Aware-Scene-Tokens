"""Seed sweep stability report CLI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rast.evaluation.seed_stability import write_seed_stability_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare sampled evaluation runs across sample seeds")
    parser.add_argument("--seed-sweep-index", required=True)
    parser.add_argument("--output", default=str(ROOT / "docs" / "seed_stability_report.md"))
    args = parser.parse_args()

    write_seed_stability_report(seed_sweep_index_path=args.seed_sweep_index, output_path=args.output)
    print(f"seed_stability_report: {Path(args.output).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
