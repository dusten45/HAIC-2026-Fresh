# 452 — candidate 첫 neutral 이후 별도 current 결정 한 번

**새 단일결정 범위에서 nominal-safe 복귀를 확인했다.** candidate의 고정451 MODEL source48행동을 독립3 worlds에서 정확 재현한 뒤, required2의 fresh current nominal H13이 모두 안전·진행을 통과했고 자기 parent 첫 전이와 held1회도 통과했다. neutral 대안은 평가하지 않았다. **원래451의 `CENSORED_NO_RECOVERY14`는 그대로이며**, 두 번째 새 결정·native 전이·전체 lap은 실행하지 않았다.

## 실행과 권위

original native448 candidate root의 state/memory/immutable native GoalLedger/보존 RNG에서 시작했다.48개의 과거 MODEL command를 재현하면서 nominal memory를 다시 계산하고 매 frame을451과 정확히 비교했다. 끝 state·memory·full ForecastLedger도 정확히 같았다. 이는 기록된 모델 source의 재현이며 native 사실이나 새로운 B 정책 선택이 아니다. 닫힌451 endpoint를 새 snapshot 하나로 복원하지 않고 live로 재구성했지만, 원래 native-to-model solver warm-start 한계는 유지한다.

코드·source·원장v471·한 결정·상한을 동결하고 정적 **234개**와 저장 감사가 첫 시도에 통과했다. 그 뒤 모델 worker를 한 번 실행했다. prefix/source/권위/반복/fidelity/기술/선택 parent 안전 오류는 없었으며 재시도·범위 변경은 없다.

`bind_model_query445`의 MODEL ForecastLedger와 immutable native GoalLedger 분리, current owner/state/memory/RNG/clock 및 모델 값 view를 그대로 썼다. required2의 context/선택/최종 state가 정확히 같았고 held의 current context도 같았다. 선택 parent의 자기 첫 전이는 기존 body/wheel/raw hull/clipping·정확 입력/nominal memory·기하 progress/goal·goal-side/age/clock/deadline/DONE 비교를 통과했다. nominal-only 완료/ranking 경로와 두 번째 새 결정은 API에서 차단했다.

| 새 scope 관측 | 결과 |
|---|---|
|재현된 과거 모델 source|48행동×3, 전체 frame/state/memory/ledger 정확|
|fresh nominal H13|독립2×required2, 모두 안전·진행 통과|
|선택된 새 parent 전이|nominal 1행동×required2 +held1, 모두 검증|
|neutral 재선택|없음|
|원래451 censor 변경|없음|

451의 neutral H13 안에 있던 nominal 미래12행동을 다음 current nominal H13의 증거로 대체하지 않았다. 새 query는 재구성된 실제 MODEL parent 상태에서 새로 수행했다. 새 scope의 복귀 증거는 첫 fallback 구성의 한 부분을 채우지만 전체 정책·native 미래·공통 경계 시간 이득·11초대·픽셀 개선은 아직 입증하지 않는다.

## 비용과 마감

실사용은 재현576 + fresh shadow208 + required parent8 +held4 = **796 model ticks/7 worlds**, CPU **10.641초**/wall **10.728초**다.7 observer posts796과 reserved796이 일치했다. planned1004/11·hard1024/16·CPU90초/wall150초·순차1을 지켰고 live worlds 최대3이었다. 실제/reset·학습·새 seed·HOLDOUT/SEALED·예비·추가 유료 자원은0이다.

정적 CPU19.841초/wall19.937초와 저장 감사 약0.658초는 별도다. 전체 준비·보고·Git·일부 import overhead는 완전 계측하지 않았다. 과거7312 ticks는 재청구·환급하지 않았다. 마지막 checkpoint는 **2026-10-17 17:19:08 KST `CLOSED`**, worker 종료 확인. v472 연구 잔여 **27,436**, 누적 실제 **1,320,628**, 예비 **84,000/사용0**이다.

## 전체 lap 정책 검증: 충족한 것과 남은 필수 작업

이미 충족한 것은448의 known-root native +60m pulse transfer,450의 첫 큰 제동/재가속 이후 +270m mixed model 이득,445/451/452의 current-model 값 view·권위·반복/held·첫 B 개입/복귀, 그리고439/442의 native 사실 우선 commit·registered pending·자기 native DONE 경계다. Backend·geometry439·허용 오차·권위 구현을 바꾸지 않는 한 이 증거는 hash/recorded fixture로 재사용할 수 있다. 같은 작은 공간 구간이나 첫 fallback을 계속 재실행할 필요는 없다.

남은 필수 작업은 다음을 **하나의 통합 검증 작업**에서 처리하는 것이다.

1. 전체 정책을 고정한다: 같은22-action prefix, candidate pre23 첫 pulse만 다름, own nominal로 +270m까지, 이후 B를 공식 native finish 또는 cap까지 지속한다.14-action/one-decision 실험의 종료 규칙을 전체 정책으로 잘못 옮기지 않는다.
2. 새 policy mode·270m 전환·late `FINISH_CONFIRM`/model-confirmed guardian·negative/at-root event·실제 DONE의 연결을 적분 없는 integration fixture로 검사한다. before270 고정 명령의 자격 실패는 중단하고 자동 fallback하지 않는다. after270의 등록된 비선택 거절과 선택 parent 실패를 구분한다. 기존 native442의 pending/current-copy 경로를 재사용하며 새 MODEL parent에 대한 blanket late-route 성공을 주장하지 않는다.
3. native reset 전에 한 번의 fresh source preflight를 실행한다. 기존 full pending/source allowance1242 ticks/35 worlds와 H1 root216/6을 상한으로 잡는다. 이제 저장448 fullgas 실제 기록도 calibration에 쓸 수 있고 selection에는 쓰지 않는다. 결과는 새 private stage에 기록해 과거442/448을 덮어쓰지 않는다.
4. 앞 gate가 모두 통과하면 고정 known-DEV native 전체 pair를 한 번 실행해 양쪽 자기 공식 finish로 lap 시간을 직접 비교한다. 미완료 arm은 censor/gain null이며 최초 오류에서 두 arm 모두 중단한다.

다음 제안의 상한은 **actual440 wrapper/reset2(각220), model planned83,826 ticks/1,625 worlds**, hard98,304/1,792·model CPU3000초/wall4200초·actual exclusive CPU240초/wall480초·순차1이다. 산식은 prefix22씩 이후 최대396결정×최악208 shadow ticks + source1458이며, raw native는 reset 포함최대1862 ticks다. fixed nominal/pulse 구간과 nominal-safe B 결정은 대개 neutral query를 생략하지만 비용 계획은 보수적으로 잡았다. actual440은 연구 잔여의 약1.6%이고 최악 후26,996을 남기며 예비는 쓰지 않는다. 모두 기존 cloud만 사용한다.

별도 전체 MODEL parent rollout을 먼저 요구하면, 같은 prefix와 각200-action cap을 가정한 보수 예만으로도140,768 ticks/2,646 worlds가 들고 native pair 비용이 뒤에 더해진다. 게다가 새 model-parent pending adapter는 native DONE 경로를 검증하는 대체재가 아니다. 특정 미해결 모델 질문이 생기면 선택할 수 있지만, 현재는 이미 검증한 native442 carrier를 재사용해 **새 routing/static/source gate와 한 번의 bounded native pair를 묶는 편**이 목표 시간 측정에 직접적이다. 새 gate가 실패하면 native 호출0에서 중단한다. 이는 native future가 이미 검증됐다는 주장이나 현재 실행 허가가 아니다.

[통합 다음 설계·재사용 근거·비용](next452_design.json)은 **제안만 했고 실행·예약하지 않았다.**11초대는 공식 native lap으로 측정해야 하며 국소 이득을 더해 추정하지 않는다. 부정적·censored 결과도 이 고정 정책 한 가설에 한정한다.

유효 종료 **2026년10월20일19:01:55 KST**, main dfb7a2de2178825ca5c5ce20bab01ba67052ba31·Participants·보호 ZIP·사용자 변경·backup을 보존했다. private state/seed/명령/RNG는 공개하지 않았다.

[실행/단일결정 경계](decision452.py) · [정적 fixture](test_decision452.py) · [저장 감사](analyze452.py).
