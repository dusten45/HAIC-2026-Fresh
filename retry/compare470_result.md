# 469 revision1 / 470 — P4만 자기 model finish, 전체 시간 이득은 미확정

**같은 pre126에서 각 whole arm을 한 번 실행했다. Original은 unsafe로 종료됐고 Projected4는 자기 모델 finish를 기록했다. 양쪽 안전한 finish가 없으므로 전체 시간 이득·승격 기준은 미통과다.** 기존+60m 이득을 finish 이득에 더하지 않았다. 새 root·구제·guardian query·랭킹·추가 tail·actual/reset은0이다.

| 관측 | Original reference | Projected4 reference |
|---|---:|---:|
| 종료 상태 | UNSAFE: path_error_over3m | FINISHED: 자기 tracker/ledger |
| whole arm 행동 / raw ticks | 34 /136 | 46 /182 |
| root 이후 관측 시간 | 2.72초 | 3.64초 |
| 자기 model finish bracket | 미완료 | **[3.62,3.64]초** |
| 종료 진행 | 221.401664m | 275.145794m |
| 종료 속도 | 61.756820m/s | 80.304950m/s |
| 최대 경로 오차 | 3.089854m | 1.589195m |
| 최대 요구 force ratio | 2.377927 | 1.818340 |
| clipped wheel samples /총 | 49 /544 | 40 /728 |
| 종료 phase /ledger DONE | FIRST_LAP /false | DONE /true |

Original은 행동34의 raw136에서 처음3m 경로 기준을 넘었고 그 법칙을 즉시 닫았다. 중립 제동이나 다른 정책으로 구제하지 않았다. P4도 처음부터 같은 고정 법칙으로 한 번 실행했으며 실제 finish event·own tracker·own model ledger DONE이 일치했다. 두 run의 길이가 다르므로 종료 시간이나 clipping 개수를 그대로 성능 순위로 쓰지 않는다. whole arm 전체 독립 반복은 하지 않았고 성공으로 표시하지 않았다.

| 공통 공간 경계 | Original bracket | P4 bracket | Original−P4 시간 이득 |
|---|---:|---:|---:|
| root+60m | [0.70,0.72]초 | [0.64,0.66]초 | [+0.04,+0.08]초 |
| root+120m | [1.46,1.48]초 | [1.46,1.48]초 | [−0.02,+0.02]초 |
| root+180m | [2.12,2.14]초 | [2.18,2.20]초 | **[−0.08,−0.04]초** |

따라서 초기 이득은+120m에서 겹치고+180m에서는 역전됐다. 동시에 Original은 더 뒤에서 안전 기준을 넘었고 P4는 완료했다. **짧은 시간 이득의 지속과 안전한 완주는 다른 결과**이며, Original의 미완료 finish를 임의 수치로 대체하지 않았다. +240m는 P4만 관측했으므로 공통 비교에서 제외했다.

+180m의 첫 raw crossing post에서 속도는89.944306→82.317279m/s다. 공통 원래 reference의 감속부채 최대/B proxy는1.513522→1.135422, 최소 거리 여유는−9.791203→−2.582483m다. 그러나 P4 자신의 낮은 미래 target 기준 proxy는3.204050B로 남는다. 다른 endpoint·lower-node 집합에서 계산한 근사 proxy이며 실제 tyre feasibility 인증이 아니다. P4 own finish 이후는 남은 제어 reference가 없으므로 terminal reference/감속부채를 N/A로 처리했다. 기하학적 wrap으로 다음 lap의 launch target을 조회한 초기 분석값은 비공개 보존하고 [saved-only terminal domain audit](compare470_terminal_audit.json)로 정정했다. 제어·raw·world·적분은 바꾸지 않았다.

source/root qualification은 기존 integrated gate 그대로 진행했다: 선행1137ticks/35worlds +두 arm 독립 H13/held216/6=1353/41. 새 whole parent는318/2이고 총 **1671ticks/43worlds**, worker **CPU40.887168초/wall41.622369초**다. 계획2018/43·hard2048/43·CPU180/wall300 안에서 종료했다. 각 whole parent가 안전한13행동에 도달한 시점에 같은 fresh qualification의 전체 row를 실제 다시 읽어 exact prefix 일치를 확인한 후14번째 행동을 허용했다. 두 prefix 모두 일치했다. SourceC point-FF·phase·각자 마지막 node·자기 tracker 규칙을 유지했고 제어 정의역을 새로 만들지 않았다.

사전 공간은 최신93,191.314B/tick×1.25, 새 source 증가837B+4KiB 여유,43개 header, plan/raw metadata, raw와 최악 archive 동시 점유 및 temp32MiB·reserve512MiB를 포함했다. `/tmp` 요구1,217,610,795B 대비 free3,410,366,464B, workspace metadata64MiB+reserve 요구603,979,776B 대비 free868,261,888B로 통과했다. 최초 정적 시도는64번째 fixture의 mock 반환 필드 누락으로 적분0에서 멈췄고 원본을 보존했다. mock만 수정한 별도 정적 기록에서 **67검사+저장 감사**를 통과한 뒤 실제 비교는 한 번만 수행했다.

새 plain raw **346파일/138,331,916B**와 검증 archive **17,430,314B**를 모두 지정 실행기의 `/tmp`에 직접 유지했다. 모든 archive member 크기·SHA/readback과 원본 SHA를 전수 확인했다. 보존CPU1.884340초/wall1.907452초. workspace에는 전체 비공개 plan, 입력 material/hash, full file manifest, Python/platform/설치 package version pins, 실행 조건과 코드·공개 집계만 남겼다. 새 raw archive의 workspace 두 번째 복사본은0이다. [상세 결과](compare470_result.json)·[보존 검증](compare470_retention.json)·[최종 gate](compare470_gate.json).

**`/tmp`의 공유·영속성을 가정하지 않는다. `/tmp`가 소실되면 이번 exact raw/archive의 재검증은 불가능하다.** workspace의 code·입력·plan·manifest는 재실행 조건과 증거 식별에 도움을 주지만 hash만으로 소실된 raw를 복원할 수 없다. 원자료를 생략했다는 뜻도 아니며 현재 실행기에서는 두 실물 모두 전수 검증했다.

기존469 미실행 기록·기존 파일/백업·main dfb7a2de2178825ca5c5ce20bab01ba67052ba31·공식 Participants·보호18파일·v475 예산은 보존했다. 새 seed/학습·HOLDOUT·SEALED·예비·유료·새 환경 사용0. 실제 사용자 연장 근거와 최신 종료 **2026-10-20 19:01:55 KST**를 계약에 유지했다. 이 결과는 고정 root의 모델 관측이며 native11초대 달성으로 외삽하지 않고 추가 실행 없이 닫았다.
