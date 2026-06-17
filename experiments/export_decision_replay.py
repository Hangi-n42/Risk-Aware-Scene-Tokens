"""WindowsMetadataSim step log에서 decision replay markdown/json을 생성합니다."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rast.evaluation.replay import find_step_log, write_decision_replay


def main() -> int:
    parser = argparse.ArgumentParser(description="Export decision replay from a WindowsMetadataSim run directory")
    parser.add_argument("--run-dir", required=True, help="step_log.jsonl이 들어 있는 run directory입니다.")
    parser.add_argument("--output", default=None, help="decision_replay.md 출력 경로입니다.")
    parser.add_argument("--json-output", default=None, help="decision_replay.json 출력 경로입니다.")
    parser.add_argument("--limit", type=int, default=20, help="replay에 포함할 최대 step 수입니다.")
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    step_log_path = find_step_log(run_dir)
    output_md = Path(args.output) if args.output else step_log_path.parent / "decision_replay.md"
    output_json = Path(args.json_output) if args.json_output else output_md.with_suffix(".json")

    payload = write_decision_replay(
        step_log_path=step_log_path,
        output_md_path=output_md,
        output_json_path=output_json,
        limit=args.limit,
    )
    print(f"step_log: {step_log_path.resolve()}")
    print(f"decision_replay_md: {output_md.resolve()}")
    print(f"decision_replay_json: {output_json.resolve()}")
    print(f"selected_step_count={payload['selected_step_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
