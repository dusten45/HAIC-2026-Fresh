# 518 — 같은 DEV 실제 공식 완주21.94→20.70초

**80/100 양쪽이 실제 source의 공식 finish를 확인했다. 같은 reset 완료 시각부터의 기록은21.94초와20.70초, 차이는1.24초다.** 모델 finish나 참조 arc 끝을 실제 완주로 대신하지 않았다. 새 full-reference 진단에서의 한 짝 결과이며 **11초대 목표는 아직 미달**이다. 과거13.640초와 설정/경로가 같다고 확인하지 않았으므로 직접 개선으로 비교하지 않는다. pixel 제출 성능·독립 평가를 주장하지 않는다.

## 전체 확장과 명시한 경계

[원 사전 계약](lap518_contract.json) · [닫힌 제어](lap518_control.py) · [모델 finish 연결](lap518_finish.py) · [순수 tests](test_lap518.py).

같은 source track의 모든283개 station을 사용하고 마지막→첫 segment를 연결했다. 장애물6개는 각각 한 번만 연결하며 원래 offset3.8m/폭16m를 원형 arc 거리로 적용했다. 원형 법선·다른 장애물 영향·기존 임시 endpoint의 제거로 기존150개 점은 최대0.286375m, arc는0.058101m,80 속도 node는3.770794m/s 달라졌다. 이를 exact 보존했다고 주장하지 않는다.100/80 사이에는 동일한 닫힌 경로와 제어 규칙을 쓰고 lateral budget만 다르다. release 보정이나 gain 탐색은 없다.

닫힌 곡률 속도 상한에 forward25/backward45 squared-speed 제약을 모든 edge에서 반복 수렴시킨다. 첫 출발에만 `q=min(주기적 q,2×25×s)`를 적용한다. 종료 node는 출발의0이 아니라 주기적 속도를 가지며, arc L 이후에도 주기적 참조를 유지해 finish 확인 전에 가짜 종점 제동을 만들지 않는다. top80, pure pursuit7m/0.3s·wheelbase3.24·steer±0.4, 속도gain2, steady pedal map, 첫24고정gas0.32는 유지했다.

projection은 이전 unwrapped progress 근처의 유효 segment를 고르고 seam에서 lap을 누적한다. perraw 역진/점프 검사를 유지하며, 출발 직전 음수 arc→0을 완주로 세지 않는다. 순수2tests는 seam wrap·주기 속도/출발 경계·장애물 중복·끝 node 비정지와 source tracker의 crossing 후 confirmation을 검사했다. 새 integrator tick은0이다.

모델에는 원본 `FinishLineTracker`를 쓰되 **예측 hull/센서 접촉·방문 타일**을 입력한다. 이미 관측한 reset/prefix 접촉 이력으로 초기/carry 방문 ledger를 구성했고 실제 방문율과 대조했다. rigid hull/joint·solver 이력 한계가 남으므로 모델 finish는 추정이다. native에서는 실제 tracker의95% 타일 자격·정방향 start-strip 통과·앞쪽 확인과 `finish_time_s`만 완주로 인정했다. 참조 path length995.445289m 도달이나 TimeLimit은 finish가 아니다.

## 출발 평가 오류의 보존과 복구

[최초 모델 실행](lap518_model.py) · [최초 실패](lap518_model_result.json). 원 계약에서 고정 gas 출발에도 사용하지 않는 속도참조 오차≤5m/s를 적용해 양쪽6holds/24ticks에서 멈췄다. 여유5.157m·force/projection은 기준 안이었고, 이때의5.25422m/s 차이가 유일한 탈락 원인이었다. 이미 검증된517 실제 고정 출발도 같은 미사용 참조 차이가5.25443m/s이며 source/safety 오류는0이었다. 고정 출발과 참조 추종을 혼동한 평가 정의의 오류였다.

**원래 계약의 실패를 통과로 소급하지 않았다.** [새 실행 계약](lap518_execution_contract.json)에 action1–24는 고정 출발을 source/기하/예측/launch-force로 검사하고, action25부터 실제로 제어에 쓰는 참조 오차≤5를 적용한다고 명시했다. 기존 부분 구간 검사(arc99이후)보다 action25–arc99에는 오히려 검사 범위가 넓다. 제어·수치 허용치·물리 안전 한도는 바꾸지 않았으며 이 phase-scope 개정은 공개한다.

[연속 실행](lap518_model_continuation.py)은 저장된 두6hold state/tracker/방문 ledger에서 action7부터 이어갔다. 기존48tick은 새 trace의 exact prefix로 재사용했고 재적분0이다. 초기 실패·원본 trace·계약은 보존했다. 모델 비용에는 최초48tick과 최초 worker 시간이 한 번만 포함된다.

## 전체 모델 선행 결과

[연속 모델 집계](lap518_continued_model_result.json).exact reset80/100이 전체 안전/finish 추정을 통과한 후에만 두 실제517 carry suffix를 실행했다. 네 모델 모두283/283 방문, source-style finish 추정과 여유≥0.50m·path≤3m·주행 참조 초과≤5m/s·주행 force ratio≤1.25/clipping≤10%를 통과했다. 고정 launch는 이전 실측 peak2.2555/46of384 근거로 사전 peak2.5·24holds 완료 fraction15%를 별도로 사용했다.

cold 추정 finish는21.94/20.70초로1.24초 차이였다. carry도 안전하게 끝났지만 출발 상태/이전 경로가 달라 carry clock 차이를 새로운 짝 인과 이득으로 합산하지 않았다. cold/carry 최소 여유는0.956685m 이상, 주행 clipping0이었다. 실제 native는 이 gate 뒤에만 실행했다.

## 실제 공식 완주 증거

[native 계약](lap518_native_contract.json) · [native 실행](lap518_native.py) · [공식 결과](lap518_native_result.json) · [전수 검증](lap518_summary.json).

80을 먼저 실제 완주·source/안전/예측 gate로 검증한 뒤100을 실행했다. 두 exact reset의 기존 DEV model/RNG/pixel fingerprint와 첫24 action/관측이 일치했다. 이후 각자의 현재 상태와 지도만 사용했고 실제 미래 상태·보호 평가를 후보 입력에 넣지 않았다.

| 실제 source 지표 |80|100|
|---|---:|---:|
| 공식 finish episode 시간 |21.94s|20.70s|
| finish 확인 wrapper/physics 시간 |21.96s|20.72s|
|95% 방문 자격 시각 |20.38s|19.24s|
| 방문 타일 |283/283|283/283|
| actions |275|259|
| 최소 도로·장애물 여유 |0.989557m|0.951836m|
| 최대 path error |1.131427m|1.236797m|
| 주행 참조속도 초과 최대 |4.452500m/s|4.557685m/s|
| 주행 force ratio 최대 |0.786943|0.964680|
| 주행 clipping |0/4008|0/3760|
| 고정 launch clipping |46/384|46/384|

official event와 확인 시각이 다른 것은 source tracker가 center crossing 시각을 저장하고 strip 앞쪽 확인 후 finish를 확정하기 때문이다. 예를 들어100의 참조 arc 도달 보간은20.691744초지만 공식 event는20.70초이며 기록에는 후자를 썼다. 마지막80 wrapper hold는 source finish로2rawticks에서 정상 종료했고100은4ticks였다.

2236raw행의 source 센서/payload/효과/마찰·projection·관측·안전 오류0이다. 실제 force8536개를 대조했고 oracle 최대 차이0.000209N, COM impulse 잔차0.0000212m/s였다.100의 한-hold 예측 최대 오차는 위치0.001306m/속도0.013069m/s/방향0.000563rad/yaw0.012172rad/s로 등록한0.10/0.15/0.02/0.05 이내였다.

100은 이 새 닫힌 참조·known DEV의 **실제 한 랩 비교**로 승격한다. 다만20.70초는11초대 목표와 거리가 남는다. 저장 실측에서100의40m/s 미만 시간은6.34초,75m/s 이상은0.78초였다. 다음에는 이 현재 전체 trace의 시간·참조 활성도·힘 사용을 근거로 큰 병목 하나를 고르며, 이번 이득을 반복 합산하거나 속도상한만 올리면 목표에 도달한다고 추정하지 않는다. 실제 COM chord path987.93m도 공식 거리나 최적 하한으로 취급하지 않는다.

## 비용·보존

실제 **534actions/2resets/2236rawticks=reset102+action2134**를 사용했다. 매 호출 전 immutable charge534개를 전수 대조했고, 두 world는 body/joint0으로 닫혔다. 연구 **25472→24938**, 예비84000/used0이다.1000actions/2resets/4102rawticks 상한 안에서 finish 직후 멈췄다.

모델 integrator **5550ticks=전체/연속 모델3414+native4tick 예측2136**, wheel force 평가22192회다. 실제 finish가 중간 raw에서 나오더라도 호출 전 예측한4tick 비용은 모두 포함했다. 모델/native worker CPU108.128840초/wall108.149326초(초기 실패 포함), 준비·복구·publication allowance3CPU/3wall는 별도다. 전체480CPU/660wall/200000model ticks 한도 이내이며 계측 source callback 비용을 포함한다. 대화 전체 경과시간 실측은 아니다.

private3328files/32,879,807B로128MiB/8192files 이하이다. native 저장은 exclusive-write admission byte/file 누적과 stdout/closing64KiB 예약으로 이전의 매raw 폴더 재검색 비용을 줄였고 최종 실제 크기를 확인했다. raw/지도/state/RNG/명령은 private에만 있다. 기존 main dfb7a2de2178825ca5c5ce20bab01ba67052ba31·Participants·사용자 변경·백업·이전 결과를 보존했다. 새 seed·보호 평가·유료 자원0, 지정 cloud·단일 작업을 유지한다. 승인 종료는2026-10-20 19:01:55 KST다.
