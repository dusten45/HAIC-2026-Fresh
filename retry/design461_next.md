# 461 다음 한 실험 — 한 sample hold 구간의 reference secant 반증

**설계만 동결한다.461의 새 actual/reset/model/world/seed/학습/HOLDOUT/SEALED/예비/유료 자원0이며 다음 비교는 실행하지 않았다.** [기계 판독 계약](design461_next.json)과 [예산 fixture](budget461.py)를 다음 구현의 단일 설정으로 쓴다. 추가 실행 승인을 대신하지 않는다.

## 선택한 가설과 root

선택은 H2B, 즉 piecewise squared-speed reference의 시작점 미분을80ms 유지하는 것이 노드 횡단 때 국소적으로 불필요한 brake를 유지한다는 가설이다. reference의 음의 기울기를 일괄 없애거나 pace/gain을 바꾸지 않는다. H2A인 reference/힘 제약 근사 불일치는 이번에 변경하지 않는다.

저장458P에서 공통pre23+450m 이후, own nominal·target 미만 braking·action 중 재계산 식의 가속 전환·secant pedal 변화가 함께 있는 첫 action을 고른다. 이는 pre126, 원래pre23+522.611849m, 저장 prefix lap경과10.00초다. 이 규칙은 저장 분석에 근거한 known DEV hypothesis 선택이며 blind 검증이라고 쓰지 않는다. root를 결과에 따라 이동하지 않는다. 미래13 actual target은 설명 검토에만 쓰고 새 명령 입력으로 쓰지 않는다.

full native prestate/wrapper/tracker/controller memory-before-nominal/RNG/관측 유래 read-only Actual GoalLedger·고정line/frozen268 nodes를 원본 receipt와 묶는다. 저장 dispatch/query/native-before의 hash와 pure binding 검사는461 집계에 있다. 다음 구현에서는 immutable source 목록과 새 policy digest에 다시 묶는다. 과거458 query의 선택/증명을 새 query의 권위로 복사하지 않는다. prefix 재적분0, 새 native0이다.

## 한 가지 변경과 후속 제어

원래 식은 `ff=f(s)*sigma/r(s)`, `a=ff+1.5*(r-v)`다. SecantOnce는 **첫 action의 ff만**

`ff_sec=[r(s+sigma*0.08)-r(s)]/0.08`

로 바꾼다. sigma는 기존 COM velocity·canonical tangent 정의,0.08은 기존4/50초이며 탐색 계수가 아니다. feedback1.5·현재r·pedal clipping/map·조향·line/profile을 그대로 둔다. constant-progress 근사이며 physics prediction이나 안전 증명이 아니다. root의 phase/positive-progress/nonpending/domain `0<s<s+sigma*.08<L`을 요구한다. epsilon·sigma clamp·profile seam 외삽·periodic launch 연결을 만들지 않는다. 내려가는 endpoint reference면 ff_sec도 음수다.

이 root에서는 변경한 전체 float32 명령이 **기존 fullgas first recipe와 exact 같다**는 저장 검사를 통과했다. 따라서 새로운 일반 controller/recipe/actuator를 구현하지 않고 기존 fixed-first short_pair 경로를 재사용할 수 있다. 다음 static/root restore에서도 이 alias 전체벡터를 exact 확인하며 다르면 적분 전에 중단한다. root나 수식을 바꿔 alias를 맞추지 않는다.

|순서|첫 query/행동|이후 최대99행동|
|---|---|---|
|Original|기존 nominal fixed pair 독립2회 valid 필수; 그 첫 명령|기존 guardian|
|SecantOnce|기존 fullgas와 동일한 secant fixed pair 독립2회 valid 필수; 그 첫 명령|동일 guardian|

각 whole arm은 **한 번**이다. query마다 독립2회는 유지하지만 whole-arm 반복 성공은 주장하지 않는다. 첫 query는 `Pilot436.short_pair`와453 fixed-policy의 valid-required/no-fallback 의미를 재사용한다. 첫 nominal/fullgas가 invalid이면 fixed variant ineligible로 닫고 다음 부모로 넘어가지 않는다. neutral이나 planner로 우회하지 않는다. 첫80ms 이후 secant를 반복 적용하지 않는다. 이후 guardian는 nominal H13 두 번을 먼저 검사하고 기존 등록 거절 때만 neutral H13 두 번을 쓴다. time ranking planner0, tail308 children0, 캐시/receipt 재사용/실패 재시도0이다.

## source·권위·한 번의 통합 검사

새 얇은 root/first-recipe adapter와 cap을 기존 통합 static fixture에 연결한다. 이때 모든 actual/model constructor/reset/step은 금지한다. 노드 보간·domain·전체 float32 alias·2arm/first1/parent100·fresh query·기존 pending/negative-DONE/restore·동일 meter cap 전달을 **한 suite**에서 확인한다.461의 저장 분석/예산 검사를 새 source qualification 성공으로 소급하지 않는다. 별도 microgate나 추가 physics 확인을 반복 만들지 않는다.

통합 fresh preflight는 old source/current/pending≤1242ticks/35worlds + 이 root≤216/6, 합계≤1458/41이다. root nominal H13 독립2회+held 첫 전이는 저장458의126–138행동과 기존439 shape/body/wheel/clock/phase/clip 허용 오차로 factual 대조한다. 그13행동이 모두 nominal임을 저장 검증했다. fullgas H13 독립2회+held 첫 전이는 모델 자기일관성이다. 이 root의 새 native fullgas factual counterpart는 없다. preflight와 main 첫 query는 목적이 다르며 서로 receipt를 재사용하지 않는다.

Original/SecantOnce는 각각 자기 새 모델 부모와 새 자식에서 시작한다. Actual GoalLedger는 read-only, ForecastLedger만 자기 모델 progress를 전진한다. current context는 자기 부모의 state/memory/RNG/clock/ledger와 새 policy에 묶는다. query 중 부모/원래 ledger/RNG 불변, 선택된 첫 명령의 자기 부모 전이 일치를 검사한다. Original의 이용 가능한 same-command actual suffix는 추가 적분 없이 factual 대조에 활용하며, 그 범위 밖 actual 적합성을 꾸미지 않는다. 지원 범위 내 fidelity 오류는 전역 중단한다.

pending은 기존 capture_pending→현재root/history/clock/RNG guardian proof→자기 부모one→verify_parent_step이다. certificate는 부모/actual DONE나 time ranking을 대신하지 않는다. 각 부모의 자기 modeled tracker official event·확인 post·모델 ledger가 있어야 finish다. parent100에서 미완료는 censor, after-cap tail/remaining-distance clamp/finish 추정0이다.

## 공통 관측 경계와 판단

주 지표는 **같은 root 이후 자기 모델 부모 finish bracket**의 Original−SecantOnce 차이다. prefix10.00초는 저장 관측으로 따로 제시하며 새 native lap를 만들지 않는다. 보조 지표는 공통 원래pre23+570/630/690/750m의 raw20ms first-crossing bracket, 첫80ms/13행동의 속도·target 오차·force clipping·gas ramp·경로/진행과 guardian 개입이다. actual 미래 target을 새 정책 입력으로 쓰거나 국소 query 이득을 finish 차이에 합산하지 않는다.

양쪽이 자기 finish·source/권위/전이 검사를 통과했을 때만 strict bracket 비교를 한다. SecantOnce가 앞서면 이 root의 단발 secant-동등 pulse에 조건부 model 학습 근거가 된다. 음수면 그 성능 가설을 반박하고, overlap/작은 값은 그대로 미해결 정보로 보존한다. 초반 경계 이득만 있고 finish가 개선되지 않으면 전체 성능 승격 근거0이다. 임의0.10초 문턱은 없다.

어떤 결과도 secant 법칙 전체·다른 root·실제 안전·픽셀·HOLDOUT/SEALED·11.99초 달성을 입증하지 않는다. 실제 승격0이며 새 native 비교는 별도 source/전체 비용/승인 판단이 필요하다.

## 전체 비용과 저장 가능량

|planned 항목|ticks|worlds|
|---|---:|---:|
|2first fixed queries×2copies×13actions×4|208|4|
|나머지198guardian queries×2recipes×2copies×13×4|41184|792|
|2parents×100actions×4|800|2|
|통합 qualification|1458|41|
|**합계**|**43650**|**839**|

제안 hard **49152ticks/896worlds·CPU1800초/wall2400초·순차1·actual/reset/seed/learning/HOLDOUT/SEALED/예비/추가 유료자원0**이다. constructor 전 원가/입력 proof, step 전4tick 예약, query와 worker에 동일 cap을 쓴다. startup/import·source 확인·qualification·제어·physics/observer·snapshot/proof/IO·cleanup을 worker 시간에 포함하고 준비/정적/저장 감사/Git overhead는 별도 기록한다. planned가 hard를 넘거나 산식에 누락이 있으면 적분 전에 중단한다. 독립 검토도43650/839를 확인했다.

461 읽기 점검에서 `/tmp` 여유 약5.47GB, workspace 약1.74GB였다.457/460의 관측 raw bytes/tick 최대64959.16을 적용하면 hard49152 기준3.193GB이며,25% 경험적 여유와 종료 dump/정산용512MiB를 포함해 **4.528GB(4.217GiB)**다. 현재 `/tmp`에 조건부로 들어간다. world별 고정 header/receipt·문자 길이·contact/관측과 감사 임시 자료 때문에 이 비율은 보장 upper bound가 아니다. 실제 시작 전 최신 free가 이 추정 이상인지 읽기 확인하고,512MiB 미만 또는 IO 오류면 다음 constructor/step 전에 전역 중단한다. 자동 삭제·이동·재시도·상한 증가·새 유료환경0이다.

기존 자료를 복사/압축해제하지 않는다. 새 raw는 같은 실행기의 private `/tmp`만 쓰고 공유/영속성을 가정하지 않는다. 핵심 코드/공개 집계/입력 hash와 full private plan은 workspace에 보존한다. 이전 보존 압축률 약0.1503을 적용한 새 raw archive의 rough 크기는 약0.48–0.60GB로 workspace 여유 안이지만 이것도 보장이 아니다. 종료 후 원본을 삭제하지 않는 private archive+member SHA256 검증은 공간이 있을 때 별도 후처리로 기록한다. 임시 raw 소실은 재현 한계이며 public 자료만으로 원본을 복원할 수 없다.

최초 source/fidelity/restore/numeric/domain/phase/clock/권위/RNG/독립 query 반복/선택 전이/resource/deadline 오류는 전체 중단한다. 기존 typed 조기 physical unsafe만 기존 의미로 보존하고 H13미만 unsupported INFEASIBLE/진행 거절은 중단한다. fixed-first invalid는 선택 우회 없이 학습 실패로 닫는다. 기존 guardian valid=False/완전H13/regular supported progress 의미를 넓히지 않는다.

10분 checkpoint·종료 집계·일반commit/push·원격SHA 확인을 남긴다. 실행은 별도 승인 뒤 한 번이며 종료2026-10-20 19:01:55 KST와 worker cap 중 먼저다. 연구26695·예비84000/사용0·SEALED·main dfb7a2de2178825ca5c5ce20bab01ba67052ba31·Participants·사용자 변경·원본/백업/보호자료를 유지한다.
