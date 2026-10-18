# 525b — 현재 상태 힘 예측 governor: 실제20.46→18.40초,2.06초 개선

**같은DEV의 실제 source 공식 finish 짝 비교를 통과했다.** baseline20.46초, governor18.40초로2.06초 개선했다. 후보 tracking 힘 peak1.057017<1.25, 한-hold 힘 비율 최대오차0.000234<0.19였다. 실제 두 완주이며 모델 시간을 기록으로 대체하지 않았다.11초대·독립DEV·pixel 정책 성능은 달성/검증하지 않았다.

[원 사전 계약](governor525_contract.json) · [원525 실패](governor525_model_result.json) · [실행 경계 수정 계약](governor525b_contract.json) · [사용한 governor](governor525b_control.py) · [모델 실행](governor525b_model.py) · [모델 결과](governor525b_model_result.json) · [실제 실행](governor525b_native.py) · [실제 결과](governor525b_native_result.json) · [저장 감사](governor525_verify.py) · [감사 결과](governor525_verification.json).

## 한 후보, 수정된 모델과 고정 요소

524의 **위치 적분 전 lever를 쓰는 wheel velocity closure**를 body propagation과 모든 planning/한-hold forecast에 적용했다. 원522/523 모델 결과를 재사용해 통과시키지 않고 baseline/candidate cold·carry를 모두 같은 새 모델로 계산했다.524의 저장3hold 검증24ticks는 읽기 재사용이며 이번 새 비용이 아니다.

Gaussian 경로·장애물 우회·pure pursuit 조향 규칙·source-drive forward·backward45·top80·steady pedal map·gain2·첫24gas0.32는 고정했다. 후보의153.384316 참조도 그대로다. 현재 root의 wheel heading/offset velocity/omega/gas/yaw/contacts를 전파해 **제동 결정만 보수적으로 선택**한다. 높은 참조의 원래 action과 backup action, 두 개만 있다. backup은 같은 steering, `gas=min(highgas,100gas)`, `brake=max(highbrake,100brake)`로 가속을 늘리거나 제동을 줄이지 않는다.100은 기존519 참조이며 새 수치 sweep이 아니다. 실제 gas/brake는 위험 상태에서만 달라진다.

매 tracking hold마다 첫 action을 시험하고 이후11hold는 backup을 쓰는 **12hold=.96초** 예측을 현재 상태에서 갱신한다. 각 raw의 바퀴별 clip 전 요구 힘<=**1.06=1.25−0.19**, 누적 tracking clipping<=10%, projection/path 조건을 확인한다. HIGH가 실패하면 동일 horizon의 BACKUP을 한 번 시험하고 둘 다 실패하면 actual 호출 전 중단한다.0.19와1.25는 낮추지 않았다. 정적 v² scaling/pooling을 사용하지 않는다. 유한 backup 예측이 재귀적/전역 안전 증명은 아니며 전체 실행 궤적의 차체 여유·안전 검증도 별도로 필요하다. 실제 미래 상태는 입력이 아니다.

## 저장 반증과 명시적인 clipping 경계 오류 복구

실제 hold41 직전 root에서는 두 action 모두 첫 force가 예측 허용치를 넘어 거절했다. 위험 상태에 이미 들어온 뒤 즉시 고친다고 주장하지 않았다. 실패8hold 전 actual root33에서 unshielded153을 수정 모델로 전파하면 hold41/raw2에1.263458로1.25 위반을 재현했다.

원525 governor는 같은 root33에서 hold38까지 안전하게 진행했으나 hold39에서 `NO_ADMISSIBLE_ACTION`으로 실패했다. HIGH/BACKUP peak1.054851/1.040980은1.06 이하였다. 실제 원인은 forecast가 매번 clipping 분모를0으로 초기화해 첫8wheel samples 중1clip=12.5%를 거절한 것이다. 직전 backup38은 같은 후속 경로를 이미2/192=1.04%로 통과시켰다. 실제/전체 모델 안전 게이트는 **이미 주행한 post24 이력까지 누적**하므로 초기화 경계가 맞지 않았다.

원 계약/소스/실패는 그대로 남겼다.525b는 동일1.06/0.19/1.25/10%·horizon·두 action을 유지하고, forecast clipping counter에 현재까지의 실제/모델 tracking clip/sample 이력을 전달하도록 별도 등록했다. root33의 이미 관측한 post24 이력은0/128, carry47은 검증된 actual518100 prefix0/352다. 실제 native에서는 그 episode의 현재 source counter만 사용한다.

기존 probe33..38의 HIGH 통과는 과거0clip 이력을 더해도 통과하며, 거절된 HIGH38은 peak1.149565>1.06 때문에 계속 거절된다. 따라서 동일했던 첫6actions/24raw를 재적분하지 않고 저장 hold38 이후부터 이어갔다. 기존353model ticks도 비용에 한 번만 포함했다.525b는 원525의 실패를 소급 통과시킨 것이 아니라 경계 수정 계약에 따른 별도 실행이다.

수정 probe48raw는 peak1.042565/최소 차체·바퀴 여유3.016516m, HIGH9/BACKUP3으로 통과했다. 미실행 original suffix를 가짜 재사용하지 않았다.

## cold/carry 선행 gate

모든 full 궤적에 sampled 전체 차체/바퀴 road+obstacle margin>=0.50m, path<=3m, tracking 참조 초과<=5m/s, projection/TimeLimit, phase별 source force/clipping을 검사했다. 후보는 추가로 실행 예측 peak<=1.06이다. 첫24 고정 launch의 기존 peak<=2.5/clip<=15% 조건은 유지했다. source-styleFinishLineTracker의 qualification/center/front 확인을 사용하며 model finish는 추정이다.

|같은524모델|baseline100|governor|개선|
|---|---:|---:|---:|
|cold finish 추정|20.46s|18.40s|2.06s|
|사전 지정 actual518 before47 동일 carry|20.46s|18.64s|1.82s|

후보 cold/carry 최소 여유0.988516/0.926230m, 최대 path1.390702/1.416653m, tracking 참조 초과2.554661/2.643866m/s, running peak1.056840/1.057365였다. HIGH 비율96.60%/97.86%로 정상 명령 유지50% 기준을 넘었다. 두 경우 모두 전체 안전·완주·0.50초 효과를 통과했으므로 native로 진행했다.

## 실제 source 결과와 예측 정확성

|actual sameDEV|baseline|governor|
|---|---:|---:|
|공식 finish|20.46s|18.40s|
|source confirmation|20.48s|18.40s|
|actual actions|256|230|
|visited tiles|283/283|283/283|
|최소 차체/바퀴 road+obstacle margin|0.974467m|0.988258m|
|최대 path error|1.184474m|1.390559m|
|tracking 참조 초과|2.209972m/s|2.554430m/s|
|tracking source raw force peak|0.944660|1.057017|
|tracking clipped wheel samples|0/3712|16/3296|
|HIGH/BACKUP tracking holds|해당없음|199/7|

공식 finish event는 source의 `finish_time_s`이며 reference arc/TimeLimit로 대신하지 않았다. 후보의 event와 confirmation이 같은 raw에 일어난 것을 보존했다. 두 reset full identity와 첫24action/observation prefix가 일치한다. 충돌·damage·source/raw guard 오류0이다.

수정 모델 한-hold 예측의 전체 최대 오차는 position4.73e-5m, speed4.77e-5m/s, angle3.50e-5rad, yaw2.88e-4rad/s, wheel raw force ratio **0.000234386**이었다. 모든 사전 기준0.10/0.15/0.02/0.05/0.19를 통과했다. 같은 현재 입력에서 source 힘 oracle 최대오차0.00024297N, COM impulse residual2.41e-5m/s였다. source force capture7776개를 보존했다.

추가 physics/replay 없이486개 current own-state 명령을 bit 단위로 재계산했다. governor의206개 tracking 인증이 현재 누적 samples+192를 사용하고, 선택 action이HIGH/보수적BACKUP과 일치함을 확인했다.486개 immutable 사전차감과 raw2046개/오류0, 두 world 종료를 검증했다. 정책 선택 과정의 실제 미래 trace 참조는 없다.

실제 시간 개선은 **2.06초**, HIGH 유지율 **96.60%**로0.50초/50% gate를 통과했다. 이 한DEV 결과는 전역 force 오차 상한, independent evaluation, pixel 정책 또는11초대 달성의 증거가 아니다.522/523 실패와524의 제한된 모델 검증은 그대로다.

## 비용·보존

preflight 전체23118ticks에는 원525의353ticks와 재사용 probe24raw가 한 번만 포함된다. native 중 governor forecast9919 + 한-hold forecast1944 =11863ticks, 새 모델 전체 **34981ticks**다. 적분 내 wheel force139924회와 별도 explicit force147800회는 별개 비용이다. 감사 추가 적분/force0이다.

actual **486actions/2resets/2046raw** = reset102 + action1944. terminal partial hold0, live worlds0.1000actions/2resets/4102raw 상한 이내다. 연구 **24641→24155**, 예비 **84000/used0**. 미사용 허용량은 차감하지 않았다.

worker CPU: 원525 0.946724 +525b 67.209420 +native76.562439 +감사0.732861 =**145.451444초**, wall145.479125초다. 준비/publication allowance3CPU/3wall는 별도다. code/input/admission/history SHA를 확인했고 원시 지도·state·명령·RNG·seed·case는 private에 보존했다. 같은 지정 cloud/DEV/단일 작업, HOLDOUT/SEALED·새 seed·보호 평가·별도 유료 자원0. main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`·Participants·사용자 변경·백업 보존, 승인 종료 **2026-10-20 19:01:55 KST**다.
