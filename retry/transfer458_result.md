# 458 — 동일112행동 prefix 이후 기존419 정책의 실제 native transfer

**양쪽 모두 자기 official native finish를 완료했다. C0 14.98초, P 14.00초로 실제 전체 lap 이득은0.98초다. P는11.99초 목표보다2.01초 느리다.** 새 결과는 한 known DEV 조건의 실제 pair이며 픽셀/새 조건 일반화·공식 서버 성적·11초대 달성은 아니다.457 모델 이득이나 query별 예상 이득을 실제 성적에 더하지 않았다.

| arm | 실제 행동 | prefix/suffix 검증 | planner/guardian | 공식 lap | event/확인 시각 |
|---|---:|---:|---:|---:|---:|
|C0|188|112/76|0/76|14.98초|16.00/16.00초|
|P|176|112/64|8/56|14.00초|15.02/15.04초|

lap은 자기 official event에서 reset-complete1.02초를 뺀 값이다. 확인 관측 시각으로 lap을 대체하지 않았다. 양쪽 새 실제112행동 prefix·pre113 full state/wrapper/controller/RNG/관측이 저장453 candidate 및 서로 exact 같았다. **C0 전체188개 native rows도 저장453 candidate와 정확히 같았다.** P 전체 arm을 두 번 실행한 것은 아니며, 이번 실제 비교는 승인된 한 pair다.

## 동결 계약과 실행 전 게이트

[458 통합 계약](design458.md)은 먼저[457 세 선택의 저장 분석](saved458_diagnosis.json)을 수행하고 같은 정책을 실제로 검증하도록 정했다.457의 첫 fullgas/fullgas/neutralbrake 선택은 이후 속도·제동 반응과 함께 남겼으며 국소 예상 이득을 합산하지 않았다.458 suffix는 그 명령을 복사하지 않고 자기 native 현재 상태에서 fresh query했다.

기존 NativeAuthority439/Native442·current read-only adapter·ObservedHistory442·suffix_step·ActualPending442를 재사용했고 **새 authority adapter는 만들지 않았다**. budget/query scope wrapper만 연결했다. P는 기존419 첫8개 적격 FIRST_LAP/nonpending 결정 후 C0와 같은 guardian이다. nominal 선택도quota1회를 소진하고 pending에서는 planner를 쓰지 않았다. recipe·H13·tail308·strict bracket ranking·독립 반복·geometry·허용 오차·거절 분류는 그대로다.

457과 같은 postroot100행동 cap을 유지해 실제 실행 scope는112+100=212/arm·424total이었다. 승인된hard220/arm·440total/reset2 안이며 cap 뒤 tail은 없다. actual 부모를 모델 world/step으로 중복 계산하지 않았다. planned 상한은 planner61,632 + guardian39,936 + source1,458 = **103,026 ticks/857 worlds**, hard212,992/1,792였다.

정적 **261개와 저장 감사가 통과**했고 실제 top-level startup에서 같은 Meter458가 qualification·query·model6000/9000·actual exclusive240/480 상한에 연결되는 것을 constructor/step 없이 확인했다. 첫 static 이전 source manifest 점검에서417 prefix frame의 명시 hash를 보강했고 최초 준비 plan도 비공개 보존했다. 이후 동결한 source/정책/상한은 실행 중 바꾸지 않았다. 계약·구현·사전 gate는 `2601182`로 일반 commit/push했다.

fresh source/current/pending qualification **1,137 ticks/35 worlds**와 같은 pre113 root 검사 **216/6**, 합계 **1,353/41**로1458/41 안에서 통과한 뒤에만 reset을 시작했다. nominal13만 저장 native453과 factual 비교했고 fullgas는 모델 자기일관성 범위였다. 이 qualification을 모든 후속 forecast 상태의 실제 안전 보장으로 확대하지 않았다.

## 실제 사실·반복·완료 권위

각 prefix 행동은 자기 charged dispatch→native fact commit→저장 actual/source 비교 순서였다.1–22의 source는 기존417 frame,23–112는 이미 관측·검증된453 selected_first였다. 저장 모델 frame이 실제 ledger를 전진시키지 않았다. pre113 이후에는 fresh query의 독립 모델 반복 뒤 선택한 첫 명령만 native로 보내고 자기 사실을 먼저 commit한 뒤 기존 fidelity/goal-side/age/clock/deadline/DONE 검사를 했다.

**364개 native 사실과 성공 dispatch,224개 prefix 검증,140개 fresh-current 전이가 저장 감사에서 확인됐다. 미확정 행동과 clipping 비교 불일치는0**이다. query/native controller memory-before/after·명령·actual ledger 연결도140개 모두 대조했다. model forecast는 실제 ledger에 commit하지 않았으며 오류 후 추가 dispatch나 재시도는0이다.

C0의 postroot76회는 모두 nominal이다. P의 planner8회는 fresh 결과로 **fullgas2·neutralbrake1·nominal5**를 선택했고 이후 guardian56회는 모두 nominal이었다. 그 neutral은 시간 순위 선택이며 guardian fallback이 아니다. 후반 추가 guardian neutral은 양쪽0이다. 고정 prefix에는 원래453 candidate의 초기 pulse와 기존B 개입이 포함되므로 suffix 선택 수와 전체 행동 수를 구분한다.

C0의 live pending query는0, P는1회다. P는 pending 현재 상태와 native history/RNG/clock을 기존 bridge로 묶고, guardian 예측 후에도 actual DONE=false를 유지한 뒤 **자기 native1 raw tick**의 official finish·fact commit·후검증으로만 완료했다.457 모델 parent의 확인 지연을 실제에 복사하지 않았다. 모델 이득 bracket[0.96,1.00]초와 이번 실제0.98초는 이 조건에서 일치했지만, 모델의 모든 상태/확인 시각이 실제와 exact였다는 주장은 아니다.

양쪽 damage0이다. C0/P force ratio 최대는1.26874/1.55739, clipped wheel 표본17/2996 대78/2804, 최대 post path error1.41497/1.44840m였다. P가 빨랐지만 모든 물리 지표가 개선된 것은 아니다. 모델/실제 progress 차이 최대는 C0 7.3514e-6m, P 7.6219e-6m, geometry 비교 구간 최대 폭은0.274872/0.268297m였다. 관측 후 검증 통과를 일반 사전 안전 보장으로 바꾸지 않는다.

## 비용과 원장

| 구간 | model ticks | worlds |
|---|---:|---:|
|fresh qualification|1,353|41|
|C0 native policy queries|7,202|152|
|P native policy queries|15,912|160|
|**합계**|**24,467**|**353**|

예약 ticks24,467과353 observer streams의24,467 raw posts가 일치한다. 실제는 **364 wrapper/reset2**, raw action749+701=1450, reset102를 포함해 **1552 native ticks**다. 단위와 예산 범위를 섞지 않았다.

| 측정 범위 | CPU초 | wall초 |
|---|---:|---:|
|model exclusive|441.623|445.953|
|actual exclusive|160.375|162.087|
|whole worker 최종 meter|602.063|608.103|
|정적 별도|25.235|26.716|

저장 감사 CPU22.064초는 별도다. actual exclusive에는 reset·고정 prefix/제어·snapshot·native physics/observer·fact commit·후검증·IO가 포함되며 model region은 제외한다. model에는 fresh qualification·query 복원/제어/physics/observer·반복·receipt/hash/IO·cleanup이 포함된다. 준비·일부 추가 저장 집계·보고/Git·전체 프로젝트 overhead는 완전 계측하지 않았으며 순수 solver benchmark가 아니다. 모든 model/actual exclusive 상한과212/arm scope를 지켰다.

**v474는 이번 새 실제364만 v473에서 한 번 차감**했다. 연구 잔여27,059→**26,695**, 누적 실제1,321,005→**1,321,369**, 예비 **84,000/사용0**이다. reset·model tick을 wrapper 잔여에서 중복 차감하지 않았고 이전 비용 환급/재청구는 없다. 합계 operating cap1,432,064를 유지한다.

## 비교 범위와 종료

과거442의 실제 P13.760초는118행동 prefix 뒤 planner54회를 사용한 정책이다.458은 초기 pulse가 포함된453 candidate112행동 prefix 뒤 planner8회다. 이번14.00초는 과거 기록보다0.24초 느리지만 **동일 정책의 전후 회귀 비교가 아니며 초기 pulse의 독립 효과도 아니다**. 기존13.760초 기록은 보존한다. 이번 실험은 후반 planner 정책의 실제 transfer를 확인했으며11.99초까지의2.01초 격차는 남았다.

마지막 checkpoint는 **2026-10-17 18:55:44 KST CLOSED**, PID177068은exit0했다. 실행은 약10분이었고 단계·arm/행동·quota·누적 model/native·시각·PID를 계속 기록/보고했다. 중간 C0 공식 완주는 `6fa6681`로 commit/push했다. 추가 실험·자동 후속 실행은 시작하지 않았다.

[집계 JSON](transfer458_result.json)·[사전 gate](transfer458_gate.json)·[진행 기록](transfer458_progress.json)·[저장 감사 코드](analyze458.py)를 제공한다. 동결source·protected/original hash와 원451 censor·456 실패를 저장 감사에서 확인했다. main dfb7a2de2178825ca5c5ce20bab01ba67052ba31·Participants·ZIP·사용자 변경·기존 백업을 보존한다. raw state/seed/명령/RNG·개인 자료는 비공개에 남겼다. 유효 종료2026년10월20일19:01:55 KST를 유지한다.

다음 판단은 저장된 실제 경로에서 남은 시간 소모와442의 다른 정책 범위를 대조하는 것이다. 이 결과로 새 실제 재시도나 예비/SEALED 사용을 자동 승인하지 않는다.
