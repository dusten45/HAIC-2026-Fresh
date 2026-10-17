# 444 — H1 국소 모델 이득과 H2 ledger 입력 기술 중단

**H1은 완료, H2는 첫 B shadow 생성 중 기술 오류로 전체 중단했다.** H2의 새 nominal13/14 predicate는 확인됐지만 B14는 미관측이다. 오류 뒤 experimental source 수정·모델 재실행·대체 root/pulse·추가 실험은 없다. 두 계획은 실행 전에 따로 동결했고 순차 별도 process/원장으로 실행했다. 정적179개와 저장 자료 감사가 통과했으며 actual 행동/reset·학습·새 조건 seed·HOLDOUT/SEALED·예비·추가 유료 자원은0이다.

## H1 — 초기 타이밍 기회의 모델 반증 결과

pre23의 현재 FIRST_LAP/nominal brake>0/30≤현재속력<현재target/정방향/네 wheel road contact 조건을 확인했다. snapshot·current nominal/memory/ledger를 실제442 기록과 연결하고, 기록된 실제13행동 replay 독립2회 및 held-parent first transition을 먼저 통과했다. 미래 실제 명령은 물리 calibration에만 사용했고 후보 선택·후보 rollout은 current state의 own nominal에서 계산했다. actual ledger는 모델이 갱신하지 않았다.

calibration은 body/wheel/raw hull·phase/contact/grass/collision/damage/clipping·439 기하 구간과 goal-side/clock/age/deadline/DONE를 통과했다. copied-current 첫 입력/memory/nominal은 정확히 같았다. 이후 전체 replay의 미래 memory drift는 current 입력 자격과 구별했다. nominal13과 첫 fullgas(기존 nominal steering 유지) 후 own nominal13 각각 독립2회가 모두13행동 안전·진행 조건을 통과했고 각 pair의 전체 signature가 정확히 같았다. 새로운 counterfactual 상태를 실제로 검증한 것은 아니다.

| 공통 원래 arc +30m | nominal | 첫 fullgas 후 nominal |
|---|---:|---:|
|raw 도착 tick bracket|47–48|33–34|
|도착 시간 bracket|0.94–0.96초|0.66–0.68초|
|raw 출구 양끝 속력 표본 범위|35.016–35.645m/s|43.260–43.968m/s|
|출구 양끝 yaw 표본 범위|0.847–0.962rad/s|0.820–1.560rad/s|
|출구 양끝 path error|0.216–0.228m|0.271–0.280m|
|출구 양끝 front joint 표본 범위|0.07178rad|0.04302–0.05006rad|
|출구 wheel omega 표본 범위|58.571–74.640|72.785–91.049|
|출구 preclip force ratio 표본 범위|0.387–0.791|0.215–0.914|

모델 국소 시간 이득은 **[0.26,0.30]초**다. 0.08초 사전 기준을 넘었고 표본 출구 속력도 더 높다. 이는 필요한 선행 제동이 모든 초기 under-target brake를 반드시 정당화한다는 단순 설명에 대한, 이 root의 첫 fullgas primitive에서 얻은 양성 정보다. 속도·제동 최적화 전체를 입증하거나 새 weight/pulse 탐색으로 확대하지 않았다.

terminal debt는 해결하지 못했다. 공통 exit에서도 yaw/joint/omega/force 및 path error가 다르고 raw bracket 양끝은 연속시간 상태의 보장 구간이 아니다. 같은13행동=1.04초 끝에서 속력은38.276 대55.869m/s, yaw는+0.361 대−0.526rad/s, path error는0.110 대0.498m이지만, 이는 서로 다른 위치의 상태라 matched-exit debt로 단정할 수 없다. 더 높은 출구 속도가 다음 코너에서 비용을 만들지 않는다는 검증은 없다. 따라서 **timing 기준 통과와 다음 단계 승격은 별개**이며 자동 승격은false다. 다음에 배울 핵심은 공통 exit의 상태·후속 안전 조건을 맞춘 효과와 counterfactual 물리 전이다. 이 이득을442의1.320초 또는13.760초에 더하거나 빼지 않는다.

H1 지출은 **316 ticks/7 worlds**, CPU5.338초/wall5.361초다. calibration104 + held4 + 네 arm208로 산술과 일치한다.512 ticks/8 worlds·CPU90초/wall150초 상한을 지켰다. [별도 H1 결과](hypothesis444_H1_result.json).

## H2 — predicate는 성립, B 결과는 기술 오류로 미관측

pre90의 factual14 replay 독립2회·held gate가 통과했다. 같은 nominal child가 H13에서 기존 같은-world snapshot/명령/memory/RNG/ledger barrier를 봉인한 뒤 단 한 행동을 더 기록했다. nominal 두 사본은 **13까지 안전,14번째 path error4.759863m>3m**로 정확히 반복됐다. 이 물리 음성 결과는 사전 predicate의 성립이며 기술 오류나 전체 방법군 부정이 아니다.

그 다음 B의 첫 current query를 준비하는 중 다음 입력 계약 오류가 발생했다.

```
guardian_parent → new(snapshot(parent), before, parent.ledger)
→ GuardianChild/Child → ForecastLedger.fork(ledger)
→ ledger.digest()
AttributeError: ForecastLedger has no attribute digest
```

`parent.ledger`는 모델 prediction 채널의 ForecastLedger다. Child 생성자가 기대하는 query-root value view 대신 이를 직접 전달했다. 물리 world 생성·restore는 이미 청구·확인된 뒤 ledger fork에서 실패했으므로 이 world 비용도 남긴다. **B parent 전이0, B shadow 적분0**이다. B가 안전/위험하거나 이득이 있다고 판정할 자료가 없다. nominal predicate를 통과한 것만으로 배포 정책 조건부 witness의 전체 가설을 입증하지 않는다.

이는 **입력 타입/실행기 연결 기술 오류**이며, physical refutation·표현 가설 반증·native failure가 아니다. 기존 코드에는 capture_context의 model_ledger_view와 `ctx.ledger`를 자식에 넘기는 경로가 있지만 이번 runner는 그 경계를 생략했다. 이 사실을 saved source/traceback으로 확인했을 뿐 수정·재실행하지 않았다. 미래 복구에서는 model current value view·query binding·immutable actual-root 권위를 정적 검사로 먼저 구분해야 한다. ForecastLedger에 digest를 임의로 추가해 actual authority처럼 다루는 처방을 제안하거나 실행하지 않는다.

H2 지출은 **228 ticks/7 worlds**, CPU4.948초/wall4.969초다. factual replay112 + held4 + nominal14 두 사본112이고 B 적분은0이다.7 worlds 중 B parent와 실패한 첫 shadow 두 world는 첫 step이 없다. model constructor가 완료된 shadow도 청구를 취소하지 않는다.6656 ticks/128 worlds·CPU240초/wall480초 안에서 종료했다. [별도 H2 결과](hypothesis444_H2_result.json).

## 중단·비용·보존

| 단계 | 결과 범주 | model ticks/worlds | 다음 판단 |
|---|---|---:|---|
|H1|정상 완료·국소 모델 양성 효과|316/7|상태 debt·실제 전이 미해결|
|H2 nominal predicate|정상 물리 음성으로 predicate 성립|112/2, H2 비용의 부분집합|B 비교에 진입 가능했음|
|H2 B 연결|기술 오류·전체 중단|B 적분0, 추가 world2|복구 전 정적 타입/권위 경계 확인 필요|

총 **544 ticks/14 worlds**가 reserved ticks 및 저장 observer raw posts 합과 일치한다. H1/H2 총량은 각각의 비용을 더한 값이며 predicate·qualification·world 비용을 다시 더하지 않는다. raw 상태·지도/seed·명령·RNG·traceback 원문은 비공개로 보존하고 공개 JSON에는 집계 결과와 표본 범위만 실었다. B 구현의 실패 byte는 동결 plan hash와 같다.

정적179개는 CPU14.261초/wall14.367초의 별도 process다. saved closure와 preparation/report/Git/import의 전체 비용은 완전 계측하지 않았으며 실제/model worker 비용과 이중 합산하지 않는다. 새 native 사용0이므로 v464의 연구 잔여 **27,516**, 누적 실제 **1,320,548**, 예비 **84,000/사용0**을 유지한다. 기존440의44 ticks·CPU 하한 불확실성과 모든 이전 실패 비용도 그대로다.

H2 기술 오류를 확인한 뒤 전체 실험을 중단했고 새 모델 생성/step·actual/reset·학습·새 seed·HOLDOUT/SEALED·예비 사용·추가 유료 자원은 없다. parent의 승인 종료 **2026년10월20일19:01:55 KST**, main dfb7a2de2178825ca5c5ce20bab01ba67052ba31·Participants·보호 archive·사용자 변경·백업을 보존한다. [집계/비용](experiments444_result.json) · [실행 구현](experiment444.py) · [저장 대조 코드](analyze444.py).
