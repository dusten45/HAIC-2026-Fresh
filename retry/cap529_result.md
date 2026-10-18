# 529 — primary cap80→90: 높은 최고속을 썼지만 전체 모델 finish 이득0

**528과 cap만 바꾼 직접 cold 비교의 기록된 source-style finish는 둘 다18.00초였다.**525 실제18.40초 대비도 모델0.40초로 사전0.50초 기준에 미달했다. carry/native/action/reset0, 실제 기록18.40초 유지. cap을 추가 sweep하지 않고 다음 연구는 경로 길이/곡률의 구조적 설계로 전환한다.

[소스/규칙 확인](cap529_source_check.json) · [사전 계약](cap529_contract.json) · [cap 하나 변경](cap529_control.py) · [모델 실행](cap529_model.py) · [모델 결과](cap529_model_result.json) · [저장 감사](cap529_audit.py) · [비교 집계](cap529_audit.json).

## cap80의 성격과 단 하나의90 선택

확인한 저장소 README 실행/완주/손상 규칙, CarRacing.step, Car.step, env_wrapper에는 fixed top80 주행 규칙/환경 clamp가 없었다.80은 연구 profile의 `min(80²,lateral/curvature)` 참조 상수다. 확인 범위 밖의 규정까지 일반화하지 않는다. engine/gas·마찰·조향·Box2D 적분 제약은 별개다.

설치된 pyBox2D2.3.5에서 `b2.maxTranslation=2m`, source world timestep0.02s를 확인했다. 공개 upstream [island solver](https://raw.githubusercontent.com/pybox2d/pybox2d/master/Box2D/Dynamics/b2Island.cpp)는 body의 step translation이 한계를 넘으면 velocity를 축소한다. 따라서100m/s 부근에는 body별 solver clamp가 있고 이것은 연구 top80과 다르다. upstream master와 컴파일 binary의 완전한 build 동일성을 확인한 것은 아니다.

단 하나의 후보를 **0.90×(2m/0.02s)=90m/s**로 사전 고정했다.10% reserve는 고정 선택 근거이지 보정된 안전 보장이 아니다.524 단순화 모델은 이 solver clamp를 직접 구현하지 않으므로, 실행 모델의 wheel world velocity·근사 hull velocity가100 미만인지 추가 적용 범위 검사했다. 이번 최대body89.5284m/s로 통과했다.

## 비교를 분리한 고정 요소

직접 cap 비교는 **528 primary top80 vs529 primary top90**다. 같은528 source-response governor 함수 객체, 경로/곡률, 조향, source-drive forward, backward80, corner153.38, 524 모델, 내부0.15수치여유/실제참조5, force0.19/예측1.06/물리1.25, post24 clipping10%, 고정launch를 유지했다. 공통 backup100 profile의 top80/backward45도 그대로다. cap 외의 알고리즘이나 값은 바꾸지 않았다.

실제 승격 기준은 검증된525의18.40초다.528은 모델18.00초뿐이고 **실제 검증되지 않았다**. 선행 모델이 통과하면 실제 짝은525 policy와529 package로 비교하도록 했으므로, 그 실제 차이가 cap만의 실제 효과가 된다는 주장은 계획하지 않았다. 이번에는 native 자체를 생략했다.

## 저장 고속 진입·다음 감속 반증

528 저장 모델에서 가장 긴 top80/ff0 run(64raw)4hold 전 root54를 선택해 양쪽32holds/128raw를 전파했다. 또12hold 안에 다음 negative-ff 구간이 있는 최고속 before-hold root75(79.8545m/s)를 고정해 양쪽12holds/48raw를 시험했다. 선택은529 결과 전에 했다. 각 current root/progress/이미 관측한 clip 이력을 공유했고 실제 미래 trace는 입력이 아니다.

|같은 root54의2.56초 모델|528top80|529top90|
|---|---:|---:|
|최고 post-step COM speed|79.8545m/s|89.5239m/s|
|끝 progress 차이|기준|+2.1041m|
|force peak|0.8963|0.8351|
|최소 전체 차체/바퀴 여유|3.2137m|3.4064m|
|최대 참조 초과|3.3545m/s|0.5295m/s|

진입 gate의 peak 증가>=1m/s·progress>=1m와 안전을 통과했다. 최고속 root75의 다음 감속 창도 양쪽 모두 안전했고 후보 progress는오히려−0.1907m였다. 이 창은 안전 gate만 요구했으며 국소 상승이 모든 구간 이득이라는 가정은 하지 않았다.

## 전체 cold와 승격 중단

525 SHA 동일 baseline cold/carry,528 SHA 동일 cold를 읽기 재사용했다. 새529 cold가 전체 안전/source-style finish·525 대비0.50초·HIGH>=50%를 통과할 때만 새528/529의 동일 actual518 before47 carry 비교를 하도록 등록했다. 그 carry까지 통과해야 native였다.

529 cold는901raw/226actions에서 source-style finish event **18.00초**, confirmation18.02초였다.528은event/confirmation18.00초였다. 비교 집계는 event 이후 confirmation raw를 시간 분해에서 제외했다. 같은20ms event clock에서 **측정된 cap 이득0.00초**이며 sub-tick 연속시간 효과까지0이라고 증명하지는 않는다.

최소 차체/바퀴 sampled 여유0.940554m, 최대 path1.782786m, 참조 초과3.307358m/s, running peak1.059999999<=1.06, clip18/3220, HIGH186/RESPONSE13/BACKUP3로HIGH92.08%였다. force/참조/기하/launch/projection/TimeLimit/finish 및 body<100 적용범위 gate는 통과했다. 그러나525 대비0.40<0.50초여서 carry/new528carry/native는0이다.

원 모델 JSON의 직접 이득2.95e-13초는 비교에 rounded18.00 literal을 쓴 부동소수점 표기 차이다. 정확한 cached52817.999999999999705와529동일값을 빼면0이며 감사 결과에 정정했다. 원 결과를 바꾸거나 재실행하지 않았다.528/529 어느 모델 시간도 새 실제 기록으로 말하지 않는다.

## 국소 최고속 증가가 전체 효과가 되지 않은 범위

source-style event까지의 배타적 label은 다음과 같다. 각 열이18.00초에 합산되며 구간별 인과 손실/회수 가능한 이득이 아니다.

|모델 reference 활성 label|528top80|529top90|
|---|---:|---:|
|고정launch|1.92s|1.92s|
|source-forward|8.48s|9.08s|
|backward80|3.58s|3.92s|
|top cap|1.58s|0.74s|
|곡률/전이|2.44s|2.34s|

529는80m/s 이상1.20초·85이상0.86초를 실제 모델 궤적에서 썼고, full gas도0.56초로528의0초보다 늘었다. cap이 전혀 사용되지 않은 반증은 아니다. 그러나 source-forward 구간은 여전히9.08초를 차지했고 새로운 속도까지 가속하고 다시 제동하는 시간도 늘었다.12개 동일arc bin에서는−0.0726초인 구간과+0.0764초인 인접 구간 등 이동이 서로 상쇄됐다. 이 분포만으로 모든 상쇄를 한 물리 원인으로 단정하지 않는다.

현재 고정 경로/528 알고리즘/80→90 한 후보에서는 더 높은 최고속이 전체 모델 시간을 줄이지 못했다. 다른 cap·제어기·트랙에서도 동일하다고 주장하지 않으며, source-forward가 물리적으로 불가피한 최소시간이라고 주장하지도 않는다. 반복 cap/제동량 sweep 대신 다음은 **Gaussian 참조 경로의 길이와 곡률을 직접 설계 변수로 다루는 한 구조적 가설**을 고정하는 방향이다. 기존521의 제한된 local spline 결과를 모든 경로 설계의 기각으로 사용하지 않는다. 참조995m/평균속도 산술이나 scalar clock을 실제 완주의 엄밀한 하한으로 사용하지 않았다. 이번에 새 경로 후보는 실행하지 않았다.

## 비용·보존

새 모델 **24456ticks** = 공유-root실행352 +cold901 +forecast23203. 적분 내 wheel force97824회, 별도 explicit force98968회.525 baseline cache body1668/planning18915,528cold cache body900/planning18276은 새 적분이 아니다. 소스 확인·저장 감사 적분/force0.

worker CPU39.304352+0.284958=**39.589309초**, wall39.451576초. 준비/소스 확인/publication allowance3CPU/3wall는 별도다. 초기 등록 script import 경로 수정과 감사 syntax 수정은 모델/force0의 준비 오류였고 과학 모델 재실행은 없다. native/action/reset/world0, 연구 **24155**·예비 **84000/used0** 유지. source/input SHA와528 comparison profile/알고리즘 동일성을 확인했다.

동일 지정 cloud/기존DEV/단일 작업, HOLDOUT/SEALED·새 seed·보호 평가·별도 유료 자원0. raw state/지도/pedal trials/명령/RNG/case는private, 코드/집계만 공개. 원결과·525실제기록·main·Participants·사용자 변경·백업 보존. 승인 종료 **2026-10-20 19:01:55 KST**다.
