# 520 — 같은 가속 목표의 응답 역산: 모델 0.16초 개선, 승격하지 않음

519의 `source_drive` 경로·속도 참조·조향·brake·첫24hold gas0.32를 고정했다. positive nominal gas가 뜻하는 4tick 종료속도 `v+0.08×80000×gas/(MASS×(v+2.7))`를 그대로 두고 gas 실행 변환만 steady/response로 비교했다. 같은 상태에서는 양쪽 목표가 정확히 같다. 각 전체 궤적은 자신의 현재 상태로 목표를 계산하므로 서로 다른 궤적의 수치 목표까지 동일하다는 주장은 하지 않는다.

[사전 계약](gas520_contract.json) · [응답 역산](gas520_control.py) · [테스트](test_gas520.py) · [모델 실행](gas520_model.py) · [원 결과](gas520_model_result.json) · [저장 진단](gas520_diagnose.py) · [진단/비용 정정](gas520_diagnosis.json).

## 방법과 선행 게이트

512 source 순서 모델의 후륜 gas ramp, 현재 wheel omega/engine multiplier, 복합 tyre clipping, 현재 grip와 contact 전이를 사용한다. gas 0..1의 9개 coarse 표본이 비감소인지 검사한 뒤 첫 목표 bracket에서 float32 이진 탐색한다. 선택 gas와 직전 float32를 검사하고 overshoot 1e-4m/s 이하를 요구한다. 표본 단조성은 연속 구간 전체의 증명이 아니며, 비단조/미인증이면 중단한다. gas0/1로 목표에 도달하지 못할 때는 목표를 바꾸거나 brake를 추가하지 않고 해당 끝점과 잔차를 보고한다.

저장519 모델의 positive-gas tracking hold 시작 상태를 COM 속도로 정렬한 네 rank quantile을 결과 관측 전에 선택했다. 각 상태에서 같은 목표를 비교하고 평균 절대오차가 50% 이상 줄어야 cold 모델을 허용했다. cold와 같은 실제 carry 상태의 양쪽 안전 완주 및 각각 **0.50초 이상** 개선이 모두 필요하다. 통과할 때만 sameDEV 실제 짝 비교 최대1000actions/2resets를 허용했다. 실제 기록 개선에는 두 실제 source 공식 finish가 필요하다. DEV 외 HOLDOUT/SEALED·새 seed는 사용하지 않았다.

## 검증 결과

순수 테스트2개 통과. 저장 네 상태의 평균 4tick 목표 오차는 steady **0.0955657555m/s**, response **2.6014e-8m/s**로 선행 게이트를 통과했다. 네 상태 모두 목표가 gas 범위 내에서 도달 가능했다. 이는 저장 모델 상태의 일관성 검사이며 독립 실제 물리 보정 검증은 아니다.

|cold 모델|steady519 재사용|response520|
|---|---:|---:|
|source-style 완주 추정|20.38s|20.22s|
|최소 sampled 전체 차체/바퀴 여유|0.979789m|0.989912m|
|최대 path error|1.203440m|1.224821m|
|tracking 참조 초과|4.317375m/s|4.309134m/s|
|tracking source force peak|0.934112|0.977482|
|tracking clipped wheel samples|0|0|
|visited tiles|283|283|

두 궤적의 scalar 참조 clock은19.848402초로 동일하다. response는 margin0.50m/path3m/overspeed5m/s, phase별 force/clipping 및 source-style finish 안전 게이트를 통과했다. 그러나 개선 **0.16초 < 0.50초**로 효과 게이트에 미달했다. 따라서 carry0, 새 native action/reset/world0으로 중단했다. 실제 최선20.70초 기록은 갱신되지 않았다. 모델 finish는 실제 공식 finish 검증이 아니다.

## 저장 진단과 다음 판단

각 궤적의 완전한 positive request hold만 보면 평균 절대 목표 오차는0.182963→0.064292m/s, 평균 gas는0.516774→0.625226이었다. 표본수가144/134로 다르고 상태도 달라 이 비교를 독립 matched 인과 효과로 해석하지 않는다. response의135개 positive request 중122개는 float32 bracket,13개는 gas1로도 목표 미달이었다. 마지막 partial finish hold는 완전한4tick 오차 집계에서 제외했다. 모든 tracking hold에서 명령 조향/brake는 해당 현재 상태의 원래 nominal과 bit 단위로 같았다.

[도달 불가능 목표 집계](gas520_unreachable.json): gas1 미달13hold는1.04초, 평균 목표 부족0.662702m/s/최대1.333518m/s다. 해당 구간 source force peak0.953225/clipping0이다. 시작 후륜 gas는0..1 범위여서 ramp 하나만을 유일 원인으로 단정할 수 없다. 다음 분석 대상은 고정 목표를 유지한 상태에서 engine/wheel 이력과4tick 도달 집합의 관계다. 참조·force cap을 높이는 것으로 대체하지 않는다. 이번 결과는 한 수정의 승격 실패이며 가속 응답 방법군의 불가능성 증명이 아니다.

## 비용·보존·승인

새 모델 적분 **17495ticks** = pure36 + 저장상태588 + cold body1011 + cold inverse forecast15860. 적분 내 source wheel force 평가69980회와 별도 진단 force oracle4044회는 별도 비용이다. 기존519 baseline1020ticks는 재적분하지 않았다. 원 결과 JSON에 남은 재사용1036 표기는518에서 상속된 라벨 오류이며 진단 JSON에서1020으로 정정했다. 원 결과와 계약을 고쳐 재실행하지 않았다.

모델 worker CPU19.417768초/wall19.421970초, 저장 진단 worker CPU0.434134초/wall0.443683초다. 별도 짧은 저장자료 분석·준비·publication에는3CPU/3wall allowance를 표시하며 실제 측정값으로 혼동하지 않는다. native/raw/reset 모두0. 연구24938·예비84000/used0 불변이다. 원시 상태·지도·명령·RNG는 비공개 경로에 보존했다. source/input SHA를 검증했으며 이전 연구 실행, 보호 평가, 새 seed, 별도 유료 자원0이다.

승인 종료는 **2026-10-20 19:01:55 KST**다. 이 작업 초기에 오래된10월16일 지시를 현재 지시와 혼동해 일시 중단한 오류를 바로잡고, 기존 초안에서 중복 구현/실험 없이 이어갔다. main 지정 SHA와 Participants, 사용자 변경 및 백업을 보존한다.
