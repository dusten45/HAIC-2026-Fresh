# 450 — 첫 제동·재가속 이후 고정+270m 모델 비교

**원래 pre23 root부터 +270m까지 누적 이득 [0.40,0.44]초가 남았다.** baseline은 [4.40,4.42]초, candidate는 [3.98,4.00]초다. 첫 큰 제동과 재가속을 통과한 이 유한 모델 구간에서 단발 pulse의 시간 이득이 소멸하지 않았다. native +270m·전체 lap·11초대·픽셀 정책 개선의 증거로 승격하지 않는다. 이 결과의 범위는 고정 root의 H1 한 가설이며 다른 방법군의 가능성을 판정하지 않는다.

## 선행 게이트와 동일-child 실행

원래 native448 두 실제 wrapper-end state·memory·관측 GoalLedger·보존 RNG를 그대로 복원했다. global RNG는 native 종료 해시와 대조한 원래 상태이며 새 seed는 없다. 최초 source/code/권한·원장v469와 root·+270m·own nominal·64행동·허용 오차·중단 규칙을 동결했다. 기존 main·보호 파일 hash도 대조했다.

정적 **220개**와 저장 감사가 첫 시도에 통과했다. baseline H13은 각 독립 사본에서 factual442의 해당13행동에 대해 기존439 물리·기하/goal/clock/deadline gate와 정확 fresh-current 첫 전이를 통과했다. 그 자리의 **같은 child/world/stream**에 H13 snapshot·memory·RNG·ForecastLedger·prefix digest·boundary key를 봉인하고 총64행동 이내로 이어 실행했다. 매 tail 행동 전후에 객체 동일성과 봉인을 확인했다. 모델 +90m endpoint를 다시 복원하지 않았다.

baseline의 전체36행동도 저장 factual442와 동일한 source 비교를 통과했고, baseline 독립2회·held 첫 전이까지 완료한 뒤에만 candidate를 시작했다. future replay의 memory drift는 fresh-current 일치로 소급 인증하지 않았다. candidate는 관측된 native root에서 시작한 모델 미래이며 새로운 native 미래 label은 없다.

| branch | initial H13/같은-child 추가 행동 | 행동/사본 | 새 모델 crossing ticks | 누적 시간 |
|---|---:|---:|---:|---:|
|nominal|13/23|36|140–141|4.40–4.42초|
|candidate|13/21|34|135–136|3.98–4.00초|

누적 시간은 native448의 전체 wrapper delta **80/64 ticks**에 새 모델 crossing bracket을 더해 계산했다. crossing 뒤 wrapper 잔여를 crossing 시간으로 반올림하거나 +60m/+90m의 불확실한 bracket을 다시 이어 붙이지 않았다. 두 branch 모두 그 crossing을 포함하는 wrapper 전체의 안전·진행 조건을 통과했다.

독립2회의 rows·최종 state·memory가 정확히 같았다. held의 state/memory/RNG 보존·자기 첫 명령/전이·정확 memory도 통과했다. 두 branch의 초기 짧은 prefix는449의6/5행동과 정확히 같았다. 같은-child H13 및 tail receipt의 child ID/key와 post/action 수를 저장 감사에서 대조했다. 최초 실행 오류·재시도·censor는 없었다. native solver 내부 warm-start의 동일성은 여전히 주장하지 않는다.

## 시간 변화와 출구 상태

+90m의 누적 이득 [0.36,0.40]초 대비 변화는 보수적으로 **[0.00,+0.08]초**다. 0을 포함하므로 엄격한 이득 증가를 입증하지 않았다. native +60m [0.34,0.38]초 대비는 이 mixed native/model 계산 아래 [0.02,+0.10]초다. 어느 것도 구간 이득끼리 가산한 lap 성적은 아니다.

| 공통+270m 양끝 body 표본 범위 | nominal | candidate |
|---|---:|---:|
|속력 m/s|61.086–61.770|59.423–60.070|
|yaw rad/s|1.48956–1.49059|1.42069–1.51858|
|path error m|0.08710–0.18052|0.05502–0.09949|
|절대 heading error rad|0.01415–0.05320|0.00668–0.03377|

candidate는 이 출구에서 더 느리지만 누적 시간 이득을 유지했다. path/heading 표본은 작고 yaw 범위는 겹친다. 모든 상태 일치를 진전 조건으로 요구하거나 차이 하나만으로 이득을 무효화하지 않았다. 반대로 더 낮은 출구 속력이 이후 재가속에서 시간을 소모할 가능성도 이 구간만으로 배제하지 않는다. **이후 terminal debt 해소는 미판정**이다.

## 타이어·actuator 비교

저장 자료의 공통 **원래 root+190..250m** 범위를 raw preclip phase로 맞췄다. factual 첫 제동192.3..239.1m를 포함하는 분석 구간이며 새 승격 허용 오차가 아니다.

| 공통 제동 구간 표본 | nominal | candidate |
|---|---:|---:|
|raw 경계/4-wheel 표본|45/180|44/176|
|클리핑 wheel 표본|5/180 (2.78%)|0/176|
|force ratio 최대|1.06896|0.97222|
|lateral slip m/s 범위|−0.05299..4.66256|−0.04820..4.24936|
|wheel joint angle rad 범위|−0.000551..0.195663|−0.000289..0.189530|
|wheel omega 범위|79.478..193.636|76.279..193.706|
|명령상 제동 raw 경계|32|32|
|명령상 fullgas raw 경계|1|2|

물리 wheel gas는 양쪽0..1, brake는0..0.3000000119였다. candidate의 해당 구간 clipping과 최대 lateral slip은 작았지만 longitudinal slip 범위는 −3.19694..4.60109로 nominal−2.98085..4.56322와 다르다. 한 지표만으로 모든 tyre 상태가 더 좋다고 결론내리지 않는다. 두 trajectory의 공간 통과 시간이 달라 표본 수는 같을 필요가 없다.

+270m lower crossing의 동일 preclip phase에서는 force ratio 최대 nominal0.97504/candidate0.91517, lateral slip1.76797..2.43969/1.63073..2.41796m/s였다. 출구 upper body 표본과 lower preclip force를 섞지 않았다. 분석 표본의 범위는 연속시간 보장 구간이 아니며 모델 내부 마찰 클리핑 자체를 새로운 안전 실패로 재정의하지 않았다. 자세한 gas/brake/joint/omega/slip 집계는 [결과 JSON](continuation450_result.json)에 있다.

## 비용·다음 최소 정책 구성 검증

새 비용은 nominal36×독립2×4=288, candidate34×2×4=272, held2×4=8로 **568 model ticks/6 worlds**, CPU **10.533초**/wall **10.574초**다. H13 부분208 + tail352 + held8이며, tail 태그는 양쪽 모두 recipe가 nominal이므로 합쳐 기록됐다. child별 observer로 branch 비용을 분리했다.6 stream posts568과 reserved568이 일치했다. planned1032/6·hard1152/8·CPU90초/wall150초·worker 순차1을 지켰고 live model world 최대2다.

정적 CPU17.795초/wall17.907초와 저장 감사 약0.840초는 별도다. 전체 준비·보고·Git·일부 import overhead는 완전 계측하지 않았다. 실제/reset·새 seed·학습·HOLDOUT/SEALED·예비·추가 유료 자원은0이다. 기존449/448 시간·비용은 재청구하지 않았다. v470 연구 잔여 **27,436**, 누적 실제 **1,320,628**, 예비 **84,000/사용0**이 유지된다. 마지막 모델 checkpoint는 **2026-10-17 16:35:34 KST**다.

의미 있는 첫 제동 이후 양의 이득이 남았으므로, 다음 작은 30m 성능 구간보다 **H1과 조건부 guardian B의 첫 개입·복귀가 올바르게 합성되는지**가 다음 질문이다. 기존 pre91 nominal unsafe witness와442 C0의91 neutral override는 nominal-only 전체 lap의 장애물로 남는다.445의 다른 root에서의 B 검증은 새 trajectory 전체를 보장하지 않는다.

다음 제안은 원래 native448 root에서 각 live model parent를 다시 +270m까지 own nominal로 재현한 뒤, **B 최대14 parent 행동**만 관측하는 정책 구성 gate다. 현재 MODEL parent의 ForecastLedger와 원래 immutable native GoalLedger를 분리하고, `bind_model_query445`의 current model 값 view·owner/state/memory/RNG/clock 검증을 사용한다. nominal H13 독립2회가 등록된 안전/진행 자격을 얻으면 nominal을 선택한다. 사전 지정한 대안 ineligibility에서만 neutral H13 독립2회를 평가하며, 선택된 명령은 자기 parent 전이와 fresh shadow 첫 전이를 기존 기준으로 검증한다.

첫 neutral 개입 뒤 nominal-safe 복귀 전이1회 또는14행동에서 끝낸다. 개입·복귀가 없으면 censor이며 trigger를 강제하거나 범위를 늘리지 않는다. 이는 서로 다른 개입 위치의 시간을 비교하는 성능 실험이 아니다. 기술/source/복원/ledger/memory/RNG/반복/fidelity 오류와 실제로 선택한 parent 안전 실패는 전체 중단한다. 예상된 비선택 대안의 ineligibility는 새 B 정책에서 명시적으로 정의해야 하며450의 own-nominal 오류 중단 규칙을 몰래 완화하지 않는다.

독립2회+held1회/branch를 유지하고 모두 +270m prefix를 live로 재현하면 worst required parent1248 + held520 + shadows11648 = **13,416 ticks/230 worlds**, hard14,336/256·CPU420초/wall600초·순차1·actual0 제안이다. source prefix는 이 안에 포함해 한 번만 청구한다. 이는 조건부 native 전체 lap 예시83,826 ticks의 약16% 상한으로 첫 fallback 구성만 검증하는 안이다. 모델 step 수에 비례한 CPU 외삽은 보장이 아니며 지정 cap에서 중단해야 한다.

B segment가 시작되면 이전 nominal-only TailRecord/Completion434를 수정된 tail의 ranking 증거로 재사용하지 못하도록 해야 한다. nominal +270m prefix를 따로 봉인하고 guarded query/parent-transition receipt를 별도 기록한다. 모델 값 view는 native 사실이나 DONE 권위가 아니다. 두 branch의 모든 terminal state가 일치할 필요는 없으며 exact independent repeat와 current-copy 검증은 유지한다.

이 finite gate가 통과하더라도 전체 정책의 pending/native DONE와 전체 trajectory 검증, 새로운 실제 pair의 비용·코드 동결은 남는다.11초대는 자기 공식 native finish로 직접 측정해야 하며450의0.40–0.44초를 기존 lap 이득과 더할 수 없다. [다음 제안](next450_design.json)은 **작성만 했고 실행·예약하지 않았다. 전체 lap 조건부 예시도 이번에 실행하지 않았다.**

유효 종료 **2026년10월20일19:01:55 KST**, main dfb7a2de2178825ca5c5ce20bab01ba67052ba31·Participants·보호 ZIP·기존 사용자 변경·backup을 보존했다. private state/seed/명령/RNG는 공개하지 않았다.

[실행/동일-child 경계](continuation450.py) · [정적 fixture](test_continuation450.py) · [저장 분석](analyze450.py).
