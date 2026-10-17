# 443 — 아직 바꾸지 않은 시작~pre119의 시간 손실과 다음 반증 설계

**새 실제/model 적분·reset·학습은0**이다. 최신442의 C0/P 전체 궤적만 재분해했다. 공통 prefix118행동은 **9.44초**, 기준선 진행의 **60.1354%**이며 P13.760초의 **68.60%**다. 442의1.320초 이득은 그 뒤에서만 생겼다. 다음 우선순위는 초기/중간 가감속 타이밍과, 앞쪽에서 nominal-C finish witness가 실제 guardian 정책을 표현하지 못하는 문제다. 두 가설은 겹친 이득으로 더하지 않는다.

현재 P와11.99초의 산술 차이는1.77초,11.00초와는2.76초다. 회수 가능한 이득·물리적 하한·달성 가능성은 검증하지 않았다. prefix를 바꾸면 pre119의 속도·조향·타이어·위치가 달라져 기존 P suffix4.32초도 그대로 재사용할 수 없다. 기존1.32초에 국소 실험 이득을 단순 가산하지 않는다.

## 412 원칙으로 최신 전체 시간 장부 계산

양의 첫 통과 구간에서 D는 기준 arc 진행, d는 hull origin 경계 chord, V는 양끝 COM 속력 평균, H는 양끝(속력×차체 정방향과 경로 접선의 내적) 평균, Q는 양끝(COM 속도 벡터와 접선의 내적) 평균이다. 고정268 profile의 제곱 속도 선형 보간에서 τr=∫ds/r(s)를 계산했다.

```
A=D/V−τr; Bh=D/H−D/V; Bs=D/Q−D/H
C=d/V−D/Q; R=dt−d/V
dt=τr+A+Bh+Bs+C+R
(d−D)/V=Bh+Bs+C  # 별도 진단, 다시 더하지 않음
```

| 초 단위 장부 | C0 전체 | P 전체 | 공통 prefix | P suffix |
|---|---:|---:|---:|---:|
|고정 참조 시계 τr|+10.019226|+10.013977|+6.247227|+3.766751|
|속도 추종 A|+5.248898|+3.889398|+3.354294|+0.535104|
|heading Bh|+0.047595|+0.063424|+0.032698|+0.030726|
|body-slip Bs|-0.011307|-0.010727|-0.008276|-0.002451|
|경로 metric C|-0.178858|-0.149665|-0.122812|-0.026853|
|경계 적분 잔차 R|-0.065554|-0.066407|-0.063131|-0.003276|
|참조 범위 밖 경계 시간|0.020000|0.020000|0.000000|0.020000|
|합계|**15.080000**|**13.760000**|**9.440000**|**4.320000**|

각20ms raw hull pre-state를 사용해 공식 event의 실제 저장 경계까지만 계산했다. C0는16.100초 event와16.120초 확인, P는14.780초 event와14.800초 확인을 구분했다. 공식 event 상태가 실제 raw 표본에 있어412의 거친 마지막 wrapper 미관측을 보완할 수 있었다. 확인 tick은 lap에 넣지 않았다.

양쪽 모두 마지막0.02초는 기준 arc가[0,L]를 가로지르거나 벗어나 참조 profile을 적용하지 않고 별도 시간 장부에 넣었다. 음수/0진행·재방문·비양수 V/H/Q도 분모 epsilon으로 감추지 않고 별도 분류했으며 이번 관측에서 그 시간은0이다. 주 장부 항등식 잔차는 약10⁻¹⁴초다. C0/P 주 장부의 τr가 조금 다른 것은 끝의 참조 지원 범위가 다르기 때문이며 이상적 동일 상태 비교가 아니다. 완전 reference 시계 **10.027245초**는 동역학·actuator·조향/접촉·경로 결합을 보장하지 않는 서술용 기준이다.

prefix의 A3.354294초가 크고 직접 Bh+Bs는 **0.024422초**다. 그렇다고 A를 회수 가능한 속도 손실로, 음의 Bs/C를 얻을 수 있는 단축 이득으로 읽지 않는다. 종방향 slip으로 감속된 효과는 이미 A에 들어가며 body-slip으로 다시 세지 않는다. 곡률이 가능한 속도를 제한하는 효과도 A의 원인 후보여서, 작은 직접 방향 항만으로 geometry/속도 결합 전체를 부정할 수 없다.

## 초기/중간 구간에서 실제로 보이는 것

| prefix 관측 | 시간/값 |
|---|---:|
|정확히0진행·역행·재방문 시간|0초|
|평균 속력0–1m/s|0.02초|
|1–10m/s|0.36초|
|10–30m/s|1.14초|
|30–60m/s|4.42초|
|60m/s 이상|3.50초|
|full gas 명령|1.28초|
|partial gas 명령|6.24초|
|제동 명령|1.92초|
|coast 명령|0초|
|nominal 제동 / guardian override|1.84초 /0.08초|

길게 정지한 구간은 없고30m/s 미만은1.52초다. 이는 launch와 코너의 관측 시간이지 제거 가능한 정체 시간은 아니다. pedal 시간과 저속 시간은 같은 시간을 다른 축으로 분류하므로 서로 더하지 않는다. 명령 gas와 실제 rear-wheel gas도 다르다. raw rear gas와 명령의 절대 차이는 시간 평균0.014899, 최대0.870509였고 이 lag를 별도 회수 시간으로 계산하지 않았다.

제동 묶음은 step23–27(0.40초),63–70(0.64초),80–82(0.24초),91–94(0.32초),114–115(0.16초),117–118(0.16초)다. 모든 제동 시점에서 현재 속력이 현재 profile target보다 낮았다. 그중 nominal 제동23행동은 모두 **음의 feedforward가 양의 속도 오차 feedback을 압도**했다. 코드의 raw=f·sigma/r+1.5(r−v)이므로 이 관측만으로 과제동이라 할 수 없다. 급격히 낮아질 참조 속도에 대한 필요한 선행 제동일 수도 있다. step91은 nominal gas를 neutral brake로 바꾼 별도 guardian 개입이다.

prefix raw path error 평균0.215661m/최대1.413613m, 평균 |steer|0.057785, front joint lag 평균0.004094rad다. front/rear clipped wheel 비율은0.9534%/3.0720%, 하나 이상 wheel이 clip한 raw 시간은0.42초, force ratio 최대1.231986이다. actual damage·collision·road loss·3m 안전 실패는 관측되지 않았다. clip 자체를 안전 실패로 바꾸거나0.42초를 시간 손실로 더하지 않는다. 작은 heading/joint lag도 경로 추종의 동역학 비용이 없다는 증거는 아니다.

| 기준 공간 구간 | C0 주 장부 시간 | P 주 장부 시간 |
|---|---:|---:|
|0–10%|2.913|2.913|
|10–20%|1.314|1.314|
|20–30%|0.887|0.887|
|30–40%|1.422|1.422|
|40–50%|1.703|1.703|
|50–60%|1.181|1.181|
|60–70%|1.302|1.112|
|70–80%|1.528|0.999|
|80–90%|1.247|0.948|
|90–100%|1.563|1.259|

공간 bin은 같은 기준 arc를 쓰되 경계를 가로지르는20ms 구간 시간을 선형 arc 비율로 배정한 서술적 proxy다. 저장 crossing bracket 폭은20ms이며 정확히 같은 중간 물리 상태를 측정한 것은 아니다. 위 표는 참조 범위 안의 주 장부만이며 각 lap의 별도0.02초를 다시 더해야 한다. 0–10%와40–50%가 느리지만 이를 독립적으로 줄일 수 있는 시간 예산으로 취급하지 않는다.

COM velocity와 hull-origin 위치의 기준점 불일치도 확인했다. raw에 저장된 origin velocity로 바꾸면 C0의 A가약0.000662초 달라진다. 이것은 기준점 민감도 비교이며 센서 오차의 상한이 아니다. chord는20ms 사이 진짜 곡선 길이보다 짧을 수 있고 R에는 가감속·표본화 차이가 남는다. Box2D GT의 float32 위치/속도, canonical projection의 segment/vertex 경계, 미관측 구간 내 운동과 spatial 분할 오차를 유지한다. 실제 픽셀 관측 오차를 측정한 결과는 아니다.

## 앞쪽 planner의 finish witness와 실행 정책이 다른 지점

현재 Child.one은 첫 recipe 뒤 **own nominal C**만 이어가며 미래 guardian을 호출하지 않는다. observer가 붙어도 continuation의 정책은 SIGNED_C_NOMINAL이다. guardian 실행은 매 현재 상태에서 nominal13을 검사하고 실패하면 neutral13을 검사한 뒤 그 첫 행동만 실행한다. choose419는 guardian baseline에 admissible13을 먼저 요구하고, completed nominal-C continuation witness가 없으면 GUARDIAN_REFERENCE_ONLY로 돌아간다. 13-step 결과나 안전한 과거 실제 lap을 가짜 finish cost로 넣을 수 없다.

442 C0/P의 첫90행동 physical/명령과 pre91 physical은 역사적 C와 정확히 같다. 더 강하게442 pre91의 전체 physical·RNG·관측 hash·wrapper 및 nominal 전후 memory가411 pre91 gate와 일치했다. 그 저장 nominal13은 offset13에서 path error약4.759846m로 실패했고 neutral13은 안전·진행 조건을 통과했다. 410에서도 pre90 nominal13은 안전하지만 pre91은 실패한 것으로 기록됐다. prefix에서 미래의 guardian neutral을 빼고 nominal C를 계속 따르는 궤적은 이 실패를 만날 수 있으므로, suffix에서의 안전한 C finish witness를 앞쪽 전체에 그대로 이전할 수 없다.

반면442 C0의 실제 명령 차이는 step91 하나뿐이며 이후 own nominal로189행동·15.080초에 손상0 완주했다. 따라서 **안전한 배포 정책 B의 존재**와 **모든 앞쪽 root에 안전한 nominal-C finish witness가 있는지**는 다른 질문이다. 저장 nominal13 실패를 새442 모델 전체 tail의 재검증이라고 표시하지 않는다. 각 초기 root의 최신 모델 finish는 아직 미관측이다. 이 문제를 해결하지 않고 모든 prefix118개에서3 recipe×독립2×최대321행동의 long query를 반복하면 단순 상한만 **909,072 model ticks/708 worlds**이며 suffix·qualification 비용도 별도다. 이는 현재 실행 계획이 아니고 그 비용을 쓰지도 않았다.

## 서로 다른 다음 가설2개 — 제안만, 예약/실행 없음

**H1: 고정 경로의 초기 가감속 타이밍 여유.** 현재 FIRST_LAP·nominal brake>0·30≤현재 COM speed<현재 target·정방향·현재 damage0·네 wheel road contact인 첫 상태만 선택한다. 저장 자료의 첫 발생은pre23이다. 미래 exit 이득·안전 결과로 anchor를 고르지 않는다. 미래 fresh predicate가 맞지 않으면 이 한 실험을 중단한다.

동일한 전체 root/clock/RNG/nominal memory·path/profile에서 nominal C13 대 첫 행동 fullgas(기존 nominal steering 유지) 후 own nominal C13을 독립2회 비교한다. 먼저 실제13행동 기록 replay2회로 restore·body/wheel/raw phase를 교정하되 그 미래 명령은 선택기에 넣지 않는다. 기존391/439의 물리·geometry·이산·clip·memory/nominal/RNG·progress gate와3m/road/damage/collision/reverse를 유지한다. altered counterfactual 타이어 상태가 아직 실제로 검증된 것은 아니다.

계획상 최대 **316 ticks/7 worlds**, hard cap **512 ticks/8 worlds·CPU90초/wall150초·순차1**이다. 실제0이다. 첫 source/restore/numeric/domain/RNG/프로토콜/비용 오류는 전체 중단, baseline13 unsafe면 후보를 열지 않고 중단한다. candidate safety 위반은 해당 branch와 남은 실험을 중단하고 다른 pulse/root를 고르지 않는다.

배울 가치와 승격을 나눈다. unsafe/no-gain은 이 root의 순진한 첫 gas 기회만 반증하며 가속/속도 최적화 방법군 전체를 반증하지 않는다. 둘 다 안전하고 공통 원래 arc exit30m를13행동 안에 통과하며 후보 도착 upper≤기준 lower−0.08초, 후보 exit-speed lower≥기준 upper일 때만 더 큰 **국소 모델 검증** 설계를 고려한다. exit-speed lower/upper는 raw crossing bracket 양끝에서 관측한 속도의 최솟값/최댓값이며 연속시간 속도의 보장 구간은 아니다. yaw·joint·omega·path·force의 terminal debt가 남거나 표본 경계 때문에 상태 비교가 불명확하면 승격하지 않는다. lap 이득·actual 권한·419 finish receipt·픽셀296 승격은 아니다.

**H2: 미래 guardian 개입을 빠뜨리는 nominal-C witness 표현.** historical C90의 nominal13은 안전하고 C91의 nominal13은 위험했다. 이 근거로 pre90 하나를 고정한다. 미래 실험은 **현재 pre90에서 새로 계산한 nominal13이 안전하고 같은 child의14번째 nominal 전이가 위험한지**부터 확인한다. 이 새로운 current-model14 결과는 미관측이며 역사 자료를 이어 붙여 예측으로 만들지 않는다. predicate가 다르면 B를 열지 않고 중단하며 다른 root를 고르지 않는다.

nominal C14 독립 두 사본과 B의14-action model parent 독립 두 사본을 비교한다. B는 매 현재 상태에서 기존 nominal13 독립2회를 검사하고 필요할 때만 neutral13 독립2회를 검사해 자기 첫 명령을 실행한다. hardcoded step91 pulse·실제 미래 명령·재귀 planner는 없다. nominal child는 H13에서 기존 같은-world snapshot/명령/memory/RNG/ledger barrier를 먼저 봉인한 뒤 같은 child의 단 한 전이만 추가해 기록한다. 14행동은 국소 관측 범위이며 H13 안전 규칙·tail308·finish 기준을 고치는 것이 아니다. 모델 parent의 ledger는 prediction 채널이며 actual ledger를 갱신하지 않는다. full finish tail·remaining-time ranking은 하지 않는다.

동일 native pre90 root/clock/RNG·memory/path/profile·391/439 gates를 쓰고 사실 replay14 두 사본은 물리 calibration으로만 사용한다. 최악 B shadows2×14×4×13×4=5824 ticks, B parent112, nominal112, calibration112, held4로 **6164 ticks/119 worlds**다. parent 자체의 model step도 빠짐없이 센다. hard cap **6656 ticks/128 worlds·CPU240초/wall480초·순차1**, 실제0이다. H1과 hard cap 합7168 ticks/136 worlds이며 예약하지 않았다.

첫 restore/source/numeric/domain/isolation/프로토콜/비용 오류는 전체 중단한다. nominal의14번째 물리 unsafe는 사전 비교 대상인 음성 결과로 그 branch를 즉시 끝내고 padding/tail을 만들지 않는다. B parent의 안전·deadline 실패는 B와 남은 실험을 중단한다. alternate backup/root·retry는 없다. **13까지 안전한 nominal이14에서 unsafe인 반면 B14가 안전하면, 미래 조건부 guardian 개입이 nominal witness에서 빠지는 표현 차이**를 국소적으로 확인한다. 둘 다 안전하면 선택 gate가 성립하지 않으며 nominal finish도 증명되지 않는다. B 실패 역시 모든 guardian/geometry 방법군 부정이 아니다.

독립 repeat·물리 gate·B14 안전/진행이 통과할 때만 별도 상한의 full B continuation 설계를 고려한다. B14를419 finish witness로 넘기거나 시간 값을 만들어 넣지 않는다. 이 가설의 배울 가치는 표현 적합성이며 아직 속도 개선량은 없다. pre91의 기존 guardian만 다시 검사하는 데 그치지 않고, 한 행동 이전의 안전한 short horizon과 그 뒤의 실패를 구분하려는 설계다.

직접 geometry/경로 단축 가설은 현재 prefix 방향 항0.024422초만으로 강하게 지지되지 않는다. 곡률을 바꿔 실현 가능한 속도를 높일 가능성은 여전히 남지만, 이번에는 증거가 더 직접적인 witness/배포 정책 불일치를 두 번째 연구선으로 골랐다. 기존 낮은 차수 selector·국소 pulse·pixel 전이 실패를 전체 최적화·경로/속도 방법군 부정으로 확대하지 않는다.

## 관측·보존·비용

모든 선택 predicate는 현재 상태와 fixed GT profile 또는 현재 상태에서 계산한 모델 예측만 쓴다. 그러나 GT line/progress·wheel/contact·finish tracker·정확한 hull 속도는 pixel296의 합법적 입력이 아니다. 정책·표현을 pixel 관측으로 옮기는 관측 오차와 전달 gate를 이 단계에서 통과시키지 않았다. 단일 조건13.760초는 pixel296 승격이 아니다.

저장 주 분석 CPU3.621957초이며, 보조 source/표현 점검과 보고/Git·import 비용은 전체 계측하지 않았다. core 분석 당시 source/result는 비공개로 보존했고 public serializer만 per-anchor raw feature를 숨기도록 정정했다. 시간 항 수치는 바꾸거나 주행을 재현하지 않았다. 연구 잔여 **27,516**, 예비 **84,000/사용0**, SEALED·보호 archive·main dfb7a2de2178825ca5c5ce20bab01ba67052ba31과 기존 보고/backup을 유지한다. 종료 **2026년10월20일19:01:55 KST**를 유지하며 새 실험 권한·예약·자동 연장은 만들지 않았다.

[집계 시간 장부](decompose443_result.json) · [계산 코드](decompose443.py) · [두 제안의 조건/상한](hypotheses443_design.json) · [보조 분석 코드](design443.py)
