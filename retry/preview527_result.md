# 527 — finite-hold 참조 인증으로 경계 실패 해결, 모델 효과0.30초로 승격 미달

**cold 모델은 안전 완주18.10초였지만, 고정525 baseline18.40초 대비0.30초 개선으로 사전0.50초 기준에 미달했다.** carry/native/action/reset0이며 실제 기록은18.40초 그대로다.526의 실패는 보존했고,527은 backward80+finite-hold 추종 결정이라는 별도 후보로 등록했다.

[사전 계약](preview527_contract.json) · [참조 인증 governor](preview527_control.py) · [모델 실행](preview527_model.py) · [모델 결과](preview527_model_result.json) · [저장 감사](preview527_audit.py) · [감사 결과](preview527_audit.json).

## 변경 범위

526의 backward80 높은 참조를 유지하고 현재 root에서 첫 action과 이후11backup holds를 전파하는 **같은12hold horizon**에 `predicted speed−reference(predicted progress)<=5m/s`를 추가했다. 매 raw의 속도·위치 갱신 후 참조 하강을 확인한다. HIGH가 실패하면 기존 실제 실행 가능한 backup100 제동을 시험하고 둘 다 실패하면 호출 전 중단한다. 새 속도/제동 값·horizon·gain sweep은 없다.

경로·조향·top80·corner153.38·source-drive forward·steady gas map·524 모델·force 여유0.19/예측1.06/물리1.25·누적 post24 clipping10%·launch/tracking 구분은 유지했다. backup은 같은 steering, gas=min(high,backup100), brake=max(high,backup100)이며 common backup100/backward45도 그대로다.527은526의 조건을 느슨하게 한 실행이 아니다. 실제 미래 상태나 궤적은 정책에 입력하지 않는다.

baseline은525 실제18.40초다. SHA가 같은525b corrected-model cold18.40/carry18.64의 body1668+planning18915ticks를 재적분 없이 재사용했다. 새 후보 cold가 전체 안전/source-style finish·0.50초 개선·HIGH>=50%를 만족할 때만 같은 actual518 before47 root/visited ledger의 carry를 시험하고, carry도 통과해야 native 짝 비교를 허용했다.

## 경계 반증과 정상 회귀

526의 저장 **모델 own-state**를 사용했다. hold75 직전 root와 그때까지의 force 이력만 초기 입력이며, 이미 실패한 미래 held-action 결과는 비교 label이다. 새 HIGH75는 reference overspeed로 거절되고 BACKUP이 실제 모델4raw를 안전하게 수행해야 했다. 이전 root74와 정상 root70은 기존 HIGH 명령을 그대로 유지해야 했다.

|저장 검사|선택|force peak|최대 참조 초과|결과|
|---|---|---:|---:|---|
|hold75 직전|BACKUP|0.503357|0|기존HIGH를 reference로 거절|
|hold74 직전|HIGH|0.012518|0|기존 명령 bit 동일|
|hold70 정상|HIGH|0.024632|0|기존 명령 bit 동일|

hold74의4raw 끝 상태가 원래 before75 root와 정확히 같음을 확인해, 이미 계산한 hold75 결과를 두-hold 경계 증거로 사용하고 중복 실행하지 않았다. 세 검사 모두 margin>=0.5m/force<=1.06/overspeed<=5를 통과했다. 추가 감사에서 새 cold의 첫74commands도 실패526과 bit 동일했고, 최초 변경은 정확히hold75였다.

526 hold75는 가속을 유지해79.84m/s가 되어 참조보다5.497m/s 빨랐다.527은 같은 시작79.807m/s에서 기존backup 제동을 실행해 hold 끝72.243m/s, 참조74.758m/s로 안전하게 내려갔다.0.19 여유나5m/s 기준을 낮추지 않고 시간 경계 실패를 해결했다.

## 전체 cold 안전 통과, 효과 gate 실패

새 cold는905raw/227actions에서 source-style finish **18.10초**를 추정했다. 마지막 hold는 모델 terminal partial1raw이며 실제 wrapper 호출은 아니다. 최소 sampled 전체 차체/바퀴 여유0.943338m, 최대 path error1.827722m, 참조 초과4.648313m/s, tracking peak1.059675<=1.06, clipped10/3236이었다. launch 고정 조건·projection·TimeLimit·source-style qualification/center/front finish 조건도 통과했다.

tracking203hold 중 HIGH188/BACKUP15로HIGH92.61%였다. source-style finish까지203개 tracking 선택의 새 force/reference 인증 보고서가 모두 통과했다. 그러나 **18.40−18.10=0.30초<0.50초**여서 carry/실제 비교는 생략했다. 실제 기록을18.10초로 갱신하지 않는다.

## 작은 효과의 근거와 다음 판단

고정525는BACKUP7hold,527은15hold였다. 후보의 배타적 실행 mode 시간은 launch1.92/HIGH14.98/BACKUP1.20초로18.10초에 합산된다. 이1.20초를 baseline의0.56초와 빼서 인과적인 손실이나 회수 가능한 이득으로 주장하지 않는다. 서로 다른 궤적/참조 상태이기 때문이다.

후보 BACKUP 구간의 평균 양의 참조 속도 부족은5.2745m/s, HIGH는3.7392m/s였다. hold75 끝에서도 참조보다2.515m/s 느렸다. 기존backup100은 한 개의 실행 가능한 보수적 제동 명령이지만, backward80의 필요한 제동량을 최소화해 주는 연속 응답 해법은 아니다. 이는 coarse backup 선택이 시간 이득을 제한할 수 있다는 구체적 다음 가설이며, 이번 효과 미달의 유일 원인이라는 독립 ablation은 하지 않았다.

다음 근거는 새 값을 반복 탐색하는 대신 source 모델의 힘·참조 제약을 만족하는 제동량을 직접 결정하는 방식이다. 이번 단계에서 inverse/추가action/다른값을 구현하거나0.50초 기준을 낮추지 않았다.527은 경계 추종의 모델 검증을 통과했지만 실제 검증 후보로 승격하지 않는다.11초대 격차를 줄였다는 실제 성능 증거도 추가되지 않았다.

## 비용·보존

새 적분 **10981ticks** = 작은 실행12 + cold905 + governor forecast10064. 적분 내 wheel force43924회, 별도 explicit force43980회. cache20583ticks는 새 비용이 아니다. 저장 감사 추가 적분/force0. worker CPU21.822095+0.083419=**21.905514초**, wall21.908410초이며 준비/publication allowance3CPU/3wall는 별도다.

native/action/reset/world0, 연구 **24155**, 예비 **84000/used0** 유지. 현재 root·이미 관측한 모델 force 이력만 사용했고 source/input SHA를 확인했다. 지도·상태·명령·RNG·case·상세 trace는 private, 코드/집계만 공개한다. 같은 지정 cloud/기존DEV/단일 작업, HOLDOUT/SEALED·새 seed·보호 평가·별도 유료 자원0. 원525/526·524모델·main·Participants·사용자 변경·백업 보존. 승인 종료 **2026-10-20 19:01:55 KST**다.
