# 515 — 실제 DEV 첫 곡선으로 이동; 제동 해제 후보의 효과가 작아 native 비교 생략

**공통 곡선 경로의 모델 안전성과 다른 제동 결정을 확인했지만 시간 이득이0.011초여서 승격하지 않았다.** 새로운 실제 wrapper action은0이다. 지도·장애물·초기 모델 입력 수집에만 reset1회/51rawticks를 사용했고 world를 닫았다. 과거499의 손실 규모를 현재 조건에 적용하지 않았다.

## 필요한 수집과 동결 조건

[수집 계약](corner515_collection_contract.json) · [수집 실행](corner515_collect.py) · [실제 비용](corner515_collection_result.json). 저장된 도로 지도에는 장애물 좌표와 exact 초기 planar 입력이 없었다. 기존에 확인한 DEV를51rawticks(reset 내부1+warmup50)만 실행해 도로·장애물·track·초기 모델/RNG/관측 fingerprint를 비공개 수집했다. 기존 geometry/obstacle/body/RNG/pixel identity가 일치했다. 새 seed·보호 평가 조회·실제 운전 수집은0이다.

첫 코너 탈출 부근에 중심선 가까운 장애물이 있어 직선용 pure pursuit나 단순 중심선을 그대로 쓰지 않았다. source 중심선에 장애물 반대쪽의 고정 Gaussian offset(중심 분리3.8m, arc 폭16m, offset ±3.8m 제한)을 주는 공통 경로를 모델 실행 전에 동결했다. 곡선 추종은 경로상의 `max(7m,0.3s×속력)` preview와 wheelbase3.24m pure pursuit, wheel target±0.4rad다. 이 조건의 곡선 안전성은 이후 실제로 모델에서 검사했다.

공통 속도 참조는 곡률 cap `min(80m/s,sqrt(80m/s²/|곡률|))`, backward 감속45m/s²·forward 가속25m/s² pass다. 현재 경로 projection에서 공간 feedforward와 속도 오차 gain2/s를 같은 steady pedal map으로 변환한다. 첫24holds는 gas0.32/brake0 공통이며 조향은 처음부터 곡선 경로 feedback이다. 가속·조향·경로·참조를 후보와 참조 양쪽에 동일하게 적용했다.

## 한 가설과 사전 게이트

[모델 계약](corner515_model_contract.json) · [제어](corner515_control.py) · [도로/장애물 판정](corner515_model.py) · [모델 실행](corner515_preflight.py) · [순수 tests](test_corner515.py).

한 후보는 **다음80ms 제동이 현재·향후40m의 최저 참조속도 아래로 내려갈 것을 예측하면 brake만 줄이거나 해제**한다. nominal brake의4raw 예측 최저속도가 floor−0.15m/s 아래일 때만, end speed를 floor+0.002m/s로 역산한다. coast도 목표 아래이면 brake0이다. 자기 nominal의 gas/steering bits는 보존한다. source 응답·현재 지도만 쓰며 실제 미래 상태·접촉은 입력에 없다. 오차 allowance는 이전 제한 표본 근거이며 미관측 조건의 안전 보증이 아니다.

exact 수집 초기 상태와 관측 trigger stress 상태에서 reference/release 네 모델 궤적을 비교했다. 모델 gate는 같은 고정 window(첫 곡률 전이20m 전부터 코너 종료40m 후) 도달, full hull/wheel 도로 및 모든 장애물 circle clearance≥0.50m, 최대 양의 참조속도 오차≤5m/s였다. window/코너 exit/50m/s 회복 사건은20ms bracket과 보간을 기록했다.

native eligibility는 네 안전 gate 통과와 각 시작에서 다른 brake 결정≥1회, 그리고 window 이득≥0.08초 또는 window 비악화·회복시간 이득≥0.08초였다. 미달이면 추가 native를 하지 않기로 했다. 전체 단계 실제 상한은320actions/3resets/1433rawticks로 사용자800/3보다 작게 등록했고, 추가 짝 비교는 모델 통과 시2resets/160actions씩만 허용했다.

## 결과: 결정은 달라졌지만 큰 손실이 재현되지 않음

| exact 초기 상태의 모델 지표 | reference | release |
|---|---:|---:|
| window 통과시간 |2.191966s|2.180623s|
| 목표 floor보다0.5m/s 이상 낮은 제동 |0.020s|0s|
| 바뀐 brake holds |0|1|
| 코너 exit 속력 |32.960820m/s|33.051623m/s|
| exit부터50m/s 회복 |0.689298s|0.693178s|
| window 종료 속력 |55.310209m/s|55.285752m/s|
| 최소 hull/wheel 도로·장애물 여유 |0.990956m|0.988586m|

trigger stress에서도 window 이득0.011240초, 바뀐 brake1회, 목표 이하 제동 감소0.020초로 같았다. 네 궤적 모두 안전 gate를 통과했지만 **정보 gate는 둘 다 미달**했다. 후보의50m/s 절대 도달 시각은 약0.010초 앞섰으나 코너 exit도 더 빨라져 exit부터 회복시간은 약0.0039초 길었다. 이를 회복 개선으로 표시하지 않았다. 새로운 native 짝 비교·완주·13.640초 개선은 없다. 모델 곡선 응답의 native 정확성도 아직 인증하지 않았다.

[전체 모델 결과](corner515_model_result.json) · [전수 검증](corner515_summary.json).190개의 모델 action에서 common steering/gas와 후보 brake≤nominal을 전수 확인했다. 모든760plant rawticks의 sampled 여유≥0.50m를 대조했다. pure2tests는 projection/참조 계산과 예상 undershoot 시 brake만 바뀌는지 검사했다.

## 저장된 힘 분석과 다음 병목

[저장 분석](corner515_audit.py) · [힘 집계](corner515_force_audit.json). 별도 native나 새 궤적 없이 reference 모델 상태의880wheel force 평가를 수행했다. 사전 상한2000평가/CPU20/wall30초 이내다.

reference는 현재 코너 내부0.8초와 exit0.9초에서 이미 gas를 쓰고 brake는0이었다. corner force ratio 최대0.7324(reset)/0.7338(trigger), clipped wheel samples0/160이었다. 따라서499의 더 긴 목표 미만 제동 지속은 이번 현재 경로/참조에서 재현되지 않았다. 작은 제동 해제 보정을 반복할 이유가 부족하다.

다음 단일 가설은 **고정 곡률 속도 상한의 lateral budget80이 현재 경로에서 보수적인가**다. 같은 경로·조향·가감속 pass를 유지하고 예컨대 고정100으로 바꾼 한 후보를 모델에서 반증할 가치가 있다. force 여유만으로 그 속도가 feasible하다고 추정하거나 안전을 인증하지 않는다. 속도를 높이면 복합 타이어 힘, 경로 추종, 장애물 여유가 달라지므로 해당 후보의 자체 모델 gate가 먼저 필요하다. 이 후속 후보는 이번에 구현·실행하지 않았다. 방법군 전체의 불가능성이나 과거 기록 회수 가능성을 결론 내리지 않는다.

## 실제·모델 비용과 보존

실제 **world1/reset1/action0/raw51/closed1**, 연구 **25804**, 예비 **84000/used0** 불변이다. 모델 **1208integrator ticks=plant760+제동예측320+pure fixture128**, 별도 저장 wheel force 평가880회다. 수집·모델·힘 worker 합계CPU8.016855초/wall8.017827초이며 준비·마감 allowance5CPU/5wall를 별도 표시했다. 모델200000ticks/180CPU/240wall 및 전체360CPU/480wall 이내다. 대화·구현 전체 경과시간 실측으로 오해하지 않는다.

private16files/2,948,961B이며 지도·장애물·state·명령·trace를 공개하지 않았다. 수집 당시 원래 control은 private에 보존했고, 지도에서 장애물을 확인한 뒤 모델 전 공통 경로를 구성한 현재 control과 각 phase source/input SHA를 별도로 대조했다. 수집/모델 과학 재실행0이다. saved verification이 system Python의 Box2D 부재로 import 전에 실패해 지정 `.venv`로 복구했으며 이 오류의 새 model/native step은0이고 기록을 남겼다.

main dfb7a2de2178825ca5c5ce20bab01ba67052ba31, Participants·사용자 변경·기존 백업·앞선 실험은 보존했다. 지정 cloud만 사용하고 새 seed·보호 평가 조회0이다. 승인 종료는2026-10-20 19:01:55 KST다.
