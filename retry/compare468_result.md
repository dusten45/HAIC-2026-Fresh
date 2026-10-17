# 468 — 공통 첫 fullgas 이후 Projected4 reference, 작은 반증 통과

**동결한 같은 pre126에서 한 번만 실행했고 모델 내 승격 기준을 통과했다. actual/native 승격·새 root·추가 tail은0이다.** 양쪽 모두 기존 point derivative FF·feedback1.5·80ms hold·line/steering/pedal map을 유지했다. 첫 fullgas 전체 벡터와 첫 전이 frame은 완전히 같고, 이후 immutable reference nodes와 그 point derivative만 달라진다. 467 gzip adapter는 사용하지 않았다. 11초대 native 목표를 달성했다는 결과는 아니다.

| 검증·관측 | Original reference | Projected4 reference |
|---|---:|---:|
| root+60m 첫 crossing bracket | [0.70,0.72]초 | [0.64,0.66]초 |
| 1.04초 진행 | 87.795862m | 90.029085m |
| 종료 속도 | 70.341335m/s | 62.433743m/s |
| 종료 속도−각자 target | +2.373264m/s | −4.887949m/s |
| 종료 속도−공통 원래 reference | +2.373264m/s | −7.908006m/s |
| 공통 원래 reference 감속부채 proxy 최대/B | 1.958533 | 0.053052 |
| 공통 원래 reference 최소 braking 거리 여유 | −0.599776m | +104.733248m |
| 최대 요구 force ratio | 1.158361 | 1.066747 |
| clipped wheel samples /208 | 7 | 5 |
| brake 명령 /13 | 4 | 5 |
| 최대 경로 오차 | 1.178062m | 1.281737m |
| 평균 절대 횡방향 slip | 1.461725m/s | 1.574951m/s |

공통 +60m strict 시간 이득은 **[0.04,0.08]초 = [2,4] raw20ms ticks**, 고정1.04초 진행 이득은 **+2.233223m**다. 두 조건과 안전·source·반복 gate를 함께 통과했다. 독립 world 반복은 결정적 재현 확인이며 통계적 신뢰구간은 아니다. Projected4는 초기 감속 한 번을 피하고 이후 더 일찍 감속해, 종료 시 더 멀리 갔으나 속도는7.907593m/s 낮았다. force 요구와 clipping은 줄었지만 경로 오차와 lateral slip은 커졌다. 각 endpoint와 미래 lower-node 집합이 다르므로 감속부채 proxy 변화는 완전한 물리 feasibility 증명이 아니다. 낮춘 자체 target의 tracking 개선만으로 승격하지 않았다.

원래 reference arm의 saved-native13 물리/geometry/ledger replay와 별도로 exact command prefix는2개이며 처음 다른 command는3번째다. Projected4는 공통 첫 전이만 native factual gate로 인증했고 이후는 model consistency 범위다. 두 arm 모두 독립 H13 두 번과 held first 한 번을 통과했다. 54개 prepared-once policy/phase 기록과 constructor 전6개 node/policy digest를 저장자료로 다시 확인했다. root의 state·memory·RNG·readonly actual ledger는 불변이다. [상세 관측](compare468_result.json)과 [통합 gate](compare468_gate.json)에 범위를 분리했다.

공간은 압축 이득 없이 hard1536ticks·41worlds·최신91890.08943089431B/tick×1.25, header770314B와 새 source manifest 증가837B의3배 및 world당16384B, plan2MiB/raw metadata16MiB를 포함했다. full raw retention1.1배+32MiB와512MiB reserve를 적용해 tmp764,531,821B/workspace822,949,496B가 필요했다. 수정 계약 시작 전 실제 free는 tmp3,537,461,248B/workspace891,727,872B로 부족량0B였다. 실행 중에도 양 volume512MiB reserve를 검사했다.

world 감사는 qualification29+pending3+parent-pending3=35, 두 arm각 independent2+held1=6으로 **41개**이며 숨은 main/probe0이다. 계획 최대1458/41은 유지하고 unused hard tick headroom만1536으로 줄였다. 실제 qualification1137/35+비교216/6=**1353ticks/41worlds**, worker CPU34.909790초/wall34.698179초였다. whole-worker cap180/300 안에서 종료했다. actual/reset·새 seed/학습·HOLDOUT·SEALED·reserve·유료 사용0, v475 연구잔액26346·예비84000사용0 불변이다.

첫 정적 시도는52번째 검사에서 fake controller의 phase() 누락으로 중단됐고 적분0이었다. 최초 plan·source·로그를 별도 보존하고 fixture만 수정했다. 같은 과학 계약의 revision2에서 [59개 정적 검사와 저장 감사](compare468_static.json)가 통과한 뒤 물리 비교를 한 번 실행했다. 실패 static-result는 덮어쓰거나 삭제하지 않고 별도 revision2 결과를 사용했다. 초기 정적CPU10.415초와 수정 정적CPU12.394초는 실제 worker 비용과 별도다.

기존 검증된 plain writer로 작성한 새 raw326파일126,087,848B 전부를 유지하고, 새 비공개 archive15,612,893B의 모든 member 크기·SHA 및 원본 SHA를 전수 확인했다. 보존 CPU1.795904초/wall1.810727초다. 기존 압축본 변환·기존 자료 삭제/이동0이다. [보존 결과](compare468_retention.json), main dfb7a2de2178825ca5c5ce20bab01ba67052ba31·공식 Participants·보호18파일·기존 백업을 유지했다. 개인 원자료는 공개하지 않았다.

현재 계약은 사용자 연장 근거와 최신 종료 **2026-10-20 19:01:55 KST**를 함께 보존한다. 과거 최초 prompt의 Oct16을 최신 철회로 해석하지 않는다. 이 결과는 고정 root의1.04초 진단이며 full episode/native 시간으로 외삽하지 않는다. 여기서 비교를 닫고 임의 후속 실행은 하지 않았다.
