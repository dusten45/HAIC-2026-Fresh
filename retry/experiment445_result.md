# 445 — H2 query-root 값 view 연결과 국소 정책 표현 반례

**동일 pre90 H2를 새로 한 번 실행해 정상 완료했다.** nominal C는13까지 안전하고14번째 path error4.759863m>3m로 실패했다. 현재 상태마다 guardian을 다시 질의한 B14는 두 사본 모두 안전·진행 조건을 통과하고 rows·최종 상태가 정확히 같았다. H1은 재실행하지 않았다. B14는 finish witness·시간 순위·실제/픽셀 승격 근거가 아니다. 원래444 H2의 기술 실패와228 ticks/7 worlds는 그대로 남는다.

## 수정 범위와 권위 경계

444는 model parent의 ForecastLedger를 Child.fork에 직접 넣어 없는 digest를 요청했다.445는 기존 **capture_context → model_ledger_view → ctx.ledger** 경로로 현재 값의 GoalLedger-schema view를 만들고 shadow 생성기에 그 view만 전달한다. ForecastLedger에 digest·actual observation·native commit 권한을 추가하지 않았다. 실제 부모의 원래 root digest는 별도 불변 binding이다. current view의 값/digest가 모델 parent 진행에 따라 바뀌는 것과 actual root 권위는 다르다.

새 ModelQuery445는 owner와 actual owner identity, ForecastLedger/GoalLedger 채널, 현재 ledger/state/native tick/clock, nominal 이후 memory, global RNG, context bytes·view 값을 묶고 spawn 전후와 shadow 평가 뒤 다시 검사한다. 현재 query용 GoalLedger 형태라는 이유만으로 native 권위가 생기지 않는다. 실제 dispatch에는 별도의 자기 native ticket·명시적 charge capability가 필요하며 이 runner는 갖지 않는다. model DONE→actual DONE 경로도 항상 거부한다.

물리·recipe·pre90 root·nominal13/14 predicate·H13/추가1 same-child 봉인·B 정책·parent/shadow 비용·상한·중단 기준은444와 같다. B는 current nominal13 독립2회, invalid일 때만 current neutral13 독립2회 후 자기 첫 명령을 적용한다. 저장 미래 step91 명령을 사용하지 않는다. 실제로 두 B 모두 decision2에서만 neutral을 골랐지만 이는 현재 예측에서 나온 결과이며 하드코딩한 시점이 아니다.

## 정적 게이트와 실행 증거

최초 정적 시도는 기존179개를 지난 뒤 새 fixture에서 context Parent의 bytes를 일반 JSON fingerprint에 넣어 직렬화 오류를 발견했다. 모델 시작 전이었다. 그180-test 결과·source·plan을 pre-model-v1에 보존하고 **기존 lossless receipt_digest/json_ready** 경로로만 바꿨다. 숫자 반올림·허용 오차·실험 조건은 바꾸지 않았다. 최초 정적 실패를 숨기거나 모델 재시도로 세지 않는다.

이후 **187개 통과**(기존179+새8)다. 새8개는 wrong channel/type, stale/변조 ledger·root/context, parent memory/RNG 변경, owner 교체, model 완료의 actual 전용과 view만으로 native dispatch 권위를 얻는 경우를 거부한다. shadow memory/ledger가 parent에 alias되지 않음도 확인했다. 원래 ForecastLedger 직접 입력은 여전히 실패한다. fixture는 기록 stand-in으로 **spawn→Experiment.new→GuardianChild→Child→fork→Stream**의 첫 shadow 생성 경로 전체를 통과했고 model/native 생성자·step을 금지해 적분0이었다.

fresh factual replay14 독립2회와 held-parent first transition이 body/wheel/raw hull·439 geometry/이산 ledger·현재 입력/memory/nominal gate를 통과한 뒤에만 predicate와 B를 실행했다. 전체 replay의 미래 memory drift와 fresh current 입력 정확성을 혼동하지 않았다. nominal 두 사본은 같은 H13 child boundary를 봉인한 후 추가1행동에서 동일하게 unsafe가 됐다. B의14행동은 model parent 자체도 모두 charge했다.

| 실행 범위 | model ticks | worlds | 결과 |
|---|---:|---:|---|
|factual replay14×2 + held first|116|3|통과|
|nominal14×2 predicate|112|2|13 safe /14 unsafe, 반복 일치|
|B parent14×2|112|2|안전·진행, 반복 일치|
|B shadows|3120|60|현재 nominal/필요 neutral 독립 반복|
|합계|**3460**|**67**|정상 종료|

모든67 observer stream·final receipt의 raw posts 합3460이 meter ticks/reserved ticks와 일치했다.28개 query root와60개 shadow가 해당 현재 값 view digest에 연결됐고 current value digest는14개로 변했지만 original actual-root digest는 그대로였다.28개의 B parent step은 각 selected shadow의 첫 물리 전이·nominal memory·이산 ledger 및 기하 progress/goal-side 비교를 통과했다. actual ledger advance·actual DONE는없다.

모델 비용은 **CPU59.981초/wall60.715초**로6656 ticks/128 worlds·CPU240초/wall480초·순차1 cap 안이다. 계획 최악6164 ticks/119 worlds는 그대로였다. 정적 비용은 두 별도 시도 CPU12.868초/14.458초이며 모델 비용에 다시 더하지 않는다. 저장 lineage 감사 CPU약1.047초는 별도이고 준비·보고·Git·일부 import 전체는 완전 계측하지 않았다.

## 해석과 남은 범위

이 결과는 **현재13까지 안전한 nominal C 뒤에 미래 guardian 개입을 생략하면 다음 전이에서 위험해질 수 있지만, 현재 상태 조건부 guardian 정책 B는 같은 국소 범위를 안전하게 진행할 수 있음**을 보여준다. 따라서 nominal-C long witness와 배포 B는 다른 정책이며 앞쪽 모든 상태의 비용을 nominal-C finish로 대표하는 데 문제가 생긴다는 국소 증거다.

B14가 안전하다는 사실은 B의 전체 finish·남은 lap 시간·최적성·일반화를 증명하지 않는다. 현재419의 finish witness 요건을 바꾸거나14-action 결과에 가짜 finish cost를 부여하지 않았다. 다음에 더 긴 B witness를 다루려면 별도 계획·비용·관측/물리 gate가 필요하다. 신규 H2 결과가 원래444 실패를 소급 통과시키지도 않는다.

## H1 최소 연장 설계 — 제안만, 현재 H1 적분0

원래 pre23·동일 nominal/fullgas 한 번·동일 path/profile을 유지한다. 저장 H13 끝의 원래 root 대비 진행은 nominal33.636m, fullgas48.496m다. **양쪽 끝보다 뒤인 다음 기존30m 격자 경계=원래 root+60m**를 공통 exit로 고른다. 미래 이득·안전 결과로 경계를 탐색하지 않는다. 새 pulse·root·weight·terminal tolerance를 찾지 않는다.

원래444 world들은 닫혔다. 따라서 H13 full state/time/controller/ForecastLedger·source hash를 복원하는 **별도로 명명한 archival continuation** 설계이며, 같은 살아 있는 child를 잇거나 과거 H13 certificate를 새로 발급하는 것이 아니다. 각 branch 두 독립 복원에서 own nominal만 최대 추가13행동(기존 H13 한 블록) 관측한다. branch별 held 복원1개로 required 사본의 첫 전이와 일치하는지 확인한다. copied current input/memory/clock/RNG·body/tile/progress/finish 복원·기존 물리/439·안전/진행 gate를 유지한다. counterfactual 실제 물리 자격은 여전히 미검증이다.

최악은 **4×13×4 +2×4 =216 model ticks/6 worlds**, hard **256 ticks/8 worlds·CPU60초/wall120초·순차1**이다. 과거 H1의316 ticks를 재청구하거나 prefix를 다시 실행하지 않는다. 숨은 solver warm-start를 저장 export가 완전히 복구한다는 증거는 없으므로 독립 restore 반복을 원래 live world 동일성으로 포장하지 않는다. 그 동일성이 필요하다면 중단하고 별도 계획을 판단해야 하며 여기서 H1을 몰래 재실행하지 않는다.

원래 root부터의 누적 raw crossing bracket·exit overshoot와 speed/yaw/heading/path/joint/omega/force/slip/contact를 비교해30m의 이득이60m에서 유지·축소·반전되는지 관측한다. 두 continuation의 소요 시간만 비교하면 출발 위치 차이를 혼동한다. 동일 시각의 다른 위치 끝 상태도 matched-exit 상태로 쓰지 않는다. 기존0.26–0.30초를 실제/lap 이득과 합산하지 않는다.

첫 technical/source/restore/channel/geometry/RNG 오류나 안전·deadline·repeat 실패/cap에서 전체 중단한다.60m에 못 닿으면 censor로 남기고26행동으로 늘리거나 경계를 앞당기지 않는다.0.08초보다 작은 효과·overlap·inconclusive 결과도 그대로 보고한다. 해결되지 않은 terminal debt·표본 상태 불일치는 승격을 막으며 새 허용 오차로 맞추지 않는다. 이 제안은 예약·실행·actual/픽셀 승격 권한이 아니다. [설계 JSON](extension445_design.json).

## 보존과 원장

새 실제 행동/reset·학습·새 seed·HOLDOUT/SEALED·예비·추가 유료 자원은0이다. v465는 새 model3460 ticks/67 worlds만 별도 기록하고 연구 잔여 **27,516**, 누적 실제 **1,320,548**, 예비 **84,000/사용0**을 유지한다.444 H2 실패·H1 국소 결과,440의44 ticks·CPU 하한 불확실성·기존 보고/backup을 유지한다. raw 상태/seed/명령/RNG는 비공개다. main dfb7a2de2178825ca5c5ce20bab01ba67052ba31·Participants·사용자 변경·보호 archive를 보존하고 종료 **2026년10월20일19:01:55 KST**를 유지한다.

[집계 결과/비용](experiment445_result.json) · [값 view binding](query445.py) · [정적 fixture](test_query445.py) · [445 실행](experiment445.py) · [저장 대조](analyze445.py).
