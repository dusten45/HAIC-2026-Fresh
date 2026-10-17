# 451 — H1+B 첫 개입·복귀의 유한 모델 구성 검증

**baseline은 neutral 개입 뒤 nominal-safe 복귀를 확인했고, candidate는14번째 첫 neutral 개입 직후 상한에 닿아 복귀가 censor됐다.** 예상 밖 실행 오류는 없었다. candidate의15번째 행동·전체 lap·실제 전이는 실행하지 않았다. 복귀를 관측하지 못한 것은 비실현성이나 전체 정책 실패의 증거가 아니다.

| branch | +270m prefix/사본 | B 행동/사본 | 첫 neutral | nominal-safe 복귀 | 결과 |
|---|---:|---:|---:|---:|---|
|nominal|36|14|13|14|첫 개입·복귀 확인|
|H1 candidate|34|14|14|미관측|`CENSORED_NO_RECOVERY14`|

## 동결·source·권위 경계

계획은 원래 native448 root에서 live parent로 own nominal +270m를 재현하고, 별도 B segment 최대14행동에서 첫 neutral 뒤 nominal-safe 전이1회 또는14행동으로 종료하는 것이다. branch별 독립2회+held1회, planned13,416 ticks/230 worlds·hard14,336/256·CPU420초/wall600초·순차1·actual0, 첫 예상 밖 오류에서 전체 중단을 실행 전에 고정했다. root·경계·허용 오차·정책을 바꾸지 않았다.

최초 정적225개 시도에서 생성자를 건너뛴 fixture의 `label` 누락을 발견했다. 원본 source/plan/실패/로그는 비공개 pre-model-v1에 보존했고 fixture만 수정했다. 기존 기록으로 새 선택-parent nominal/neutral 경로도 추가 검증한 뒤 **정적229개**와 저장 감사가 통과했다. 이 두 정적 시도는 적분0에서 수행했으며 모델 worker는 한 번만 실행했다.

6개 parent/held 모두 native448 state·memory·native GoalLedger·보존 RNG에서 시작했다. baseline H13 및 전체 finite source gate를 factual442에 대조했고, +270m rows/state/memory/full ForecastLedger가450과 정확히 같았다. baseline 검증 뒤 candidate를 열었고 candidate prefix도450과 정확히 같았다. H13 이후와 B segment를 같은 live parent에서 이어 실행했다. held도 prefix를 재현하고 B 첫 nominal을 계산한 채 나머지 사본 동안 state/memory/RNG가 그대로임을 확인했다.

각 B 결정은 `bind_model_query445`로 full parent **ForecastLedger**와 원래 immutable native **GoalLedger**를 분리했다. current owner/state/memory/RNG/clock과 GoalLedger-schema **모델 값 view**를 검사한 뒤 그 값 view로만 shadow를 fork했다. nominal H13 독립2회가 안전·진행 자격을 얻으면 nominal을 선택하고, 등록된 물리/진행 거절일 때만 neutral H13 독립2회를 평가했다. finish 시간으로 선택하지 않았다.

nominal +270m prefix를 별도 봉인했고 B 시작 후 nominal-only `TailRecord`, `continue_tail`, `evidence` ranking 경로를 차단했다. guarded parent step은 current 선택 검증을 통해서만 허용했다. 모델 값이 native 사실이나 DONE를 commit하지 않았다.

## 예상된 거절과 실제 선택 검증

두 branch 모두 첫 neutral 직전 nominal 대안은13번째 예측 행동의 **`path_error_over3m`** 때문에 거절됐다. 각 required/repeat parent에서 두 shadow가 정확히 같았고, neutral 대안은 H13 안전·진행을 통과했다. 이 사전 정의된 비선택 대안의 거절을 선택 parent의 안전 실패나 기술 오류와 혼동하지 않았다.

저장 감사에서 **56개 current query,120개 shadow worlds,8개 예상 거절 worlds**를 확인했다. 모든 shadow required/repeat rows·최종 state·ledger가 정확히 같았다. 선택된 parent56전이는 기존 body/wheel/raw hull/clipping·현재 입력과 nominal-memory의 정확 비교·기하 유도 progress/goal 구간·정확 goal-side/age/clock/deadline/DONE 검사를 통과했다. 선택 parent의 안전/fidelity 실패는0이다.

branch별 두 parent 전체 rows·최종 state·memory와 개입/복귀 순서가 정확히 같았다. held의 첫 B context digest도 required 첫 context와 같았고 자기 첫 선택 명령·전이를 검증했다. native 원장은 변하지 않았다. 후보의14번째 neutral 자체는 유효하고 안전했지만 **그 다음 nominal-safe 복귀는 관측하지 않았다.** 둘 다 복귀했다고 표시하거나 censor를 성공으로 소급 변경하지 않는다. neutral H13 안의 이후 nominal12행동이 안전해도, 다음 current nominal H13은 예측 끝이 한 행동 더 뒤이므로 그 복귀 검증을 대체하지 못한다.

개입 종료 위치가 서로 다르므로 새로운 공통 경계 시간 이득은 계산하지 않았다.450의+270m 이득과 더하거나 이를 전체 lap/11초대/픽셀 개선으로 해석하지 않는다. 현재 결과는 이 고정 H1+B 구성의 유한 증거이며 다른 방법군을 판정하지 않는다. 원래 native-to-model 복원의 숨은 solver warm-start 한계도 유지한다.

## 비용·마감과 남은 질문

새 모델 비용은 **7,312 ticks/126 worlds**, CPU **133.714초**/wall **134.953초**다. prefix 재현840 + required/repeat parent B224 + held 첫 전이8 + shadow6240이며,126 stream raw posts7312와 reserved7312가 일치했다. 실제/reset·학습·새 seed·HOLDOUT/SEALED·예비·별도 유료 자원은0이다. hard/planned 상한을 모두 지켰고 live model worlds 최대3이다.

별도 정적 두 시도 CPU16.873/21.186초, 저장 감사 약3.487초이며 추가 적분은 없다. 준비·보고·Git·일부 import를 포함한 프로젝트 전체 overhead는 완전 계측하지 않았다. 과거450/445 비용은 재청구·환급하지 않았다. 마지막 checkpoint는 **2026-10-17 17:03:03 KST `CLOSED`**이며 worker 종료를 확인했다. v471 연구 잔여 **27,436**, 누적 실제 **1,320,628**, 예비 **84,000/사용0**은 그대로다.

남은 최소 질문은 candidate 첫 neutral endpoint에서 **다음 한 결정이 nominal-safe 복귀인지**다. [별도 미실행 제안](next451_design.json)은 candidate만 original native448 root에서 새 모델3개로 시작해451의 고정48행동 MODEL source tape를 정확히 재현하고, current B 결정 한 번만 required2+held1로 검증한다. 과거 tape 재현은 새로운 정책 선택이나 native 사실이 아니며 현재 결정은 fresh H13·typed current view·선택 first 검증을 유지한다. source replay576 + 최악 shadow416 + 선택/held12 = **planned1004 ticks/11 worlds**, hard1024/16·CPU90초/wall150초·actual0 제안이다. 독립 재구성된 새 단일결정의 증거이며451의 censor는 영구히 그대로 남긴다. 이 제안은 **실행·예약하지 않았다.**

유효 종료 **2026년10월20일19:01:55 KST**, main dfb7a2de2178825ca5c5ce20bab01ba67052ba31·Participants·보호 ZIP·사용자 변경·backup을 보존했다. private state/seed/명령/RNG는 공개하지 않았다.

[실행/동결](composition451.py) · [B 선택과 거절 분류](guard451.py) · [policy segment 차단과 선택 parent 검증](segment451.py) · [정적 fixture](test_composition451.py) · [저장 감사](analyze451.py).
