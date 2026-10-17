# 464 — 지속 제어의 다음 작은 반증 계약

**464는 저장 자료·코드 분석과 설계만 수행한다. 새 model/native 적분·world/reset·seed·학습·HOLDOUT·SEALED·예비·유료 자원 사용은0이다. 이 문서와 JSON은 실행 승인을 부여하지 않는다.** 최신 종료는2026-10-20 19:01:55 KST다. 463의 실제14.000→13.780초,0.220초 이득과462 모델[0.20,0.24]초의 부합을 유지한다. 기존 최선442P13.760초는 갱신되지 않았다.

## 문제 계약과 서로 다른 가정

목표는 알려진 DEV의 남은 시간 격차를 설명할 지속 제어를 찾는 것이다. 저장 native의 속도 deficit·reference clock·힘 요구·guardian 선택을 구분한다. 원하는 reference와 실제 lap의 차이를 전부 회수 가능한 추종 손실로 계산하지 않는다. 같은 privileged 고정 line/frozen268 reference·80ms wrapper·기존 steering/phase/finish/ledger 정의에서 가정 하나씩 대조한다. 사용자 방법론의 문제 계약→가정이 다른 후보→작은 반증→통과한 범위만 승격 순서를 적용하며, 새 원문 완독이나 방법군 소진을 주장하지 않는다.

|가설/지속 후보|다른 핵심 가정|현재 근거|아직 없는 증명|
|---|---|---|---|
|H2A: scaled reference 재투영|pace 뒤 reference도 근사 종·횡력·경로 제약과 일관돼야 함|pace 적용 후 제약 재투영 없음; gradient와 기존 allowance 잔차; 공동 tyre clipping·gas ramp|reference 전체의 실제 달성 가능/불가능 판정, exact tyre inverse|
|H2B: 매80ms reference secant|시작점 미분을 hold한 FF보다 유한 구간 평균이 나을 수 있음|저장 hold 부호 충돌, 첫 pulse 실제0.220초 이득, 후속 상태에서도 secant 명령 변화 존재|단발 fullgas 밖의 추가 이득, 지속 법칙 안전·전체 lap 개선|

H2A 후보는 scaled squared-speed nodes를 상한으로 고정하고 기존 source-grounded drive A(v)/brake B 전달식으로 nodewise 재투영하는 것이다. uniform pace1·음의 FF 삭제·gain 탐색이 아니다. 예컨대 기존 backward/forward 전달을 고정4회 적용한 뒤 양방향 잔차를 검사하고, 잔차가 남으면 그 결과를 feasible로 쓰지 않는다. 기준점/현재속도 접합과 초기·finish 정의역을 먼저 확인한다. 조향·line·feedback1.5·samplehold·pedal map은 유지한다. 이 A/B 자체가 보수 근사라 투영 성공도 exact coupled tyre feasibility 인증은 아니다. 이번 선택 계약에서는 투영 profile을 생성하거나 시험하지 않는다.

H2A 근거의 크기를 과장하지 않는다.461의238구간 중 기존 brake allowance 초과54, 상수 drive allowance 초과166, scaled gradient−223.40…106.92m/s²다. lateral/base allowance 최대비2.417은 base가 nominal aggregate friction의0.4배인 같은 allroad/grip1 점질량 가정에서 약0.967배 횡력 요구에 해당한다. 물리 마찰2.417배 위반이라는 뜻이 아니다. 그 점의 단순 원형 공동가용 종력비 약0.255는 바퀴별 배분·slip·실제κ·접촉을 무시한 proxy다. 서로 다른 위치의 최대 gradient와 최대 곡률을 합쳐 위반을 만들지 않는다.

461의442P/458P speed tracking 항3.097/3.347초는 signed 시간 항등식의 관측 분해다. 더 빠른442P가 제동·clipping 노출도 더 컸다. steering/횡력의 간접 효과는 작은 heading projection 항으로 지워지지 않는다. reference clock10.027초는 달성 가능 시간·하한·11초대 보장이 아니다.

## 선택: 같은 첫 pulse 뒤 지속 FF의 추가 효과

다음 하나는 **PulseOnce 대 S13**이다. 이미 고정된458P/463 pre126 root를 그대로 쓴다. 새로운 위치/seed/DEV 검색은0이다. 양쪽 첫 명령은 같은 fullgas alias다. 이후 PulseOnce는 기존 nominal, S13은 매80ms 경계에서 secant를 다시 계산한다. Original nominal과 S13만 비교하면 알려진 첫 pulse 이득을 지속 secant 이득으로 다시 셀 수 있으므로 선택하지 않는다. Original 저장 자료는 factual calibration/맥락으로 유지한다.

이 선택은 H2A를 반박했다고 보기 때문이 아니다. H2A는 실제 feasibility 정보가 부족하고 reference 재투영은 목표 자체와 접합을 바꾼다. H2B의 추가 효과는 동일 첫 pulse·같은 root·같은 reference로 더 싸고 직접적으로 반증할 수 있다. 463은 첫13행동 뒤에도 neutral1회가 필요했고 기존 최선도 넘지 못했으므로 fullgas 위치들을 쌓는 방식으로 다음 단계를 정하지 않는다.

### 법칙과 입력 경계

현재 상태의 canonical origin projection s, COM tangent speed sigma, COM speed v와 원래 squared-speed 보간 r를 사용한다. h=4/50=0.08초로 고정하고

`a_sec = [r(s + sigma*h) − r(s)]/h + 1.5*[r(s) − v]`

를 기존 pedals에 넣는다. C.act를 각 행동 경계에서 정확히 한 번 호출해 기존 steering·phase·cursor·last_time·memory를 전진한 뒤, 그 현재 명령의 gas/brake만 바꾼다. `one`에 `prepared_before`와 `prepared_nominal`을 함께 전달해 ObserveMixin 안에서 act가 다시 호출되지 않는지 검증한다. 새 law는 stateless다. 조향 정책은 같아도 속도·상태가 달라 후속 steer 값과 횡력은 달라질 수 있다. 같은3차원 float32 명령을 최대4×20ms 동안 유지하며, 관측 post마다 새 제어를 넣거나 action을20ms로 줄이지 않는다. wheel gas ramp≤0.1/rawtick·wheel omega brake·종횡력 공동 vector clipping·조향 joint 동역학은 원본 그대로다.

S13 정의역은 finite 입력·기존 canonical tie 규칙·FIRST_LAP·sigma>0·positive r·`0<s<s+sigma*h<L`다. epsilon, sigma clamp, profile seam 회귀, terminal 외삽은 없다. `compare462.secant_command`를 그대로 반복하면 안 된다. 그 함수는 매 호출마다 fullgas alias를 강제하는 단발 검사용이다. 새 순수 식은 임의의 합법 pedal을 낼 수 있으며 첫 단계에서만463 fullgas와 전체벡터 exact 일치를 요구한다.

secant는 endpoint reference가 낮으면 음의 FF를 내므로 제동을 없애는 법칙이 아니다. 하지만80ms 안에 내려갔다 다시 올라오는 reference valley는 endpoint 평균에 가려질 수 있다. 모든 crossed node와 최소 target을 진단에 남긴다. backward profile이 미래 감속을 어느 정도 담고 있어도 pace 후 정합성이 미증명이고,80ms 밖 장애물/곡선 감속을 새로 예견하는 알고리즘은 아니다. 현재 sigma 고정 외삽은 실제 가속·회전·origin/COM 이동을 예측하지 않는다.

기울기 전환만의 수정도 아니다. 한 squared-speed 선형 segment 안에서도 `ff_sec/ff_point = 2*r(s)/[r(s)+r(s+sigma*h)]`라서 보통 다르다. rising segment에서는 FF가 작아지고 falling segment에서는 음의 크기가 커질 수 있다. feedback1.5를 유지한 이 식은 `(r_future−v)/h`의 exact ZOH 추종법이나 actuator inverse가 아니다. 따라서 양성 결과도 'node switch 하나가 원인'으로 해석하지 않는다.

전체 lap 후보로 확장한다면 LAUNCH/STOP/FINISH_CONFIRM과 pending 확인은 기존 phase 법칙·현재 tracker/clock 검사를 유지해야 한다. FIRST_LAP 끝에서 lookahead가 L을 넘는 영역은 **기존 nominal로 명시적 terminal handoff**하는 piecewise 정책을 별도 동결해야 한다. 실제 action h는 줄이지 않고 reference를 launch로 연결하지 않는다. 그 외 정의역 위반은 중단한다. 이것은 '모든 상태에서 secant'와 다른 정책이며 S13에는 아직 그 handoff 자격이 없다. 전체 적용·preview valley 보정·새 reference 투영을 이번13행동에 끼워 넣지 않는다.

### guardian와 shadow의 정확한 범위

현재 `pilot420_backend.Child.one`·`guardian426_confirmed.GuardianChild.one`의 recipe override는 첫 행동에만 적용되고 이후 old SourceC nominal로 돌아간다. 기존 short_pair의 독립2회 H13·planner tail은 그 법칙을 검사한다. 따라서 새 secant 첫 명령만 넣은 뒤 old nominal을 굴린 shadow는 **반복 secant의 미래를 인증하지 않는다**. old419의3recipe/first-vector 증명에 새 임의 secant pedal을 nominal/fullgas로 위장해 넣지도 않는다.

선택 S13은 실제 selector 승격 전의 **모델 내 고정 법칙 반증**이다. 각13행동 trajectory 내부의 매 경계가 자기 arm 법칙을 사용한다. guardian query/neutral fallback/랭킹/308tail은0이다. PulseOnce도 첫 fullgas 뒤13 끝까지 old nominal이다. raw마다 기존 path3m·road/contact·collision·damage·reverse·numeric·progress/clock 기준을 검사한다. unsafe를 guardian로 구조해 다른 정책의 성공으로 바꾸지 않는다. 관측·fidelity·source gate를 재사용하되 selector가 있어야 성립하는 증명은 만들지 않는다.

나중에 guarded 지속 정책을 설계하면 새 recipe/digest와 자식 controller를 등록하고, secant proposal 뒤의 미래 H13도 매번 secant로, neutral-first 뒤도 그 지속 base law로 돌려야 한다. 이것도 미래 guardian 재선택까지 재귀적으로 시뮬레이션한 exact 전체 정책 예측은 아니다. 조건부 base-law continuation forecast로만 표시하고, guarded 정책 자체의 매80ms 재질의는 새 model parent가 직접 수행해 전체 결과를 따로 검증해야 한다. 무한/숨은 재귀 guardian 비용을0으로 놓지 않는다. 현재 S13로 native 안전·전체 guarded loop를 인증하지 않는다.

## 한 번에 묶은 최소 계약

1. constructor/step/native 금지 통합 static에서 formula·node/valley·strict domain·첫 full-vector alias·memory once·source/protected hash·budget 전달을 검사한다.464의 저장 검사는 새 source qualification으로 소급하지 않는다.
2. 기존 source/current/pending qualification≤1242ticks/35worlds를 먼저 통과한다. 모든 parent/world와 auxiliary를 이 cap에 포함한다.
3. 같은 frozen root에서 PulseOnce H13 독립2개와 held 첫 전이1개를 실행한다. 저장463 SecantOnce의 첫13 실제 행동은 fullgas1+nominal12다. exact 복원된 첫 current 입력·memory·float32 명령·첫 전이는 native factual 검증을 요구한다.13행동은 기존439 physical/geometry/clock/phase·wheel clip 허용 오차로 closed-loop calibration한다. 각 행동의 실제 float32 명령 동일성을 별도로 기록해 최초 분기 뒤에는 '동일 명령 native factual' 자격을 확장하지 않는다. 같은 정책이라고 명령열까지 같다고 보지 않으며, 이후는 자기 model 일관성과 제한된 calibration 범위다. fidelity/불연속 discrete 오류는 기존 의미대로 중단하고 새 tolerance를 만들지 않는다. 이 범위를 통과해야 S13을 연다.
4. S13 H13 독립2개와 held 첫 전이1개를 실행한다. 두 trajectory는 첫 행동부터13번째까지 같은 반복 법칙이고 signature exact 반복·held 첫 전이를 검사한다. 첫80ms의 native counterpart만463에 있고, 이후 S13은 모델 자기일관성이다.
5. 바로 이4개 H13 trajectory에서 반증 지표를 계산한다. 자격 확인과 동일한13행동 과학 질문을 위해 별도 main parents를 다시 만들지 않는다. native dispatch receipt/승격 증명으로 재사용하는 것은0이다. root Actual GoalLedger는 read-only, 각 세계의 ForecastLedger만 전진한다.

주 지표는 사전 고정한 **root+60m 첫 통과 raw20ms bracket의 PulseOnce−S13**이다. 양쪽 미도달이면 미도달/censor를 남기고 경계를 옮기거나 tail을 연장하지 않는다. 보조 지표는 동일1.04초의 진행 거리·현재위치 reference 대비 속도·terminal speed·brake/gas-ramp/clipping·전체 raw path/yaw/contacts/force·node/valley 노출이다. 고정 시간13행동 자체의 elapsed가 같다는 것을 lap 이득으로 해석하지 않는다.

승격 조건은 두 arm의 독립 반복/모든 gate 통과, strict 양의 통과시간 bracket,1.04초 종료 진행의 양의 추가 이득이다. 임의0.10초 문턱은 없다. 양성이면 **다음 전체 model 정책 계약을 설계할 근거**까지만 얻는다. native/11초대/전체 안전 승격은0이다. 음수/겹침·반복 무효·domain/progress·physical unsafe를 구분하고, typed physical rejection은 원래 의미로 보존한다. H13미만 unsupported 진행 거절·fidelity/restore/RNG/권위/IO/numeric/resource 오류는 전역 중단한다. 고정 law invalid를 neutral로 우회하지 않는다. pending/finish에 이르면 scope 종료로 기록하고 다른 law로 이어 H13성공을 꾸미지 않는다. 어떤 resource 실패도 기술 가설 실패라고 부르지 않는다.

## 전체 비용·공간·승격의 가격

|선택 계약의 모든 적분|ticks 최대|worlds|
|---|---:|---:|
|old source/current/pending 및 그 parent/aux|1242|35|
|PulseOnce H13 독립2+held 첫80ms|108|3|
|S13 H13 독립2+held 첫80ms|108|3|
|**합계**|**1458**|**41**|

별도 main parent0, 새 actual/reset0이다. 같은 trajectory를 분석하므로1666/45로 불필요한4×H13 비교를 추가하지 않는다. future hard는2048ticks/64worlds·whole worker CPU180초/wall300초·순차1이며 실험 scope는1458/41에서 끝난다. unused cap은 다른 root/후속 비교 권한이 아니다. startup/import·source 확인·adapter/control·physics/observer·snapshot/proof/hash/IO·cleanup을 whole 시간에 포함하고 준비/static/저장 감사/보고/Git 비용은 별도 기록한다. 미래 wall/CPU는 아직 실측하지 않았으며 cap을 성능 예측으로 쓰지 않는다.

읽기 확인 당시 /tmp free3667374080B, workspace 약922MB다. 최신463 raw890158797B/10375ticks=85798.438265B/tick이462의83723.180104보다 높아 새 산식은 큰 쪽을 쓴다. latest world 최대 constructor368983+firststep369298+runtime-link31192=769473B를별도 가산한다. 실제 시작 전 새 source manifest/header 증가와 최신 free를 재계산해야 한다.

hard2048×관측최대×1.25+41×world고정비=약251.192MB payload, /tmp 종료512MiB 포함 **788063307B**다. archive는 압축률에 기대지 않고 그 전체 raw payload×1.10+32MiB metadata=309866066B, workspace512MiB 포함 **846736979B**를 배정한다. 두 기존 볼륨에 현재 조건부로 들어간다. 고정 header와 tick비용의 중복 가산도 유지한다. 경험적 추정은 보증 상한이 아니며 현재 workspace 여유가 약75MB밖에 더 남지 않으므로 시작 직전 gate가 필수다. 매 constructor/step/큰 write 전 reserve를 확인하고 첫 공간/IO 오류에 멈춘다. raw 전수·full private plan·member SHA 보존 몫을 빼서 억지로 맞추지 않는다. 기존 파일 삭제·이동·새 환경·유료 자원0이다.

전체 guarded model로의 후속 승격은 훨씬 비싸다. 같은 root에서 각정책 whole parent 독립2, 각70행동을 잡으면 firstfixed4query416/8 +guardian276query57408/1104 +parent1120/4 +qualification1458/41 = **60402ticks/1157worlds**, actual/reset0이다. 각 query2recipes×독립2×H13의 최악 비용이며 조기 finish에 기대어 축소하지 않는다. 예시 hard65536/1280이면 같은 보존 산식의 /tmp 요구 약8.46GB로 현재3.67GB에 들어가지 않는다. 이는 현재 자원상 **미실행** 사유이며 지속 secant 기술 실패를 뜻하지 않는다. exact future-guardian 재귀나 native 이전은 이 숫자에도 포함되지 않고 이번 선택/승인 범위가 아니다. S13이 양성이어도 그 비용 게이트를 생략하지 않는다.

연구 잔액26346·예비84000/사용0과 v475, 기존 최선/실패/원본/백업, main dfb7a2de2178825ca5c5ce20bab01ba67052ba31·Participants·사용자 변경을 유지한다.464 종료 후 자동 후속 실행은0이다.
