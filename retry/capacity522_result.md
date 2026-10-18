# 522 — source 횡력70% 후보: 모델 통과, 실제 바퀴별 힘 안전 실패

**153.384316 후보는 실제41번째 hold의 힘 안전 실패로 중단했다.** baseline은 source 공식20.46초로 완주했으나 후보는 완주하지 않아 실제 시간 개선을 주장하지 않는다. 모델18.22초를 실제 기록으로 사용하지 않는다. 기준 완화·재시도·추가 native0이다.

[사전 계약](capacity522_contract.json) · [단위 검사](capacity522_units.py) · [단위 결과](capacity522_units.json) · [후보](capacity522_control.py) · [순수 검사](test_capacity522.py) · [모델](capacity522_model.py) · [모델 결과](capacity522_model_result.json) · [실제 실행](capacity522_native.py) · [실제 결과](capacity522_native_result.json) · [사후 검증](capacity522_verify.py) · [검증 결과](capacity522_verification.json).

## 질량과 힘 단위

source fixture 면적×density에서 hull7.06kg, wheel 각0.06048kg, body 합7.30192000kg을 얻었다. 저장된 실제 assembly COM 질량7.301919966936kg과 차이는3.31e-8kg로 부동소수점 수준이다.

519·520 steady convention의29.249793766662kg은 `7.301919966936 + 4×1.6/0.54²`와 정확히 같다. 1.6kg·m²는 source가 별도로 둔 wheel omega spin 관성이며, wheel body의 평면 yaw 관성0.0074592kg·m²와 다르다. 직선 이상 구름에서는 회전 운동에너지를 포함해 종방향 유효 질량을 만들 수 있다. 따라서7.30과29.25의 차이를 기존 코드 버그라고 해석하지 않았다. 이 convention은 gas ramp·finite slip·조향·yaw에서 exact 전달함수가 아니다.

source의 실제 COM 운동은 tyre 외력 합/실제 assembly 질량이다. wheel_response의 `82×속도 slip`은 source force이고 이를kg으로 나누면 source 일관 단위m/s²가 된다. 종방향 구름 등가질량을 모든 방향에 등방적으로 적용하면 안 된다. 정렬된 바퀴의 lateral1m/s/forward60m/s 순수 source fixture에서 종방향 slip/spin 변화0, 횡력 합−328N을 확인했다. COM 가속은−44.9197m/s²이며29.25로 나눈−11.2138m/s²가 아니다. 적분/world 없이 force4회다.

따라서 후보를 고르는 산식에는 actual mass를 사용해 `0.70×(4×400N)/7.301919966936kg = 153.384316052693m/s²`로 고정했다. **합계 마찰력/질량은 외력 크기의 느슨한 상한이며 실제 횡가속 실현 가능성 증명이 아니다.** 선회 중 rolling/steering/yaw/복합 slip과 바퀴별 힘 배분은 별도 제약이다.70%는 임의의 고정 여유로 명시했으며 보정값·최적값으로 주장하지 않는다.

## 한 후보와 선행 모델

519의 Gaussian 경로/곡률/arc/장애물 우회, source-drive forward, backward45, top80, steady gas, gain2, 조향과 첫24hold gas0.32를 유지했다. corner lateral budget100→153.384316만 바꿨다.521 spline·520 gas inverse·sweep은 넣지 않았다. 순수1test가 geometry 불변·새 corner cap·closed forward/backward 제약·끝점 nonzero를 검사했다.

cold baseline519의1020ticks를 SHA 확인 후 재사용했다. 새 cold 후보가 안전 완주 및0.50초 개선을 통과할 때만, 사전 지정한 실제518 action47 직전의 **같은 root와 visited ledger**에서 baseline/candidate를 각각 시험했다. 그 carry 비교도 안전 완주 및0.50초 개선을 요구했다. model은 source-styleFinishLineTracker 기반 추정이며 실제 finish가 아니다.

|모델|baseline|153.38 후보|개선|
|---|---:|---:|---:|
|cold 완주 추정|20.38s|18.22s|2.16s|
|같은 actual carry 완주 추정|20.46s|18.54s|1.92s|

후보 cold/carry 최소 차체·바퀴 sampled 여유0.877464/0.916438m, 최대 path error1.405922/1.418871m, tracking 참조 초과2.822844/2.612453m/s였다. running raw 복합 힘 peak1.184540/1.166200, clipped23/3264와8/2976samples, 모두 사전 gate 이하였다. 각 raw에서 margin0.50m/path3m/overspeed5m/s, running peak1.25/clipping10%, phase별 launch 조건과 projection/TimeLimit/source-style finish를 검사했다. 세 새 모델2496ticks로 통과해 조건부 실제 짝 비교를 실행했다.

## 실제 결과와 가장 먼저 깨진 가정

두 reset의 DEV full identity와 첫24action/observation prefix가 일치했다. baseline은256actions로 공식 **20.46초**, confirmation20.48초에 완주했다.283/283 방문, margin0.974467m, path1.184474m, tracking 초과2.209972m/s, running force peak0.944660/clipping0으로 실제 gate를 통과했다. 이전20.70초와 다른519 source-drive baseline의 첫 실제 검증이며 이번 paired 후보의 성공을 뜻하지 않는다.

후보는41actions, reset 후3.24초의 hold41/raw2에서 front wheel1의 source raw 복합 힘 비율 **1.26364959>1.25**가 최초 안전 위반이었다. 이미 발행된 wrapper hold의 나머지2raw를 마친 뒤 중단했고 추가 wrapper call0이다. 후보는40/283 방문으로 미완주이며 finish 시간/이득은null이다. running clipping9/272=3.31%<10%, margin3.961155m/path1.242985m/참조 초과0은 각 기준을 만족했다. 해당 실패를 다른 안전 조건까지 통과한 전체 lap으로 해석하지 않는다.

첫 실패 바퀴의 raw 종력−76.43N/횡력−499.65N, 복합 크기505.46N이었다.400N 한계를 초과해 source가 clip했다. 이때 전체 postclip COM 외력 크기/질량은151.49m/s²로 global budget153.38보다 작았다. **global70% 용량이 바퀴별 힘 집중을 제한하지 못했다**는 직접적인 반례다.

동일 hold/raw의 cold 모델은 해당 바퀴 raw 비율1.168187을 예측했다. 실제1.263650과의 차이는, candidate cold 전체 peak1.184540이 native gate 통과를 보장하지 못했음을 보여 준다. 한-hold 예측 오차는 후보 전체에서 position0.006954m/speed0.028518m/s/angle0.001447rad/yaw0.027404rad/s로 허용0.10/0.15/0.02/0.05 이하였다. 작은 kinematic 오차만으로 force peak 안전성을 인증할 수 없다. 두 closed-loop 상태가 달라 단일 yaw/joint/solver 결함이나 단일 원인의 인과 증명으로 단정하지 않는다.

모든 source force oracle 최대오차0.000216N, COM impulse residual 최대2.03e-5m/s로 source 단위·힘 적용 오류의 증거는 없다. actual own-state 명령297개와 연속 사전차감297개를 저장자료로 재검증했다. 유일 실패 class는 위 force peak다. 자세한 바퀴 상태·지도·명령은 private에 보존했고 [사후 분석 계약](capacity522_failure_contract.json)의 force8회/적분0으로 종료했다.

## 판단·다음 연구·비용

이번153.38 패키지는 중단한다.70% 또는1.25기준을 사후 수정해 재시도하지 않는다. 모델의2초대 이득은 가설을 탐색할 근거였지만 실제 안전 완주 증거가 아니다. 다음 연구 대상은 global scalar budget을 바퀴별 복합 힘/선회 이력 제약으로 대체하는 corner reference다. 저장된 실패 상태에서 모델의 바퀴별 힘 예측 민감도를 먼저 확인하고, 큰 시간 이득을 유지할 별도 후보를 사전 고정해야 한다. 이 보고서에서 추가 후보를 실행하지 않았다.

unit4force, 새 preflight2496ticks, native 한-hold forecast1188ticks, 합계 새 모델3684ticks. 적분 내 wheel force14736회와 별도 explicit force oracle14736회는 별도 평가다. unit4+사후진단8은 추가12회다. 실제297actions/2resets/1290raw = reset102 + action1188, 두 world 모두 종료했다. 연구 **24938→24641**, 예비 **84000/used0**이다. 정해진1000actions/2resets/4102raw 이내이고 미사용 action은 차감하지 않았다.

measured worker CPU: unit0.009111 + model34.359454 + native33.284633 + verify0.492342 =68.145541초, wall68.137730초. 준비/publication allowance3CPU/3wall는 측정값과 별도다. source/input/admission SHA를 검증했고 원래 모델·실제 결과를 보존했다. 같은 지정 cloud/DEV, HOLDOUT/SEALED·새 seed·보호 평가·별도 유료 자원·이전 연구 실행0. main·Participants·사용자 변경·백업을 보존한다. 승인 종료는 **2026-10-20 19:01:55 KST**다.
