# 457 — 동일 candidate root에서 기존419 planner의 제한된 후반 제어 비교

**네 모델 부모가 모두 자기 tracker official finish를 관측했고 두 전체 arm 반복이 각각 정확히 일치했다. root 이후 전체 모델 이득은[0.96,1.00]초다.** 실제 행동/reset·새 seed·학습·HOLDOUT/SEALED·예비·추가 유료 자원은0이다. 모델 결과이며 새로운 native finish witness·실제 승격·11초대·픽셀/새 조건 일반화·공식 서버 성적이 아니다.

| arm | 자기 부모 행동 | planner/guardian 결정 | 자기 모델 finish raw bracket | root 이후 모델 시간 |
|---|---:|---:|---:|---:|
|C0-1|76|0/76|[300,301]|[6.00,6.02]초|
|P-1|64|8/56|[251,252]|[5.02,5.04]초|
|C0-2|76|0/76|[300,301]|[6.00,6.02]초|
|P-2|64|8/56|[251,252]|[5.02,5.04]초|

각 C0/P의 전체 semantic rows·명령·상태·memory·ledger·tracker·완료 bracket 서명이 독립 반복 사이 정확히 같다. 평균이나 빠른 반복을 택하지 않았다. 이득은 완료한 자기 모델 부모의 전체 event bracket에서 직접 계산했으며 query별 예상 이득을 더하지 않았다. 남은 시간에 과거 native prefix를 더해 새로운 실제 lap 성적으로 표시하지 않았다.

## 고정 계약과 456 수정 범위

[455 계약](design455.md)과 직접457 승인대로 원래453 candidate native113행동 직전, 공통 pre23 root+453.716m 부근을 선택했다. 같은 full source state/wrapper/tracker·controller memory-before-nominal·관측 유래 ledger·저장 RNG에서 C0-1/P-1/C0-2/P-2를 순차 실행했다. 각 부모 상한100행동, P의 첫8개 적격 FIRST_LAP/nonpending 결정만 기존419 time-ranked planner, 나머지는 C0와 같은 guardian이었다. 네 pulse 위치를 하드코딩하지 않았다.

456의 `PREMODEL_RUNNER_BINDING_STOP`·동결 소스·원문 오류·모델/실제0 기록은 그대로다. 새 [runner](compare457.py)는 `BudgetMeter457` 명시 alias로 검증된456 budget adapter를 사용한다. 새 startup fixture는 실제 `run()`→동일 budget meter 생성→qualification 연결→실제 Comparison 초기화→기존 planning_query의 Budget까지 constructor/step 없이 도달해 동일 객체와212992/1792·6000/9000 연결을 검사했다. 기존 policy/root/scope/root qualification은 stage label을 제외한 AST 동일성을 확인했다. physics·recipe·ranking·tail·pending·반복·허용 오차·상한은 바꾸지 않았다.

정적 **255개**와 저장 감사가 통과한 뒤 구현/게이트를 `6b06500`로 commit/push했고 새 model worker를 한 번만 시작했다. 실행 중 코드 수정·실패 후 retry·범위 확장은0이다. inherited budget의 private checkpoint `stage` 필드에는 legacy456 label이 남는다. 현재 실행은 별도stage457 폴더·동결 plan·worker PID176121·457 runner log로 식별하며, 이전456 폴더를 쓰거나 소급 성공 처리하지 않았다.

## Fresh qualification과 완료 권위

기존 source/current restore/pending qualification은 새로 **1,137 ticks/35 worlds**로 통과했다. 같은 선택 root의 nominal/fullgas 독립 H13 및 recipe별 held 첫 전이 검사는 **216/6**, 합계 **1,353/41**로1458/41 안에서 통과한 뒤 본실험을 시작했다. nominal13은 같은 저장453 native13행동과 기존 factual 기준으로 대조했고 fullgas는 모델 자기일관성만 검사했다. fullgas와 이후 새로운 상태의 전체 궤적을 실제 물리 qualified로 표시하지 않는다.

각 planner query는 기존 세 distinct recipe·H13·같은 자식의 nominal tail≤308·typed early physical ineligibility·strict finish bracket ranking·독립 반복을 유지했다. query/current proof와 입력·constructor·restore·첫 step 증명을 먼저 저장했다.16개 planner query의48개 recipe 비교 쌍 중42개는 모델 FINISHED witness,6개는 지원되는 typed early physical ineligibility였으며 각 쌍의 독립 반복을 포함했다. 거절된 분기를 성공이나 전역 오류로 바꾸지 않았다. 최초 예상 밖 오류·미지원 H13 미만 진행 거절·권위/숫자/반복/부모 또는 RNG 변경·상한/기한 오류에서 전역 중단하는 경로를 유지했다. 이번 실행에는 그런 전역 오류가 없었다.

전체 **280개 모델 부모 전이**가 fresh selected-first 관측 비교를 통과했다. C0는각76회 모두 nominal이다. P는각 planner8회 중 **fullgas2·neutralbrake1·nominal5**를 선택했다. 앞의 세 번은 `MODEL_TIME_CHOICE`, 나머지는 `GUARDIAN_REFERENCE_ONLY`였다. 이후 guardian56회는 모두 nominal이며 추가 neutral fallback은0이다. neutral 한 번을 guardian의 위험 회피 개입과 혼동하지 않는다.

C0 각 반복의 live pending query는0, P 각 반복은1이며 자기 부모의 registered pending 확인도1회다. `capture_pending`·guardian proof·부모 자신의 `one`·`verify_parent_step`을 사용했다. FINISHED guardian certificate는 각 arm13회였고 모델 확인 자격만 주었다. 시간 순위나 실제 DONE·부모 DONE를 대신하지 않았다. 최종 완료는 자기 부모 tracker event와 확인 post·raw clock·ledger로만 판정했다. 원래 native ledger는 read-only로 유지됐다.

## 저장 공간 구간 진단

새 root 이후 모델 raw post를 기존 순수 canonical projection으로 투영하고 같은 pre23 origin 기준 첫 crossing의20ms bracket을 계산했다. 새 적분·보간은0이다.

| 공통 공간 경계 | C0 대비 P 모델 crossing 이득 |
|---|---:|
|root+510m|[0.18,0.22]초|
|root+570m|[0.36,0.40]초|
|root+630m|[0.56,0.60]초|
|root+690m|[0.66,0.70]초|
|root+750m|[0.88,0.92]초|
|자기 전체 모델 finish|[0.96,1.00]초|

이 표의 root 표기는 **원래pre23 공간 원점**이며 새 실행의 시작점은+453.716m다.270/450m crossing을 새 부모에서 관측하거나 이전 궤적을 재구성 적분하지 않았다.570m 이후에도 차이가 커져, 첫 몇 결정의 효과를 한60m 구간의 시간만으로 평가할 수 없다는 모델 증거를 얻었다. 조향·제동·tyre·속도 상태 각각의 독립 인과 기여는 분리하지 않았다.

454는 초기 pulse candidate와 원래 native baseline의 대비이고,457은 **그 candidate의 같은 후반 root에서 두 모델 정책**의 대비다. 두 표의 이득/손실을 서로 빼거나 합산하지 않는다.442의13.760초 P는118행동 prefix 뒤 다른 범위의 planner를 사용한 별도 실제 정책이므로 이번5.02–5.04초 remaining model time과 직접 lap 우열을 비교하지 않는다.

## 원가·저장 감사·종료

| 구간 | model ticks | worlds |
|---|---:|---:|
|fresh preflight|1,353|41|
|C0-1|7,503|153|
|P-1|16,165|161|
|C0-2|7,503|153|
|P-2|16,165|161|
|**합계**|**48,689**|**669**|

예약 ticks도48,689이며669 observer streams의48,689 raw posts와 일치한다. planned206,194/1,677·hard212,992/1,792 및 CPU6,000초/wall9,000초를 지켰다. whole model worker 최종 meter는 **CPU730.335초/wall738.511초**, 정적 별도 **CPU22.225초/wall22.116초**, 저장 감사 **CPU12.998초/wall15.450초**다. worker에는 import·source 확인·qualification·제어·모델 physics/observer·snapshot/proof/hash/IO·cleanup이 포함된다. 준비·추가 보고/Git·전체 프로젝트 overhead를 완전 계측하거나 순수 solver 시간으로 표현하지 않았다.

동결 source·protected/original 자료 hash를 저장 감사에서 다시 확인했다. 원문 state/seed/명령/RNG·개인 문서는 공개하지 않았다. [집계 JSON](compare457_result.json)·[사전 static gate](compare457_gate.json)·[진행 기록](compare457_progress.json)·[저장 감사 코드](analyze457.py)를 제공하며 raw 증거는 비공개에 보존했다. 중간 상태는 `9b7f5ff`, `66b1585`로 commit/push했다. 실제 단계·arm/행동·quota·ticks/worlds·시각·PID를 기록했고10분 checkpoint도 보고했다.

마지막 checkpoint는 **2026-10-17 18:33:21 KST `CLOSED`**, worker PID176121은 exit0했다. **새 actual/reset/seed/학습/HOLDOUT/SEALED/예비/유료 자원0**, v473 연구 잔여 **27,059**, 누적 실제 **1,321,005**, 예비 **84,000/사용0**이다. main dfb7a2de2178825ca5c5ce20bab01ba67052ba31·Participants·보호 ZIP·백업·사용자 변경과451 censor/456 실패를 보존한다. 유효 종료2026년10월20일19:01:55 KST를 유지한다.

이 결과는 기존419 planner를 초기 pulse 이후의 후반 root에 적용할 모델 연구 근거다. 실제 승격은 하지 않았다. 다음 판단은 저장된 세 번의 time-ranked 선택과 이후 상태 반응·새 상태의 factual 범위를 검토해 별도 연구/실제 계약의 필요성을 정하는 것이다. 새 실험이나 자동 후속 실행은 시작하지 않았다.
