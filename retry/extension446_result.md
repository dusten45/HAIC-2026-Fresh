# 446 — H1 archival continuation의 공통+60m 비교

**두 독립 archival 복원 반복과 held 첫 전이를 통과했고, 원래 root+60m에서 누적 모델 이득 [0.34,0.38]초가 관측됐다.** 기존+30m의[0.26,0.30]초보다 사라지지 않았지만 이는 같은 pulse의 누적 비교이므로 두 이득을 더하지 않는다. 원래444 live world의 연속 실행·실제 물리 검증·lap 개선으로 표시하지 않는다. H2의 더 긴 B witness도 실행하지 않았다.

## 고정한 실험과 복원 한계

445에 사전 명시한 원래 pre23·동일 두 branch·+60m 경계·추가 최대 H13을 그대로 썼다. 과거 nominal/fullgas H13 끝 상태·time·tile/finish·controller memory·전체 ForecastLedger와 source hash를 복원했다. current 값 view는 constructor 입력 형식에만 쓰고, archived full model ledger의 original root digest·goal hit 이력·clock을 observer 부착 전에 복구했다. actual ledger나 native 권위는 만들지 않았다. 새로운 fullgas pulse 없이 **두 continuation 모두 own nominal만** 실행한 것을 기록과 대조했다.

각 branch에서 같은 archive의 독립 복원2회와 held 복원1회를 생성했다. 초기 body/tile/progress/finish의 기존 정확 gate, memory/ledger/time 복원 및 RNG hash를 확인했다. RNG는 보존된 archive global state를 복원했으며 새 조건 seed를 고르지 않았다. held는 nominal을 미리 계산한 채 두 continuation 동안 state·memory·RNG가 그대로임을 확인하고, 이후 자기 첫 전이를 required 사본 첫 전이와 기존 body/wheel/clip 및 정확 nominal-memory 기준으로 비교했다. 두 continuation의 rows·최종 상태 signature는 정확히 같았다.

이 gate는 **독립 복원의 일관성**이다. 닫힌 원래 world의 숨은 solver warm-start/contact 내부 상태가 완전히 이어졌다는 증명이 아니다. archive H13 snapshot은 새 archival root의 출처이지 과거 같은-live-child tail certificate가 아니다. 이번에 과거 prefix를 다시 실행하거나 새로운 실제 fidelity를 측정하지 않았다. 원래 source export의 복원 한계를 유지한다.

## 원래 root부터의 crossing bracket

| 공통 경계·비용 | nominal | 원래 첫 fullgas 후 nominal |
|---|---:|---:|
|보존 H13 끝의 원래 root 대비 진행|33.636m|48.496m|
|새 continuation 행동, 사본당|7|3|
|continuation 내+60m raw tick bracket|27–28|9–10|
|continuation 소요 시간 bracket|0.54–0.56초|0.18–0.20초|
|보존 prefix52 ticks를 포함한 누적 bracket|**1.58–1.60초**|**1.22–1.24초**|

crossing은 실제 저장된50Hz 위치 표본의 bracket이며 보간한 공식 시간이 아니다. prefix52 ticks는 이미 소비된 같은 old13행동의 시간 출처이며 이번에 다시 적분·청구하지 않았다. 각 wrapper의 첫 crossing이 들어 있는 행동까지 관측했고 그 wrapper 전체 raw ticks의 안전 조건도 유지했다. 13행동 cap에 걸린 branch나 미도달은 없었다.

+60m 누적 시간 이득은 **[0.34,0.38]초**다. 과거30m 결과는 같은 root와 같은 한 번의 pulse의 더 이른 관측이므로 별도 가산 이득이 아니다.446의 concat clock은 old13관측과 새로 복원된 continuation의 합이며, 원래 live solver를 계속 관측한 것과 동등하다고 가정하지 않는다.442의1.320초 또는13.760초에도 더하거나 빼지 않는다.

## 공통 경계의 terminal debt

| +60m 경계 양끝 body 표본 범위 | nominal | fullgas branch |
|---|---:|---:|
|속력 m/s|56.114–56.767|61.897–62.568|
|yaw rad/s|−0.03799–−0.01160|−0.19583–−0.00756|
|path error m|0.00418–0.02797|0.14832–0.19560|
|절대 heading error rad|0.02170–0.02193|0.03909–0.03924|

body는 각각 crossing bracket 양끝의 실제 저장 표본이다. nominal의 upper body 표본은 마지막 wrapper post에서도 읽었으며 없는 상단 preclip force 표본을 만들어 넣지 않았다. tyre 비교는 두 branch 모두 crossing을 일으킨 **lower raw boundary의 동일 preclip phase**로 맞췄다.

| lower crossing preclip의 wheel 전체 범위 | nominal | fullgas branch |
|---|---:|---:|
|joint angle rad|0.0000001–0.001382|0–0.002430|
|wheel omega|99.566–110.925|109.908–122.045|
|force ratio|0.439–0.768|0.448–0.781|
|lateral slip m/s|−0.141–0.060|−0.363–0.423|
|longitudinal slip m/s|−2.306–3.744|−2.332–3.793|

출구 속력 차이는 남아 있고 fullgas의 path/heading 오차와 yaw/slip 표본도 다르다. 관측 범위 안에서는 기존 안전/진행 조건을 통과했지만 **terminal debt 해소는 미판정**이다. 더 높은 속력 자체를 debt라고 하거나, 모든 상태가 같아야 유익하다고 요구하지 않는다. 반대로 이 유한 국소 범위의 안전·force ratio만으로 이후 코너/actuator/접촉 비용이 없다고 결론내리지 않는다. branch 간 상태 차이에 기존 actual-vs-model fidelity 허용 오차를 잘못 적용하거나 결과에 맞춘 새 수렴 임계값도 만들지 않았다. 표본 범위는 연속시간 상태의 보장 구간이 아니다.

## 비용·중단·다음 최소 검증안

실사용은 nominal7행동×독립2×4=56, fullgas3×2×4=24, held first2×4=8로 **88 model ticks/6 worlds**다. reserved88과6 observer stream의 raw posts88이 일치했다. 계획 worst216/6, hard256/8·CPU60초/wall120초·순차1을 지켰다. 모델 meter 비용은 **CPU3.263초/wall3.263초**다. 기존 H1의316 ticks와 과거52-tick prefix 시간을 새 비용에 더하지 않았다.

모델 전 최초 static fixture에서 ForecastLedger import 누락을 발견해189-test 오류 결과·source·plan을 보존했다. 명시적 import만 수정하고 **193개 정적 통과** 후 모델을 한 번 실행했다. Root·pulse·경계·허용 오차·상한 변경이나 모델 재시도는없다. 정적 두 시도 CPU13.666초/17.960초는 별도이며 모델 비용에 이중 합산하지 않는다. saved audit CPU약0.077초 외 준비·보고·Git·import 전체는 완전 계측하지 않았다.

다음 최소 검증 질문은 **H13의 archival restore 경계 없이도+60m 이득이 남는가**다. 원래444 H1의 branch별 before-constructor/current-input proof에 고정된 같은 pre23 physical root·memory·ledger·global RNG를 써서 동일 두 branch를 새 모델로 시작해 H13에서 같은 child의 snapshot/명령/memory/RNG/ledger를 봉인하고, 그 살아 있는 child만+60m까지 추가 최대13행동 이어가도록 제안한다. branch별 독립2회와 held 첫 전이1회를 유지한다. nominal H13의 factual442 물리/439 비교는 해당 계획의 baseline 표본을 재사용해 cost를 한 번만 센다. candidate를 열기 전에 baseline/source gate를 통과해야 한다.

제안 worst **4×(13+13)×4 +2×4 =424 ticks/6 worlds**, hard512 ticks/8 worlds·CPU90초/wall150초·순차1·actual0이다. 이는 새로 승인된다면 새 호출 비용이며 기존88/316의 환급·재청구가 아니다. 과거 H13 데이터와 일치하지 않으면 차이를 보존하고 중단한다. 이후 첫 source/restore/geometry/ledger/memory/RNG/repeat·기술·안전·진행 오류에서 중단하며,60m에 못 닿으면 censor로 남기고 root/pulse/경계/추가13 범위를 바꾸지 않는다. 같은-live 관측과 이번 archival concat의 시간·상태 차이를 비교할 뿐, 작은 효과/overlap도 숨기지 않는다. 실제 transfer와 픽셀296/전체 lap 승격은 여전히 별도 문제다. **이 다음 설계는 실행·예약하지 않았다.** [다음 제안](next446_design.json).

새 실제 행동/reset·학습·새 seed·HOLDOUT/SEALED·예비·추가 유료 자원은0이다. 더 긴 B witness를 추가하지 않았으며445 H2 증거와444/440 실패·비용 불확실성도 유지했다. v466의 연구 잔여 **27,516**, 누적 실제 **1,320,548**, 예비 **84,000/사용0**은 그대로다. main dfb7a2de2178825ca5c5ce20bab01ba67052ba31·Participants·보호 자료·기존 사용자 변경·backup과 종료 **2026년10월20일19:01:55 KST**를 유지한다. raw 상태/seed/명령/RNG는 비공개다.

[집계 결과/비용](extension446_result.json) · [실행](extension446.py) · [복원 계약](archive446.py) · [정적 fixture](test_archive446.py) · [저장 분석](analyze446.py).
