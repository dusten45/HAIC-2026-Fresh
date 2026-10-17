# 437 실제 paired 검증 — pre119 adapter 비교에서 중단

**새 실제 paired 완료·전체 실제 이득은 확인하지 못했다.** C0는 새 reset 후 공통 prefix118행동과 저장 pre119 full state/memory/clock/RNG 일치까지 통과했다. 첫 suffix 모델 질의를 시작하며 `TechnicalStop: read_only_actual_proxy_snapshot_mismatch`가 발생했다. 첫 실패 global-stop/no-actual-retry 규칙에 따라 **suffix 행동0, P reset0**, 추가 actual/model 재시도0으로 종료했다. 완료·lap time·paired 이득은 모두 `null`이며 미완주 시간을 추정하지 않는다.

실행 전 plan을 동결하고 정적 **130개**를 통과했다. 기존436의118개와 actual dispatch ticket/다른 env·clock·소모/실패 ticket·가짜 모델 완료·memory/ledger mismatch·호출 상한 등12개를 포함한다. 새 world/actual0회였다. 이어 저장423C0/427P 실제 replay 각각2회,12개 실제 state의 첫 전이 각각2회,425 pending 및435 저장 pending의 독립 모델 확인을 다시 수행했다. 기존 body/wheel/raw hull·phase·clipping 허용 오차를 통과했고 observer 결과는 archived unobserved433와 정확히 같았다. 선행 실측은 **1,137 ticks/35 worlds**였다. 저장 실제와의 물리 오차가 전부0이라는 뜻이나 새 높은 force 상태 자격은 아니다.

actual adapter는436 selector·recipe·gain·H13/tail308·strict bracket·조향·경로·안전/진행 기준을 재사용한다. 선택기는 실제 현재 상태에서 새 모델을 질의하도록 분리했고436의 미래 명령/선택을 입력으로 읽지 않는다. `ActualAuthority437`은 actual post-tracker 관측 provenance를 모델 관측과 구분한다. pending routing bridge는 planner 순위/actual 실행/DONE 권한이 없으며, actual ledger commit은 자기 env의 성공한 미소모 dispatch ticket·진행 clock·공식 tracker 확인을 요구한다. guardian 미래 확인으로 actual DONE를 만들 수 없다. **이 연결은 구현·정적 대조 수준이며 실제 pending 경로는 이번에 도달하지 않았다.**

최악 모델 계산은 planner64회×3 recipes×(13+308)행동×4 ticks×독립2회 =493,056 ticks, 나머지 guardian116질의×2 recipes×13×4×독립2회 =24,128 ticks, 선행 보수적1,242 ticks로 **518,426 ticks/883 worlds**였다. 실제 suffix 전이를 모델 parent로 추가 적분하지 않는다. 유지한 model cap은524,288 ticks/1,024 worlds/CPU1,800초/wall2,400초/순차 적분1개다. actual cap은prefix118씩+C0 suffix80+P suffix100 = **416 wrapper actions/reset2**, 최대 raw ticks1,766(reset warmup 포함), exclusive actual CPU180초/wall360초였다. P FIRST_LAP planner64 후 또는 pending/FINISH_CONFIRM에서는 guardian만 허용했다.

| 실제 결과 | C0 | P |
|---|---:|---:|
| reset / prefix / suffix |1 /118 /0|0 /0 /0|
| 상태 |첫 suffix 질의 전 adapter 중단|첫 실패 후 미시작|
| 공식 완료·lap time |미확인·null|미확인·null|
| 손상 |0|미관측|
| 최대 post 경로 오차 |1.37915m|미관측|
| 최대 force ratio |1.23199|미관측|
| clipped wheel samples |38 /1,888|미관측|

표의 물리 지표는 **공통 prefix만**의 값이다. 새 명령 조합·suffix 높은 force·actual pending·새 첫 전이의 충실도나 완료 자격을 얻지 않았다. prefix118개의 pre/post·명령·memory·raw tire/hull·terminal 기록은 저장423 actualC0와 정확히 같고 기존 source prefix 비교도 통과했다. actual ledger는 pre119 root 값, done=false로 유지됐다. suffix selected-first 비교·actual ledger commit은0개다. 전체 row 검사가 통과했다는 저장 요약의 Boolean을 빈 suffix 자격으로 해석하지 않는다.

중단 뒤에는 저장 상태와 코드만 분석했다. 실제 tracker 생성자는 `center/forward`를 tuple로 만들고 `complete_state`의 기존 `plain()`은 이를 list로 저장한다. 새 proxy guard는 canonicalization 없이 직접 `!=`를 사용했다. 따라서 물리 값이 같아도 이 두 필드의 표현 차이만으로 실패한다. **이 표현 대조를 실행 전 정적 게이트에 넣지 못해 prefix 비용이 발생했다.**

별도 순수 counterexample은 저장 actual 상태의 physical capture만 mock하여 tuple/list 차이를 재현했다. raw 비교는 false, 기존 `plain()`을 양쪽에 적용한 비교는 true였고, 실제 좌표0.001m 변조는 정규화 후에도 거부됐다. 추가 world·tick·reset·actual은 모두0이다. 당시 live proxy 원본을 별도 저장하지 않아 다른 차이를 배제하거나 물리 충실도를 인증하지 않는다. 실행 코드는 고치지 않았고 원계획·원소스·실패 상태를 보존했다. 제안되는 후속 작업은 **별도 정적 범위에서 같은 canonical 표현을 비교하고 live mismatch diff를 보존하도록 하는 것**이며, 실제 재시도는 수행하지 않았다.

전체 실제 사용은 **118 wrapper actions/reset1**, action raw472 ticks와 reset raw51 ticks로 합계523이다. actual exclusive CPU **11.850초**, wall **11.989초**다. 모델은 선행 검증만 **1,137 ticks/35 worlds**, CPU **37.001초**, wall **38.872초**다. 미확인 actual 호출/tick은0이다. worker 전체 CPU 48.944초/wall 50.947초와 exclusive region 밖 overhead CPU 0.092821초/wall 0.086830초도 기록했다. 정적 CPU 11.269초, 저장 분석 CPU 0.060초, 순수 진단 함수 CPU 0.050초, 정리 검증 CPU 16.133초는 별도다. 준비·보고·Git 및 저장 분석 import 비용은 완전 계측하지 않았다. 과거 비용은 다시 청구하지 않았다.

v457은 연구 잔여 **28,444→28,326**, 누적 실제 **1,319,620→1,319,738**, reserve **84,000/사용0**이다. 보호 archive·고정 source와 기존 기록 **14,137개**를 확인했다. 원격 main/공식 Participants·기존 사용자 변경·백업·선택 archive를 유지한다. 지도/seed/state/RNG/명령/원문 receipt는 비공개이며 공개 기록은 코드와 집계뿐이다. 새 학습·actor·HOLDOUT/SEALED·seed·유료 자원·reserve 사용은0이다.

437은 첫 실패로 종료했고 새 실제 paired 비교나 자동 후속 실험을 실행하지 않는다. 종료 시각은2026년10월20일19:01:55 KST로 유지하며 자동 연장은 없다. 436의 모델 이득은 이번 실제 이득으로 대체하거나 승격하지 않는다.

Plan SHA256: `09a246e51384176ea37c0259cc1e3a08dedf5e28299ed4cc5314ae3ab2bc490e`.

[기계 판독 결과](paired437_result.json) · [순수 표현 진단 코드](diagnose437_snapshot.py) · [436 모델 결과](pilot436_result.md).
