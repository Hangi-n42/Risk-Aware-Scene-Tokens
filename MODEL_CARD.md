# RAST MVP-0 Model/Data Card

## 개요

RAST MVP-0에는 learned model이 포함되어 있지 않습니다. 현재 시스템은 `WindowsMetadataSim` synthetic metadata와 deterministic rule-based tokenizer/planner로 구성된 research prototype입니다.

## Intended Use

- RAST token contract와 planner decision trace를 API로 확인
- metadata-only controlled scenario에서 representation/planner 비교
- replay artifact, evidence pointer, sampling reliability report 재현

## Out-of-Scope Use

- real robot safety 판단
- real-world performance 주장
- 실제 RGB-D perception robustness 평가
- 실제 uncertainty calibration 평가
- learned model interpretability 주장
- visual replay 또는 real sensor evidence 제공

## Data Source

- `WindowsMetadataSim` synthetic metadata
- deterministic scenario definitions
- optional synthetic noise fields

## Model Behavior

모든 planner는 deterministic rule-based policy입니다. Event-aware, Uncertainty-aware, Affordance-aware planner는 token-to-decision 연결 가능성을 관찰하기 위한 experimental policy이며 성능 개선을 의미하지 않습니다.

## Limitations

- 실제 image crop, RGB/depth frame, sensor fusion 결과를 사용하지 않습니다.
- EvidenceToken은 metadata pointer 기반입니다.
- sampled extended evaluation은 exhaustive grid result가 아닙니다.
- 결과는 seed, sample size, scenario composition에 의존할 수 있습니다.
