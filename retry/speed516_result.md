# 516 — 곡률 budget80→100, 현재 DEV 곡선 window 실제0.1494초 개선

**같은 고정 경로·조향·가감속 pass에서 lateral budget만80→100으로 바꾼 후보가 사전 native 효과 gate를 통과했다.** 전체 공통 window의 실제 통과시간은2.191018→2.041604초, 보간 이득0.149414초(6.82%)이며20ms event bracket의 보수적 이득 하한도0.120000초로0.08초 기준을 넘었다. 현재 DEV 한 구간의 결과이며 전체 랩·11초대·과거13.640초의 개선으로 환산하지 않는다.

## 사전 조건과 모델 게이트

[사전 계약](speed516_contract.json) · [후보/force oracle](speed516_control.py) · [모델 실행](speed516_model.py) · [순수 테스트](test_speed516.py).

515의 exact 수집 초기 상태, 장애물 우회 경로, 곡선 pure pursuit, forward25/backward45 pass와 gain2/s·steady pedal map을 그대로 사용했다. 후보의 유일한 변경은 curvature cap의 `sqrt(80/|k|)`를 `sqrt(100/|k|)`로 바꾼 것이다. top speed80m/s와 첫24holds gas0.32/brake0은 같고 release 보정은 사용하지 않았다. 순수 테스트는 경로/arc/window 동일성, 참조속도 증가, 가감속 pass 제약, 같은 현재 상태의 동일 steering을 확인했다.

exact reset/관측 trigger stress × budget80/100 네 자기 모델 궤적을 사전 검사했다. 기준은 whole hull/wheel 도로·장애물 여유≥0.50m, 경로 오차≤3m, 참조속도 초과≤5m/s, 복합 tyre raw-force/friction 최대≤1.25 및 clipped wheel fraction≤10%였다. 양쪽 시작에서 같은 window의 모델 시간 이득≥0.08초여야 native로 넘어가기로 했다. 낮았던515 force ratio를 고속 안전성의 근거로 대신하지 않았다.

100 후보의 모델 최소 여유는0.95653m, 최대 경로 오차1.13282m, 참조 초과0.82007m/s, force ratio 최대0.86988, clipping0이었다. 각 시작의 window 이득은0.149254/0.149211초였다.80 참조의384raw 상태·명령은515 저장 nominal과 exact였다.

최초 모델 집계의 재현 검사에는 `asdict` tuple과 저장 JSON list를 직접 비교한 형식 오류가 있었다. 원래 runner/결과는 보존했고, 이미 저장한384행을 같은 JSON 형식으로 전수 대조해 exact임을 확인했다. 코드의 비교 형식과 gate 판정만 정정했으며 모델 적분·정책·안전/효과 기준은 바꾸지 않았다. [원래 모델 집계](speed516_model_result.json)의 `MODEL_NO_NATIVE`/재현false를 그대로 두고 [정정 증거](speed516_model_gate_correction.json)와 [native 실행 계약](speed516_native_contract.json)으로 연결했다. 과학 재실행은0이다.

## 실제 source·센서·효과·예측 확인 후 짝 비교

[native 실행](speed516_native.py) · [native 집계](speed516_native_result.json) · [전수 검증](speed516_summary.json).

80을 먼저 실행하고 모든 source/safety/accuracy 조건을 통과한 뒤에만100을 실행했다. 각 reset의 기존 DEV geometry/장애물과 exact515 full model-input/RNG/pixel fingerprint가 같았고, 두 arm 첫24action·관측도 exact였다. 각자의 현재 상태에서 같은 함수로 한 번 명령을 계산했다. 후보 입력에80의 실제 미래 상태/접촉을 주지 않았다.

| 실제 whole-window 결과 |80|100|
|---|---:|---:|
| actions |60|58|
| window 시간 |2.191018s|2.041604s|
| 코너 exit 속력 |32.969492m/s|36.028678m/s|
| window 종료 속력 |55.311997m/s|57.577257m/s|
| 최소 도로·장애물 여유 |0.989558m|0.951831m|
| 최대 경로 오차 |0.982842m|1.131320m|
| 최대 참조속도 초과 |0.134410m/s|0.820096m/s|
| 실제 source force ratio 최대 |0.763325|0.900122|
| clipped wheel samples |0/456|0/424|

두 arm 모두 같은 begin/end 공간 경계를 통과했다.80 duration bracket은[2.18,2.22]초,100은[2.02,2.06]초이며 이득 하한은2.18−2.06=0.12초다. 초기/종료 시각 또는 서로 다른 prefix 길이의 차이를 whole-window 이득으로 대신하지 않았다. 실제 경로 오차와 force 사용량은100에서 늘었지만 등록한 기준 안이었다.

source frame/센서/마찰/효과/payload·관측·안전 오류는574raw행에서0이었다. 실제 명령으로 source force를1888회 capture하고 current-state oracle과 대조한 최대 vector 차이는0.000153N, assembly COM impulse 잔차 최대0.0000161m/s였다. 후보의 매4tick 예측 최대 오차는 위치0.001227m, 속력0.011403m/s, 방향0.000535rad, yaw0.011451rad/s로 등록한0.10/0.15/0.02/0.05 한도 안이었다. 곡선에서 오차가 직선보다 커졌다는 점은 유지하며 solver warm-start나 모든 상태의 안전성을 인증하지 않는다.

[저장 실제 raw 회복 분석](speed516_audit.py) · [회복 event](speed516_recovery.json): 코너 exit 이후50m/s 회복은0.688857→0.556418초로0.132439초 짧았다. 이는 같은 완료 window 안의 보조 지표이고 window 이득에 더해 합산하지 않는다. 모델 대비 실제 window 시간 차이는80에서−0.000947초,100에서−0.001107초였다.

## 판단과 다음 범위

100은 **이 DEV 경로·곡선 window의 국소 속도계획 후보**로 승격한다. 더 높은 타이어 힘 사용과 약0.038m 작은 최소 여유를 지불하고 통과시간을 줄였다는 결과다. 보호 평가나 독립 seed·full lap finish를 확인한 것은 아니다.100을 무조건 전체 트랙 또는 pixel 제출 정책에 적용하지 않는다.

다음 검토는 같은 후보를 다음 곡률 전이까지 확장했을 때 경로 추종·복합 힘·장애물 여유·시간 이득이 유지되는지의 모델 qualification이다. 이번 한 window의 이득을 랩 전체에 반복 적용하거나 과거13.640에서 빼지 않는다. 이번 stage의 남은 action 상한으로 추가 주행·튜닝을 하지 않았다.

## 실제 비용과 보존

실제 **118actions/2resets/574rawticks=reset102+action472**다. 모든118실제 호출 전에 immutable charge를 남겼고 전수 대조했다.2world 모두 body/joint0으로 닫혔다. 연구 **25804→25686**, 예비84000/used0이다.320actions/2resets/1382rawticks 상한 안에서 필요한 만큼만 실행했다.

모델 integrator **1224ticks=사전752+native 한-hold 예측472**, 별도 wheel force 평가4896회다. 순수 테스트의 새 integrator step은0이다. 모델·native·저장 회복 worker 합계CPU19.843338초/wall19.849146초이며 형식 오류 검증·준비 allowance2CPU/2wall를 별도로 둔다. 전체360CPU/480wall/200000model ticks 안이다. 계측 observer/trace가 포함된 비용이며 비계측 실행 성능이나 대화 전체 경과시간으로 해석하지 않는다.

private828files/6,592,108B로64MiB/3000files 이하이며 실제 지도·state·RNG·명령·trace는 private에만 있다.118개 action의 등록된 own-state 법칙 일치,384baseline 모델 재현행, 모든 raw/charge/source/input SHA를 확인했다. 새 seed·보호 평가 조회·유료 자원0, 지정 cloud·단일 작업을 유지했다. main dfb7a2de2178825ca5c5ce20bab01ba67052ba31·Participants·사용자 변경·백업·기존 결과를 보존했다. 승인 종료는2026-10-20 19:01:55 KST다.
