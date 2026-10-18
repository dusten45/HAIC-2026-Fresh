# 530 — 전 지점 경로 설계: 기하 선별 실패, 물리 실험 미진행

**단 하나의 283지점 racing-line 설계 절차를 사전 고정해 실행했고, 기하·수치·scalar 선별에서 탈락했다.** 조건을 바꾸거나 다른 초기화/방법/가중치를 시도하지 않았다. 위험구간 전파·cold/carry·native/action/reset/world는 모두0이다. 검증된 실제 기록18.40초, 연구24155·예비84000/used0 유지.

[사전 계약](line530_contract.json) · [저장 분석](line530_analysis.json) · [경로/profile 구현](line530_control.py) · [단일 설계 코드](line530_design.py) · [설계 결과](line530_design.json) · [실패 감사](line530_audit.json).

## 저장 지도·528 궤적에서 확인한 가설 범위

새 지도/seed/보호 평가 없이 같은DEV의 저장 지도와528 cold 궤적을 읽었다. 중심선994.000000m, Gaussian 경로995.445289m로 차이는 **1.445289m**였다. 따라서 Gaussian 우회 길이만 크게 줄여 대폭 개선할 근거는 작다. 다만 경로의 절대 굽음14.735773rad 중4.494186rad(30.5%)가 장애물20m 이내에 있고, 곡률 제곱 적분0.924386/m와 최대곡률0.103753/m가 있어 코너 진입/탈출·장애물 우회의 곡률 배치를 함께 바꾸는 가설을 선택했다. 이 근접성은 장애물이 모든 굽음을 유발했다는 인과 증거가 아니다.

저장528의 최대 추종오차1.702909m, 실제 모형 차체/바퀴 최소 여유0.934400m였다. 도로 중심선에서 가장 가까운 저장 경계까지6.586744~6.666667m였다. nominal 전체 footprint는 COM 기준 횡±1.380001m, 종−2.319541~+2.680459m였고, 조향 바퀴를 포함하도록 설계용 외곽 직사각형을 횡±1.58m·후2.320m·전2.681m로 보수적으로 고정했다. 이는 nominal 설계 외곽이며 모든 동적 joint 오차를 덮는 증명은 아니다. 실제 물리 gate는 기존 전체 hull/wheels 기준을 별도로 유지하도록 했다.

## 하나로 고정한 설계 절차

521의16계수 local coordinate 탐색을 반복하지 않았다. 현재283개 track station의 횡변위를 **동시에** 다루는 SLSQP 단일 run을 선택했다. seam 양쪽20m의 원래 지점10개를 고정하고, 나머지273개 변수를 Gaussian 초기값에서 시작해±4m 안에서 조정했다. 변수 범위 밖 값만 초기 clip하며 실제 초기값은 범위 안이었다. side/homotopy 열거·multi-start·방법/가중치 sweep는 없다. 비선형 solver가 장애물 통과 측면을 전환하지 않았는지의 별도 topology 증명은 없으며, 새 측면을 찾는 절차도 아니다.

목적함수는 기존528과 동일한 top80/corner153.384316/backward80/source-drive-forward 법칙으로 재생성한 launch scalar clock `sum(2*ds/(v_i+v_next))` 하나다. 임의의 곡률 가중치를 추가하지 않았다. 거리는ds, 곡률은같은속도상한/profile을 통해 목적에 함께 들어간다. backup도 바뀐 **동일한 경로**에 기존100/top80/back45 법칙을 적용한다. 공유528 `choose/forecast` 함수 객체, source-response governor·조향 알고리즘·pedal mapping은 그대로다. baseline 경로를 재생성한 profile 최대 수치 차이는1.82e-12였고 함수 객체 동일성을 확인했다.

SLSQP는 전 구간을 동시에 조정하지만 **전역 최적해 보장은 없다.** [SciPy SLSQP 문서](https://docs.scipy.org/doc/scipy/reference/optimize.minimize-slsqp.html)의 bounds/inequality·ftol/maxiter 기능을 사용했다. [곡률 기반 racing-line 연구](https://arxiv.org/abs/2309.09186)는 경로 형상 자체를 설계하는 접근의 근거로 참고했으나 해당 논문의 spline 알고리즘을 구현·재현한 것은 아니다.

사전 수치예산은 maxiter120,ftol1e-7,finite-difference eps1e-5,objective40000/constraint41000회, 단일 BLAS thread, CPU180초/wall240초였다. Numpy1.26.0은 기존 환경 버전으로 보존했고 SciPy1.14.1을 설치했다. 최초 설치가 의존성에 따라 Numpy2.4.6으로 바꿔 이를 **설계 시작 전에** 원래 버전으로 복구했다. 읽기 전용 분석/설계/물리 어느 것도 바뀐 Numpy 버전에서 실행하지 않았다. uv 기본 cache의 쓰기 제한도 /tmp cache로 복구했으며 별도 유료 자원은 쓰지 않았다.

각 node와 segment midpoint566개에서 외곽 직사각형의 도로-normal support와 모든6개 원형 장애물 거리를 검사했다. nominal 목표여유1.25m, 곡률≤tan(.4)/3.24,segment≥2m를 제약으로 고정했다. 도로-normal 근사는 정확한 도로 union/곡선 경계의 대체 증명이 아니므로, 최종 polygon 경로를0.5m 이하 간격으로 나눠 저장 도로 union·경계·장애물에 대한 외곽 직사각형의 여유를 별도 계산했다. **solver success+제약위반≤1e-6+촘촘한 footprint 여유≥0.75m+scalar clock 개선≥0.50초**가 다음 단계의 선행 gate였다. scalar clock은 후보 선별값이며 실현 가능한 하한이나 실제 gain이 아니다.

## 한 번의 종료 결과와 반증

|집계|기존528 Gaussian|530 종료 후보|
|---|---:|---:|
|scalar clock|17.250273s|17.877554s|
|경로 길이|995.445289m|997.095268m|
|곡률 제곱 적분|0.924386/m|1.118594/m|
|최대 절대 곡률|0.103753/m|0.121359/m|
|0.5m 이하 간격의 외곽 최소 여유|0.946887m|0.500722m|

SLSQP는6회 반복·objective1648/constraint1656회 후 `Inequality constraints incompatible`로 종료했다. 이는 **solver 종료 메시지이지 feasible 경로가 존재하지 않는다는 증명은 아니다.** 종료 후보는 도로 근사 제약6개에서 최대0.045185m, 장애물 제약6개에서 최대0.032057m 위반했다. scalar clock도0.627281초 나빠졌고, 최종 footprint 여유가0.75m gate에 미달했다. 서로 독립적인 여러 선별 조건을 통과하지 못했다.

읽기 전용 감사에서 초기 Gaussian은 도로/곡률/segment 제약을 만족했지만 새로 정한1.25m 장애물 nominal allowance에는24sample에서 최대0.231097m 미달했다. 반면 촘촘한 기존 footprint 여유0.946887m는 최종0.75m geometry screen을 통과했다. 따라서 초기화를 **새 설계 제약의 feasible start**라고 부를 수 없다. 불가능한 도로라는 결론, 기존528의 안전 gate 실패라는 결론, 추종·마찰이530 실패를 유발했다는 결론을 내리지 않는다. 보수적인 설계 제약과 비평활 scalar profile을 직접 다루는 단일 SLSQP 초기화/복구 절차가 이번 입력에서 성공하지 못했다는 범위로 한정한다.

후보를 바꿔 재시도하거나 allowance를 낮추지 않았다. 별도의 위험구간은 후보 결과 전에 저장528에서 **장애물 point-clearance 최솟값35m 전, 최대 Gaussian 곡률35m 전** 두 root로 선정하고 각24hold/96raw, 동일 root/clip-history의528/530 짝을 계획했다. 하지만 geometry 선행 gate가 실패하여 위험구간 전파 자체를 하지 않았다. 준비된 [조건부 모델 코드](line530_model.py)는 실행·동역학 검증하지 않았다.

## 승격·관측 경계와 다음 조치

계약은 위험구간 모두 안전한 경우에만 cold를, cold의 전체 force/추종/geometry/source-style finish 및525실제18.40 대비모델≥0.50초·528모델대비≥0.10초/HIGH≥50%를 통과한 경우에만 동일actual518 before47 carry를 허용했다. carry도525대비≥0.50초·528 carry 대비비악화·전 안전을 통과해야 native였다. native는 검증된525 policy와530 package의 동일DEV source official finish 짝이며,528과의 path-only 모델 차이와 구분한다.

기존 force 불확실성0.19/예측1.06/물리1.25,참조초과5(528 내부4.85),누적tracking clipping10%,launch24gas.32/peak2.5/clip15%,model여유0.5/native0.25m,path3m,관측/손상/force oracle/one-hold prediction/sourceTimeLimit 경계를 유지했다. native 상한1000actions/2resets/4102raw/2world, precharge 및 finally world body/joint0 정리도 사전 계약했다. **이번에는 어떠한 world도 만들지 않았다.** DEV는 기존 저장 입력만 사용했으며 HOLDOUT/SEALED·새 seed·보호 평가 호출0이다.

다음에 경로 가설을 별도로 승인·고정한다면 우선 검토할 장애물은 **feasible corridor 초기화와 외곽 직사각형 기하 근사의 불일치**다. 이것을 고치면 기록이 좋아진다고 예단하지 않는다. 이번 결과를 보고 같은 과제 안에서 solver/가중치/초기화 sweep나 새 경로 후보를 실행하지 않았다. 경로 설계군 전체를 기각하지 않는다.

## 비용·재현·보존

저장 분석 CPU0.228139초/wall0.228139초, 설계 CPU14.084150초/wall14.086568초, 읽기 전용 감사 CPU2.407840초/wall2.407972초, 합계 **CPU16.720129초/wall16.722679초**였다. 준비·소스 확인·설치·간단한 수치 동일성 검사·publication은 별도로 CPU5초/wall30초 allowance이며 실측 worker 비용과 혼합하지 않았다. 새 모델 적분/force/native actions/resets/world0, 연구24155·예비84000/used0 유지.

`DESIGN_STARTED`와 원 종료 후보/반복 이력을 비공개 보존했으며 단일 run이다. 소스·private input SHA 및 기존528 baseline/profile/controller 동일성을 감사했다. 공개물은 코드/계약/집계뿐이며 지도·좌표·횡변위·root·원시 궤적·seed/RNG/case는 비공개다. main 지정SHA·Participants·기존 사용자 변경·원결과·백업은 보존한다. 승인 종료는2026-10-20 19:01:55KST이며 자동 연장하지 않는다.
