# 559 — exactfeasible 전사 통과, 한 안전 시간 방향은 .437/.533ms로 효과 기준 미달

**저장551의 reset부터 도달한 안전 source 궤적을 world/fullstate 그대로 정확히 재현했다.**9개 hold node에서 독립 전파한36raw와 초기 상태부터 연속 전파한36raw가 저장 상태·접촉 ID·힘에 모두 정확히 일치했다. 임의의 합성 주기나 목표 시간을 요구하지 않았고, 일반 도로 주행에 주기 잔차를 필수조건으로 넣지 않았다.

이 gate 뒤에만 source 상태 민감도와 **한 제약 LP 방향·한 source 후보**를 검사했다. 후보는 기존 전역 안전·공통 공간 gate의 상태 비교를 통과했지만, 보간 시간 이득 **.437093ms·후속 .532663ms**로 사전 양쪽5ms 기준에 미달했다. **전사 실패도 실행 안전 실패도 아닌 효과 부족**이다.558 원실패는 보존했고 반복/기간을 늘려 재시험하지 않았다. 실제 기준13.66초·551source13.22초 유지, 전체 랩/실제 성능 개선 관측0이다.

## 사전 선택·전사와 정보 경계

선택 규칙은 `551 tracking에서 before-action progress가 기존533station37 이상인 첫 행동`이다. 결과는 **행동35부터**이며 효과/안전 지표를 보고 창을 고르지 않았다. 처음6hold를 제어 변수,다음2hold를 고정 후속으로 두었다.9번째 저장 행동은 미세하게 늦어진 finite-difference 경로도 두 번째 plane을 bracket할 수 있게 하는 **사전 측정 buffer**다. 최적화/비교 목표는6/8hold 뒤 동일 공간 경계이고 buffer를 새 개선 구간으로 쓰지 않는다.

551 cold는 이 조건에서 reset부터 안전하게 source 완주한 기존 기록이다. 여기서 “도달”은 그 **source 모델의 실제 전파 기록**을 뜻한다. native Box2D에 이 상태로 도달했다거나 합법 픽셀 정책이 재현한다는 주장은 아니다. 기존closure524 rigid-body 근사 map과 저장 지도/입력/코드 hash를 사용했다. 실제 Participants나 main을 바꾸지 않았다.

먼저 저장 fullstate를 hold node로 두고, 각 node에서 해당 float32 행동4raw를 독립 전파해 다음 node의 defect와 중간 raw 전체를 검사했다. pose·COM 속도·yaw/각운동량·wheel omega/gas/heading/offset/friction·joint/rate·lever·steer·상수·**current contact ID까지** 비교했다. immutable roads는 동일 hash 입력으로 분리했으며 tuple/list 표현만 canonical JSON으로 정규화했다. 모든 수치는 정확히 일치해야 다음 단계를 열도록 고정했고 허용치를 사후 완화하지 않았다.

그 뒤 연속36raw replay도 모든 저장 root와 force에 정확히 일치했고 저장 geometry/path 안전 수치도 재현했다. 초기 tracking clipping 이력 **3/160**을 보존했다. 새 변수의0 변화가 원 안전 궤적인 **exactfeasible 초기화**임을 확인했다. 상태를 추가 변수로 둔 큰 nonlinear multiple-shooting을 푼 것은 아니다. hold-node 전사 defect를 검증한 뒤 source로 condense한 상태 민감도를 썼다.

## 사전 고정한 한 시간 방향

첫6hold의 steer/signed pedal12변수에 대해12개의 one-sided source FD rollout을 계산했다. step은 steer1e−5·pedal1e−4,분모는 실제 float32 변화량이다. 원 pedal/brake-lock 분기를 유지하고,trust box steer±.002rad·pedal±.02 및 기존 행동 bounds 안에서만 방향을 만든다. 이 범위는 유한 국소 설계 선택이며 물리적 최대 개선 범위가 아니다.

목적은 **두 공통 공간 plane 도착 시간 평균 최소화**다. plane은 저장6/8hold endpoint 위치와 저장 속도 방향으로 실행 전에 고정했다. 기존 raw 안전,두 plane의 world/fullstate 비교,양쪽 시간 비악화,원 baseline보다 새 clipping sample을 만들지 않는 보수적 조건을 선형화했다. LP는 기존 slack의 절반을 남기며 `G*delta>=−.5*g0`를 요구한다.0방향의 feasibility도 확인했다. SciPy HiGHS **한 번**,full LP 방향 **한 후보**로 끝내고 backtracking·계수/방향 재탐색을 금지했다.

후보와 모든 FD에는 **원551 참조** overspeed≤4.85,force≤1.059,footprint≥.5,path≤3,모든 hull/wheel<100,저장 초기 이력을 포함한 누적 clipping≤10%를 검사한다. new-clip mask/trust/slack/endpoint 비교는 이번 방향의 보수적 설계 조건이며 모든 안전 제어의 물리 필요조건은 아니다. source 모델 내 새 body domain은 모든 forecast에서도100 미만을 강제한다. LP의 효과 gate는 양쪽 보간 이득 각각≥5ms이며 실제/전체 랩 승격 gate가 아니다.

공통 plane의 첫 정방향 crossing을 raw 위치 사이 선형 보간으로 측정한다. 그 시간의 숫자 worldstate도 비교 지표로 보간한다. **보간 fullstate는 도달 가능한 source 중간 상태가 아니다.** 실제 source raw마다 안전을 확인하고 bracketing 상태/접촉 ID를 보존하며,경계 위치 오차≤.15m·방향/기계 기억의 사전 비교 허용치를 별도로 확인했다. 전사에서는 contact ID까지 정확히 비교했고,변형 궤적의 gate contact ID는 bracket별 로그로 남겼다.

## 결과: 전사·예측·안전·효과 분리

| 단계 | 검증된 결과 |
|---|---|
|9개 독립 node 전사|36raw의 전체 root/힘 정확 일치,모든 terminal defect0|
|연속 재전파|36raw 전체 root/힘 정확 일치,저장 world geometry/path 재현|
|한 LP|HiGHS optimal,0방향 feasible,예측 평균 이득.486611ms|
|한 source 후보|모든 원 전역 안전·gate 상태 비교 통과|
|효과|양쪽5ms 미달,추가 후보/확대0|

| 동일 공간 plane |저장/재현 baseline|559 후보|보간 이득|LP 예측|
|---|---:|---:|---:|---:|
|6hold 뒤|.480000s|.479562907s|.437093ms|.438341ms|
|8hold 뒤 후속|.640000s|.639467337s|.532663ms|.534880ms|

예측 오차는 각각 **−.001249/−.002217ms**,약1.25/2.22µs였다. 이 한 국소 방향에서의 수치 예측 일치이며 전체 모델 calibration/모든 방향의 정확성이나 물리 시간 보장은 아니다. 두 plane의 world 위치 차이는 **.017173/.019043m**로 허용 안이었다. body/COM·yaw·wheel omega/gas·joint/rate·heading/offset 등 world 비교 조건도 통과했다.

baseline과 후보의 raw bracket은 각각 **[.46,.48] / [.62,.64]초로 동일**하다. 따라서 보간 이득을 한 raw tick 개선이나 실제 시뮬레이터 성능으로 부르지 않는다. HiGHS의 최적 판정도 이 trust box의 선형 문제에 대한 것이며 비선형 원 문제의 시간 최적성/개선 상한 증명이 아니다.

후보36raw의 footprint최저 **1.136855m**,path최대1.325267m,원551 참조 overspeed최대−1.521495m/s,force최고 **1.058972**,모든 body최고64.300964m/s였다. 누적 clipping은 **10% 경계**에 닿았다. 새 clipped sample은 baseline mask의 subset이었다. 전역 안전은 통과했지만 넓은 여유가 있다고 주장하지 않는다. 후속2hold와 사전 buffer1hold도 변경된 현재 상태에서 source로 직접 전파·검사했다. 과거 미래 명령을 무검증 안전으로 간주하거나 그 뒤 전체 랩으로 연결하지 않았다.

## 해석·비용·보존

558의 미수렴은 일반 전사법이 안전 source 궤적을 보존하지 못한다는 증거가 아니었다.559는 **도달 source trajectory를 쓰면 full worldstate 전사가 정확히 feasible이고,작은 제어 변화의 시간 응답을 예측할 수 있음**을 확인했다. 동시에 이 한 제한된 국소 방향의 효과는 매우 작았다. 결과를 전체 접근의 실패/성공이나1초 랩 개선 근거로 확대하지 않는다. 임의 합성 주기 목표의 feasibility와 초기화/수치 conditioning 문제는 여전히 별도이며,이번 단계에서558을 다시 풀지 않았다.

상한은 계산 전 **model800틱·명시 힘4,000회·geometry700회·CPU90초/wall120초**,독립 node9·FD12·LP1·후보1로 고정했다. 실제 비용은 **540틱** =독립 전사36 +baseline36 +FD432 +후보36,명시 휠 힘 **2,160회**·적분 내부2,160회,geometry **518회**,body검사540이다. **CPU7.876836초/wall7.863592초**다. FD의 거절 forecast1raw가force1.059036을 기록했으며 비용/로그에 포함했다. 안전한 후보 실행으로 표시하지 않는다. inherited residual_calls0은 미사용 필드다.

읽기 전용 감사 **19항목**이 입력/소스/STARTED·사전 구간·실제 저장 tracking 이력·모든 node/연속 fullstate/force·LP 예측 재계산·같은 공간 crossing·bracket overlap·기존 안전·no-new-clip/상태 비교·효과 판정·모든 비용·main을 확인했다. 감사 source/force/geometry 평가0이며 편집·대화·Git 총비용을 과학 CPU로 주장하지 않는다.

실제 행동/reset/world·새seed/HOLDOUT/SEALED·다른환경·별도 유료0,연구 **22,758**·예비 **84,000/사용0**이다. 원시 지도/seed·fullstate/명령·node/FD/Jacobian 재현 입력·gate 좌표·checkpoint는 저장소 밖 비공개다. main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`·Participants·사용자 변경·558 실패·기존 백업을 보존한다. 개인 문서는 parent의 완독·허용된 필요 내용 전달 범위로 진행했으며 직접 원문 독해나 파일 요청/전송을 주장하지 않는다. 종료 **2026-10-20 19:01:55KST**,자동 연장 없음이다.

[사전 계약](transcribe559_contract.json) · [전사 gate](transcribe559_transcription.json) · [실행기](transcribe559_model.py) · [원결과](transcribe559_result.json) · [감사·공통 공간 시간 재계산](transcribe559_audit.json)
