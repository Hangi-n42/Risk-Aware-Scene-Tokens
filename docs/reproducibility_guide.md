# RAST MVP-0 Reproducibility Guide

## 1. Environment Assumptions

- 이 guide는 Windows / PowerShell 환경과 Python virtualenv 사용 가능성을 기준으로 합니다.
- AI2-THOR, Webots, CoppeliaSim, real robot deployment는 이 guide의 실행 범위가 아닙니다.
- 모든 재현 절차는 `WindowsMetadataSim` metadata-only path를 기준으로 합니다.
- 최신 dependency version은 구현 시점의 공식 문서와 로컬 `pyproject.toml`을 확인해야 합니다.

## 2. Quick Verification

빠른 검증은 전체 pytest suite로 수행합니다.

```powershell
python -m pytest
```

Batch 16E 기준으로는 전체 테스트 통과가 기대됩니다. 테스트 개수는 이후 문서/검증 테스트 추가에 따라 달라질 수 있으므로, 실제 완료 여부는 pytest exit code와 최종 summary를 기준으로 확인합니다.

## 3. Recreate Default Baseline Report

default suite는 빠른 canonical baseline 재현용입니다.

```powershell
python experiments\run_windows_eval_suite.py --config configs\windows_eval_suite.yaml
python experiments\generate_result_report.py --results runs\windows_eval_suite\<LATEST_RUN>\aggregate_results.csv --summary runs\windows_eval_suite\<LATEST_RUN>\aggregate_summary.csv --output docs\result_report.md
```

`<LATEST_RUN>`은 실제 생성된 `runs/windows_eval_suite/...` directory로 바꾸십시오.

## 4. Recreate Sampled Extended Report

extended grid 전체는 매우 큽니다. 전체 조합을 실행하지 말고 sampling 또는 limit를 사용하십시오.

```powershell
python experiments\run_windows_eval_suite.py --config configs\windows_eval_suite_extended.yaml --sample-size 500 --sample-seed 42 --sampling-mode stratified --export-replays --max-replays-per-suite 10
```

그 다음 생성된 run directory로 결과 보고서를 재생성합니다.

```powershell
python experiments\generate_result_report.py --results runs\windows_eval_suite_extended\<LATEST_RUN>\aggregate_results.csv --summary runs\windows_eval_suite_extended\<LATEST_RUN>\aggregate_summary.csv --suite-metadata runs\windows_eval_suite_extended\<LATEST_RUN>\suite_metadata.json --replay-index runs\windows_eval_suite_extended\<LATEST_RUN>\replays\replay_index.json --output docs\result_report.md
```

주의: `configs/windows_eval_suite_extended.yaml`은 약 8,294,400 planned runs를 만들 수 있습니다. `--sample-size`, `--limit`, `--dry-run`, 또는 명시적인 `--allow-large-run` 없이 실행하지 마십시오. large-run guard가 accidental full run을 막아야 합니다.

## 5. Recreate Comparison Report

default baseline과 sampled extended candidate를 비교합니다.

```powershell
python experiments\compare_eval_runs.py --baseline-results runs\windows_eval_suite\windows_eval_suite_20260612_162821\aggregate_results.csv --baseline-summary runs\windows_eval_suite\windows_eval_suite_20260612_162821\aggregate_summary.csv --candidate-results runs\windows_eval_suite_extended\windows_eval_suite_20260612_224531\aggregate_results.csv --candidate-summary runs\windows_eval_suite_extended\windows_eval_suite_20260612_224531\aggregate_summary.csv --candidate-metadata runs\windows_eval_suite_extended\windows_eval_suite_20260612_224531\suite_metadata.json --candidate-coverage docs\sampling_coverage_report.md --candidate-seed-stability docs\seed_stability_report.md --candidate-sample-size-convergence docs\sample_size_convergence_report.md --output docs\eval_comparison_report.md
```

이 비교는 sensitivity exploration이며 performance superiority claim이 아닙니다.

## 6. Recreate Sampling Coverage Report

sampled extended run의 axis coverage를 분석합니다.

```powershell
python experiments\analyze_sampling_coverage.py --results runs\windows_eval_suite_extended_seed_sweep\seed_sweep_20260612_231815\seed_42\windows_eval_suite_20260612_231908\aggregate_results.csv --metadata runs\windows_eval_suite_extended_seed_sweep\seed_sweep_20260612_231815\seed_42\windows_eval_suite_20260612_231908\suite_metadata.json --output docs\sampling_coverage_report.md
```

Coverage는 sampling representativeness 점검입니다. RAST 성능 점수로 해석하지 마십시오.

## 7. Recreate Seed Stability Report

여러 sample seed에서 sampled extended evaluation을 반복 실행합니다.

```powershell
python experiments\run_sampled_seed_sweep.py --config configs\windows_eval_suite_extended.yaml --sample-size 500 --seeds 7,13,42 --sampling-mode stratified --export-replays --max-replays-per-suite 5
python experiments\compare_seed_sweep.py --seed-sweep-index runs\windows_eval_suite_extended_seed_sweep\<LATEST_SWEEP>\seed_sweep_index.json --output docs\seed_stability_report.md
```

`<LATEST_SWEEP>`은 실제 생성된 seed sweep directory로 바꾸십시오.

## 8. Recreate Sample-size Convergence Report

sample-size별 convergence와 sampling quality score를 계산합니다.

```powershell
python experiments\run_sample_size_sweep.py --config configs\windows_eval_suite_extended.yaml --sample-sizes 100,200,500 --seeds 7,13,42 --sampling-mode stratified --export-replays --max-replays-per-suite 3
python experiments\analyze_sample_size_convergence.py --sample-size-sweep-index runs\windows_eval_suite_sample_size_sweep\<LATEST_SWEEP>\sample_size_sweep_index.json --output docs\sample_size_convergence_report.md
```

`<LATEST_SWEEP>`은 실제 생성된 sample-size sweep directory로 바꾸십시오. Sampling quality score는 reliability heuristic이며 planner 성능 점수가 아닙니다.

## 9. Export Replay Artifacts

suite 실행 시 replay를 함께 생성할 수 있습니다.

```powershell
python experiments\run_windows_eval_suite.py --config configs\windows_eval_suite_extended.yaml --sample-size 500 --sample-seed 42 --sampling-mode stratified --export-replays --max-replays-per-suite 10
```

단일 run directory에서 replay markdown을 따로 export할 수도 있습니다.

```powershell
python experiments\export_decision_replay.py --run-dir <RUN_DIR> --output runs\replays\sample_decision_replay.md
```

Replay artifact는 visual replay가 아니라 metadata/action/evidence trace입니다.

## 10. What Not To Claim

- real-world performance claim을 하지 마십시오.
- real robot safety claim을 하지 마십시오.
- real perception uncertainty calibration claim을 하지 마십시오.
- EvidenceToken이 real sensor evidence나 visual evidence를 제공한다고 주장하지 마십시오.
- replay artifact를 visual replay라고 부르지 마십시오.
- sampled extended result를 exhaustive extended grid result라고 해석하지 마십시오.
- deterministic rule-based planner 결과를 learned model interpretability로 해석하지 마십시오.
