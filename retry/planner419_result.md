# 419 — 현재 상태의 세 recipe를 긴 C witness로 비교하는 정적 planner

**상태 기반 질의·근거 검증·시간 선택과 진행 ledger를 순수 코드로 구현하고 정적36개 테스트를 통과했다.** 새 실제·모델 적분은0이다. rollout backend와 actuator는 연결하지 않았다. 긴 C tail의 실제 fidelity·새 planner 성능·안전 fallback을 검증한 결과가 아니다. [동결 설계·다음 실험 제안](planner419_design.md), [planner 코드](planner419.py), [집계 결과·비용](planner419_result.json).

## 선택 규칙

현재 signed C nominal, 첫 nominal 조향+gas1/brake0 후 C, 기존 첫 neutral `[0,0,float32(.3)]` 후 C의 세 recipe만 쓴다. 새로운 조향·pedal 크기·gain·경로 탐색은 없다. FIRST_LAP·r>0·projection·현재 안전·restore·actual 진행 ledger·비용이 적격인 **현재 decision boundary**에서 질의한다. 절대 행동 번호·arc 구간·seed를 활성화 트리거로 쓰지 않는다. 이미 같은 첫 명령인 recipe는 dedup한다.

기준은 기존 guardian이다. nominal13이 부적격이면 기존 neutral13을 확인하고, 둘 다 불가면 gas가 빠르더라도 중단한다. 복원·반복·부모/RNG·수치 fidelity 실패도 중단한다. q>1 자체를 새 안전 거부 조건으로 쓰지 않는다. 정지·미소 음수 sigma는 기존 signed 식 그대로, 의미 있는 후진·r=0·현재 vertex 거부·phase/finish 경계는 기존 조건대로 처리한다. epsilon·projection 수리·COM/origin 수정은 없다. 비용이 현재 guardian조차 검증하기에 부족하면 중단하며, 새 안전 제동 fallback을 발명하지 않는다.

**후속 비용 방법은 더 긴 C nominal continuation witness 하나**다.13행동 적격 child의 전체 물리·controller 상태를 같은 world에서 이어, 공식 finish 또는 첫 안전·진행·정의역·비용 실패까지 C nominal로 진행하는 프로토콜이다. 추가308행동 cap과13행동 이하 checkpoint를 둔다. speed·yaw·경로 오차·타이어·가스 이력·남은 경로의 효과는 이 동역학 continuation에 들어간다. terminal 벡터를 가중 점수로 합치거나 `남은 거리/속도`로 미관측 시간을 채우지 않는다.

각 적격 recipe의 같은 root부터 공식 finish까지의 raw50Hz bracket을 비교한다. 대안 upper가 guardian baseline lower보다 엄격히 작을 때만 보장 양의 시간 이득이다. 중첩·접촉은 baseline을 유지한다. 여러 대안이 baseline을 지배하면 가장 작은 finish upper를 택하는 유한 후보의 보수적 선택이다. **417의0.08초는 보편 기준으로 전용하지 않았다.** 짧은30m exit는 진단값이며, locally 느린 neutral이 더 좋은 finish witness를 보이면 선택할 수 있다. 미완료·검열·안전 실패 tail에는 finish 점수가 없다.

이 witness는 매 미래 상태에서 guardian을 재귀 질의하는 정책 전체가 아니라 **feasible nominal C continuation**이다. 그 nominal tail이 실패하면 나중에 guardian이 구해줄 것이라고 가정하지 않는다. 실제 guardian이 명령을 바꾸면 exact witness와 실제 정책 결과를 분리해야 한다.13행동 실제 자격을 긴 counterfactual tail이나 다른 상태로 확대하지 않았다. 코드 출력은 모델 제안이며 `actual_execution_allowed=False`다.

## 현재 입력·goal·memory 분리

parent의 현재 state·nominal 계산 직전 memory·RNG·raw clock를 immutable bytes로 묶는다. child마다 새 복사본을 주며 branch end memory를 부모로 commit하지 않는다. root/ledger/policy digest가 다른 receipt, 다른 controller tail, profile 시계, 새로운 첫 명령을 거부한다. current 입력 통로에는 future trace·다음 actual state·lap 결과를 넣지 않는다.

실제3.24m goal은 실제 commit 관측의 도달에만 갱신하고13행동 deadline은 그동안 유지한다. 별도 [ForecastLedger](planner419_model_ledger.py)는 예측 child 내부에서만 다음 goal을 갱신한다. MODEL prediction을 actual ledger에 전달하거나 실제 관측을 MODEL 채널로 전달하면 거부한다. child가 도달했다는 이유로 부모의 실제 goal을 미리 앞으로 밀지 않는다.

## 정적 검증

| 검증 범위 | 결과 |
|---|---:|
| selector·단위·불확실성·phase·비용·입력/메모리 논리 | 26개 통과 |
| 저장412·414·418 사례 | 6개 통과 |
| 별도 모델 ledger/실제 채널 분리 | 4개 통과 |
| 합계 | **36개, 실패0** |

테스트의 완료 tail 숫자는 명시적 synthetic logic fixture이며 모델 성능 증거가 아니다. 실제 사례 테스트는 다음을 확인했다.

- **412:** profile 참조 시계·조건부 회수율을 공식 finish score로 받지 않는다.
- **414:** 짧은 이득 뒤의 O 진행 검열을 보존한다. O의 실패 tail을 C continuation으로 바꿔 붙이지 않는다. 새 planner가 실제로414를 피했을 것이라고 주장하지 않는다.
- **418:** clipping 보정과13행동 exit 이득만으로는 C tail이 없으므로 선택을 확정하지 않는다. 실제 C fork의 현재 입력을 구성해 recipe 질의를 확인했고, 저장된 실제 goal 갱신과 parent/memory 복사 독립성을 검사했다.

그 밖에 raw tick과 초 혼용, overlap에서 가짜 이득, locally 느린 neutral의 부당한 제외, censored time 추정, stale root/clock/RNG/ledger, 별도 gain/steer·tail horizon 수리, forecast의 실제 goal 갱신, 동일 명령 alias의 가짜 시간 이득을 검사했다. 정상 partial official finish도 처리한다. 현재 vertex 구멍과 COM/origin 차이는 고치지 않았다. 주 테스트 중 integration module import를 차단했으며 시도는0이었다. [주 테스트](test_planner419.py), [모델 ledger 테스트](test_planner419_model_ledger.py).

## 필수 질의와 자격 중복 비용

세 distinct recipe의 첫13행동은 필수156tick/3world다. 같은 child에서 추가308행동까지 이어 공식 finish를 확인하는 최악 필수 비용은3852tick/3world이고, 연구용 독립 반복의 추가 비용도3852tick/3world다. 합계7704tick/6world다. 첫13을 continuation에 이중 계산하지 않는다. 원래 상태와 다른 approximate cache를 현재 증거로 쓰지 않는다.

418 실측 query별 CPU/tick의 최대는 약0.003646초, wall/tick 최대는0.003686초였다. 이를7704tick에 곱한 보수적 **경험적 예산 추정**은 CPU28.09초/wall28.40초다. 긴 tail·다른 상태의 증명된 상한이 아니므로 hard cap·중단 계측이 필수다. real-time80ms 이내를 주장하지 않는다.

다음 모델 pilot은 같은 보정 root에서 C0와 planner의 부모 **모델 상태를3회 갱신**하고, 이후 둘 다 C nominal continuation을 공식 finish/실패까지 확인하는 제안이다. 설계 문서의 ‘실제 상태 갱신’은 예측만 읽지 않고 부모 모델을 step한다는 뜻이며 actual 환경 실행을 뜻하지 않는다. short exit 하나만 반복 비교하지 않고 연속 선택의 모델 내 후속 상쇄를 확인한다. 제안 cap은32768tick/64world/CPU150초/wall240초다. 관측 rate에 따른32768tick 추정은 CPU119.5초/wall120.8초이며 보장 비용은 아니다.

모델에서 양쪽 적격 공식 finish·엄격한 시간 지배·복원/반복/부모/단계 fidelity를 확인할 때만 다음 actual **보정** 대조를 제안한다. A/B history118+suffix13 각각1회(262wrapper/reset2), planner는 첫3 decision만 사용하고 이후는 C0 guardian이다. 추가 모델 query의 제안 cap은32768tick/128world/CPU150/wall240, 실제 exclusive CPU90/wall180·400wrapper/reset2다. 이 숫자들은 **제안이며 실행·예약하지 않았다.** 새 연속 명령 조합의 실제 전이와 carry는 여전히 후속 검증 대상이고, actual13만으로 full tail의 실제 시간 순위를 승격하지 않는다.

## 이번 비용과 보존

정적 계측 CPU 합계0.244초/wall0.121초로60/120초 이내다. 기본 검사0.190/0.109초와 ledger 검사0.054/0.011초를 포함한다. 첫 worker 전체 CPU는 마지막 직렬화 전0.596초였으며 모든 프로세스 startup/import CPU를 완전히 합산한 값은 아니다. 구현 marker 이후 구간585.634초와 보조 ledger 준비 구간120.043초를 별도로 남겼다. 앞선 읽기·설계 및 전체 준비 CPU/wall·보고/git 전체는 미계측이므로 추정치로 채우지 않았다.

원장v439: 새 actual/reset/model적분/world/actor/학습/SEALED/예비/유료 자원 **전부0**, 연구29,618·예비84,000(사용0)·실제 누적1,318,446 유지다. 기존 실행 C·296·rollback240·보호 자료·408 원기록·417 판단·공식 main·기한을 보존했다. 개인 seed·지도·state·trace·RNG는 저장소 밖에 유지했다. 실제 planner 동작·long-tail 모델 신뢰도·정책 성능은 이번 정적 테스트가 검증하지 않는다.

공개 synthetic30개는 `python -m unittest retry.test_planner419.PlannerLogic retry.test_planner419_model_ledger`, 저장 사례까지는 지정 private root가 있는 workspace에서 `python -m unittest retry.test_planner419 retry.test_planner419_model_ledger`로 재현할 수 있다. 이번에는 통과 후 불필요한 반복 검사를 하지 않았다.
