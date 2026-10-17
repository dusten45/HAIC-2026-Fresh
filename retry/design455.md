# 455 — 초기 pulse trajectory의 후반부에 기존419 planner를 적용하는 단일 비교 계약

**설계 확정만 수행한다. 새 모델/실제 적분0이다.** 454에서 확인한450–570m 손실 위치와442 planner의 선택 위치 겹침을 근거로,453 후보의 같은 native 저장 root에서 guardian nominal 기준과 기존419 시간 순위 planner를 비교한다. 기록된 네 fullgas 위치를 하드코딩하지 않는다. 이 계약은 다음 한 번의 bounded model-only 비교를 정의하며 실행 완료나 실제 승격을 뜻하지 않는다.

## 공통 root와 유일한 정책 차이

root 선택 규칙은 원래453 pre23 progress에서450m 이상인 **첫 native 행동 직전**이다. 저장 candidate의113행동 직전, pre23 대비453.716m 부근이다. 선택은 geometry 규칙으로 고정하며 미래 성적이나 recipe별 결과로 root를 옮기지 않는다. 이 root는 FIRST_LAP이고 pending/finish/deadline-missed가 아니다. 이후 저장13행동은 모두 own nominal이었다는 사실을 calibration에만 사용한다.

동일한 full state/wrapper/finish tracker·관측·controller memory-before-nominal·전역 RNG·관측 유래 GoalLedger·고정 line/profile/source를 네 실행의 immutable 출발점으로 사용한다. raw 내용과 locator/hash manifest는 비공개다. current context는 매 query의 자기 모델 부모에서 새로 capture하고 새 정책 digest에 묶는다. 과거453 query receipt나442 미래 명령을 선택 입력으로 재사용하지 않는다.

| arm | 제한된 결정 구간 | 이후 공통 제어 | 최대 자기 부모 행동 |
|---|---|---|---:|
|C0|처음부터 기존 guardian nominal reference|동일 guardian|100|
|P|처음 최대8개의 적격 FIRST_LAP·nonpending 결정에 기존419 time-ranked planner|8회 소진 뒤 동일 guardian|100|

적격 planner 결정은 선택 결과가 nominal이어도1회 소진한다. 시간 이득·속도·공간 pulse trigger로 planner를 켜고 끄지 않는다. pending/FINISH_CONFIRM에는 planner를 쓰지 않으며 남은 quota로 후반에 새 연구선을 만들지 않는다. 순서는 C0-1, P-1, C0-2, P-2로 고정한다. 전체 arm도 매번 새 부모와 새 query 자식으로 실행하고 cache·receipt 재사용·실패 후 재시도는0이다. 최초 실행 쌍의 결과로 정책·상한·두 번째 반복을 조정하지 않는다.

기존 guardian은 nominal H13 독립 두 번을 우선 검사하고, 등록된 물리/진행 거절 때만 neutralbrake H13 독립 두 번을 검사한다. fullgas로 guardian 양쪽 실패를 우회하지 않는다. 이 기준은 순수 무검사 nominal과 구분해 `GUARDIAN_NOMINAL_REFERENCE`로 보고한다.450m 이후 저장453에 neutral 개입이 없었다는 사실은 새 모델의 개입 여부를 보장하지 않는다.

## 재사용 구현과 qualification

`planner419`의 세 recipe·alias 제거·H13·3.24m 진행 목표·tail308·strict finish bracket dominance·tie/overlap 시 guardian 유지 규칙을 그대로 쓴다. `pilot436_run.planning_query`·435 observer/receipt·434 same-world tail barrier·436 pending 경로·기존 source physics·439 factual 비교/허용 오차를 재사용한다. planner 내부 각 recipe 자식은 첫 명령만 recipe를 적용하고 이후 SIGNED_C_NOMINAL H13와 같은 자식의 nominal tail≤308을 관측한다. 선택된 첫 명령을 실행하는 **모델 부모**는 매 결정 새 planner/guardian 검사를 한다. 내부 평가 tail과 부모의 후속 제어를 같은 것으로 표시하지 않는다.

실행 전에 하나의 정적 검사와 하나의 합친 fresh preflight를 수행한다. 새 미세 gate를 반복 생성하지 않는다. 기존 관련 static/current-adapter/restore/receipt/negative-DONE fixture를 재사용하고 새 부분은 root binding,8회 quota,전체 반복,cap adapter 연결만 검사한다. 정적 검사에서는 모든 실제·모델 constructor/reset/step을 금지한다.

- 기존 native source/current restore/pending qualification은 출력 목적지만 새 private stage로 바꿔 **최대1,242 ticks/35 worlds**로 fresh 수행한다. 기존442/453에서 관측한1,137/35는 참고치이고 새 실행의 성공으로 소급하지 않는다.
- 선택 root의 nominal H13을 독립 두 번 수행해 저장 native453의 같은13행동과 기존439/shape/wheel/clock/phase 기준으로 factual 비교한다. 별도 held parent는 query 중 state/memory/RNG/ledger 불변과 선택된 첫 전이 일치를 확인한다.
- 같은 root의 fullgas H13 독립 두 번과 별도 held 첫 전이도 모델 자기일관성으로 검사한다. **이 fullgas에는 새 native factual counterpart가 없으므로 실제 물리 검증이라고 쓰지 않는다.** 등록된 조기 물리 거절은 유한 관측·원가·독립 반복 일치를 보존하고 padding 없이 ineligible로 둔다. 기술/복원/숫자/권위/반복 오류는 전체 중단한다.
- 새 root 검사 전체는 최대 **216 ticks/6 worlds**다. 합친 qualification 상한은 **1,458/41**이며 새 root calibration과 old pending fixture의 결과를 각각 표시한다. 어느 것도 바뀐 counterfactual 전체 궤적의 실제 적합성을 보장하지 않는다.

## 권위, guardian과 finish witness

원래 native GoalLedger와 그 digest는 read-only다. 각 모델 부모/자식은 ForecastLedger만 전진한다. 현재 query에 필요한 GoalLedger 모양의 view는 자기 forecast 값임을 표시하며 actual provenance로 재commit하지 않는다.439의 saved-native calibration과 source 적합성 범위를 이후 새 상태에 대한 actual 안전 보장으로 확대하지 않는다.

부모가 pending이면 기존 `capture_pending`→동일 root/history/clock/RNG를 묶은 guardian proof→부모 자신의 `one`→`verify_parent_step` 경로를 쓴다. pending에서는 remaining path의 부호를 임의로 clamp하거나 FIRST_LAP으로 되돌리지 않는다. guardian FINISHED certificate는 모델 확인 자격만 주며 time ranking·부모 DONE·actual DONE를 부여하지 않는다. capture434/435의 same-world H13/tail/pending 완료 증명은 기존 의미를 유지한다.

**새 비교의 완료 witness는 자기 모델 부모가 직접 적분해 관측한 tracker official finish event와 그 확인 post뿐이다.** event/확인 시각·raw clock·tracker history·ledger DONE·source/root/policy·pending 여부·마지막 자기 행동을 묶고 원래 raw tick bracket을 보고한다. pending 자식 예측이나 planner tail 완료로 부모의 완료를 대신하지 않는다. 100행동 안에 자기 finish가 없으면 censor이고 남은 시간을 추정하지 않는다.

455에는 새로운 actual finish witness가 없다. 기존453의15.08/14.98초는 저장 native 사실이며 비교의 calibration/reference다. 미래 실제 승격을 검토할 때는 별도 승인된 계약 안에서 자기 charged native 행동·관측·tracker official event·확인 post·commit·후검증을 모두 갖춰야 한다. 모델 성공으로 이 actual gate를 열지 않는다.11.99초와의 차이도 현재는 known DEV native 기록에 대해서만 말한다.

## 한 번의 비교 전체 상한

최악 세 recipe×독립2, guardian 두 recipe×독립2를 모두 계산한다. alias/조기 거절/빠른 완료로 덜 쓰면 실제 소비를 남기며 범위를 추가하지 않는다. 네 부모 모두100행동, P 두 번 각 planner8회이므로 planner query≤16, guardian query≤384다.

| 항목 | 최대 model ticks | 최대 worlds |
|---|---:|---:|
|planner:16×3×2×(13+308)×4|123,264|96|
|guardian:384×2×2×13×4|79,872|1,536|
|네 자기 부모:4×100×4|1,600|4|
|기존 qualification|1,242|35|
|선택 root qualification|216|6|
|**전체 사전 계산**|**206,194**|**1,677**|

hard cap은 **212,992 model ticks/1,792 worlds, model worker CPU6,000초/wall9,000초, 순차1개**다. constructor 전 입력 증명·정확 복원 검사, 각 step 전 최악4tick 예약, raw posts/실제 소비 대조, exclusive meter와 주기 checkpoint를 유지한다. guardian의 FINISHED 확인은 기존 H13 안에서 끝나며 별도14번째 행동을 숨기지 않는다. source qualification·자식·반복·부모·실패 원가를 전부 위 상한에 포함한다. 정적 검사·저장 감사·준비/보고/Git 비용은 따로 기록하며 순수 solver나 전체 프로젝트 overhead 측정이라고 표현하지 않는다.

기존436 runner를 무수정 실행할 수는 없다. `planning_query`의 `Budget(524288-…,1024-…)`와 inherited meter의1024-world 상수가 이 계약과 다르다. **필요한 얇은 adapter는** 새 plan의212992/1792를 query와 meter 양쪽에 동일하게 연결하고, 검증된453의 입력 증명/constructor/restore 순서를 유지하며 actual entry point를 비활성화한다. 이전 모듈은 수정하지 않는다. physics·recipe·ranking·허용 오차·tail·pending authority를 바꾸지 않는다. 전체 query 예산 부족을 guardian-only 정책으로 조용히 바꾸지 않고 중단한다. 실행 전 정적 fixture가 이 연결을 확인해야 한다. 현재455에서는 adapter를 실행하거나 모델을 생성하지 않는다.

새 실제 step/reset/seed/학습/HOLDOUT/SEALED/예비/별도 유료 자원 cap은 모두 **0**이다. 연구 잔여27,059·예비84,000/사용0을 유지한다. CPU/wall 상한은 지정 cloud의 이전 비용에 근거한 보수적 제한이며 완료 예상시간이 아니다. 기한 **2026-10-20T10:01:55Z, KST10월20일19:01:55**와 worker 상한 중 먼저 오는 경계에서 중단하고 자동 연장하지 않는다. 시작 전에 남은 시간과 고정 상한을 확인한다.

## 사전 중단, 연구 판단과 실제 승격

첫 source/qualification/restore/numeric/nonfinite/reverse/phase/clock/권위/부모 또는 RNG 변조/독립 반복/비용/기한 오류는 전체 중단한다. 부모 자체 unsafe·progress miss·nonfinish terminal, guardian nominal/neutral 양쪽 불가도 중단하며 다음 arm을 시작하지 않는다. 이미 완료한 사실·소비·미완료 arm을 보존한다. recipe 자식의 조기 H13 물리 거절은 기존 `audit431.audit_pair`가 인증하는 유한 물리 토큰만 ineligible로 처리한다. **H13 미만 INFEASIBLE/진행 deadline 거절은 이 early receipt가 지원하지 않으므로 전역 중단한다.** guardian의 기존 valid=False와 완전 H13/정규 tail receipt가 지원하는 진행 거절은 각각 기존 경로의 의미만 유지한다. 기존453 guardian의 추가 status 허용을 planner early 경로에 가져오지 않는다. 다른 오류를 물리 거절로 바꾸지 않는다. cap 내 미완료는 censor이며 완료를 위해 scope를 늘리지 않는다.

각 query의 required/repeat, 전체 arm 두 반복의 명령·semantic rows·상태·ledger·tracker·완료 bracket이 label/ID를 제외하고 일치해야 한다. 반복 불일치 시 평균이나 빠른 결과를 선택하지 않는다. 두 arm 모두 완료했을 때만 root부터의 직접 전체 finish 차이를 계산한다. 새 root 이후510/570m 등의 이미 정의된 경계와 제어/guardian 변화는 진단으로 보고하며 국소 이득을 전체 성적으로 합산하지 않는다.270/450m crossing은454의 저장 참조일 뿐 이번 새 부모가 관측한 값이 아니다. 새 root 이전의 궤적을 재구성 적분하지 않는다.

**연구 판단에는0.10초의 일률적 문턱을 두지 않는다.** 아래 결과를 모두 보존한다.

- planner가 nominal을 유지하거나 bracket이 겹치면, 현 root/세 recipe/제한8회에서 기존419가 강건한 개선을 찾지 못했다는 정보다. 이를 모든 후반 제어 가설의 반증으로 확대하지 않는다.
- 작은 양수는 효과 크기·bracket·개입 위치·비용을 그대로 기록한다. 음수는 receding 선택과 tail 평가의 차이·제동/상태 반응을 조사할 근거이며 숨기거나 기준을 바꾸지 않는다.
- strict positive 전체 finish dominance와 독립 일치·안전/진행/권위 통과는 다음 모델 연구 후보로 유지할 근거다. 절대 격차와 비용 대비 정보가치를 함께 판단하며 자동 후속 실행은 없다.
- **실제 승격은 별도 결정이다.** 이 비교의 크기나 부호와 관계없이 새 actual gate는 닫혀 있다. 실제 실행을 제안하려면 전체 결과·새 상태 factual 범위·미해결 fidelity·완료 경로·별도 actual 예산/중단 기준을 검토한다. 모델 이득0.10초나11.99초 모델 완료만으로 native 성적·픽셀 일반화·공식 서버 성공을 주장하지 않는다.

현재 단계 산출물은 이 계약과 [454 집계](saved454_result.md)뿐이다. 실제 정책 차이·원가 상한·부정/작은 결과의 해석까지 실행 전에 고정했으며 새 모델 실행 결과는 없다. 보호 main/Participants/ZIP/백업·기존 사용자 변경과 원래451 censor를 보존한다.
