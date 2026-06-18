# RAST MVP-0 Retrospective

## 목표

RAST MVP-0의 목표는 raw observation과 planner 사이에 planner-facing token contract를 두고, 여러 representation/planner를 같은 evaluation contract로 비교할 수 있는 연구 prototype을 만드는 것이었습니다.

## 구현한 것

- Core token set: Entity, Risk, Relation, Event, Uncertainty, Evidence, Affordance
- Baseline/planner: Object List, Flat Feature Table, Scene Graph, RAST, Event-aware, Uncertainty-aware, Affordance-aware
- WindowsMetadataSim controlled scenario suite
- Decision trace, evidence pointer, replay artifact
- sampled extended evaluation, seed stability, sample-size convergence
- FastAPI API, 최소 HTML UI, Docker/CI/submission hardening

## 어려웠던 점

- Windows native 환경에서 AI2-THOR 실행 제약이 있어 metadata-only simulator 경로를 안정화해야 했습니다.
- token contract와 baseline fairness를 동시에 유지하면서 log/summary/report schema를 확장해야 했습니다.
- sampled extended evaluation을 exhaustive result처럼 오해하지 않도록 문서 경계를 반복해서 정리해야 했습니다.

## 실험 한계

- WindowsMetadataSim은 deterministic metadata simulator입니다.
- 실제 3D rendering, physics, detector error, RGB-D perception latency, real robot action feasibility를 반영하지 않습니다.
- 모든 planner는 deterministic rule-based experimental policy입니다.
- 현재 결과는 RAST가 일반적으로 우수하다는 결론을 지원하지 않습니다.

## 다음 단계

- replay artifact와 report 연결 강화
- Docker 배포와 release tag 정리
- Webots/perception-bound adapter spike
- learned extractor와 VLA/LLM planner 연동 가능성 검토

## 오픈소스 관점에서 배운 점

재현 가능한 연구 prototype은 코드뿐 아니라 실행 방법, 실패 대응, 해석 한계, 제출 체크리스트가 함께 정리되어야 외부 사용자가 안전하게 평가할 수 있습니다.
