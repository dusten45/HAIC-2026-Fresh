# 523 — 실제 root 힘 보정과 국소 힘 기반 속도 cap: cold 여유 게이트 실패

**native action/reset/world0.** 실제 hold41 직전 root의 같은 명령을 보정한 뒤, 모델의 바퀴별 힘 이력으로 위험한 구간의 속도 node만 낮추는 후보 하나를 시험했다. 저장 root 반증은 통과했지만 cold 전체 모델에서 사전 불확실성 여유를 지키지 못해 중단했다. carry0, 다음 실제 검증 후보로 제안하지 않는다.

[보정 사전 계약](force523_calibration_contract.json) · [보정 코드](force523_calibrate.py) · [보정 결과](force523_calibration.json) · [후보 사전 계약](force523_contract.json) · [후보](force523_control.py) · [순수 검사](test_force523.py) · [모델 실행](force523_model.py) · [모델 결과](force523_model_result.json) · [저장 감사](force523_audit.py) · [감사 결과](force523_audit.json).

## 초기 상태 누적 차이와 한-hold 모델 오차

522 실제 hold41 직전의 full own-state root, 같은 historical command로 source512를4ticks 예측하고 실제4raw를 비교 label로만 사용했다. 해당 실제 미래 상태/명령 trace를 정책 입력으로 쓰지 않았다.

|힘 비율 비교|최대 절대오차|
|---|---:|
|기존 cold 궤적의 같은 hold vs 실제|0.102515|
|실제 직전 root에서 한-hold 예측 vs 실제|0.112348|

실제 초기 상태로 바꿔도 개선되지 않았다. root의 첫 force 평가는 source 비율과 약1.01e-7 차이였지만, 전파 후 raw2/3/4 오차가0.084880/0.109491/0.112348로 생겼다. 따라서 누적된 cold 초기 이력 차이만으로 설명할 수 없고, 한-hold 상태 전파의 힘 예측 오차가 남는다. 작은 kinematic 오차(position0.006954m, speed0.026903m/s, angle0.001447rad, yaw0.027404rad/s)를 힘 정확성의 인증으로 사용하지 않았다.

민감도는 사전 고정한 네 항목의± 단일 변화만 사용했다: front heading/joint0.002rad, front wheel lateral offset velocity0.10m/s, yaw0.03rad/s(angular momentum/rigid offset 일관 delta), wheel spin slip0.10m/s. 조합/factorial/크기 sweep 없이8개와 원래1개, 합36ticks다. 최대 힘 비율 변화는0.020400이었다. 이 유한 검사는 heading/offset/yaw/spin 중 유일 원인을 분리하지 못한다.

등록한 산식 `ceil100(0.1123475+0.0203996+0.05)/100`으로 경험적 여유0.19, 모델 예측 허용치 **1.25−0.19=1.06**을 고정했다. 1.25 물리 안전 기준을 완화하지 않았다. 추가0.05도 경험적 여유이며 한 hold 보정이 전체 상태의 통계적/결정적 오차 상한이라는 주장은 하지 않는다.

## 하나의 후보와 작은 반증

522의153.384316 속도 참조를 기반으로 **위험 구간의 squared-speed cap만 변경**했다. frozen519 Gaussian 경로·조향 규칙·source-drive forward·backward45·top80·steady gas map·gain2·첫24gas0.32는 유지했다. numerical gas/brake는 변경된 참조에 따라 달라지며 별도의 pedal 최적화는 아니다.521 spline·520 inverse·70% sweep은 없다.

기존522 cold 모델의 tracking raw에서 각 force 평가 직전의 COM 속도v, progress, 최대 바퀴 raw 비율P를 읽었다. P>1.06인16raw의 선회·wheel omega/gas/slip 이력을 사용해, 해당 지점의 원형 arc 거리10m 이내 node에 `q_cap<=v²×1.06/P`를 적용하고 원래 cap과 local minimum을 취했다. 직접 바뀐 node는21/283개다. 그 뒤 **원래와 같은** forward/backward envelope로 미리 제동하게 했다. 실제 실패 raw는 여유 보정에만 쓰고 profile에는 모델 이력만 사용했다. v² scaling/10m pooling은 새 궤적에 대해 검증해야 할 근사 가설이다.

실패8hold 전인 실제522 action33 직전 root에서 양쪽을 동일하게 시작해12holds/48raw씩 예측했다. 위험한 상태에서만 대응하면서 정상 구간의 속도 이득을 남긴다는 작은 반증이다. 후보는 동일 안전·추종 기준과 peak<=1.06, peak 감소>=0.05를 모두 요구했다.

|저장 root probe|원래153 참조|힘 기반 cap|
|---|---:|---:|
|완료 raw|48|48|
|최대 raw 힘 비율|1.184536|0.998961|
|최소 전체 차체/바퀴 여유|2.549957m|3.333036m|
|최대 path error|1.242002m|1.136508m|
|최대 참조 초과|0|0.452023m/s|

작은 반증은 통과했다. 이는 모델의 force 감소이며 실제 개선이나 전체 lap 안전 증거가 아니다. 같은 DEV 저장 상태를 사용한 개발 검사이고 독립 검증도 아니다.

## cold 결과와 승격 실패

519 cold baseline1020ticks/20.38초는 SHA 확인 후 재사용했다. 새 cold가 source-style finish·안전·0.50초 개선을 통과할 때만, 사전 지정 실제518 action47 직전의 같은 root/visited ledger에서 baseline/candidate carry 비교를 하도록 등록했다. carry도 양쪽 완주·안전·0.50초 개선이 필요했고 이번 단계 native는 결과와 무관하게0이다.

새 cold는 **hold204/raw2, episode16.28초**에 front wheel1의 예측 비율 **1.06616192>1.06**으로 중단했다. physical1.25 기준 이하지만 여유0.19를 더하면1.25616192>1.25다. 좁은 차이라고 허용치를 낮추거나 모델을 끝까지 이어가지 않았다.814raw/252visited tiles까지 최소 여유0.932278m, 최대 path1.371700m, 참조 초과2.204940m/s, tracking clipped2/2872samples로 나머지 기준은 만족했다. 완주 시간과0.50초 효과는 측정 불가(null), carry0이다.

실패 지점10m 이내의 원래522 모델23raw 중 최고 비율1.165937,1.06 초과2raw가 있었다. 즉 기존 risk mask 밖의 완전히 새 위치만의 문제가 아니다. 해당 구간 cap을 줄였어도 changed closed-loop yaw/wheel 상태에서 v² scaling과 고정 pooling이 요구한 힘 여유를 보장하지 못했다. 전체 scalar clock은 baseline19.848402/원래153참조17.783505/후보18.289074초지만 실제 또는 완주 모델 시간으로 사용하지 않는다.

이번 후보는 실제 검증으로 보내지 않는다. 위험 구간의 정적 이력 cap이 작은 probe에서 효과가 있다는 증거와 전체 cold에서 여유가 깨졌다는 증거를 함께 남긴다. 다음 연구는 한-hold 전파 후 wheel force 오차를 직접 다루고, 바뀐 현재 선회 상태에서 재평가하는 per-wheel 제약을 별도 후보로 고정하는 방향이다. 이번 실패 결과로 기준·pooling·속도값을 수정하거나 재시도하지 않았다.

## 비용·보존

보정36 + probe96 + cold814 = 새 모델 **946ticks**. 적분 내 source wheel force3784회, 별도 explicit force oracle3784회. pure1test는geometry/profile불변·에너지 제약을 검사하며 적분0이다. 522 history912ticks와519 baseline1020ticks는 읽기 재사용으로 재적분하지 않았다. carry/native/reset/world0, 연구24641·예비84000/used0 유지다.

보정 CPU0.090958/wall0.078084초, 후보 worker CPU12.259925/wall12.262836초, 저장 감사 CPU0.070566/wall0.070566초. 합 worker CPU12.421448/wall12.411487초이며 준비/publication allowance3CPU/3wall는 별도다. source/input SHA를 검증했다. 원시 actual/model state·명령·지도는 private에 보존했고 코드/집계만 공개한다. 같은 지정 cloud·기존DEV·단일 작업이며 HOLDOUT/SEALED·새 seed·보호 평가·별도 유료 자원·옛 연구 실행0이다. main·Participants·사용자 변경·백업을 보존했다. 승인 종료는 **2026-10-20 19:01:55 KST**다.
