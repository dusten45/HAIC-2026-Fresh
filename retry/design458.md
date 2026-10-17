# 458 — 저장457 선택 분석과 동일 정책의 once-only native transfer 계약

직접458 승인에 따라 정적·합친 fresh source gate 뒤 한 번의 known-condition native pair를 실행하는 통합 계약이다. 새 authority adapter가 필요하거나 아래 예산/검사가 성립하지 않으면 native0에서 중단한다. 첫 예상 밖 실행 오류는 두 arm을 중단하며 재시도하지 않는다.456 실패·457 모델 결과·원본 자료는 보존한다.

## 저장 분석과 검증할 대비

457 P의 첫 세 time-ranked 결정은 fullgas/fullgas/neutralbrake였다. 같은 경과 행동 뒤 P/C0 모델 속도는 각각62.23/53.73,64.41/46.44,56.71/39.12m/s였다. 세 번째 제동 뒤에도 P가 더 빠르지만 이 표는 같은 시간 표본의 기술 통계이며 각 제어 성분의 독립 인과 기여는 아니다. 세 query의 국소 예상 이득[0.36,0.40]·[0.20,0.24]·[0.36,0.40]초를 더하지 않는다. 실제 부모의 전체 모델 이득은[0.96,1.00]초였고 원래 pre23 공간570m에서[0.36,0.40]초,750m에서[0.88,0.92]초였다. 이후 상태 반응을 끝까지 보아야 한다는 근거다. [집계](saved458_diagnosis.json)는 저장 자료만 읽었으며 새 적분0이다.

458은 이 모델 이득을 실제 성적으로 더하지 않고 같은 정책을 직접 검증한다. C0/P 모두453 candidate의 알려진 초기 조건에서 **같은 실제112행동 prefix**를 재현해 같은pre113에 도달한다. 그 뒤 C0는 guardian nominal reference, P는 기존419 첫8개 적격 FIRST_LAP/nonpending 결정 후 같은 guardian이다. nominal을 선택해도 quota1회를 쓴다. planner는 기록된 세 선택이나442의 네 공간 pulse를 명령으로 복사하지 않는다. 매 query는 자기 현재 native 관측/ledger/controller에서 새로 판단한다.

457의 postroot100행동 상한을 그대로 유지한다. 따라서 arm당 실행 범위는112+100=212이며 **hard220/arm·전체440/reset2** 안이다. parent100을108로 늘려 cap 이후 tail/finish를 붙이지 않는다. 순서는 C0→P 한 번이며 C0가 안전하게 자기 official native finish를 완료해야만 P를 시작한다. prefix는 사전 고정 재현 범위이고 suffix는 fresh policy이다.

## 재사용 권위와 관측 경계

NativeAuthority439/Native442·현재 read-only adapter·ObservedHistory442·suffix_step·ActualPending442/436 bridge를 그대로 사용한다. 새로운 actual authority 클래스나 forecast→actual ledger 경로는 만들지 않는다. Query458는 Query442의 current/pending flow에 기존 Planning456.planning_query와scope457의8회 상한만 연결한다. recipe/H13/tail308/ranking/strict bracket/반복/geometry/허용 오차·거절 분류는 바꾸지 않는다.

prefix 각 행동은 자기 charged native dispatch→자기 native fact commit→Native442.verify_prefix 순서다. native reference는453 candidate row이다. source frame은1–22행동의 기존417 source-prefix와23–112행동의 이미 관측·검증된453 해당 selected_first이다. 저장 모델 frame은 prefix의 fidelity 비교 자료일 뿐 actual fact 입력이 아니다. 각 실제 pre/post·명령·nominal memory·raw hull/tyre·clock·ledger·RNG/관측을 원본과 대조한다.

112개 검증이 끝난 pre113에서 full state/wrapper/controller/RNG/관측이453 candidate의 저장pre113과 exact 같아야 한다. P는 새 C0 root와도 exact 같아야 한다. 이 시점에만 ObservedHistory442를 만들며 각 suffix는 fresh independent model query 뒤 기존 fact-first suffix_step으로 실행한다. 실제 사실은 forecast 비교보다 먼저 commit하고, fidelity·clipping·ledger·권위·진행·물리 검사가 실패하면 다음 dispatch를 막는다. 새 상태의13-step query나 model tail을 실제 전체 궤적 안전 보장으로 표시하지 않는다.

pending은 기존 native observation provenance/history와현재 root/RNG/clock에 묶은 경로만 허용한다. guardian FINISHED certificate는 actual DONE를 부여하지 않는다. 자기 charged native tracker official event·확인 post·성공 fact commit·후검증 뒤에만 완료를 인정한다. remaining path를 clamp하거나 finish를 추정하지 않는다. 재사용 snapshot의 legacy442 라벨은 현재458 승인이나 실제 사실 권위를 대신하지 않는다.

## 실행 전 한 번의 통합 검사

하나의 static suite에서 기존 검증을 재사용하고 새 부분만 더한다. 실제 top-level runner의 명시 meter alias, qualification/query/실제 exclusive timer의 동일 객체 연결,112 fact-first prefix→pre113 fresh query,scope8과parent100,Planning456 연결,기존98304 tick/arm명 제한 우회가 새 cap과 일치하는지 constructor와 step 없이 검사한다. static 실패 시 native0에서 중단하고 같은458에서 수정/재시도하지 않는다.

fresh source gate는 old source/current/pending≤1242ticks/35worlds + 선택pre113 root≤216/6, 합계 **≤1458/41**다. 기존 qualify453/qualify_parent453와457 root qualification을 목적지만 새 stage로 사용한다. source/current/pending gate 뒤 qualification flag를 세우고 same-root nominal13은 저장 native453과 factual 비교한다. fullgas는 두 모델 반복+held 첫 전이의 자기일관성만 검사한다. source gate 실패는 native0에서 중단한다. 실제 reset은 전체 통과 뒤에만 허용한다.

## 전체 비용 동결

| 항목 | model ticks 최대 | worlds 최대 |
|---|---:|---:|
|P planner8×3recipes×2copies×(13+308)actions×4ticks|61,632|48|
|나머지192queries×2guardian recipes×2copies×13×4|39,936|768|
|합친 fresh source qualification|1,458|41|
|**planned 상한**|**103,026**|**857**|

actual 부모는 모델 world/step이 아니므로 모델 산식에 중복 가산하지 않는다. fixed112 prefix는 새 모델을 적분하지 않으며 native 행동으로 청구한다. 실제 scope는최대424wrapper/reset2이고 hard440/reset2·각220을 유지한다. 고정 조건의 reset51raw ticks씩을 가정한 scope raw 최대는424×4+102=1798이다. wrapper·raw tick·모델 tick·reset을 구분한다.

hard model **212,992ticks/1,792worlds·exclusive CPU6000초/wall9000초**, actual **exclusive CPU240초/wall480초**, 순차1이다. query scheduler와 meter 모두 같은 hard cap을 읽으며 step 전4tick 예약, constructor 전 입력/복원 증명과 원가를 기록한다. 실제 region에서 model 시간은 빼고 model region은 별도 누적한다. startup/import·snapshot/proof/IO·cleanup과 정적/저장 분석·Git overhead의 측정 범위를 분리한다. 원가 절감분으로 새 recipe/arm/seed를 추가하지 않는다.

## 중단과 판단

첫 static/fresh source 오류는 native0이다. 실행의 첫 예상 밖 technical/restore/fidelity/numeric/reverse/phase/clock/권위/부모 또는 RNG 변경/독립 반복/선택된 실제 명령 검증/진행/자원/기한 오류는 두 arm을 중단한다. C0/P 각212 scope 안 미완료는 censor이며 실제 완료 시간을 추정하지 않는다. 등록된 planner 조기 H13 물리 거절만 기존 typed receipt로 ineligible 처리한다. 지원되지 않는 H13미만 INFEASIBLE/진행 거절은 전역 중단한다. guardian·완전H13/tail의 기존 지원 범위를 확대하지 않는다.

양쪽 자기 official native finish가 있을 때만 실제 lap 차이를 직접 계산하고11.99초 목표와 비교한다. 작거나 음수·겹치는 결과도 비용/실패와 함께 남긴다. 457 모델 이득·query 국소 이득을 실제 성적에 합산하지 않는다.442의13.760초 P는118행동 prefix와다른 planner 범위의 정책이므로 같은 정책의 전후 비교라고 쓰지 않는다. 이 실제 pair도 known DEV GT 진단이며 픽셀/새 조건/공식 서버 일반화는 별개다.

실행 단계·arm/행동·quota·ticks/worlds·CPU/wall·checkpoint 시각·PID를 기록하고10분마다 보고한다. 완료/중단 뒤 저장 감사·원가와 실제 행동 원장 정산·일반 commit/push·원격 SHA 확인까지 수행한다. 추가 실행은 자동 시작하지 않는다. 연구 잔여27,059·예비84,000/사용0에서 실제 새 wrapper만 차감한다. SEALED/새 seed/학습/추가 유료 자원0, main dfb7a2de2178825ca5c5ce20bab01ba67052ba31·Participants·ZIP·사용자 변경·백업·과거 실패를 보존한다. raw state/seed/명령/RNG·개인 문서는 공개하지 않는다.

종료는 **2026년10월20일19:01:55 KST**와 각 worker 상한 중 먼저 오는 경계다. 자동 연장·실패 후 같은458 재시도는 없다.
