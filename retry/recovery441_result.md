# 441 — 승인 시각 오판 정정과 중단된 440의 저장 증거 정리

**적용 종료는 2026년10월20일19:01:55 KST다.** 440은 이 승인 기간 안에 시작했으며, 모델·성능·충실도 실패로 중단된 것이 아니다. 어시스턴트가 최초 요청의 오래된 마감을 다시 적용해 외부 SIGTERM을 보냈다. 새 사용자 취소를 확인한 적은 없다. 앞선 [종료 보고서](window440_closure.md)와 v460은 수정하지 않고 보존하며, 그 보고서의 승인 만료·기간 밖 실행 판단을 이 정정 기록에서 철회한다. C0의 검증된 완료 사실도 그 오판을 이유로 무효화하지 않는다.

441은 **새 actual 행동·reset·model 적분·world 생성 모두0**이다. 440 정적 테스트도 재실행하지 않았다. 저장 JSON·원본 연결 hash·동결된 구현의 AST를 확인했다. P를 이어 달리거나 pair를 다시 시작하지 않았다. 두 실제 arm의 완료가 필요하다는 승격 조건은 그대로이므로 paired gain은 null이다.

## 오판의 입력과 확인 가능한 시각

소비 실행기에 보인 최초 `codex_delegation/input`에는 “승인 기간은 … 10월16일19:01:55까지 KST”와 “종료 후 새 실험이나 자동 연장 없이 결과를 정리”라는 문장이 있었다. 이를 새 취소·마감 변경으로 간주한 것이 오류였다. 인계 요약에는 유효한 10월20일 연장이 명시돼 있었고, `research-deadline-current.json`은 10월16일11:11:35 UTC에 그 연장 출처를 기록했다. v459와 440 동결 계획도 모두 10월20일10:01:55 UTC였다. 이 증거를 먼저 적용했어야 했다. 오래된 원문 문장이 보였다는 점과 이를 판단 근거로 삼았다는 점은 확인되지만, 그 입력이 다시 노출된 전달·문맥 처리 경로까지 독립적으로 확인하지 못했다. 자동화가 원인이라고 단정하지 않는다.

부모가 다시 제공한 사용자 원문은 10월16일11:08:23.287890 UTC의 3일 연장과 이후의 자율 진행 지시다. 부모의 추가 메시지 조회 확인에 따르면 **440 시작 메시지 자체에도10월20일19:01:55 KST가 명시**돼 있었고, 같은 turn 안에서 그 뒤10월16일로 바꾼 사용자 지시는 나타나지 않았다. 이 조회 결과는 부모가 제공한 확인 근거이며 이 소비 실행기가 원격 원문을 직접 다시 조회했다고 표시하지 않는다. 사용자 원문·메시지/turn 식별자와 잘못 적용한 입력 문장은 비공개 정정 receipt에 남겼다. 이 환경에서 별도의 새 취소 원문이나 취소 시각은 발견하지 않았다. 원래 입력이 다시 전달된 시각을 사용자 취소 시각으로 만들지 않는다.

440 worker opening은 **10월17일05:25:34.242355 UTC**, 마지막 durable budget의 파일 시각은 **05:35:47.974440 UTC**다. SIGTERM 명령을 보낸 사실은 확인하지만 그 명령의 정확한 송신·프로세스 종료 시각 receipt는 없다. 파일 시각을 종료 시각으로 대신하지 않는다. 이전 보고서 커밋은 `ed11977`(05:36:48 UTC)이다.

SIGTERM은 설치된 SIGPROF/SIGALRM 자원 중단 handler와 다르다. Python 기본 SIGTERM 종료에서는 `except BaseException`과 `finally`가 실행된다고 보장할 수 없다. 실제로 최상위 result/stop, P final/result, 마지막 query decision/dispatch receipt가 없다. 따라서 이것을 runner가 판정한 technical failure나 정상 DNF로 재분류하지 않는다.

## 440에서 확인된 결과와 미관측 범위

저장 정적 결과는 **179개, 실패0·오류0**, CPU19.168359초/wall19.301646초다. 439의171개에 native 통합 stand-in8개를 추가한 결과다. 당시 검사에서는 실제/model/world 생성자를 금지했다. 저장 전제 검증도 통과했고, 실제 reset 전 qualification 지출은 **1,137 model ticks/35 worlds**였다. 이는 알려진 저장 상태의 충실도·복원·pending 경계 자격이며 새 상태 전체나 픽셀 정책의 일반화 자격이 아니다.

| 저장 결과 | C0 | P |
|---|---:|---:|
| 실제 행동 = 성공 dispatch = native 사실 |189|140|
| 공통 prefix 검증 |118|118|
| fresh current query 뒤 검증된 suffix |71|22|
| 행동 raw ticks |755|560|
| reset raw ticks |51|51|
| 공식 완료 |예|미관측·외부 중단|
| 기록된 lap |15.080초|미관측|
| 관측 damage |0|0|
| 최대 progress 모델/실제 차이 |0.0000314133m|0.00000190167m|
| 최대 progress 비교 구간 폭 |0.263746m|0.214832m|

각 행동의 pre→post→native fact hash 연결, 자기 ticket/clock/raw-post 개수, prefix/suffix 통과 receipt와 실제 ledger 일치를 저장 자료에서 확인했다. suffix 비교 구간 폭은 439의 기존 위치 범위에서 유도한 관측 후 비교이며 사전 안전 여유나 새 epsilon이 아니다. 실제 ledger는 forecast 값을 commit한 결과가 아니다. 두 arm의 pre119 fork는 저장된 동일 전체 상태·controller·clock·RNG와 일치한다.

C0의 공식 event는 simulation time16.10초, 완료 확인 관측은16.12초다. reset 후 시작 clock1.02초를 뺀 공식 lap15.080초를 쓴다. event와 confirmation을 바꾸거나 189행동을 lap clock으로 환산하지 않는다. 71개 suffix 전이는 guardian 경로로 검증됐다. 전체 관측의 force ratio 최대1.231986·clipped wheel44/3020, suffix 최대1.114719라는 기록은 유지하며 이를 임의로 무클리핑 주행이라고 부르지 않는다.

P는 planner suffix22개까지 실제로 검증됐다. 중단 시에는 **decision23**을 평가 중이었다. 실제 step141의 dispatch 전 receipt·charge·native fact는 없고, decision23 선택 완료 receipt도 없다. 다음 nominal 준비와 모델 평가가 시작됐다는 사실을 다음 실제 전이의 성공으로 세지 않는다. P의 최종 완료 시간·남은 구간 성능은 추정하지 않는다. 완료한 C0와 미완료 P 사이의 승패, 11초대 달성, 픽셀 기준선 개선 또는 독립 조건 일반화를 주장하지 않는다.

## 미완결 model world와 비용 원장

| 증거 층위 | 저장 수량 | 해석 |
|---|---:|---|
| 모델 meter ticks / reserved ticks |30,806 /30,806|마지막 durable 원장, 미반납 reservation 차이0|
| raw observer posts |30,762|원문으로 확인되는 raw tick 하한|
| raw observer action records |7,758|raw tick과 다른 단위|
| final receipt가 있는292 worlds의 posts |30,606|위30,762의 부분집합, 더하지 않음|
| 생성 청구·확인 / 첫 step 증거 |295 /294|held pending parent1개는 적분하지 않음|
| final receipt 없는 worlds |293·294·295|각 H13의52 posts/13 actions는 저장됨|

세 미완결 항목은 decision23의 neutralbrake repeat와 fullgas required/repeat다. 저장된 마지막 child dump는 모두 ACTIVE/H13이며, tail 완료나 forecast 실패를 입증하지 않는다. meter30,806과 raw 원문30,762의 **44 ticks 차이**는 원장에는 계측됐지만 최종 observer dump에 없는 부분이다. 실행 순서상 neutralbrake repeat continuation 구간과 연결되지만, 그44개 raw post 원문이나 종료 snapshot을 복원했다고 주장하지 않는다. world293의 최종 tick 수와 전체 process 최종 CPU를 독립적으로 확정할 수 없다.

따라서 **청구 모델 비용30,806은 유지하고44를 환급하지 않는다.** raw 관측 하한30,762와 최종 물리 tick 확정 여부는 별개다. reserved=ticks라는 사실만으로 누락된 관측 원문을 만들지 않는다. 이를 확인하려고 모델을 다시 적분하지 않았다. 기존 437의118행동 실패와438의119행동 실패·원장도 그대로다.

실제 비용은 **329행동/reset2**, 행동 raw1315 + reset raw102 = **1417 raw ticks**로 대조됐다. wrapper 행동, raw tick, model tick을 하나의 budget 단위로 합치지 않는다. v460의 실사용 차감은 맞으므로 v461에서는 이를 재차 차감하지 않는다. **누적 실제1,320,186 + 연구 잔여27,878 + 예비84,000 =1,432,064**, 예비 사용0이다. v461은 승인 종료와 상태만 정정하며 잔액을 유지한다.

## CPU·observer·검증·IO의 포함 관계

마지막 저장 시점의 수치는 다음과 같다. 비정상 종료 뒤 최종 rusage가 없으므로 **최종 완료 비용이 아닌 durable 하한 기록**이다.

| 포함 범위 | CPU초 | wall초 |
|---|---:|---:|
| actual exclusive |146.861466|148.330783|
| model exclusive |488.648324|496.764620|
| 위 둘 밖의 잔차 |0.082024|0.078999|
| whole worker |635.591814|645.174402|
| model 내부의 narrow setup/step tags |21.393838|22.992108|

`paired440_meter.Meter`의 actual clock은 `begin_actual` 이후 전체 시간에서 model region 증가분을 뺀다. 따라서 actual exclusive에는 env 생성/reset, nominal 제어·prepare, full snapshot/RNG·canonical 검사, native `env.step`, raw observer와 trace dispatch, native fact 계산/commit, readonly history, forecast 비교, 각 단계 JSON/hash·파일 저장과 arm 정리가 포함된다. **실제 함수 호출 자체만의146.861초가 아니다.** 이 구성 요소별 독립 timer는 없어 각각을 숫자로 분해할 수 없다.

model exclusive는 초기 process CPU 기준값과 명시적인 qualification/query region으로 구성된다. 초기 import·source 검증 CPU, restore·자식 생성·제어·물리, raw observer/안전·ledger 검사, 독립 repeat, H13 barrier, 증거 조립·비교, snapshot/hash·직렬화·readback·파일 저장 및 query 안 cleanup이 포함된다. model region이 actual clock에서 빠지므로 같은 model query를 actual에 다시 더하지 않는다. 완료 region 목록은 종료되지 않은 decision23과 초기 기준 비용을 모두 담지 않으므로 region 합계만으로 전체 모델 비용을 대체하지 않는다.

상속 meter의 narrow tags는 constructor와 `m.step` 호출 주변 timer다. step 안 tracker callback·raw capture·활성 tracer dispatch를 포함하므로 순수 solver 시간이 아니다. nominal·projection·ledger·observer 후처리·receipt/barrier·dump·상당한 IO는 그 바깥의 model region에 잡힌다. narrow21.393838초는 모델488.648324초의 **부분집합**이고, 나머지467.254486초를 전부 IO라고 단정할 수 없다. 이 둘을 더해 별도 비용을 청구하지 않는다. Trace의 payload timer도 일부 target-line 작업만 재므로 observer 전체 overhead가 아니다. 계측 없는 baseline benchmark는 없다.

`save_receipt`는 직렬화 후 flush/fsync와 atomic link를 쓰고, 일반 budget 저장은 temp→replace 방식이며 fsync를 하지 않는다. 저장된 파일에서 확인한 durable이라는 표현은 이번 프로세스 종료 뒤 파일을 읽을 수 있다는 뜻이며 전원 장애 복구 인증이 아니다. 직렬화·hash의 CPU는 호출된 region에, IO 대기는 wall에 포함된다. 작은 CPU/wall 차이로 IO·tracer 기여가 작다고 결론내리지 않는다. query의 별도 `query_CPU_s`나 model tag/trace timer를 exclusive 합계에 다시 더하지 않는다.

정적179개의 비용은 별도 프로세스다. 441 저장 감사 CPU16.619830초/wall17.721642초도 별도이며, 준비·설명·보고서 작성·Git과 감사 import overhead 전체는 완전 계측되지 않았다. 이를 누락 없이 전체 프로젝트 CPU라고 포장하지 않는다.

## 다음 pair의 비용 상한 제안 — 실행 없음

기존 actual cap은416행동/reset2·CPU180초/wall360초다. 329행동에서 CPU 여유는 **33.138534초**뿐이다. reset·검증·IO가 포함된 관측 평균은0.446387 CPU초/행동이며416행동에 단순 적용하면 **185.697초**다. C0 arm 내부 actual76.768292초를 뺀 잔차70.093174초에는 P140행동뿐 아니라 arm 사이 보고 overhead도 있어 이를 순수 P 비용이라 부르지 않는다. 그 잔차 비율로 현재 C0 완료와 P cap218까지를 단순 외삽해도 약185.913초다. 둘 다 예측 참고치이며 안전 상한 증명은 아니다.

따라서 다음에 같은 통합 경로의 pair를 계획한다면 **행동416/reset2는 유지하고 actual exclusive CPU240초/wall480초**를 사전 제안한다. 모델 cap524,288 ticks/1024 worlds·CPU1800초/wall2400초와 첫 실패 중단 기준은 별개로 유지한다. 이는 현재 평균 외삽에 여유를 둔 공학적 제안이며 최악의 snapshot/IO/모델 tail 비용까지 완주를 보장하지 않는다. 모델 tick cap이 CPU cap 안에 모두 들어간다는 증거도 없다. 상한을 늘려 실패 뒤 계속 달리는 방식으로 사용하지 않는다. 441은 새 계획을 등록하거나 이 상한으로 실행하지 않았다.

## 구현과 보존

440의13개 구현 파일은 실행 전 plan에 동결된 hash와 byte가 모두 일치하며 변경 없이 연구 브랜치에 보존한다.

- `native440.py`, `step440.py`: charged own ticket·전체 pre/post·clock/finish를 연결하고, forecast 입력 없이 native 사실을 먼저 commit한 뒤 별도로 비교한다. 검증 실패 시 사실은 남고 다음 dispatch는 차단된다.
- `routing440.py`, `paired440_query.py`: 실제 관측만 담는 readonly routing과 현재 상태의 fresh query를 연결한다. 모델 certificate는 실제 DONE·행동 권한이 없다. 저장436의 미래 명령은 selection 입력이 아니다.
- `paired440_actual.py`, `paired440_meter.py`, `paired440_run.py`: 한 번의 독립 C0/P reset, prefix·suffix gate, exclusive 비용과 호출 상한을 구현한다. 이번 외부 종료에 대한 SIGTERM graceful closure는 구현돼 있지 않다.
- `qualify440.py`, `qualify_parent440.py`, `fixture440.py`, `test_native440.py`, `static440.py`, `paired440_analyze.py`: 저장 상태 qualification, stand-in8개와 정적179개 경로, 정상 최상위 result를 전제로 하는 사후 분석이다. 미생성 result를 만들어 마지막 분석기를 실행하지 않고, interrupted 자료는 stdlib 전용 [audit441](audit441.py)로 조사했다.

main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`, Participants·사용자 변경·기존 백업과 보호 archive를 유지한다. 개인 원문·지도·조건 seed·state·RNG·실행 명령·raw receipt는 비공개다. 공개 산출물은 구현과 이 집계 보고서/[JSON](recovery441_result.json)이다. SEALED·예비84,000·추가 유료 자원은 사용하지 않았다.
