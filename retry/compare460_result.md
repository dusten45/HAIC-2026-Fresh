# 460 — 동일 후반 정책에서 초기 pulse history 비교

**네 모델 arm이 자기 finish를 확인했고, NoPulse/Pulse의 전체 반복이 각각 exact 일치했다. 관측 prefix와 모델 tail을 합친 hybrid 진단에서 Pulse가[0.24,0.28]초 앞섰다.** 실제 행동/reset·새 seed·학습·HOLDOUT·SEALED·예비 사용·추가 유료 자원은 모두0이며 실제 승격은 하지 않았다. 아래 합은 새 official native lap가 아니다.

|arm|저장 native prefix 경과|자기 모델 tail bracket|hybrid 합|부모 행동|planner/guardian|
|---|---:|---:|---:|---:|---:|
|NoPulse-1|9.28초|4.96–4.98초|14.24–14.26초|63|8/55|
|Pulse-1|8.96초|5.02–5.04초|13.98–14.00초|64|8/56|
|NoPulse-2|9.28초|4.96–4.98초|14.24–14.26초|63|8/55|
|Pulse-2|8.96초|5.02–5.04초|13.98–14.00초|64|8/56|

각 tail의 자기 모델 finish raw bracket은 NoPulse[248,249], Pulse[251,252]다. 평균이나 빠른 반복을 선택하지 않았다. 각 root는 같은453 prefix 정책에서 시작하되 NoPulse는pre117(+450.335m), Pulse는pre113(+453.716m)다. 동일한 첫 pre≥공통pre23+450m 규칙이며 overshoot·상태·clock·guardian 역사 차이는 초기 pulse의 매개 이력이다. 같은 state root나 같은 위치라고 표현하지 않는다.

## 비용 오류 정정과 선행 gate

459의206,410ticks/1,683worlds 산식은 네 arm 중 두 planner arm을 빠뜨렸다. 원래459 오류와 실행0 기록을 보존하고,460 명시 승인 및 [수정 계약](design460.md)에 따라 비용을 동결했다. 독립 검토도 아래 합계를 확인했다.

|planned 항목|ticks|worlds|
|---|---:|---:|
|32planner queries×3recipes×독립2×321actions×4|246528|192|
|368guardian queries×2recipes×독립2×13×4|76544|1472|
|4parents×100actions×4|1600|4|
|fresh qualification|1674|47|
|**합계**|**326346**|**1715**|

hard327680ticks/1792worlds·CPU9000초/wall12000초·순차1·actual0을 적용했다. `planned_budget()`가 실제 네 arm `scope460` quota에서32/368을 도출한다. 정적 fixture는 네 arm 순서·각 root binding·두 root qualification·관측 prefix 시간·실제 startup meter·query의 남은 Budget·timer·step cap 연결을 검증했다. 부모 제어 loop는457과 라벨/scope adapter 외 AST가 같다. 새 authority·물리식·recipe·거절 분류는 만들지 않았다.

통합 정적260개와 저장 감사가 적분0에서 통과했다. 이후 fresh preflight는 old source/current/pending1137ticks/35worlds와 두 root 각216/6, 합계 **1569/47**로 통과했다. 각 root nominal13은 저장 native13과 factual 대조했다. fullgas는 두 모델 반복과 held 첫 전이의 자기일관성이다. 이 검증 범위를 이후 counterfactual 전체 궤적의 실제 안전/적합성 보장으로 넓히지 않는다.

## 정책·권위·거절과 관측 결과

두 arm 모두 처음8개 적격 FIRST_LAP/nonpending 결정에 같은419 planner를 쓰고 이후 같은 guardian를 썼다. native prefix 재적분·cache·과거 receipt를 새 query 권위로 재사용·실패 후 재시도0이다. 각 full arm 직전 자기 root의 state/memory/read-only Actual GoalLedger/저장 RNG를 연결했다. 모델은 ForecastLedger만 전진했다. 두 root의 ledger/state/receipt를 섞거나 forecast를 actual fact로 바꾸지 않았다.

NoPulse의 각 planner8회는 fullgas1·nominal7, Pulse는 fullgas2·neutralbrake1·nominal5였다. 각 guardian55/56회는 모두 nominal이다. planner neutral은 guardian fallback과 다르다. 32planner query의96개 recipe 독립 쌍 중88개는 FINISHED,8개는 기존 typed EARLY_PHYSICAL_INELIGIBLE이다. 원가와 거절을 보존했으며 지원되지 않는 H13미만 진행 거절이나 전역 technical 오류는0이었다.

Pulse 각 반복은 pending query와 자기 부모 pending 확인이1회, NoPulse는0회다. 기존 capture_pending→guardian proof→자기 부모one→verify_parent_step을 유지했다. 각 arm의 guardian finish certificate13개는 모델 확인 자격만 주며 부모/actual DONE를 대신하지 않았다. 모든 완료는 자기 모델 tracker event·확인 post·모델 ledger로 판정했다.

## 판단의 범위

이번 H1 비교에서는 **공통 후반 정책에서도 초기 pulse history의 hybrid 이득이 남았다.** prefix에서0.32초 앞섰고, Pulse의 model tail은0.04–0.08초 더 걸려 hybrid 이득이0.24–0.28초가 됐다. 남은 model tail만 비교해 pulse의 총효과를 판단하지 않았다. 서로 다른 history를 source model로 이어붙인 조건부 결과이며 새 native 반증/검증을 대신하지 않는다.

따라서459에서 본442P13.760 대458P14.000의 역전을 초기 pulse 단독 손해로 해석할 근거는 없다.442P는 시작 위치와54회 planner가 함께 다른 정책이다. 이번 결과를 그 native 성적과 빼서 quota나 두 추가 fullgas의 실제 인과효과를 산출하지 않는다.11.990초 목표까지 남은1.77–2.01초도 아직 설명하지 못했다. H2인 reference/추종/경로 구조 감사는 후속 판단 대상으로 남으며 새 변경·실험은 시작하지 않았다. 작거나 음수·overlap인 결과도 보존한다는 사전 기준을 변경하지 않았다.

## 실제 비용·재현·종료

|측정 구간|ticks|worlds|
|---|---:|---:|
|fresh preflight|1569|47|
|NoPulse-1|16722|159|
|Pulse-1|16165|161|
|NoPulse-2|16722|159|
|Pulse-2|16165|161|
|**합계**|**67343**|**687**|

reserved ticks도67343이며687 observer stream의 raw post67343개와 일치한다.254개 부모 전이가 fresh selected-first 비교를 통과했다. whole worker 최종 meter는 **CPU839.455초/wall839.442초**, 정적 별도 **CPU23.582초/wall23.503초**, 저장 감사 **CPU19.309초/wall22.135초**다. worker에는 import·source 확인·qualification·제어·physics/observer·snapshot/proof/hash/IO·cleanup이 포함된다. 별도 준비/개발/보고/Git·후처리 보존 비용을 포함한 전체 프로젝트 비용을 완전 계측하거나 이 값을 순수 solver 시간으로 부르지 않는다.

종료 checkpoint는 **2026-10-17 19:26:57 KST CLOSED**, PID178029 worker는 exit0이다.10분 checkpoint는19:23:16 KST의NoPulse-2/48행동,50236ticks/496worlds·CPU618.504초/wall618.468초였고 저장·보고·push했다. 중간 계약/입력/checkpoint는4c03362,d0c442c,1f67397로 보존했다. 새 worker나 자동 후속 실행0이다.

[실행 코드](compare460.py)·[정적 fixture](test_compare460.py)·[집계 JSON](compare460_result.json)·[gate](compare460_gate.json)·[진행 기록](compare460_progress.json)·[입력 hash](compare460_inputs.json)·[저장 감사 코드](analyze460.py)를 연구 브랜치에 보존한다. 전체 비공개 plan/input manifest는 workspace에도 별도로 보존했다. raw state/좌표/명령/seed/RNG·개인 자료는 공개하지 않는다.

새 raw 증거는 이 지정 실행기의 `/tmp`에 썼다. 다른 실행기와의 공유를 가정할 수 없고, 임시 볼륨 소실로 그 경로가 없어질 수 있다는 재현 한계가 있다. 종료 후에는 [보존 코드](retain460.py)로 workspace 비공개 압축본과 파일별 SHA256 manifest를 만들고 **6093개 archive member의 SHA256을 전부 대조했다.** 원본3821319539bytes를574234672bytes로 보존했다. 보존 후처리 비용은CPU46.343초/wall46.521초이고 새 모델/실제 적분0이다. [보존 집계](compare460_retention.json)를 제공한다. 원본은 이동/삭제하지 않는다. 공개 코드/집계/hash만으로 비공개 입력이 복원되지는 않으며 재적분에는 별도 승인과 원본 입력 접근이 필요하다.

v474 누적 실제1321369·연구 잔여26695·예비84000/사용0을 그대로 유지했다. source·protected3·original15 hash를 감사에서 확인했고main dfb7a2de2178825ca5c5ce20bab01ba67052ba31·Participants·기존 사용자 변경·원본/백업/보호자료를 보존했다. 최신 종료 **2026-10-20 19:01:55 KST** 이후 새 실험·자동 연장 없음이다.
