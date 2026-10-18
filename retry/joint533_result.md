# 533 — 승인된 유한 수렴 계속:320회 후 gtol 미달, 마지막 경로 보존

**533은 추가320회 반복을 사용했지만 최적성2.497677e-5가 고정기준1e-5에 도달하지 못했다. 자동 증액 없이 중단했으며 위험구간/cold/carry/native는 실행하지 않았다.** 종료 경로는 기하/기존profile scalar 선별을 통과했지만 수렴 gate가 미완료다. scalar14.407176초를 실제 gain이나 물리 모델 finish로 보고하지 않는다. 실제 검증 기록18.40초,연구24155·예비84000/used0 유지.

[별도 계속 계약](joint533_contract.json) · [초기 동일성](joint533_initial_verification.json) · [문제](joint533_problem.py) · [단일 계속 실행](joint533_design.py) · [설계 결과](joint533_design.json) · [잔차/profile 감사](joint533_audit.json).

## 변경하지 않은 문제와 유일 초기화

532의 마지막 accepted **839변수 전체**를 유일 초기화로 사용했다. 당시비공개 `design-solution`과`latest-iterate`의 x가 정확히 같음을 확인했다. 원래531 geometry basis/고정seam/횡변위 범위/목적 정규화17.37270759초도 유지했다. 초기 objective·gradient·constraints의532/533 차이 모두0,bounds 동일,초기 primal 위반0이었다.

공동 문제의 횡변위273개·periodic q283개·launch w283개,실제 `sum(2ds/(sqrt(w_i)+sqrt(w_next)))` 시간 목적,top80/곡률153.384316/source-forward 두 branch/backward80/periodic seam/launch 제약과 기하 nominal1.25/계산1.252m를 바꾸지 않았다. 기존528 controller와 profile 생성식도 그대로다. [원532 예산 종료 결과](joint532_result.md)는 수정하거나 덮지 않았다.

수치 solver는 동일trust-constr/sparse AugmentedSystem/BFGS/gtol1e-5/xtol1e-8/barrier_tol1e-8/초기barrier1e-5다. 변수 x의 warm start이며 저장하지 않았던 BFGS/trust 내부 상태를 복원한 것은 아니다. 이전과 같은 초기 solver 설정을 사용했다. 문제 소스의532→533 차이는 geometry Jacobian 상한170→800 한 줄뿐임을 검사했다.

사용자가 추가 승인한 **maxiter320/Jacobian800/CPU600초/wall720초**를 별도 등록했고,objective/constraint4000·geometry sample3000만 상한도 유지했다. 수렴하면 즉시 끝내며 이번 유한 실행 후 자동 증액은 하지 않는다. 원532 비용과533 새 비용은 분리했다.

## 종료와 다시 확인한 gate

|집계|532 마지막 endpoint|533 마지막 endpoint|
|---|---:|---:|
|설계 speed해 clock|17.023256s|14.969723s|
|동일 경로의 기존528 재생성 scalar|16.209396s|14.407176s|
|원래528 Gaussian17.250273 대비 scalar 개선|1.040877s|2.843097s|
|경로 길이|993.159346m|978.609832m|
|최대 절대 곡률|0.0903752/m|0.0839060/m|
|독립 외곽 최소 여유|1.253229m|1.252015m|
|최적성 norm|2.561243e-4|2.497677e-5|

533의320회/579Jacobian/solver CPU317.682543초에서 `maxiter320` 상한으로 종료했다. SciPy status0의 메시지는 `The maximum number of function evaluations is exceeded.`였으나 별도 objective4000회 상한을 소진한 것이 아니다. 최대 정규화 constraints/bounds 위반0,road union 밖0,최대 표본 간격0.218750m였다. geometry33sample/segment와 독립530 all-boundary oracle의 최소 여유가 모두1.252015m로 nominal1.25를 만족했다.

periodic/launch 설계 speed가 재생성 speed를 초과한 최대값은각각0m/s여서 기존0.001m/s 보수성 검사도 통과했다. 기존profile 재생성 오차0,설계 source-forward/back80 acceleration 초과0을 감사했다. 설계 speed clock은재생성 scalar보다0.562547초 느리다. 설계 speed는deploy하지 않으며 최종 선별은 기존528 profile만 사용했다.

**기하·scalar 조건과 primal feasibility는 충족했지만, status1/최적성≤1e-5 수렴 조건은 미충족**이다. 최적성은 기준의약2.50배다. global optimum이나 물리 안전의 증명은 어느 쪽도 아니며,수렴 기준을 결과 후에 완화하지 않았다. 자동 연장·새 초기화·weight/method sweep·다른 iterate 선택은 없다. 마지막 accepted endpoint와320개 반복 이력을 그대로 보존했다. 이 경로를 무효하거나 주행 실패한 후보라고 해석하지 않는다.

## 물리 실행 전에 발견하고 분리한 평가기 초기화 보정

원530~533 조건부 모델 초안은 late saved-root에서도 cold-start용 signed `project(...,None)`을 사용했다. 사전선택 위험 root 둘은 첫lap의0.521381/0.633401 지점인데 signed 표현은−0.478619/−0.366599 lap이 되어 참조속도가0으로 잘못 초기화됐다. 이 초안들은 지금까지 물리 실행한 적이 없다.

원533 초안을 보존하고 [first-lap 초기화 helper](joint533_projection.py)와 [분리된 보정 모델 entry](joint533_model_fixed.py)를 준비했다. 등록된 root는첫lap의완료 이력임을 이용해 `completed>0`이고 초기 own-path progress가음수일 때만L을 더한다. 이후의 연속 projection/공유528 controller는 바꾸지 않는다. [읽기 검증](joint533_projection_check.json)에서 baseline 저장 progress와오차0m였고 참조63.877932/73.428023m/s를 복구했으며,cold signed seam 의미는그대로였다. 이 보정은 force/적분0이며 실제 모델을 실행·검증한 것은 아니다. 수렴 gate 미통과로 보정 모델도 실행하지 않았다. 향후 사용 시에는 active source/hash를 별도 model registration에 고정하도록 준비했다.

## 후속 순서·경계·남은 장애물

사전 순서는 수렴+기하+기존profile scalar 선별→같은 두 위험 root 각24hold/96raw 짝의 전 안전→cold/carry source-style finish·525실제18.40 대비모델≥0.50초/528모델대비≥0.10초 및 full force/추종/기하/HIGH 기준→조건부 sameDEV fresh525 policy vs533 package 실제 official finish 한 짝이다. 이번에는 첫 수렴 gate에서 멈춰 이 순서의 어떠한 물리 적분도 하지 않았다. 실제528이 검증됐다고 주장하지 않는다.

0.19불확실성/예측1.06/물리1.25,참조초과5(내부4.85),tracking 누적clipping10%,geometry/launch/sourceTimeLimit/one-hold prediction/source-force oracle/관측·손상 gate,고정528 controller/top80/back80 및backup100/back45는 유지했다. native1000actions/2resets/4102raw/2world,attempt 사전 차감과finally body/joint0 정리도 계약대로이며 이번 world 생성0이다. 기존DEV만 사용하고 새seed/HOLDOUT/SEALED/보호 평가0이다.

남은 장애물은 **이 유한 계속 실행에서의 최적성 수렴 미완료**다. 개선된 표본 기하 경로를 보존했지만 추가 자동 계산이나 gate 예외 처리로 물리 단계에 보내지 않았다.

## 비용·보존

원532 worker CPU100.018804초/wall100.101974초는 그대로다. **533 새 worker**는 초기 동일성0.475263/0.475339초,설계(후처리 포함)319.956558/320.086489초,읽기감사0.180864/0.180905초,projection 읽기검증0.008661/0.008660초로 합계 **CPU320.621345초/wall320.751393초**다. 준비·소스 확인·publication allowance5CPU/5wall는 실측 worker와 별도다. 새 비용은 요청한600CPU/720wall 안이다.

533 geometry sample15,858,381회,Jacobian579회,objective581/gradient579/constraint581회(초기/최종 읽기 포함)였다. 새 물리 적분/force/native action/reset/world0,연구24155·예비84000/used0 유지. source/input pins·controller 동일성·원532 종료와비용·533 단일DESIGN_STARTED/마지막x/반복 이력·530/531 원실패를 보존했다. 공개물은 코드/계약/집계뿐이며 지도·좌표·횡변위·speed해·root·raw 궤적·seed/RNG/case는 비공개다. main 지정SHA·Participants·사용자 변경·기존 백업을 보존하고 승인 종료2026-10-20 19:01:55KST를 자동 연장하지 않는다.
