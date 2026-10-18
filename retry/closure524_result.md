# 524 — wheel velocity의 lever 시점 수정, 저장3hold 모델 검증 통과

**한 구조적 모델 수정이 사전 검증을 통과했다.** force 계산식이나 motor gain을 바꾸지 않고 다음 force용 wheel offset velocity에 위치 적분 전 lever를 사용했다. 실패 hold의 힘 최대 비율 오차0.112348→0.000223, 별도 선회 hold0.069076→0.000155로 줄었다. native/action/reset0이며, driving policy·전체 lap·실제 성능 검증은 하지 않았다. 기존523 코드/실패/결과,0.19 여유와1.25 물리 기준은 보존했다.

[입력 분해 사전 계약](closure524_diagnostic_contract.json) · [진단](closure524_diagnose.py) · [진단 결과](closure524_diagnosis.json) · [한 수정](closure524_control.py) · [검증 사전 계약](closure524_validation_contract.json) · [검증 코드](closure524_validate.py) · [검증 결과](closure524_validation.json) · [저장 감사](closure524_audit.py) · [감사 결과](closure524_audit.json).

## 입력 분해와 소스 근거

실제522 hold41 직전 root에서 같은 historical command로 원 모델을4ticks 예측했다. 각 force 직전의 heading, COM/world/offset velocity, omega/gas, hull/yaw, joint angle/rate, lever를 실제 raw와 비교했다. tick별 최대 오차는 공개 집계에,4ticks×4wheel 상세 오차16records는 private에 보존했다.

|raw2 force 입력 오차|값|
|---|---:|
|최대 wheel offset velocity|0.478842m/s|
|최대 wheel heading|4.49e-6rad|
|최대 omega|4.36e-7rad/s|
|hull yaw|4.09e-5rad/s|
|COM velocity|7.11e-6m/s|
|최대 joint angle/rate|5.25e-6rad /2.65e-4rad/s|

raw2에서 다른 입력은 잘 맞는데 wheel velocity 재투영이 크게 어긋났다. 사전 고정한7개 source force 재계산을 수행했다. 아래 실제 입력 치환은 calibration용 saved-only 검사이며 정책 입력이나 독립 인과 효과가 아니다.

|치환 입력군|힘 비율 RMSE|최대 절대오차|
|---|---:|---:|
|원래 예측|0.055368|0.112348|
|실제 heading만|0.057755|0.120648|
|실제 COM velocity만|0.049253|0.091686|
|실제 wheel offsets만|0.006457|0.013283|
|실제 omega/gas만|0.056265|0.114789|
|실제 hull/joint/yaw로 같은 rigid law 재구성|0.063167|0.114557|
|모든 실제 force 입력|3.64e-8|1.01e-7|

실제 raw2..4 wheel offset을 `actual yaw × 같은 tick lever`와 비교한 잔차RMSE는0.491598m/s, `actual yaw × 이전 tick lever`와 비교하면0.0001343m/s였다. offset 치환과 lever clock 검사가 모두 사전50% 개선 기준을 통과해 단일 수정을 허용했다.

local source는 `car.step`의 force 후 `world.Step(.02,180,60)`를 호출한다. 공개 upstream [island solver](https://raw.githubusercontent.com/pybox2d/pybox2d/master/Box2D/Dynamics/b2Island.cpp)는 velocity constraint를 먼저 풀고 위치/각도를 적분하며, [revolute joint](https://raw.githubusercontent.com/pybox2d/pybox2d/master/Box2D/Dynamics/Joints/b2RevoluteJoint.cpp)는 초기 각도의 lever로 속도 Jacobian을 만든다. 이 순서가 관측된 lever clock 차이와 일치한다. 설치본은 pyBox2D2.3.5이며 upstream master와 컴파일 binary의 동일성까지 검증한 것은 아니다; 결론의 직접 근거는 저장 상태와 검증 결과다.

finite motor torque64.8은 실제 source와 이상 모델의 차이지만, 이 hold의 front commanded-vs-observed 상대 joint rate 최대오차는7.45e-7rad/s였다. rear 상대 rate는최대0.000303rad/s였다. motor impulse/torque가 저장되지 않아 saturation을 직접 측정하지 않았고, 이를 주원인으로 주장하지 않는다. clip 전 요구 힘 오차는 커도 COM에는 clip 후 힘이 들어가므로 작은 COM 오차와 양립한다.

## 한 수정과 별도 저장 hold 검증

기존512/504를 편집하지 않은 새 wrapper다. 원래 tick으로 engine/friction/contact/pose/yaw/momentum/joints를 그대로 갱신한 후 **wheel offset만 새 yaw×step 전 lever로 대체**한다. 새 위치 lever는 기존처럼 회전시킨다. gain·motor torque·pooling·속도 참조를 튜닝하지 않았다. 실제 다음 상태는 모델 전파에 넣지 않고 비교 label로만 사용했다.

검증 전에 기존522 baseline 중 action>=25/speed>=30/완전4ticks/flags0 조건에서 최소|yaw| 정상 hold111, 최대|yaw| 선회 hold225를 고정했다. 실패41은 보정 상태이고 나머지 둘은 별도 hold지만 같은DEV이며 독립DEV 평가가 아니다. 원래 실패4tick 통계는 진단에서 재사용해 중복 적분하지 않았다.

|4tick 힘 비율 오차|원 RMSE→수정 RMSE|원 max→수정 max|
|---|---:|---:|
|실패 hold41|0.055368→0.000106|0.112348→0.000223|
|정상 hold111|9.31e-7→8.24e-7|1.84e-6→1.60e-6|
|선회 hold225|0.036997→0.0000604|0.069076→0.000155|

실패 hold의 수정 peak **1.263676**은 실제1.263650에 가깝고1.25 위반을 정확히 식별한다. 원 모델 peak1.178769는 이 위반을 놓쳤다. 이는 위험한 주행을 안전하게 바꾼 결과가 아니라, 이미 위험했던 힘을 모델이 더 정확히 예측한 결과다.

사전 기준은 실패RMSE/max 각각50% 감소 및 max<=.05, 알려진 실패peak>1.25 식별, 별도2hold pooledRMSE25% 이상 개선/각 max<=min(.05,old+.01), 기존 kinematic gate 전부였다. 모두 통과했다. 수정 모델의 세 hold 최대 position 오차4.93e-5m, speed3.71e-5m/s, angle3.72e-5rad, yaw0.000256rad/s였다. 실패 hold의 max postclip force-vector 오차는39.2638→0.0924N, 선회는32.2244→0.06485N으로 감소했으나 exact full solver라는 주장은 하지 않는다.

## 범위·비용·다음 판단

주된 지역적 오차를 lever clock 불일치로 좁혔고 별도 저장 선회에서도 개선을 확인했다. finite joint/motor/position solver와 긴 horizon의 근사는 남는다. 세 hold 결과만으로 기존 경험적 여유0.19를 낮추지 않으며1.25 기준도 그대로다. 기존523을 재실행하거나 실패를 소급 통과시키지 않았고, static cap·whole-lap·native 추가0이다. 다음 driving 후보는 이 수정 모델을 명시적으로 채택한 별도 사전 등록과 전체 검증이 필요하다.

새 적분은 진단4 + 검증20 = **24ticks**. 적분 내 wheel force96회, 별도 force oracle112+80=192회다. 실제 replay label12raw는 기존 자료이며 새 물리 실행이 아니다. worker CPU0.207612초/wall0.092607초, 준비·소스 읽기·publication allowance3CPU/3wall는 별도다. 모든 원래 결과와 source/input SHA를 보존/확인했다. 연구24641·예비84000/used0 불변. 같은 지정 cloud/DEV/단일 작업, HOLDOUT/SEALED·새 seed·보호 평가·별도 유료 자원0. raw state·명령·지도·상세 치환 자료는 private, 코드/집계만 공개했다. main·Participants·사용자 변경·백업 보존, 승인 종료 **2026-10-20 19:01:55 KST**다.
