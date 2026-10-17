# 465 — 동일 첫 pulse 뒤 지속 S13은 승격 기준 미통과

**PulseOnce와 S13 모두 독립2회 H13·held 첫 전이를 통과했지만, S13의 추가 진행 이득은 없었다.** root+60m raw20ms 통과 bracket은 양쪽[0.70,0.72]초로 겹쳐 PulseOnce−S13 차이는[−0.02,+0.02]초다. 동일1.04초 종료 진행은 S13이3.680588m 적었다. 사전 strict 양의 통과 bracket·종료 진행 이득 조건을 모두 충족하지 못했으므로 승격하지 않는다. actual/reset0이며 전체 lap 이득·새 native 기록을 만들지 않는다.

|새 모델 H13, 동일root·동일첫fullgas|PulseOnce|S13|
|---|---:|---:|
|root+60m 통과|0.70–0.72초|0.70–0.72초|
|1.04초 진행 거리|87.795862m|84.115274m|
|종료 속도|70.341335m/s|60.388108m/s|
|자기 종료위치 reference 대비 속도|+2.373264m/s|−7.959090m/s|
|제동 행동/13|4|5|
|최대 경로오차|1.178062m|1.155208m|
|최대 절대 yaw|1.742083rad/s|1.717345rad/s|
|평균 절대 tyre lateral slip|1.461725m/s|1.410108m/s|
|preclip force/friction 최대비|1.158361|1.066747|
|clipped wheel samples/208|7|4|
|clipped raw ticks/52|6|4|

종료위치가 달라 reference 오차를 같은 공간 점의 성적으로 비교하지 않는다. 두 trajectory 모두13×80ms를 그대로 유지했고 steering 정책은 같지만 상태에 따른 steering/횡력은 달랐다. S13은 진행·속도를 더 잃는 대신 경로·yaw·slip·clipping 노출이 조금 줄었다. clipping은 적용된 힘이 물리 한계를 초과했다는 뜻이 아니다. 최초 fullgas의0.220초 효과를 지속 secant 법칙의 효과로 다시 세지 않았다.

## 늦은 감속 부채와 해석 범위

H13 밖을 추가 적분하지 않았다. 각 종료 상태에서 앞으로 남은 reference node 중 현재속도보다 낮은 node에 대해 `B_req=(v_end²−r_node²)/(2*distance)`와 기존 상수B로의 거리 여유를 저장 계산했다. PulseOnce의 최대B_req/B는1.958533, 최소 여유−0.599776m, S13은0.038533/+112.024991m였다. 각각 현재속도·종료위치·대상 lower node 집합이 다른 **1차원 점질량 proxy**다. B가 보수 근사이고 tyre 결합·gas/omega·조향·현재/미래 경로를 정확히 풀지 않으므로 PulseOnce의 실제 미래 불가능성이나 S13의 미래 안전을 증명하지 않는다. 더 느린 S13에 감속 부담이 적다는 trade-off를 보여주며 이를 lap 시간으로 환산하지 않는다.

이번 결과는 이 fixed root의 첫13행동에서 단발 pulse보다 지속 secant가 추가로 좋아진다는 승격 가설을 지지하지 않는다. H2B 전체·다른 sustained law·H2A의 reference/힘/경로 가설을 소진하거나 반증했다고 확대하지 않는다. 기존 최선442P13.760초와463의13.780초·실제0.220초 이득/모델 부합을 보존했다.

## 선행 gate·정책·factual 경계

[464 계약](design464_next.md)·[JSON](design464_next.json)을 변경하지 않고 같은pre126 root를 사용했다. 첫 명령의 전체 float32 fullgas alias를 양쪽에서 요구했다. PulseOnce는 이후 기존 nominal, S13은 매80ms 경계의 자기 현재 상태에서 일반 secant를 재계산했다. nominal C.act는 한 번만 전진하고 prepared_before/prepared_nominal을 함께 전달해 observer 내부 추가 act0회와 memory_before/after를 검증했다. first recipe만 바뀐 old shadow를 반복 정책 증명으로 쓰지 않았다. 새 비교의 guardian selector·ranking·추가tail·root검색0이며, 기존 qualification의 pending/parent 보조 적분은 비용에 포함했다.

constructor/step/native를 금지한 통합277개와 저장 audit가 모두 통과했다. 코드·gate는ef1e55b로 먼저 commit/push하고 원격SHA를 확인했다. fresh 기존 source/current/pending/parent는1137ticks/35worlds로 통과했다. 그 뒤 PulseOnce H13 독립2+held_first(108/3), 이어 S13도108/3을 사용했다. 총 **1353ticks/41worlds**, reserved1353, observer post1353개/stream41개가 일치했다. 과학 비교와 자격 검사에 바로 같은 네 H13 trajectory를 사용해 별도 main을 반복하지 않았다.

PulseOnce의13행동 physical/geometry/ledger calibration과 첫 current exact 검증은 통과했다. 다만 저장463과 bitwise 같은 명령 prefix는2행동이고3번째부터 갈라졌다.13행동을 전부 fresh current 또는 동일 명령 native factual 자격으로 확장하지 않았다. S13은 첫 명령만 native counterpart를 가지며 이후는 모델 일관성이다. 두 arm의 독립 signature exact·held 첫 전이·원래 root state/memory/read-only Actual GoalLedger/RNG 불변을 확인했다. 허용 오차나 raw 안전/진행/정의역 기준을 완화하지 않았다.

## 비용·보존·종료

planned 최대1458/41, hard2048/64를 별도로 강제했고 whole CPU180초/wall300초를 유지했다. 실제 worker **CPU35.233559초/wall36.693448초**이며 import·source확인·qualification·제어·physics/observer·snapshot/proof/hash/IO·cleanup을 포함했다. 정적23.679/23.606초, 저장 감사5.087/5.323초, private 보존1.586/1.599초는 별도다. 개발·보고·Git 전체 overhead 완전 계측이나 순수 solver 시간이라고 부르지 않는다.

시작 직전 source manifest 증가841B를 읽고 world고정769473B에 증가분3배+16KiB/world를 더했다. 새 full plan1666720B·raw metadata16MiB도 별도 잡았다. 최신85798.438265B/tick·25%·각512MiB reserve를 포함한 모델 요구807282430B/workspace869544734B가 당시 free3667374080B/921288704B 안에 들어갔다. worker 시작 직전에도 free를 재검사했다. 등록 scope와 hard headroom을 다른 실험에 쓰지 않았다.

새 raw319파일124327291B를 /tmp에 그대로 두고, workspace private archive15095687B의 모든 member와 원본 SHA256을 검증했다. 전체 raw×1.1+32MiB+512MiB reserve의 보존 사전 검사와 쓰기별 reserve 검사를 통과했다. 기존·새 원본 삭제/이동0, 별도 환경·유료 자원0이다. 이번 raw/tick은 약91890.089B로 더 높으므로 다음 비용에 이전 비율을 자동 재사용하지 않는다. [보존 집계](compare465_retention.json)와 [입력 hash](compare465_inputs.json)를 제공한다. full private plan은 workspace에도 있고 개인 자료/seed/RNG/좌표/명령 벡터는 공개하지 않았다. /tmp 공유·영속성은 가정하지 않는다.

PID181610은2026-10-17 20:44:32 KST에 exit0으로 종료했다. [최종 checkpoint](compare465_progress.json)와 [집계 JSON](compare465_result.json)에 실제 단계를 남겼다. v475와 보호18파일·원본/백업·main dfb7a2de2178825ca5c5ce20bab01ba67052ba31·Participants·기존 사용자 변경을 보존했고 장부 추가 차감0, 연구26346·예비84000/사용0이다. 정적 이후 저장 감사 도구의 보호파일 합산과 factual 범위 표기만 보완했으며 동결 실행 코드/적분을 수정·재시도하지 않았다. 전체 guarded 실험의 현재 공간 부족은 기술 실패로 처리하지 않았다. 이 작은 시험 밖의 후속 실행0이며 최신 종료2026-10-20 19:01:55 KST 이후 새 실험·자동 연장 없음이다.
