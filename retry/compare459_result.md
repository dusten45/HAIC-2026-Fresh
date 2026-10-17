# 459 — 저장된 네 native trace의 공간 경계 대조

**이번 단계는 저장 분석만 완료했다. 실제 행동·reset·모델 tick/world·학습·새 seed·HOLDOUT·SEALED 조회 모두0이다.** 442P 13.760초와458P 14.000초의0.240초 차이는 초기 pulse, planner 시작점, quota가 함께 달라진 관측 비교다. 명령 위치와 시간 차이를 인과효과로 등치하지 않는다. 11.990초 목표까지 남은1.770/2.010초의 원인을 규명했다고 주장하지 않는다.

## 같은 공간에서 어디에 차이가 생겼는가

공통으로 exact 같은 처음22행동 이후 pre23를 원점으로 쓴다. 아래는 native raw post의 첫 통과20ms bracket이며 보간하지 않는다. finish만 자기 official event의 단일 시각이다. 속도 경계 역시 인접 표본의 범위이지 연속시간 보장은 아니다.

|원점 대비m|442P|453 baseline|453 pulse|458P|
|---:|---:|---:|---:|---:|
|60|3.34–3.36|3.34–3.36|2.98–3.00|2.98–3.00|
|270|6.16–6.18|6.16–6.18|5.74–5.76|5.74–5.76|
|450|9.26–9.28|9.26–9.28|8.90–8.92|8.90–8.92|
|510|10.14–10.16|10.22–10.24|10.04–10.06|9.84–9.86|
|570|10.82–10.84|11.14–11.16|11.02–11.04|10.64–10.66|
|630|11.54–11.56|12.28–12.30|12.12–12.14|11.54–11.56|
|690|12.22–12.24|13.18–13.20|13.00–13.02|12.32–12.34|
|750|13.08–13.10|14.30–14.32|14.18–14.20|13.28–13.30|
|official finish|13.760|15.080|14.980|14.000|

458P는442P보다450m에서0.34–0.38초 빠르다. 그러나450–510에서0.02–0.10초,510–570에서0.08–0.16초,570–630에서0.14–0.22초 더 걸려630m에는 통과 bracket이 같다.630–690과690–750은 각각0.06–0.14초,750–finish는0.02–0.06초 더 걸린다.450–finish 전체의 추가 소요는0.58–0.62초다. 각 구간의 보수적 bracket 폭을 독립 오차처럼 합산하지 않는다.

453pulse→458P는 같은112행동 prefix에서 시작하는 별도 대비이며 official0.980초 개선이다. 458C0 전체 trace가453pulse와 exact 같음을 확인했다. 이 비교를453baseline→pulse 또는442P→458P와 합산해 새 causal 성적을 만들지 않는다.

## 실제 recipe와 guardian 반응

- 442P:118행동 prefix 후 planner54회, 그중 fullgas119/121/129/132가 원점+460.796/470.837/517.876/539.132m에 있다. 나머지50회 nominal, 이후 guardian nominal1회다. prefix의91행동은453baseline의 neutral 개입과 같은 위치다.
- 453baseline/pulse:22행동 공통 prefix, pulse만23행동 fullgas. 각자 nominal로+270m까지 간 뒤 conditional guardian이다. neutral은 각각91/86행동, +326.897/+327.367m다. 앞선454의 저장 receipt 감사에서 nominal shadow의 `path_error_over3m` 거절로 확인했으며, 이번 분석은 이를 새 물리 검증으로 세지 않는다.
- 458P:453pulse112행동 prefix 후 planner8회다.113/114는 fullgas(+453.716/+458.660m),115는 neutralbrake(+463.691m), 나머지5회 nominal이다. 이후56회 guardian nominal이며 suffix guardian neutral은 없다. planner neutral과 guardian neutral의 권위를 구분한다.

따라서 quota8 이후 guardian가 계속 nominal을 선택한 사실은 관측됐으나, quota를 늘리면 빨라진다는 결론은 나오지 않는다.442P는 더 늦게 시작해 다른 상태에서54회 평가했다.

## 실제 적용 식과 구조 가설의 관측 근거

`retry/signed417_executor.py`의 FIRST_LAP 식과 `paired417_common.policy`의 frozen268 pace 적용을 사용했다. `nodes=free_profile.speed*frozen268`, `r=sqrt((1-u)*nodes[j]^2+u*nodes[j+1]^2)`, `f=(nodes[j+1]^2-nodes[j]^2)/(2*ds[j])`, `sigma=velocity·tangent`이며,

`raw_accel=f*sigma/r + 1.5*(r-speed)`

이다. 이를 기존 clipping/pedal map에 넣으면 네 trace의720개 FIRST_LAP nominal pedal이 float32로 exact 일치한다. LAUNCH4개와 FINISH_CONFIRM2개는 해당 일반식 감사에서 제외했다. 선택된 fullgas/neutral 명령 자체를 nominal 식으로 설명하지 않는다.

458P의450–510/510–570/570–630 구간에서 실제 brake 노출은0.14/0.16/0.32초다. 같은 구간에서 **명목** 식이 target 미만 속도에도 braking을 요구한 표본 노출은0.30/0.16/0.32초다.442P는 실제0.16/0.08/0.24초, 명목0.24/0.24/0.16초다. planner가 nominal을 override하므로 두 노출이 같을 필요가 없다.450–510의 평균 속도는442P68.56,458P64.20m/s;510–570은87.15 대74.49,570–630은82.77 대66.50이다.

이 세 구간의 progress/speed 비 평균은442P0.996–0.998,458P0.991–0.999로 거의 전진한다. grass 표본은 두 arm 모두0이다. 바퀴 하나 이상 force clipping 노출은450–510에서0.38/0.42초,510–570에서0.02/0.04초,570–630에서둘다0이다.690–750은442P가 더 빠르지만 경로오차 최대2.772m로458P1.251m보다 크다. 따라서 단순히 경로오차가 더 큰 쪽이 느리다거나 clipping이 전체 시간손실의 원인이라고 단정할 근거는 없다.

평균 preaction feed/feedback과 raw20ms 속도 변화율도 JSON에 남겼다. 이들은 다른 상태와 명령 이력을 가진 표본 평균이다. pedal 요구 가속도와 실제 body 가속도의 차이를 즉시 actuator 식별값이나 안전한 가속도 상한으로 사용하지 않는다.

## 최대 두 가설과 반증 순서

**H1 — 초기 pulse의 이득이 동일 후반 정책에서도 유지되는가.** 현재0.24초 역전은 quota·시작 위치와 섞여 있다. 두453 저장 prefix 각각의 첫 pre≥450m에서 같은419 quota8→guardian를 적용하고 prefix 경과시간을 포함한 hybrid 총시간을 비교한다. 이것이 다음 한 실험이다. 부호가 반대이면 공통 후반 정책에서 pulse의 이득 가설은 반박된다. 겹치면 미해결이다. 전체 native 시간의 인과효과로 확대하지 않는다.

**H2 — 남은 격차에는 reference/추종/경로 구조의 손실이 있는가.** 정확히 재구성된 식에는 음의 feed가 양의 feedback보다 커 target 미만에서도 braking이 나오는 구간이 있다. 이는 reference를 추종하는 정상 결과일 수도 있다. 느린 구간에서 해당 노출·입력포화·경로진행 손실이 없거나 작으면 그 설명을 약화한다. 이번 자료는 국소 reference-demand 감사 필요성을 지지하지만1.77–2.01초 전부를 설명하지 않는다. 향후에는 속도 envelope의 상한과 추종 target의 의미, sampled tracking/유한 actuator 응답/경로 곡률을 분리해 단일 변경을 고른다. quota·pace·gain 일괄 상향은 이 가설의 검사가 아니다.

방법론 연결은 기존 고정 검토문 `3e584dff988f0b90fce3dd563b7f6351a13d21f8:retry/static_control_audit_20261016.md`의49–55,69–77,89행 범위와 현재 구현 식에 한정한다. chain rule 수정은 순간 추종식이지 미래 제약 보장이 아니며, envelope/target·profile/tracker/path를 분리하고 저장 반증부터 시작한다는 원칙이다. 원논문 전체를 새로 읽었다거나 다른 방법 전체가 실패했다고 주장하지 않는다.

## 재현과 비용

`python -m retry.analyze459 PRIVATE_ROOT retry/compare459_result.json`은 기존 trace/rawpost만 읽고 순수 projection을 수행한다. private 입력738개 SHA256 manifest와 CPU/wall은 private stage459에 둔다. 이번 측정은 CPU6.234초/wall6.248초이며 physics 비용이 아니다. raw tick 간격20ms, post 개수, unwrap progress, 공통prefix,458C0 동일성, nominal 식 exact 일치 검사를 통과했고 독립 재실행의 공개 JSON이 byte-for-byte 일치했다. 공개 JSON은 공간·시간·제어 요약만 포함한다. raw 위치·명령벡터·state·seed·RNG·개인 자료는 올리지 않는다.

연구 잔여26,695, 최종 예비84,000/사용0은 v474 그대로다. 다음 실험은 [design459_next.md](design459_next.md)에 동결했으며 아직 실행하지 않았다. 종료2026-10-20 19:01:55 KST 이후 새 실험·자동 연장은 없다.
