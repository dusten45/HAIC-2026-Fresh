# 439 정적 계약 — actual 권위와 forecast 연속값 비교 분리

정적 **171개**와 저장 데이터 감사를 통과했다. **새 actual/model 적분·reset·world·actor·학습·HOLDOUT/SEALED·예비·유료 자원은 모두0**이다. 438은119행동 비용과 실패 상태 그대로이며 새 actual 완주나 시간 이득을 주장하지 않는다.

`derive_actual()`은 forecast 인자가 없다. 이전 actual GoalLedger, 자기 native pre/post 관측의 원래 투영·clock·공식 완료만으로 후보 actual ledger를 계산한다. `NativeAuthority439`는 자기 env의 성공한 미소모 dispatch ticket을 검증해 이 실제 사실을 **forecast 검증 전에 독립적으로 기록**한다. forecast는 수치 비교 자료일 뿐 값이나 commit 여부의 근거가 아니다. forecast 검증 실패는 actual 사실을 rollback하지 않고 authority를 halt시키며 다음 prepare/dispatch·대체 예측으로 재시도를 차단한다. native provenance 자체가 무효이면 commit하지 않는다. 실제 관측 기록은 모델 충실도나 안전 검증 성공과 구분한다.

기본 native 실행 권한은 없다. 미래의 명시적 실행기가 charge-before-dispatch 함수를 제공해야 하며439는 제공하지 않았다. 이 모듈은 selector나 actual runner가 아니다. 미래 연결에서도 기존 current-query/restore/RNG/receipt/guardian 게이트를 유지해야 한다. 기록된 ticket을 주입한 Python stand-in 테스트는 새로운 live dispatch 자격 증명이 아니다.

연속값 범위는 관측된6.979244×10⁻⁶m에 epsilon을 맞추지 않고 **기존 body 위치 허용 오차0.1m**와 원래 투영 함수에서 유도했다. 고유 segment 내부에서 원래 식은 아래와 같다.

`arc(x) = S[j] + clip(((x-a[j])·e[j]) / d[j]², 0, 1) * d[j]`

같은 고유 내부 segment를 실제/모델 양쪽이 선택한 경우에만 위치0.1m를 포함하는 각 좌표 box에서 이 식을 평가한다. `e, d, S`는 원래 numpy 기하 계산의 같은 고정 상수다. 각 사칙연산 결과를 `nextafter`로 바깥쪽 반올림해 원래 binary64 연산 오차도 포함한다. 완전히 같은 입력 위치는 같은 원함수 arc 점값, 같은 canonical vertex는 상수 arc임을 별도로 증명한다. **서로 다른 segment·내부/vertex 전환·모호한 투영은 통과시키지 않는다.** 기존 physical norm 비교도 그대로이며 box 축 범위는 Fraction으로 정확히 검사해 반올림 경계에서 느슨해지지 않게 했다.

progress는 원래 연산 순서도 유지한다. `(old + mod) - L/2`를 `old + (mod-L/2)`로 재배열하지 않는다. modulo는 불확실 구간 전체가 같은 winding 영역에 있을 때만 적용하고 half-period cut을 걸치면 중단한다. 새 goal은 같은 관측 progress에서 기존3.24m 규칙으로 계산하며, forecast goal 범위는 해당 goal anchor의 progress 범위를 전파한다.

전체 replay에서는 다음 항등식과 검증된 arc 연속성·같은 winding으로 중간 arc 오차를 상쇄했다.

`p[i] = p[i-1] + arc[i] - arc[i-1] - k[i]*L + rounding[i]`

`rounding` 범위는 점 입력으로 원래 식을 바깥쪽 평가한 구간에서 정확한 Fraction 이상식을 뺀 것이다. 관측 ledger 차이를 허용 오차로 쓰지 않는다. 따라서 매 행동 위치 box를 반복 더하지 않고 초기/현재 arc 불확실성과 연산 반올림 합만 남긴다. 최초166개 통과판의 과도한 누적 폭(C0 약33.15m)을 이 방식으로 줄였고, 원판/source/결과를 보존했다. 최종 C0 전체 suffix 최대 구간 폭은 **0.282664m**, P는 **0.280887m**다. 이 폭은 판정 허용 오차를 새로 고른 값이 아니라 기존 위치 범위와 각 기하 방향의 결과다.

연속 범위 안이어도 **goal의 수치 경계, ledger goal-hit, clock·age·deadline·DONE는 정확히 같아야 한다**. 양쪽 DONE가 true여도 raw progress가 goal의 반대쪽이면 실패한다. 둘 다 deadline을 놓쳐도 성공하지 않는다. actual telemetry의 progress/goal과 forecast의 progress/goal은 각각 자기 관측 기하·자기 원식에서 정확히 재계산해 변조를 거부한다. 다른 env/ticket·소모/실패 ticket·model을 actual channel에 넣기·NaN/Inf·clock/DONE/goal 뒤집기·허용 범위 안의 progress 필드 변조·source input drift·clip/안전 실패·실패 뒤 대체 forecast 재시도 등의 음성 대조를 통과했다.

| 저장 자료 | 물리 비교 | 새 ledger 비교 | 자격 범위 |
|---|---:|---:|---|
|423 C0 prefix|118/118|118행 진단 일치|model memory/ledger 원필드 누락, 소급 인증 아님|
|423 C0 suffix|71/71|71/71|기록된 전체 replay 비교|
|427 P prefix|118/118|118행 진단 일치|동일 누락 한계|
|427 P suffix|59/59|59/59|기록된 전체 replay 비교|
|427 current restore 12개×독립2|24/24|24/24|동일 현재 입력 첫 전이|
|438 첫 실제 suffix 저장 행|1/1|새 정적 규약 통과|원438 실패/ledger/cost는 그대로|

총366행을 점검했고 suffix130행에서 기하 미지원·이산 경계 반전은 관측되지 않았다. prefix236행은 Source 모델의 memory/ledger가 기록되지 않아 actual phase를 사용한 재구성 진단으로만 남겼다. 없는 증거를 새 증명으로 채우지 않았다. 저장437의 adapter 생성/capture/비교 경로와438의 기록된 live canonical·parent memory/RNG/ledger 불변 조건도 다시 확인했다. 437의 당시 live proxy 원본이 없다는 한계는 유지한다.

438의 차이는 새 규약에서 수학적 구간 내이며 실제 후보는 native 관측값과 정확히 같고 forecast 값과 다르다. 해당 현재 첫 전이 progress 구간의 폭은 **0.263746m**다. 새 규약의 정적 재검토가438을 통과 실행으로 바꾸거나 실제 ledger를 나중에 commit하는 것은 아니다.

다른 first-transition 필드도 함께 점검했다. 누적 full replay에서 C0는70행, P는58행의 after-memory가 달랐고 주요 연속 필드는 `laststeer`, `C.previous_arc`, `C.s`였다. 이 미래 memory drift를 현재 입력 복원의 통과로 완화하지 않았다. 원래 shared current 입력을 정확히 복사한 뒤 nominal memory는 **physics 전에** 계산되므로 현재 Root pose/COM velocity/angle/yaw/time·memory-before·nominal memory-after의 정확 비교는 유지한다. 저장 suffix를 이 추가 current 게이트에 넣으면 각 첫 행만 통과하고, 24개 fresh restore와438 첫 행은 모두 통과했다. 따라서 full replay 충실도와 fresh current-first 자격을 혼동하지 않는다.

body·wheel·raw hull의 기존 비영 오차 기준, phase·grass/contact/collision/damage/terminal/raw count·clipping·COM/mass/inertia의 기존 정확 조건, command·actual-root digest의 입력 identity, 같은 actual 관측을 두 경로로 읽는 canonical snapshot/RNG/memory 정확 비교는 그대로다. post velocity를 기존 속도 크기 기준과 달리 새 vector bitwise 기준으로 만들지 않았다. actual official event·DONE는 자기 env tracker/ticket에서만 오며 guardian 예측은 권한이 없다.

정적 버전166→167→170→171을 각각 보존했다. 중간 강화는 telescope 범위, DONE가 goal 경계를 숨기는 경우, active deadline root/실패 latch, native 사실 commit과 forecast 검증의 분리였고 모두 적분0이었다. 네 정적 worker의 source 확인·테스트·저장 감사 합계 CPU **70.190초**, wall **76.051초**다. 마지막171개/전체 감사는 CPU18.843초였다. 정리 검증 CPU **23.163초**는 별도이며 준비·보고·Git·import overhead는 완전 계측하지 않았다. binary64(radix2/mantissa53/round-to-nearest)를 확인했다.

한계는 명확하다. 이 범위는 **관측 후 비교**이며 사전 안전 보장이 아니다. 서로 다른 투영 branch·half-period cut·모호성·current input drift는 보수적으로 중단한다. 여러 segment를 가로지르는 민감도나 임의 geometry/새 상태의 자격을 주장하지 않는다. prefix 누락 필드와 full replay memory를 소급 인증하지 않는다. 미래 native 연결·실제 paired 재검증은439에서 수행하거나 승인하지 않았다.

v459 연구 잔여 **28,207**, 누적 실제 **1,319,857**, 예비 **84,000/사용0**은 그대로다. 기존 기록 **14,969개**와 보호 archive·고정 source·이전437/438 보고서와 비용을 검증했다. main/Participants·기존 사용자 변경·백업·선택 archive를 유지한다. 지도/seed/state/RNG/명령·원문 비교 기록은 비공개다. 종료2026년10월20일19:01:55 KST와 비자동 연장을 유지한다.

Plan SHA256: `3895d380f7ce930cb16512f8c3c4a5c3f28dfc21bbbc417192517fdf506e4305`.

[기계 판독 결과](ledger439_result.json) · [기하 구간](geometry439.py) · [ledger 비교](ledger439.py) · [native 권위 경계](authority439.py) · [438 원실패](paired438_result.md).
