# 419 — 상태 기반 세 recipe와 C continuation witness

이 단계는 **적분 backend 없는 순수 planner protocol·정적 테스트**다. signed417 C와 기존411 guardian을 기준으로 현재 nominal, 첫 nominal 조향+gas1/brake0 후 C, 첫 고정 neutral `[0,0,float32(.3)]` 후 C만 고려한다. 새 조향·pedal 크기·gain·경로 최적화는 없다. 실행 제어·296는 바꾸지 않는다. 417의 보장0.08초 미달은 그대로다.

## 현재 상태 질의와 memory 계약

모든 현재 decision boundary에서 phase·현재 projection·r>0·유한성·현재 안전·진행 ledger·restore·비용을 먼저 검사한다. FIRST_LAP의 적격 상태이면 현재 guardian을 질의하고 비용이 허용할 때 **서로 다른 세 첫 명령 모두**를 비교한다. 현재 nominal이 full-gas와 이미 같으면 동일한 recipe를 중복 적분하지 않는다. 조건은 현재 상태·법칙·budget에만 의존하며 absolute 행동 번호·arc 구간·seed를 트리거로 사용하지 않는다. original arc는 진행/remaining path/같은 위치 진단에 필요하지만 구간별 활성화 기준으로 쓰지 않는다. 테스트 root의 기존418 pre119는 이미 보정한 fixture 선택이며 배포 트리거가 아니다.

C nominal을 현재 부모에서 한 번 계산한 후, 그 **계산 직전 memory**와 현재 physical/finish/wrapper state·RNG를 독립 child에 준다. 부모는 nominal 계산 뒤의 실제 memory를 유지한다. child의 end memory를 부모에 덮어쓰지 않는다. root state/memory/RNG/clock와 actual-goal ledger digest·policy/path/조건 digest가 같은 receipt만 받는다. stale·다른 부모·미래 actual·다른 controller의 증거를 거부한다. JSON bytes에 현재 입력을 고정하고 child마다 새 복사본을 만든다. future trace·다음 actual state·lap 결과는 현재 입력 통로에서 금지한다. 미래 source 예측은 별도 evidence 통로이며 actual ledger를 갱신하지 않는다.

## 안전과 시간 선택

guardian의 baseline은 현재 nominal13이 적격이면 nominal, 아니면 기존 neutral-brake13이다. 둘 다 부적격이면 gas가 빠르게 나와도 중단한다. 복원·독립 반복·부모/RNG·수치 fidelity 실패는 기술 중단이다. 안전/진행을 위반한 recipe는 실행 후보에서 제외한다. q>1 자체를 거부하지 않고 기존 force clipping·도로/grass·충돌·손상·raw/post3m·의미 있는 후진·진행 조건을 유지한다.

초기13행동은 같은 root에서 평가하고 실제 현재3.24m goal과13행동 deadline을 유지한다. actual goal은 실제 행동을 commit한 관측이 도달했을 때만 갱신한다. forecast의 도달로 goal을 앞으로 밀지 않는다. deadline 이전의 계속된 작은 진행만으로 갱신하지 않는다. 원래 arc+30m의13행동 exit bracket은 진단으로 남긴다. 그 exit를 못 갔거나 느리다는 이유만으로 장기적으로 유리할 수 있는 neutral recipe를 자동 탈락시키지 않는다.

**유일한 후속 비용 방법은 더 긴 C nominal continuation witness**다. 적격13행동의 각 child를 같은 world·memory에서 그대로 C nominal로 이어 공식 finish 또는 첫 안전·진행·domain·비용 실패까지 본다. computational cap은 추가308행동(기존411 상한), 검사는13행동 이하의 연속 block으로 나눈다. 임의 terminal weight나 `남은 거리/속도` 보간은 없다. speed·yaw·path error·wheel omega/gas/joint·slip·마지막 적용 force와 contact·remaining path가 들어 있는 **전체 동역학 상태**를 이어 쓴다. 요약 벡터는 검사/기록용이지 low-dimensional 재시작 상태나 가중 점수가 아니다. last raw tire force의 preclip/preworld phase도 post hull과 구분한다.

모든 적격 recipe의 tail을 확인한다. baseline과 대안이 같은 root에서 공식 finish까지 모델상 적격일 때, 원래 raw50Hz의 finish bracket을 비교한다. 대안 upper가 baseline lower보다 **엄격히 작으면** 보장 양의 이득이다. 0.08초를 보편 기준으로 재사용하지 않는다. bracket overlap·접촉은 보장 이득이 없어 baseline을 유지한다. 여러 대안이 baseline을 지배하면 finish upper가 가장 작은 것을 택하고, 동률은 lower와 고정 recipe 순서로 결정한다. 유한 recipe 집합의 보수적 선택이며 전역 최적성은 아니다. local exit가 느린 neutral도 finish가 더 좋으면 선택할 수 있다.

finish는 실제 tracker의 qualified official event다. source raw tick으로 event를 포함한 bracket을 만들며 초기13행동과 tail 시간을 **같은 root부터 합산**한다. 초기13 이전에 정상 partial terminal(1–4raw tick)이 나오면 그 공식 finish로 끝낸다. qualification/candidate crossing만으로 finish로 세지 않는다. tail 미완료·안전 실패·비용 검열에는 finish 점수 자체를 주지 않는다. 미관측 tail·failed arm 시간을 추정하지 않는다. 412의10.027초 profile 시계나 조건부 회수율은 이 score 통로에 넣지 않는다.

## 13행동 자격의 한계

긴 continuation은 **모델상 feasible한 C nominal witness**이며,13행동 실제 자격을 긴 horizon으로 확장한 것이 아니다. 각13행동 checkpoint에서 state/domain/safety/progress·반복·복원을 확인해도 미래 counterfactual의 실제 fidelity는 미확인이다. planner 출력은 `MODEL_TIME_CHOICE` 같은 제안이며 actuator·실제 실행 허가는 없다. `long_tail_physics_qualified`를 자동 True로 만들지 않는다.

continuation 안에 guardian의 재귀13행동 예측까지 매번 중첩하지 않는다. 이는 비용을 제한하는 보수적 nominal-C witness다. nominal tail이 안전/진행을 실패하면 guardian이 나중에 구해줄 수 있다고 가정하지 않고 그 witness를 버린다. 실제 guardian이 후속 명령을 바꾸면 witness의 exact-policy 예측은 끊어지고 실제 정책 결과와 따로 기록해야 한다. witness가 끝나지 않은 baseline에는 장기 시간 순위를 선언하지 않는다. 현재 guardian13만 적격인 경우의 baseline reference는 기존 정책을 가리키는 것이지 새 안전 fallback 인증이 아니다.

## 보류·실패 동작

- 정지·미소 signed sigma: r>0이면 식을 그대로 유지하고 같은 질의를 할 수 있다. restart 안전을 검증한 것으로 해석하지 않는다. sigma/bodyforward<−0.1의 기존 의미 있는 후진 중단을 유지한다.
- r=0 FIRST_LAP: positive-target domain 중단. LAUNCH/STOP/FINISH_CONFIRM은 기존 phase만 위임하며 새 fallback을 만들지 않는다. DONE official finish에는 새 명령이 없다.
- 정확 vertex의 기존 projection 거부: epsilon/tie 수리 없이 중단한다. COM velocity와 origin projection의 기존 의미도 바꾸지 않는다.
- 복원/부모/반복/fidelity 실패: 전체 질의 중단. 현재 guardian 둘 다 불가: 중단. 비용이 optional tail에는 부족해도 현재 guardian 검증을 끝낼 수 있으면 optimization 없이 그 reference만 반환한다. guardian조차 못 끝내면 비용 중단이며 검증된 제동 명령을 발명하지 않는다.

## 필수 질의·중복 자격·비용 제안

서로 다른 세 recipe의 필수 stage13은156tick/3world다. 같은 child를 이어 추가308행동까지 보면 최대3852tick/3world다. 연구 자격용 독립 반복을 모두 한 번 더 하면 **추가3852tick/3world**, 총7704tick/6world다. 첫13을 별도 재적분한 뒤 tail에 또 더하지 않는다. child를 유지할 수 없으면 checkpoint cold restore 자격·추가 비용을 다시 등록해야 하며 따로 세지 않는 shortcut을 허용하지 않는다. 동일 명령 dedup와 root/memory/RNG/clock가 정확히 같은 증거만 cache할 수 있다. 가까운 상태의 cached suffix를 현재 것처럼 쓰지 않는다.

418의26 query 실측은2808tick/54world, model CPU7.479초/wall7.558초였다. nominal 중복만 있는 보통 query는104tick이고 B 첫 gas 추가 query는208tick이다. query별 tick/CPU 비율의 관측 최대를 계산해 다음 cap 제안의 근거로 쓴다. 이는 경험적 비용 envelope이지 새 상태·긴 tail의 증명된 시간 상한이 아니다. 실제 backend는 tick/world/CPU/wall hard cap과 미완료 중단을 별도로 지켜야 한다. real-time80ms 이내를 주장하지 않는다.

## 다음 최소 실험 제안 — 미실행·미예약

먼저 기존418 actual fork의 같은 root에서 C0와 이 planner를 **모델 폐루프로3개 실제 상태 갱신 decision**만 비교한다. 매 decision은 현재 상태에서 다시 질의하며 절대119를 정책에 넣지 않는다. 이후 둘 다 같은 nominal C witness로 공식 finish/실패/cap까지 잇는다. 따라서 첫 짧은 exit만 비교하지 않고 실제 모델 내 다음 상태 및 장기 상쇄를 확인한다. 3은 이 bounded pilot의 계산 한도이고 배포 트리거·새 control horizon이 아니다. recipe horizon13은 그대로다.

planner3회×7704=23112tick, baseline guardian3회 최악624tick, 두 부모의3행동24tick, 두 마지막 C tail2464tick으로26224tick이다. root/현재 nominal·parent/복원 보정 gate 여유를 포함한 다음 모델 제안 cap은 **32768tick/64world/CPU150초/wall240초·동시1개**다. branch duplicate와 essential query를 분리 보고한다. 기존13행동 실제 자격 구간에서 먼저 body·wheel·raw hull을 대조하고, 새 모델 상태·더 긴 tail을 실제 자격으로 표시하지 않는다. 첫 restore/fidelity/parent/domain/비용 실패 또는 baseline guardian 불가에서 pilot을 중단한다. candidate unsafe/censored time은 점수에서 제외한다.

둘 다 model official finish·안전·진행을 충족하고 planner finish bracket이 baseline을 엄격히 지배하며 child/실제-model 부모 전이가 일치할 때만 다음 **actual 보정 대조**를 제안한다. 같은 history118+suffix13의 A/B 각1회(262wrapper/reset2, 상한400/reset2), planner는 첫3개의 현재 상태 decision에만 사용하고 이후10개는 기존 C0 guardian으로 끝내는 pilot이다. 실제 모델 query는 별도32768tick/128world/CPU150/wall240 상한 제안, actual은 모델 구간을 뺀 CPU90/wall180이다. 실제의 모델 world는 planner3회18world와 A13+B의나머지10 guardian이각각neutral fallback까지4world를쓸최악92world, gate여유를포함해128로잡았다. 새 조합의 첫 변경 전이·clipping·일치 recipe 구간 fidelity가 필수이며 guardian divergence 이후는 실제 정책 결과로 분리한다. 이 실제13행동도 full tail의 실제 성능 승격이 아니라 보정이다. 전체 실제 carry/독립 DEV/296 승격은 별도 단계다.

지금은 어떤 모델/actual/학습 자원도 실행·예약하지 않는다. 제안의 CPU·world 여유가 충분한지는 다음 등록 전에 실측 계측기로 재확인해야 한다. 419의 정적 CPU60초/wall120초·동시1개, 연구29,618·예비84,000·296·보호 자료·기한을 유지한다.
