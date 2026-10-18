# 512 — 제동거리 가설은 미판정: 공통 조향의 안전 실패로 선행 중단

**참조34actions 후 도로 여유 gate에서 중단했다. 후보 world는 생성하지 않았다.** 속도계획 이득·반증·짝 비교 성공·완주를 주장하지 않는다. 사전 계약의 안전 실패 시 pair 중단을 따랐으며 남은 예산으로 조향이나 판정 기준을 바꾸어 재실행하지 않았다.

## 499·500·501에서 선택한 가설 하나

[499](diagnostic499_result.md)은 과거13.640초에서11.99초까지1.65초 차이가 있으며 중반 진입 제동·속도계획을 검토할 근거를 제시했다. scalar clock 차이는 회수 가능한 시간의 증명이 아니었다. [500](envelope500_result.md)은 고정B=91.16873397261595m/s² envelope의 산술 feasible 인증이며 실제 타이어/휠 응답 인증이 아니다. [501](screen501_result.md)은 후보의 다음 명령에서 exactEMPTY_SET으로 멈췄고 직전 scalar 예측보다 model 속도가+0.847159m/s 높았다. 그 결과만으로 일정 감속 가정이 유일한 원인이라고 단정할 수는 없다. 유실501 raw는 복구하지 않았다.

[511](brake511_result.md)은 현재 source 응답의 짧은 속도목표 역산을 실제 wrapper에서 확인했지만 도달 시간·타일 진행률은 같았다. 이번 단일 가설은 **같은 다음 속도 제한에 대해 현재 휠/엔진/접촉 응답을 제동거리까지 예측하면 scalar 계획의 다음 상태 feasible 소실을 피할 수 있다**였다. pixel 추정 연구나 두 번째 깊은 연구선으로 확대하지 않았다.

## 실행 전 고정한 비교

[계약](plan512_contract.json) · [제어](plan512_control.py) · [실행](plan512_run.py) · [순수 tests](test_plan512.py).

510/511과 같은 검증된 DEV 초기 조건을 사용했다. 첫24 PixelAgent(adaptive) actions 이후 양쪽 모두24번째 steering을 유지하도록 했다. 현재 지도에서 첫 abs heading change>0.08rad 직전 마지막 직선 station을 gate로 정하고, 물리 목표30±0.5m/s·공유 planning node29.85m/s를 고정했다. 이는 코너 진입 전 종방향 진단 목표이며 해당 속도의 코너 타이어 안전성을 인증한 것은 아니다.

참조는500의 exact scalar envelope와 float32 pedal 인증을 그대로 사용한다. 후보는 현재 state/map에서 한4tick action 뒤 최대 brake를 이어가는 응답을 예측해29.85m/s까지 필요한 거리를 계산한다. 페달 범위는 둘 다 gas≤1, brake≤float32(0.3)이며 미래 실측 상태·접촉은 입력에 없다. 모델의 가속 확장은 source 엔진 update·후륜 gas ramp를 순서대로 추가했다. 첫 feasible coarse bracket과18 bisections만 사용하며 global optimality를 주장하지 않는다.

후보가 안전하게 gate 속도 범위에 도달하고 참조 PLAN_STOP/과속을 피하거나, 둘 다 통과할 경우 **참조 crossing 시간 하한−후보 상한≥0.08초**여야 실질적 효과로 승격하기로 했다. 작은 속도 오차 개선만으로는 통과하지 않는다. crossing은20ms raw bracket과 선형 보간을 함께 기록하도록 했다. 최대400actions/2resets/1702rawticks(reset102 포함), 가상 model200000ticks, CPU180/wall240초, private64MiB/3000files였다. safety/technical 실패 시 pair를 중단하고 scalar 수학적 PLAN_STOP만 후보 reset을 허용했다.

## 실제 관측과 실패 원인 범위

기존 DEV geometry/obstacle/body/RNG/pixel 초기 identity와 첫24action·관측 prefix는 일치했다. **두 번째 world가 없으므로 paired initial/trigger identity는 확인하지 않았다.** 원시 result의 scalar `trigger_identity=true`는 첫 arm의 trigger snapshot 수집을 뜻하며 두 arm 일치 증거로 읽지 않는다.

| 실제 참조 결과 | 값 |
|---|---:|
| 실제 actions / 제동 actions |34 / 4|
| 첫 제동 action |31|
| 첫 여유 위반 |action34, sampled margin0.108984m|
| 그때 gate까지 거리 |6.368648m|
| wrapper 종료 시 gate까지 거리 |5.517446m|
| 횡방향 중심선 오차, trigger→종료 |0.418080→4.944964m|
| raw 물리 속도 예측 최대 절대 오차 |0.000116419m/s|
| 후보 실제 actions / resets |0 / 0|

지도 중심선이 직선이라는 검사만 통과시키고 작은 pixel steering을 계속 유지한 선택이 충분하지 않았다. 고정한 비영점 steering이 고속 접근 동안 횡방향 이탈을 누적시켰다. 전체 hull/wheel sampled margin이 action34의 세 번째 raw 경계에서0.25m 아래로 내려갔고, wrapper4tick hold를 끝낸 뒤 추가 action 없이 멈췄다. raw 두 행에 ROAD_MARGIN이 있으며 다른 source/payload/friction/effect/prediction 오류는0이다. margin은 샘플 검사이며 연속 충돌 방지 보증이 아니다.

이번 참조에서는 scalarEMPTY_SET이 재현되지 않았다. 실제−scalar 요청속도 차이는−0.579936..−0.004407m/s, 제동 holds만 보면−0.269421..−0.004407m/s로501의 양의 surrogate 잔차와 방향도 다르다. 작은 실제 명령 예측 오차는 source 응답 모델의 이 구간 calibration 근거이지만, 실행하지 않은 후보의 거리계획 정확도나 시간 이득을 대신하지 않는다. 가설은 **정보 부족으로 미판정**, 이번 benchmark 구성은 선행 안전 gate 탈락이다. gate crossing·공식 finish 모두 없으며 과거13.640초와 직접 개선 수치로 비교하지 않는다.

## 비용·보존·다음 조치

[실행 집계](plan512_result.json) · [저장 자료 전수 검증](plan512_summary.json). actual34actions/1reset,187rawticks=reset51+actions136을 전수 대조했다. 호출 전 immutable charge34개가 연속이며 연구 잔액은 **25909→25875**, reserve84000/used0이다. 생성한1world는 body/joint0으로 닫혔다. controller/검증용 가상 model136ticks를 썼고, 실행 비용은 child test 포함CPU2.382424s/wall2.394995s였다. 이는 성공 worker 비용이며 구현·별도 순수 tests·사후 읽기까지 포함한 세션 전체 실측은 아니다. private266files/1,682,536B이며 state/map/명령/trace는 공개하지 않았다. 보호 평가·새 seed·추가 검증 world는0이다.

순수4tests는 무가스 기존508 예측과 exact 일치, source 엔진/후륜 ramp, 제약 없는 두 법칙 호출, gate 산출/비용 범위를 확인했다. 최초 synthetic fixture는 코너를 half-loop search 밖에 놓아 실패했고 return leg를 추가해 fixture만 수정했다. 원본·실패 설명은 private에 보존했으며 당시 world0이었다.

다음 우선 작업은 pixel 추정이나 제동 gain 조정이 아니다. **공유 map 기반 직선 centering/heading 참조가 측정 지점까지 안전한지 저장 상태의 모델 예측에서 먼저 확인**해야 종방향 비교가 의미를 갖는다. 이번512의 동결 참조를 사후 교체하지 않았고 남은366actions/1reset을 새 짝 비교로 간주하지 않았다. 유효한 공통 참조가 마련되기 전에는 응답 후보를 승격하지 않는다. 승인 종료2026-10-20 19:01:55 KST와 기존 main/Participants/사용자 변경/백업 보존 조건을 유지한다.
