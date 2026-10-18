# 508 — 8hold 곡선 corridor의 국소 제어 gate 통과

정확한 지도와 현재 body/wheel 상태를 주는 진단 조건에서 geometry 후보를 더 길게 검증했다. 반경40m·반폭4.5m의 같은 곡선을 uniform 마찰1.0과 혼합 material0.35/1.0의 두 조건으로 만들었다. source grass multiplier도0.35로 고정했다. 이 **새 합성 물성 조건**은 실제 트랙 기본 물성이나 이전 강제 접촉 사건의 결과로 이전하지 않는다. static sensor polygon만으로 접촉이 바뀌며 수동 `tiles` 변경은 없다.

각 조건에서504 접촉 고정과 geometry 후보를 같은 초기 상태·목표·조향으로8hold(0.64s)씩 비교했다. 매 hold 실제 현재 상태를 재관측해 제동을 선택하며, 조향은 동일한 `atan(3.24/40)` feedforward다. 목표는 같은 initial speed에서 매hold0.8m/s씩 낮춘다. 위치 오차에 따른 조향 feedback이나 gas 가속은 추가하지 않았다.

| 혼합 material 조건 |504|geometry|
|---|---:|---:|
|목표 속도 RMSE|0.013712m/s|0.003286m/s|
|최대 목표/폐루프 속도 예측 오차|0.028987m/s|0.005932m/s|
|닫힌4tick 예측의 최대 위치 오차|0.018203m|0.001295m|
|현재 상태 보정 없는 열린 예측의 최대 위치 오차|0.221445m|0.010565m|
|닫힌 effective-friction 불일치|24/128wheel-ticks|0/128|
|열린 effective-friction 불일치|40/128|0/128|
|최소 sampled hull/wheel 경계 여유|1.757472m|1.758400m|

열린 예측은 처음 root에서 시작하고 이후에는 **실제로 선택한 명령만** 받는 model shadow다. 실제 현재/미래 상태·접촉으로 다시 맞추지 않는다. 독립적인 열린 제어기의 주행 결과는 아니다. geometry의 최대 열린 속도 오차0.003749m/s가 닫힌 예측0.005932보다 작기도 했으므로, 재관측이 모든 지표를 단조 개선한다고 하지 않는다. 위치에는 열린 누적 drift가 더 컸다.

uniform에서는 두 제어기의 명령·주행·제동 work가 같았다: 최대 목표 오차0.002206m/s, 닫힌 위치 오차0.000177m, 열린 위치 오차0.015378m, 최소 여유2.009852m다. 혼합 조건에서 실제 마찰 전환16wheel-events와 한계 힘에 도달한33wheel-ticks를 각 arm에서 관측해 material이 이름만 바뀐 시험이 아님을 확인했다.

geometry의 혼합 조건 총 arc 진행은36.745529m로504보다0.000366m 적었다. 전체 기계식 brake work는10063.75J(504:10085.14J), 최대 불필요 감속0.005932m/s다. 큰 whole-lap 개선을 보인 결과가 아니다. norm 속도와 곡선 tangent 진행속도도 분리해 저장했으며, 그 차이는 혼합 조건에서 최대0.055293m/s였다.

## 기준·재현·비용

[사전 계약](brake508_contract.json): geometry의 sampled 전체 hull/wheel 경계 여유>=0.25m, 모든 end-target 및 닫힌 속도 예측 절대 오차<=0.15m/s, 닫힌 마찰 불일치0, source prepose oracle 불일치0, 불필요 감속<=0.2m/s, 조건별 최종 arc 진행 손실<=504의0.5%를 고정했다. 전체32holds가 완성됐고 모든 gate를 통과했다. sensor membership actual-pose oracle은 양쪽 arm 전체에서0불일치였고, 같은 틱 source 힘 재계산 최대 차이는0.000199N·omega0.00000117rad/s였다.

[조건/동등한 AABB 가속](brake508_corridor.py) · [실행](brake508_diagnostic.py) · [집계](brake508_result.json) · [요약](brake508_summary.json). 불필요한 polygon distance 계산만 건너뛰며506 알고리즘을 바꾸지 않았다. 순수3tests에서 full polygon search와60footprints 대조, forecast bit 동일성, **전체 분기 예약식 `2cases×2arms×8holds×4ticks=128` 및4world/4zero-primes**를 검사했다. 실패 분석 분기도 저장 자료만 읽도록 고정해 추가world/tick0을 예약했다. 이번에는 통과해 물리 반증·재실행을 추가하지 않았다.

실제4world/128positive ticks/4zero-dt contact primes, 모두 body/joint0으로 종료했다. CPU2.242702s/wall2.246736s(테스트 child 포함), 상한90/120s 이내다. 완료한 모든 tick·hold·world 종료를 즉시 저장했다. private166파일/1,155,193B로16MiB/256file 상한 이내. 후보/조건/판정 변경·기술 재실행0이다. native wrapper action/reset/track seed/HOLDOUT/SEALED 접근0, 연구26027·예비84000/used0 유지. 측정 raw는 같은 지정 cloud private 로컬에만 보존한다.

경계 여유는 실제 hull/wheel polygon과 corridor의 inner/outer/end 경계 거리다.20ms sample 사이의 연속 swept 안전, 장애물, 실제 트랙 finish 또는 독립 일반화는 검증하지 않았다. 현재 상태·완벽한 full road map·효과 계수는 진단 privilege이며 pixel 제출 정책으로 승격하지 않는다.

## 실제 트랙 연결에 필요한 최소 다음 검증 — 제안만

먼저 wrapper adapter의 입력 단위와 효과를 순수 검사한다: 현재 wheel omega/COM·body frame, 실제 grass/grip에 따른 road effective-friction 정규화, engine/steering multipliers,4rawtick sensor phase, float32 명령과 nominal memory1회 보존이다. 이번 두 fixture의grip=1만으로 damage/grip 변화까지 인증하지 않는다. 가속 요청은 기존 동결 참조 제어기가 유지하고 제동 요청만 교체해야 한다.

그 다음 별도 사전 등록한 DEV 한 조건에서 실제 wrapper를 두 arm으로 짧게 비교하는 것이 최소 bridge다. 예를 들어 각32actions·총64actions/2resets를 상한으로 두면 완전 차감 시 연구25963·예비84000/used0이다. seed/동결 참조와 초기 identity, reset/raw 비용·중단 기준을 실행 전에 고정해야 하며 이번에는 해당 조회·실행을 하지 않았다. 이 단계도 우선 정확한 map/state 진단으로 표시하고, 참가자 관측만으로 그 입력을 얻는 추정/성능 gate를 별도로 통과해야 실제 제출 제어기 성능을 주장할 수 있다.
