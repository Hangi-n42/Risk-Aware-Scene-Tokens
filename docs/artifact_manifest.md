# RAST MVP-0 Artifact Manifest

## 1. Overview

이 문서는 RAST MVP-0의 현재 실험 산출물, canonical run directory, 주요 report, 재현 명령을 한곳에 묶은 artifact manifest입니다. 현재 구현은 `WindowsMetadataSim` 기반 deterministic metadata simulator에서 동작하며, 실제 3D rendering, real robot, RGB-D perception, detector error, real sensor evidence를 검증하지 않습니다.

이 manifest의 목적은 제3자가 저장소를 열었을 때 어떤 문서를 먼저 읽고, 어떤 run directory를 기준으로 해석하며, 어떤 명령으로 report를 재생성할 수 있는지 추적할 수 있게 하는 것입니다.

## 2. Canonical Reports

| Artifact path | Purpose | Source inputs | Generation command | Interpretation caution |
|---|---|---|---|---|
| `docs/result_report.md` | 최신 sampled extended evaluation 결과, replay artifact, coverage/stability/convergence artifact를 연결한 결과 보고서 | `runs/windows_eval_suite_extended/windows_eval_suite_20260612_224531/aggregate_results.csv`, `aggregate_summary.csv`, `suite_metadata.json`, `replays/replay_index.json`, `docs/sampling_coverage_report.md`, `docs/seed_stability_report.md`, `docs/sample_size_convergence_report.md` | `python experiments\generate_result_report.py --results runs\windows_eval_suite_extended\windows_eval_suite_20260612_224531\aggregate_results.csv --summary runs\windows_eval_suite_extended\windows_eval_suite_20260612_224531\aggregate_summary.csv --suite-metadata runs\windows_eval_suite_extended\windows_eval_suite_20260612_224531\suite_metadata.json --replay-index runs\windows_eval_suite_extended\windows_eval_suite_20260612_224531\replays\replay_index.json --sampling-coverage docs\sampling_coverage_report.md --seed-stability docs\seed_stability_report.md --sample-size-convergence docs\sample_size_convergence_report.md --output docs\result_report.md` | sampled extended subset 결과이며 exhaustive extended grid 결과가 아닙니다. |
| `docs/technical_report.md` | RAST MVP-0의 방법론, token set, baseline/planner 구조, 실험 범위, 한계를 설명하는 paper-style 기술 보고서 | `docs/result_report.md`, canonical run outputs, project PRD/stack/tasks | 수동 갱신 문서입니다. 최신 수치와 구조는 `docs/result_report.md`와 대조해야 합니다. | 연구 주장 최종본이 아니라 MVP-0 기술 정리 문서입니다. |
| `docs/eval_comparison_report.md` | default baseline run과 sampled extended candidate run의 비교 보고서 | default aggregate files, sampled extended aggregate files, candidate metadata, coverage/stability/convergence reports | `python experiments\compare_eval_runs.py --baseline-results runs\windows_eval_suite\windows_eval_suite_20260612_162821\aggregate_results.csv --baseline-summary runs\windows_eval_suite\windows_eval_suite_20260612_162821\aggregate_summary.csv --candidate-results runs\windows_eval_suite_extended\windows_eval_suite_20260612_224531\aggregate_results.csv --candidate-summary runs\windows_eval_suite_extended\windows_eval_suite_20260612_224531\aggregate_summary.csv --candidate-metadata runs\windows_eval_suite_extended\windows_eval_suite_20260612_224531\suite_metadata.json --candidate-coverage docs\sampling_coverage_report.md --candidate-seed-stability docs\seed_stability_report.md --candidate-sample-size-convergence docs\sample_size_convergence_report.md --output docs\eval_comparison_report.md` | metric 차이는 sampled composition 차이일 수 있으며 planner 성능 우열 증거가 아닙니다. |
| `docs/sampling_coverage_report.md` | sampled extended run의 scenario/policy/threshold/noise axis coverage 분석 | seed 42 sampled run aggregate and metadata under `runs/windows_eval_suite_extended_seed_sweep/seed_sweep_20260612_231815` | `python experiments\analyze_sampling_coverage.py --results runs\windows_eval_suite_extended_seed_sweep\seed_sweep_20260612_231815\seed_42\windows_eval_suite_20260612_231908\aggregate_results.csv --metadata runs\windows_eval_suite_extended_seed_sweep\seed_sweep_20260612_231815\seed_42\windows_eval_suite_20260612_231908\suite_metadata.json --output docs\sampling_coverage_report.md` | coverage 분석은 sampling 대표성 점검이며 성능 평가 점수가 아닙니다. |
| `docs/seed_stability_report.md` | sample seed 7/13/42의 seed-to-seed metric stability 비교 | `runs/windows_eval_suite_extended_seed_sweep/seed_sweep_20260612_231815/seed_sweep_index.json` | `python experiments\compare_seed_sweep.py --seed-sweep-index runs\windows_eval_suite_extended_seed_sweep\seed_sweep_20260612_231815\seed_sweep_index.json --output docs\seed_stability_report.md` | seed variation은 sampling sensitivity로 해석해야 합니다. |
| `docs/sample_size_convergence_report.md` | sample-size 100/200/500에서 metric convergence와 sampling quality score 비교 | `runs/windows_eval_suite_sample_size_sweep/sample_size_sweep_20260613_010716/sample_size_sweep_index.json` | `python experiments\analyze_sample_size_convergence.py --sample-size-sweep-index runs\windows_eval_suite_sample_size_sweep\sample_size_sweep_20260613_010716\sample_size_sweep_index.json --output docs\sample_size_convergence_report.md` | sampling quality score는 heuristic reliability score이며 RAST 성능 점수가 아닙니다. |

## 3. Canonical Run Directories

| Run path | Run type | Config | Sample / seed | Total runs / failed runs | Generated outputs | Replay index |
|---|---|---|---|---|---|---|
| `runs/windows_eval_suite/windows_eval_suite_20260612_162821` | default baseline suite | `configs/windows_eval_suite.yaml` | not sampled | 900 / 0 | `aggregate_results.csv`, `aggregate_results.json`, `aggregate_summary.csv`, `aggregate_summary.json` | not generated for this canonical default run |
| `runs/windows_eval_suite_extended/windows_eval_suite_20260612_224531` | sampled extended candidate | `configs/windows_eval_suite_extended.yaml` | sample size 500, seed 42, stratified | 500 / 0, from 8,294,400 planned runs | aggregate files, `suite_metadata.json`, replay artifacts | `runs/windows_eval_suite_extended/windows_eval_suite_20260612_224531/replays/replay_index.json` |
| `runs/windows_eval_suite_extended_seed_sweep/seed_sweep_20260612_231815` | seed-to-seed sampled sweep | `configs/windows_eval_suite_extended.yaml` | sample size 500, seeds 7/13/42, stratified | 1,500 / 0 across 3 sampled runs | `seed_sweep_index.json`, per-seed aggregate files and replay indexes | per-seed replay indexes recorded in `seed_sweep_index.json` |
| `runs/windows_eval_suite_sample_size_sweep/sample_size_sweep_20260613_010716` | sample-size convergence sweep | `configs/windows_eval_suite_extended.yaml` | sample sizes 100/200/500, seeds 7/13/42, stratified | 2,400 / 0 across 9 sampled runs | `sample_size_sweep_index.json`, per-run aggregate files and replay indexes | per-run replay indexes recorded in `sample_size_sweep_index.json` |

## 4. Config Files

| Config path | Purpose | Expected use | Safe for default execution | Sampling or limit required | Known planned run scale |
|---|---|---|---|---|---|
| `configs/windows_eval_suite.yaml` | 빠른 default evaluation suite | 기본 regression/evaluation 및 baseline report 재생성 | Yes | No | 900 runs in the canonical default run |
| `configs/windows_eval_suite_extended.yaml` | threshold/noise/uncertainty grid를 넓힌 extended sensitivity grid | `--dry-run`, `--sample-size`, `--limit`와 함께 사용 | No | Yes, unless `--allow-large-run` is explicitly chosen | 8,294,400 planned runs |
| `configs/windows_eval_suite_sampled.yaml` | extended grid를 sampled execution profile로 문서화한 config | `--sample-size`와 `--sample-seed`를 명시해 sampled extended run 실행 | No | Yes | extended grid와 같은 축을 사용하므로 sampling 필요 |
| `configs/windows_metadata_sim.yaml` | 단일 WindowsMetadataSim episode 설정 | local smoke/diagnostic episode 실행 | Yes | No | single episode config |

## 5. Replay Artifacts

Replay artifact는 특정 suite run의 `step_log.jsonl`에서 중요한 decision step을 추출해 markdown/json으로 저장한 metadata/action/evidence trace입니다. canonical sampled extended run의 replay index는 다음 경로입니다.

```text
runs/windows_eval_suite_extended/windows_eval_suite_20260612_224531/replays/replay_index.json
```

대표 replay markdown/json은 같은 `replays/` directory 아래에 저장됩니다. 지원되는 replay case type은 collision, near-miss, planner disagreement, RAST vs Scene Graph disagreement, RAST vs Uncertainty-aware disagreement, RAST vs Affordance-aware disagreement, event-triggered action, uncertainty-triggered action, affordance-triggered action, high RiskToken step, high UncertaintyToken step입니다.

Replay는 visual replay가 아닙니다. 현재는 WindowsMetadataSim의 metadata snapshot, selected action, PlannerDecision, token/evidence pointer를 재구성한 trace입니다.

## 6. Interpretation Boundaries

- 현재 모든 canonical result는 `WindowsMetadataSim` deterministic metadata simulator 기반입니다.
- real robot, real perception, real sensor evidence, RGB-D detector error, 실제 3D rendering/physics 결과가 아닙니다.
- sampled extended result는 exhaustive extended grid result가 아닙니다.
- sampling quality score는 sampling reliability를 요약하는 heuristic이며 RAST 성능 점수가 아닙니다.
- Object List, Flat Feature, Scene Graph, RAST, Event-aware RAST, Uncertainty-aware RAST, Affordance-aware RAST planner는 deterministic rule-based experimental policy입니다.
- replay artifact는 metadata/action/evidence trace이며 visual replay 또는 learned interpretability 결과가 아닙니다.
- 보고서의 metric 차이는 controlled metadata simulator에서 관찰된 decision boundary 차이이며, real-world safety나 task performance 향상을 증명하지 않습니다.
