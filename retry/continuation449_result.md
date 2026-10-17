# 449 — native wrapper-end 이후 +90m 모델 비교

**원래 pre23 root부터 +90m까지 누적 시간 이득은 [0.36,0.40]초**다. baseline은 [2.04,2.06]초, candidate는 [1.66,1.68]초다. native448 +60m의 [0.34,0.38]초와 겹치므로 **이득 증가를 입증하지 않았다.** 두 branch 모두 유한 +90m 모델 crossing과 선행 게이트를 통과했다. candidate의 +90m는 모델 예측이며 새로운 native transfer나 전체 lap 결과가 아니다.

## 고정한 root·시간·게이트

native448의 실제 wrapper-end 전체 physical/wrapper/관측 hash·controller memory·자기 관측 GoalLedger를 그대로 썼다. nominal의 최종 전체 상태가 저장 factual442 pre43의 nominal 계산 전 상태와 정확히 같음을 확인했다. global RNG 원상태는448 마지막 current-query의 보존 blob을 복원하되 Python/NumPy 각각의 protocol5 해시를 native 종료 기록과 정확히 대조했다. 새 seed를 고르거나 기록에 없는 native RNG를 만들어 넣지 않았다. 각 constructor의 기존 body/tile/progress/finish 복원 gate도 유지했다.

정적 **214개**와 저장 감사가 첫 시도에 통과했다. branch마다 독립2회와 별도 held1회를 만들었고, 모두 own nominal로 최대13행동 또는 +90m를 포함하는 wrapper까지 실행했다. baseline6행동의 두 사본이 factual442의 해당6행동에 대해 기존439 body/wheel/raw hull·기하 progress/goal·이산 clock/age/deadline/DONE source gate를 통과했다. fresh-current 첫 전이의 command·memory/input은 정확 비교했고, 이후 future replay memory drift를 fresh-current 일치로 소급 인증하지 않았다. 이 baseline source·정확 반복·held 첫 전이가 끝난 후에만 candidate world를 만들었다.

| branch | 관측된 native wrapper 누적 ticks | 새 모델 행동/사본 | 새 모델 crossing ticks | 원래 root부터 누적 시간 |
|---|---:|---:|---:|---:|
|nominal|80|6|22–23|2.04–2.06초|
|candidate|64|5|19–20|1.66–1.68초|

계산은 `(실제 전체 wrapper 누적 ticks + 모델 crossing ticks)/50`다. +60m crossing bracket을 이어 붙이지 않았고 candidate의 마지막 native wrapper 안 남은 시간을 중복 계산하지 않았다. baseline80과 candidate64 ticks는 과거 소비한 실제 시간이며 이번 비용에 재청구하지 않았다.

독립2회의 모든 rows·최종 state·memory가 정확히 같았고 held의 state/memory/RNG 보존, 자기 첫 명령·물리·memory 비교가 통과했다. 자기 native 원장은 모델에서 갱신되지 않았으며 미래 candidate는 actual-qualified가 아니다. 닫힌 native world의 solver warm-start 내부 상태를 복원했다는 주장도 하지 않는다. 최초 실행 오류·실험 재시도·censor는 없었다.

## +60m 이후 변화와 terminal state

+60→90m의 보수적인 시간 구간은 nominal[0.44,0.48]초, candidate[0.42,0.46]초다. 누적 이득의 변화 구간은 **[−0.02,+0.06]초**다. 이는 +60m native bracket과 +90m mixed native/model bracket에서 얻은 보수 구간으로, 추가30m에서 확실한 이득 증가도 감소도 입증하지 않는다. 기존 +60m 이득과 더하지 않는다.

| +90m 양끝 body 표본 범위 | nominal | candidate |
|---|---:|---:|
|속력 m/s|71.524–72.193|76.678–77.343|
|yaw rad/s|−0.09313–−0.08918|−0.06055–−0.04054|
|path error m|0.00147–0.00839|0.04319–0.06668|
|절대 heading error rad|0.00828–0.00916|0.01431–0.01577|

candidate의 path error는 native +60m의0.14832–0.19560m보다 줄었고 heading error도0.03909–0.03924rad보다 줄었다. 더 높은 속력은 남는다. +90m의 candidate yaw 절댓값은 오히려 nominal보다 작다. 상태 차이를 모두 불리한 debt로 분류하거나 완전 일치를 진전 조건으로 삼지 않는다.

동일 lower crossing preclip phase의 force ratio 최대는 nominal0.77807/candidate0.77667, lateral slip 범위는 −0.17954..−0.12804/−0.15426..−0.00446m/s다. joint/omega/longitudinal slip 집계도 [결과 JSON](continuation449_result.json)에 보존했다. 이 표본 범위는 연속시간 보장 구간이 아니다. **첫 큰 제동·코너 이후의 terminal debt와 native +90m transfer는 아직 미판정**이다. 초기 가속 구간의 path/heading 수렴만으로 전체 영향 소멸을 주장하지 않는다.

## 비용과 다음 검증 규모

새 모델 비용은 nominal6×독립2×4=48, candidate5×2×4=40, held2×4=8로 **96 ticks/6 worlds**, CPU **3.244초**/wall **3.290초**다.6 observer stream의 raw posts96과 reserved96이 일치했다. planned216/6·hard256/8·CPU60초/wall120초·worker 순차1을 지켰다. held world를 보존하므로 동시 live model world 최대는2다. 추가 실제/reset·학습·새 seed·HOLDOUT/SEALED·예비·별도 유료 자원은0이다.

정적 CPU18.501초/wall18.605초, 저장 감사 약0.379초는 별도다. 전체 준비·보고·Git·일부 import overhead는 완전 계측하지 않았다. v469의 연구 잔여 **27,436**, 누적 실제 **1,320,628**, 예비 **84,000/사용0**은 변하지 않았다. 마지막 모델 checkpoint는 **2026-10-17 16:24:49 KST**다.

30m씩 더 보는 방식은 물리 계산 자체는 싸지만, 이번에는 정적 검사가 모델 실행보다 약5.7배의 CPU를 썼다. 같은 형태를 반복하면 source/world setup·보고 overhead와 복원 경계가 늘며, 계속 가속 구간만 확인해 첫 제동에서의 이득 소모라는 핵심 질문을 미룰 수 있다. 이미 종료한449 model endpoint를 다시 복원해 작은 구간들을 계속 연결하기보다 **동일 native448 root에서 더 긴 동일-child 관측**으로 전환할 가치가 있다.

다음 우선 제안은 고정 **원래 root+270m**다. 저장 factual442의 첫 이후 brake run은63–70행동, 원래 root+192.3..239.1m이고 다음 brake run은+279.2m에서 시작한다. +270m는 첫 큰 감속과 재가속을 포함하며 알려진 pre91 guardian 경계(+326.9m) 전이다. candidate의 미래를 새로 관측하거나 이득이 좋아지는 지점을 찾아 선택하지 않았다.

native448 두 root부터 own nominal, 독립2회+held1회/branch, **각 최대64행동(H13+같은 child의 추가51)**, baseline 첫13 source gate를 같은 trajectory에서 재사용한다. worst `4×64×4+2×4`=**1032 ticks/6 worlds**, hard1152/8·CPU90초/wall150초·actual0을 제안한다. 이번96틱 기반 단순 CPU 외삽은 약34.9초이나 보장은 아니며 hard limit에서 중단해야 한다. 첫 오류에서 전체 중단·미도달 censor·작거나 겹치거나 음수 효과 보존을 유지한다. 처음부터 새 root/H13을 적분하므로 그 비용은 새로 세고 과거449 비용을 환급하지 않는다. **이 안은 실행·예약하지 않았다.**

## 11초대 목표와 전체 lap으로 넘어갈 조건

저장442 C0의15.08초에서11.99초까지는 전체3.09초 차이다. 현재 mixed 국소0.36–0.40초는 lap 이득도,442 P13.76초와 합성된 이득도 아니다. 작은 양의 효과를 계속 더해11초대를 주장할 수 없다.

현재 own nominal 계약은 바로 전체 lap 비교로 승격할 수 없다. 기존 pre91의 own nominal H13 unsafe witness가 있고442 실제 C0에도91의 neutral override가 있다. 더 긴 구간에서 안전하게 이득이 남는지 확인한 뒤, 필요한 guardian을 포함한 **전체 정책을 별도로 동결하고 수정된 두 trajectory의 current-input SourceG1·fallback·pending/native DONE 경계를 검증**해야 한다.445의 다른 root에서 통과한 B 증거만으로 새 trajectory 전체를 승인하지 않는다. 선택된 정책의 안전/진행·시간 증거가 조건이며 두 branch의 모든 terminal state가 같을 필요는 없다.

그 조건을 통과했을 때의 **추후 native 전체 lap pair 예시 상한**은220행동/arm·합계440/reset2다. prefix22씩 이후 최대396 current 결정, 최악2 recipes×독립2×H13×4=208 ticks/결정, 기존 full pending/source allowance1242 + pulse/source216을 포함하면 planned **83,826 ticks/1,625 worlds**다. hard98,304/1,792·model CPU3000초/wall4200초, actual exclusive CPU240초/wall480초·순차1의 비용 검토가 필요하다. 이는 현재 승인이나 예약이 아닌 guardian 정책을 새로 정할 때의 조건부 예시다. 예정된 대안 shadow의 예상 rejection과 실제 선택 정책의 안전 실패도 사전에 구분해야 하며449의 오류 중단 원칙을 몰래 바꾸지 않는다.

실제 전체 pair에서는 두 arm 모두 자기 native 공식 finish event로 완료하고 같은 reset 이후 기준의 lap 시간을 직접 비교해야 한다. 첫 source/fidelity/ledger/memory/RNG/선택정책 안전/기술 오류에서 중단하며 재시도하지 않는다. 더 긴 모델 비교가 이득을 지지하지 않거나 source/안전 gate를 통과하지 못하면 큰 lap 성능 실험으로 승격하지 않는다. source/pending/정책 구성의 최종 코드와 비용 원장은 새 실행 전에 동결해야 한다. [다음 설계와 비용/게이트](next449_design.json)에 명시했으며 **+90m 이후 실험은 이번에 하지 않았다.**

유효 종료 **2026년10월20일19:01:55 KST**, main dfb7a2de2178825ca5c5ce20bab01ba67052ba31·Participants·보호 ZIP·기존 사용자 변경·backup을 유지했다. private state/seed/명령/RNG는 공개하지 않았다.

[실행](continuation449.py) · [native root 복원 계약](root449.py) · [정적 fixture](test_root449.py) · [저장 분석](analyze449.py).
