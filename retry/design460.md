# 460 — 네 planner arm 비용을 정정한 단일 두-root 모델 비교

**460 명시 승인에 따라 통합 정적 검사와 fresh qualification 통과 후 한 번만 실행한다. actual0.** H1의 confound를 가장 적은 변경으로 분리하는 단일 bounded model-only 비교다. H2용 profile/tracker/path 변경 연구선은 동시에 시작하지 않는다.

## 입력과 정책

453baseline(NoPulse)과453candidate(Pulse)의 저장 native history를 사용한다. 각자 공통 원래pre23 progress+450m 이상인 첫 native prestate를 geometry 규칙으로 고른다. NoPulse는pre117, +450.334734m, 관측 prefix lap경과9.28초; Pulse는pre113,+453.715631m,8.96초다. 서로 같은 root가 아니다. 같은 wrapper trigger의 overshoot·상태·시간·guardian 역사 차이는 초기 pulse의 매개 이력이다. prefix를 새로 적분하지 않는다. 각 root 이후 저장13행동이 모두 own nominal임을 calibration에만 사용한다.

각 root의 full state/wrapper/finish tracker·controller memory-before-nominal·global RNG·관측 유래 read-only Actual GoalLedger·고정line/profile을 따로 hash로 묶는다. 서로의 state/receipt/ledger를 섞지 않는다. 새로운 query context는 자기 부모에서 capture하고 현재 root/policy digest에 묶는다. archived 결과로 미래 recipe를 복사하지 않는다.

두 arm **모두** 처음8개 적격 FIRST_LAP/nonpending 결정에 동일419 planner를 적용하고 이후 동일 guardian다. nominal 선택도quota1회다. NoPulse 라벨을 기존 C0/guardian-only 분기로 잘못 연결하지 않도록 얇은 root/label adapter를 검증한다. parent100행동, 세 recipe alias 제거·H13·3.24m 목표·tail308·2독립 반복·strict finish bracket dominance·overlap/tie guardian 유지·pending 경로는 기존455/457 계약 그대로다. planner 자식의 nominal tail과 자기 부모의 매번 새 query 제어를 혼동하지 않는다.

순서는 NoPulse1,Pulse1,NoPulse2,Pulse2다. 네 full arm은 fresh 부모·fresh child로 수행하며 cache·receipt 재사용·실패 재시도0이다. 첫 결과로 두 번째 반복·정책·root·quota·cap을 바꾸지 않는다.

## 한 번의 통합 preflight와 권위

정적 suite에서 constructor/reset/step을 금지하고 root 규칙·두 arm P8 연결·fresh full반복·parent100·cap meter·hybrid 시간 산식·기존 negative-DONE/restore fixture를 합쳐 검사한다. 통과 뒤 old source/current/pending qualification≤1242ticks/35worlds와 **각 root** qualification≤216/6을 한 번 수행한다. 합계≤1674/47이다. 목적지/라벨 연결 외 물리·observer·receipt·restore 의미는 변경하지 않는다.

각 root nominal H13 독립2회는 해당 저장 native의13행동과 기존439 허용 오차·shape/wheel/clock/phase로 factual 비교한다. 별도 held 부모 첫 전이와 query 중 state/memory/RNG/ledger 불변도 확인한다. fullgas H13 두 모델 반복+held 첫 전이는 자기일관성 검사다. 새 native factual fullgas counterpart가 있는 것으로 쓰지 않는다. qualification 결과를 counterfactual 전체 궤적의 실제 충실도 보장으로 확대하지 않는다.

원래 Actual GoalLedger는 read-only, 각 모델은 ForecastLedger만 전진한다. forecast view를 actual fact로 재commit하지 않는다. pending은 기존capture_pending→현재root/history/clock/RNG guardian proof→자기 부모one→verify_parent_step을 유지한다. guardian FINISHED는 부모/actual DONE를 부여하지 않는다. 자기 부모의 공식 modeled finish event와 확인 post, 성공 fact 검증으로만 모델 완료를 인정한다. 남은 거리를 clamp하거나 cap 이후 tail을 덧붙이지 않는다.

## 전체 비용·중단

459의206410/1683은 C0/P 방식의 planner16회를 잘못 가져온 오류다.460은 실제 네 arm scheduler의 quota를 계산하는 `planned_budget()`와 정적 fixture에 산식을 연결한다. 독립 검토도32planner/368guardian·326346/1715를 확인했다. planned가 hard를 넘거나 다른 누락이 발견되면 적분 전에 중단한다.

raw 증거는 같은 지정 클라우드의 `/tmp/haic-retry-stage460-private`에 저장하고 private stage460에서 연결한다. 기존 자료는 이동/삭제하지 않는다. 시작 전7GiB 이상 여유를 요구하고512MiB 미만이면 다음 모델 step/constructor 전에 resource stop한다. 원가는 filesystem/IO·snapshot을 포함하는 worker 시간과 tick/world를 별도로 기록한다.

|항목|model ticks 최대|worlds 최대|
|---|---:|---:|
|4arms×8planner×3recipes×2copies×321actions×4|246528|192|
|나머지368queries×2guardian recipes×2copies×13×4|76544|1472|
|4parents×100actions×4|1600|4|
|통합 source/root qualification|1674|47|
|**planned 합계**|**326346**|**1715**|

hard327680ticks/1792worlds, exclusive CPU9000초/wall12000초, sequential1, actual/reset/seed/learning/HOLDOUT/SEALED/추가 유료자원0이다. source gates·자식·부모를 모두 포함하고 tick 전 예약·constructor 전 world 원가를 기록한다. startup/static/saved IO/Git overhead와 physics timer를 분리한다. 절약분으로 arm/recipe/seed를 추가하지 않는다. 연구26,695·예비84,000/사용0은 actual0이므로 차감하지 않는다.

첫 static/source/fidelity/restore/numeric/reverse/phase/clock/authority/RNG/독립반복/unsupported progress/resource/deadline 오류는 전체 중단한다. H13미만의 지원되지 않는 INFEASIBLE·진행 거절은 중단이며, 기존 typed 조기 physical unsafe만 기존 범위에서 ineligible 처리한다. 기존 guardian valid=False 및 완전H13/regular tail의 지원된 진행 거절 의미를 임의 확장하지 않는다. parent100내 미완료는 censor다. 실패 후 같은 stage 재시도·자동 cap 증가0이다.

## 판단과 승격 경계

주 지표는 **저장 관측 prefix lap경과시간+자기 모델의 root 이후 완료 bracket**이다. root가 다른 두 arm의 남은 시간만 비교해 초기 pulse의 총효과라고 쓰지 않는다. 이는 hybrid model 진단이며 새 official native lap가 아니다. 모델 적합성과 같은 후반 정책이라는 조건 아래의 비교로 제한한다.

네 부모가 모두 자기 event로 완료하고 반복 일치·원가·권위 검사가 통과했을 때만 full-arm bracket을 비교한다. Pulse가 strict 앞서면 공통 후반 정책에서도 초기 pulse 이득이 남는다는 조건부 근거, NoPulse가 strict 앞서면 그 가설의 반증, overlap이면 미해결이다. 작은/음수/겹침 결과도 보존하며 임의0.10초 문턱으로 버리지 않는다. source 실패·censor·반복 불일치면 성능 승격0이다. 어느 결과도 자동 actual/HOLDOUT/SEALED 승격이 아니며 다음 단일 native 실험은 별도 검토한다.

10분마다 실제 진행·arm/quota·ticks/worlds·CPU/wall·장애물을 한국어로 보고한다. 완료/중단 뒤 원가·저장 감사·일반commit/push와 원격SHA 확인으로 닫고 자동 추가 실행하지 않는다. 종료는2026-10-20 19:01:55 KST와 worker 상한 중 먼저다. main dfb7a2de2178825ca5c5ce20bab01ba67052ba31·Participants·기존 사용자 변경·원본/백업/ZIP을 보존한다. raw 상태·명령·seed·RNG·개인 자료는 private에만 둔다.
