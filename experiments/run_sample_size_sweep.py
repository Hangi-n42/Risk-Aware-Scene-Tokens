"""Run sampled extended evaluation for multiple sample sizes and seeds."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run sampled RAST evaluation suite across sample sizes and seeds")
    parser.add_argument("--config", default=str(ROOT / "configs" / "windows_eval_suite_extended.yaml"))
    parser.add_argument("--sample-sizes", default="100,200,500,1000")
    parser.add_argument("--seeds", default="7,13,42")
    parser.add_argument("--sampling-mode", choices=("stratified", "random"), default="stratified")
    parser.add_argument("--export-replays", action="store_true")
    parser.add_argument("--max-replays-per-suite", type=int, default=3)
    parser.add_argument("--output-root", default=str(ROOT / "runs" / "windows_eval_suite_sample_size_sweep"))
    args = parser.parse_args()

    sample_sizes = _parse_int_list(args.sample_sizes)
    seeds = _parse_int_list(args.seeds)
    sweep_id = f"sample_size_sweep_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    sweep_dir = Path(args.output_root) / sweep_id
    sweep_dir.mkdir(parents=True, exist_ok=True)

    runs: list[dict[str, Any]] = []
    for sample_size in sample_sizes:
        for seed in seeds:
            run_output_root = sweep_dir / f"sample_size_{sample_size}" / f"seed_{seed}"
            run_output_root.mkdir(parents=True, exist_ok=True)
            command = [
                sys.executable,
                str(ROOT / "experiments" / "run_windows_eval_suite.py"),
                "--config",
                str(args.config),
                "--sample-size",
                str(sample_size),
                "--sample-seed",
                str(seed),
                "--sampling-mode",
                args.sampling_mode,
                "--output-dir",
                str(run_output_root),
            ]
            if args.export_replays:
                command.extend(["--export-replays", "--max-replays-per-suite", str(args.max_replays_per_suite)])

            print(f"[sample_size {sample_size} seed {seed}] running sampled suite")
            result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)

            run_dir = _latest_suite_dir(run_output_root)
            if result.returncode != 0 or run_dir is None:
                runs.append(
                    {
                        "sample_size": sample_size,
                        "seed": seed,
                        "run_dir": str(run_dir or run_output_root),
                        "aggregate_results": "",
                        "aggregate_summary": "",
                        "suite_metadata": "",
                        "replay_index": "",
                        "failed_runs": 1,
                        "status": "failed",
                        "error": result.stderr or result.stdout,
                    }
                )
                continue

            metadata_path = run_dir / "suite_metadata.json"
            metadata = _read_json(metadata_path)
            runs.append(
                {
                    "sample_size": sample_size,
                    "seed": seed,
                    "run_dir": str(run_dir),
                    "aggregate_results": str(run_dir / "aggregate_results.csv"),
                    "aggregate_summary": str(run_dir / "aggregate_summary.csv"),
                    "suite_metadata": str(metadata_path),
                    "replay_index": str(run_dir / "replays" / "replay_index.json")
                    if (run_dir / "replays" / "replay_index.json").exists()
                    else "",
                    "failed_runs": int(metadata.get("failed_runs", 0) or 0),
                    "status": "success",
                }
            )

    index = {
        "sample_size_sweep_id": sweep_id,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "config_path": str(args.config),
        "sampling_mode": args.sampling_mode,
        "sample_sizes": sample_sizes,
        "seeds": seeds,
        "runs": runs,
    }
    index_path = sweep_dir / "sample_size_sweep_index.json"
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"sample_size_sweep_index: {index_path.resolve()}")
    return 0 if all(run.get("status") == "success" for run in runs) else 1


def _parse_int_list(value: str) -> list[int]:
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def _latest_suite_dir(output_root: Path) -> Path | None:
    candidates = [path for path in output_root.glob("windows_eval_suite_*") if path.is_dir()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
