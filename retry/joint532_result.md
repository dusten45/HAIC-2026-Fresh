# 532 — 명시적 경로·속도 공동 설계: scalar 개선1.041초, 수렴 gate 미완료로 물리 실행 보류

**기존528 profile 재생성 scalar는17.250273→16.209396초로1.040877초 개선됐고, 독립 외곽 여유1.253229m를 만족했다. 그러나 사전 수렴 gate를 통과하지 못해 위험구간/cold/carry/native를 실행하지 않았다.** 이 값은 실제 주행 개선이나 물리 모델 finish가 아니다. 검증된 실제 기록18.40초, 연구24155·예비84000/used0 유지.

[사전 계약](joint532_contract.json) · [초기 feasibility/미분 확인](joint532_initial_verification.json) · [공동 문제](joint532_problem.py) · [단일 solver](joint532_design.py) · [설계 결과](joint532_design.json) · [잔차/profile 감사](joint532_audit.json).

## 초기화와 실제 시간 목적

531 성능 끝점이 아니라 비공개 `design-history`의 **검증된 feasibility 복구 endpoint 하나**를 사용했다. 같은528 generator에서 periodic q와 launch w를 구성했으며 초기 시간17.372708초·최대 정규화 위반3.09e-11·외곽 여유1.252m였다. 기존 Gaussian이 직접 비교 baseline이며 scalar17.250273초다.

변수는 횡변위273개(기존283station,10개seam 지점 고정),periodic 속도제곱283개,launch 속도제곱283개로839개다. q와w는6400으로,횡변위는4m로 정규화했다. launch w0=0은 고정하며 periodic q는닫힌 seam을 가진다. 목적은 **`sum(2*ds/(sqrt(w_i)+sqrt(w_next)))`**이며 초기 시간으로만 정규화한다. 임의 smooth 곡률 목적이나 source-forward/backward profile의 min/max 미분을 사용하지 않았다.

각 station에서 top80 및 `q*curvature<=153.384316`, `-q*curvature<=153.384316`을 명시했다. 종방향은 다음을 periodic q와launch w 모두에 적용했다.

- `next<=current+2*REAR*ds`와 `next<=current+2*(80000/(MASS*(sqrt(current)+2.7)))*ds`를 동시에 적용해 기존source-forward min 두 branch를 정확히 표현했다.
- `current<=next+160*ds`로 backward80을 유지했다.
- launch w_next≤periodic q_next,첫 launch w0=0,마지막 w_N≤periodic q0로 출발과 seam의 관계를 유지했다.

따라서 종방향 제약을 생략한531 surrogate를 반복한 것이 아니다. 수치 trial이 속도제곱 양수 domain을 벗어날 때만 sqrt floor를 사용하며 최종 bounds/제약 충족은 별도 요구한다. 해당 trial 확장을 controller나 물리 한계 변경으로 쓰지 않는다.

기하는531과 같은 외곽 직사각형·33sample/segment·저장 road union/경계/원형 장애물 거리,nominal1.25m/계산1.252m,횡변위±4m,최소segment2m,조향곡률 한계를 유지했다. 표본 검사이며 연속시간/동적 차체 안전 보장은 아니다. 독립적인 기존530 all-boundary oracle도 요구했다.

## 단일 수치 절차와 사전 중단 기준

[SciPy1.14.1 trust-constr](https://docs.scipy.org/doc/scipy-1.14.1/reference/optimize.minimize-trustconstr.html)의 sparse Jacobian/AugmentedSystem과BFGS objective/constraint Hessian을 한 번 사용했다. 시간 목적과 속도 제약은 analytic derivative,기하와 경로 곡률은 physical1e-5m local finite difference다. 사전 고정9개 column 검사에서 목적 gradient 최대 오차9.61e-10,Jacobian3.41e-8로 확인했다.

maxiter160,gtol1e-5,xtol1e-8,barrier_tol1e-8,초기barrier parameter/tolerance1e-5,objective/constraint4000회,geometry Jacobian170회,geometry sample3000만,solver CPU600초/wall720초·후처리30/40초로 고정했다. NumPy1.26.0/SciPy1.14.1/BLAS1thread다. method/weight/multistart/초기화 sweep나 budget 자동 증액은 없다.

**status1/optimizer success/최적성≤1e-5/최대 정규화 제약·bounds 위반≤1e-6**를 수렴 gate로 고정했다. 이 gate에 더해 nominal 기하≥1.25m·530 dense screen≥0.75m·기존528 재생성 scalar 개선≥0.50초가 필요했다. 수치 budget 종료 시에는 사전에 정한 마지막 accepted callback endpoint를 보존하고 승격하지 않도록 했다. 각 반복의 시간·잔차·최적성·비용 및 마지막 x를 비공개 기록했다.

## 종료 결과와 profile 일치/보수성

108회 accepted callback 이후 **171번째 geometry Jacobian 요청이170회 완료 상한 때문에 계산 전에 거절**됐다. 반복당 Jacobian 요청이1회보다 많아 반복/CPU 상한보다 먼저 소진됐다. 원 예외는 `RuntimeError:GEOMETRY_JACOBIAN_CAP`로 보존했다. 이 예산 설계가 수렴 확인을 제한했으며 수렴 성공으로 보고하지 않는다. 마지막 accepted 최적성 norm2.5612434e-4는 기준1e-5의약25.6배였고,primal 위반은0이었다. 수치 비용 상한이나 수렴 기준을 결과 후에 바꿔 재개하지 않았다.

|마지막 accepted endpoint|집계|
|---|---:|
|경로 길이|993.159346m|
|최대 절대 곡률|0.0903752/m|
|33sample 외곽 최소 여유|1.253229m|
|독립530 oracle 최소 여유|1.253229m|
|최대 sample 간격 / road union 밖|0.218750m / 0|
|설계 속도해의 clock|17.023256s|
|동일 경로의 기존528 재생성 profile clock|16.209396s|
|원래528 Gaussian scalar 대비 재생성 개선|1.040877s|

설계q/w와 기존 generator의 profile을 모두 비교했다. periodic/launch 설계 speed가 재생성 speed를 초과한 최대값은각각0m/s였다. 즉 사전0.001m/s 허용 범위에서 **설계 속도해는 보수적**이었다. 설계 clock이 재생성보다0.813860초 느린 것은 미수렴한 설계 speed 변수의 여유를 보여준다. 기존 profile 재생성 오차0,명시source-forward/backward80의 acceleration 초과0을 읽기 감사했다. 이 관계는 물리적 실현 가능성이나 전역 최적성 증명이 아니다.

최종 성능값은 설계q의 clock으로 바꾸지 않고 재생성528 profile만 사용했다. 설계 speed는deploy하지 않으며 공유528 controller/steering/source-response/top80/back80/corner153/source-drive forward·공통backup100/top80/back45 법칙은 그대로다. 바뀐 경로의 동일 법칙 재생성만 허용했다. native가 있었다면525 실제 policy와532 package 짝이며528과의 경로-only 모델 차이와 다르다.

## 왜 물리 반증을 하지 않았는가

기하·scalar screen은 통과했지만 **수렴 gate는 미완료**다. 따라서 사전 지정한530/531의 같은 두 위험 root(장애물/최대 Gaussian 곡률 진입,각24hold/96raw 짝)부터 물리 전파0이다. cold/carry/native도0이다. [조건부 모델 코드](joint532_model.py)는 실행·동역학 검증하지 않았다. 이 후보를 실패한 주행이나 무효한 경로라고 부르지 않으며,유망하지만 미승격인 마지막 endpoint로 보존한다.

후속 gate는 위험구간 전 안전→cold 전체 force/추종/기하/source-style finish와525실제18.40 대비모델≥0.50초·528모델대비≥0.10초/HIGH≥50%→동일actual518 before47 carry의 전 안전/finish·525carry대비≥0.50초·528carry 비악화→조건부 sameDEV fresh525 vs532 실제 official finish 한 짝이다. 어느 모델/설계 clock도 실제18.40초를 덮지 않는다.

기존0.19불확실성/예측1.06/물리1.25,참조초과5(내부4.85),누적tracking clipping10%,geometry/launch/one-hold prediction/source-force oracle/COM impulse/관측·손상/sourceTimeLimit gate는 유지했다. native1000actions/2resets/4102raw/2world,실제 wrapper attempt 사전 차감·finally body/joint0 정리를 계약했다. 이번에는 world 생성0이다. 기존DEV만 사용했고 새seed·HOLDOUT/SEALED·보호 평가 호출0이다.

남은 조치는 동일 문제의 수치 수렴 미완료와 Jacobian 예산 소진을 해석하는 것이다. **이번 실행을 budget 증액으로 이어서 돌리거나 gate를 예외 처리하지 않았다.** 경로 개선 자체가 불가능하다거나 scalar1.041초가 실제로 회수된다는 결론 모두 내리지 않는다.

## 비용·재현·보존

초기 확인CPU2.074703초/wall2.074881초,단일 설계(후처리 포함)97.766933/97.849859초,읽기 감사0.177167/0.177234초로worker 합계 **CPU100.018804초/wall100.101974초**다. solver 부분은95.331717/95.413423초였다. geometry sample4,688,046회,완료Jacobian170회·차단요청1회다. objective172/gradient171/constraint172/Jacobian요청171 카운트는 최종 읽기 계산과 차단 요청을 포함한다. 준비·초기 단순 읽기·publication allowance5CPU/5wall는 별도다.

새 물리 적분/force/native/action/reset/world0,연구24155·예비84000/used0 유지. source/input SHA·공유controller 동일성·재생성profile·단일DESIGN_STARTED와 원오류/accepted 이력을 보존했다. 공개물은 코드/계약/집계뿐이며 지도·좌표·횡변위·speed해·root·raw 궤적·seed/RNG/case는 비공개다.530/531 원실패·끝점·main 지정SHA·Participants·사용자 변경·기존 백업을 보존한다. 승인 종료2026-10-20 19:01:55KST이며 자동 연장하지 않는다.
