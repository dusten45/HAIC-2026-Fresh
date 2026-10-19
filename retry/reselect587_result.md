587 — 날짜 정정과 source0 연구 방향 재선택

현재 승인 종료는 **2026-10-20 19:01:55 KST / 10:01:55 UTC**다. 586 보고서에서 승인이 끝났다고 한 판단을 정정한다. 이번에는 기존 데이터 분석과 다음 단일 반증 제안만 수행했고 새 source·force·FD·solver·profile·native 실행은 모두0이다. 실제13.66초/source13.20초 incumbent, 원장22,758 및 reserve84,000/사용0을 유지한다.

날짜 정정과 원본 보존

이번 사용자 전달 원문에서 2026-10-16T11:08:23.287890Z의 사용자 연장 지시, 11:08:35.874793Z의10월20일 종료 확인, 11:11:53.197403Z의 계속 진행 지시를 확인했다. 기존 [541 계약](joint541_contract.json)의 authorization_evidence와 [541 보고서](joint541_result.md)에도 같은 근거가 이미 있었다. 따라서 586의 '연장 승인 근거 미확인/승인 종료' 설명은 잘못이었다. 현재 전달된 정확한 종료 시각을 따르며 자동 연장은 없다. 사용자 지시의 '3일'과 당시 응답의 달력 계산을 새로 재해석해 종료일을 바꾸지 않는다.

[명시적 정정 기록](reselect587_date_correction.json)에 근거 시각·의미와586 원본 보고서/result SHA를 남겼다. 원문 발췌·메시지 식별자는 비공개에만 보존했다. `shoot586_result.md/json`을 고쳐 쓰거나 과학 실패를 재실행하지 않았다. 586의 국소12.782μs 개선·raw312 REFERENCE 실패·replay0·승격0은 그대로다.

586: 초기 조작이 없었던 이유를 표현·제약·gradient로 분리

[읽기 전용 분석 코드](reselect587_analyze.py)는 보존된 두 전체 Jacobian과127개 후보의 저장값만 읽고 단순 배열 산술을 한다. 새 derivative나 최적화는 계산하지 않는다. [결과 JSON](reselect587_analysis.json)에 입력 hash와 집계가 있다. 원시 명령·상태·Jacobian 전체는 공개하지 않는다.

50차원은 holds25..49의 개별 조향·signed pedal이었다. seed를 포함한 전체 물리 경계를 열었고 추가 tube로 초기 좌표를 막지 않았다. seed pedal25개 중10개는 이미 절대값1 경계였다. 제안13개는 모두40좌표, 그중 초기25..34의20좌표 중19좌표를 바꿨다. **초기 조작은 제안됐지만 최선 후보로 선택되지 않았다.** 최종 최선 case23은 여전히 pedal 한 좌표 +0.00010000169277191162의 FD 점이며 초기25..34와 초기 준비 상태 차이는0이다. 이를 큰 초기 공동 계획 성과로 해석하지 않는다.

첫 seed Jacobian의50개 FD 중36개가 실패했다(FORCE11/PATH25). 초기20개에서는18개가 실패하고2개만 안전했다. 실패점 목적함수는 통과 시간이 아니라 `baseline+1+(156−관측행수)/156`였으므로 seed에서 약1.295~1.622초의 불연속 점프를 만들었다. 정규화 FD0.001로 나눈 최대 목적함수 기울기는 약1621.53초/정규화단위였고, 안전 FD의 최대는 약0.0127822였다. 초기 안전2열의 최대는0.00589756이었다. 이 둘은 같은 물리 시간 민감도로 해석할 수 없다.

1718개 inequality에는 완주·유효 통과 여부의 ±1 terminal과 미관측 residual−1도 들어갔다. 첫 Jacobian의36열에서 terminal 차분이0이 아니었다. 일부 후속 geometry가 관측되지 않은 점과 완전 궤적의 차분이 섞여 있으므로, 그 열은 매끄러운 동역학의 미분이 아니다. seed는 clipping residual0, path residual1.90672e−5(정규화 전 약57.20μm), 한 wheel force slack1.00217e−5에 놓여 있었다. 경계·누적 정수 clipping·최초 실패에 따른 관측 절단이 실제로 있었다. 제약 개수가 변수보다 많다는 사실만으로 불가능성을 주장하지 않는다.

저장 첫 Jacobian으로 제안 변위를 단순 내적하면 case53은 목적함수 약−187,651초, case61은−555.35초의 변화를 예측한다. 실제는 전자가 force 실패, 후자가 기준보다1.663524ms 느린 안전 통과였다. 이 숫자는 solver의 내부 예측 로그가 아니라 보존 df와 실제 변위의 사후 선형 계산이다. 특히 case53..60은 이 선형 제약에서 음수 residual이0개였지만 실제 force/footprint에서 실패했다. 실패 penalty/미관측 padding 차분과 큰 외삽의 조합이 유용한 물리적 gradient를 제공하지 못한 직접 증거다.

첫 큰 제안 case52의 초기 최대 조향 변화0.161771rad/pedal1.0은 raw98 clipping 실패였다. backtracking된 제안은 FORCE→FOOTPRINT 실패를 거쳐 작은 변화에서 안전해졌다. 안전한 공동 제안은 다음3개였다.

| case | 초기 조향 최대 변화(rad) | 초기 pedal 최대 변화 | 전체 조향/pedal 최대 변화 | 기준 대비 s300 시간 |
|---|---:|---:|---|---:|
|61|0.0002164841|0.0013382320|0.0005603246 / 0.0023806095|+1.663524ms|
|62|0.0001082420|0.0006691140|0.0002801605 / 0.0011903048|+0.826752ms|
|114|0.0000912547|0.0006830801|0.0002797265 / 0.0011721849|+0.476036ms|

세 후보 모두40좌표/초기19좌표를 바꿨지만 기준보다 느렸다. 초기 조작을 시험하지 않은 것이 아니라 첫 방향의 안전 backtracking이 작은 느린 해로 들어간 것이다.

case62에서 만든 두 번째 전체 Jacobian은50열 모두 안전했다. 초기20열의 최대 시간 기울기0.0327775, 후반30열0.0127827이며 terminal 차분은0이었다. case114의 모델 예측은 이 anchor보다0.351678ms 개선, 실제는0.350716ms 개선으로 가까웠다. 따라서 모든 gradient가 무용했다는 설명도 틀린다. 다만 anchor 자체가 seed보다 느려 seed를 이기지 못했고 세 번째 Jacobian14열 중 예산이 끝났다. 결론은 **이 최초 실패 제약 표현과 유한 SLSQP 예산에서 충분한 초기 공동 조작의 이득을 찾지 못했다**는 것이다. 더 많은 FD가 해결한다거나 고정 경로의 물리 한계라는 결론은 없다. 이 결과를 핑계로 raw312의 작은 reference 초과만 수리하는 후속은 선택하지 않는다.

큰 실행 개선이 있었던 구조와 현재 고정 설계

|기록|실제로 바꾼 구조|검증된 효과와 한계|
|---|---|---|
|[539](profile539_result.md)→[541](joint541_result.md)|533 기하는 유지하고 cap80→90의 전역 속도 profile과540 출발을 결합|541 새 실제 비교14.22→13.66초,560ms. 단독240ms+320ms의 인과 가산성을 입증한 것은 아님|
|[549](retime549_result.md)→[551](whole551_result.md)|동일533 기하/cap90에서 축별 종·횡 힘을 결합한 전체 speed retiming|source13.66→13.22초,440ms·안전 완주. native0,500ms 효과 gate 미달은 물리 안전 실패가 아님|
|현재551 reference/path 주변 직접 shooting|기하·속도 기준을 고정하고 명령을 국소 변경|source13.20초가 incumbent. 586의12.782μs는 전체 실패로 승격0|

541과551은 모두 새 경로 기하의 효과를 검증한 기록은 아니다. 그러나 **출발/속도 설계 구조를 바꾸었을 때 큰 실제 또는 source 개선이 관측됐다**는 근거다. 현재551 reference가 최적인지, 그 주변 micro repair가11초대의 적절한 표현인지 입증하지 않는다.

[578의 저장 전구간 분류](reframe578_result.md)에서 source13.20초 중 launch1.92초, 직선·가감속2.76초, 고정 곡률 코너4.58초, 장애물 근접1.34초, 회복2.60초였다. 코너·근접·회복 합8.52초는 실제 소요 시간이며 회수 가능한 손실이 아니다. 551 fullgas 거절 관측은 force37/reference56/clip1/forecast footprint2였고 forecast 최소 여유는.500039446m, 실행 body최대96.934782m/s·누적 clipping최대10%였다. reference와 force·차체 여유가 함께 구속하며, 한 조건의 삭제만으로 회수할 시간을 계산할 근거가 없다. 578의 s800 이득22.88ms 중 뒤100m에서16.77ms가 상쇄된 관측은 첫 코너 뒤 유지 구간을 보는 이유다.

전체랩의 구조적 비용 후보는 반복되는 높은 곡률·회전 과도·감속 뒤 회복, 그리고 설계 reference에 묶인 고속 구간이다. 아직 그중1초가 제거 가능한 손실이라는 증거는 없다. 578의12.46788초 및555의11.507초는 실제 도달·과도·전체 주행을 검증하지 않은 proxy이므로11초대 가능성이나 개선량의 근거로 쓰지 않는다. 541 native와 현재 source의 서로 다른 정책 시간 차이도 모델 오차로 해석하지 않는다.

요구 안전과 채택한 설계·인증 조건

현재 사용자 요청은 실제 차체/도로/장애물·원물리 domain·force/누적 clipping을 유지하라고 명시한다. 과거 원문 전체를 새로 읽었다고 주장하지 않으며, 아래 출처는 보존된 코드·계약·보고서다.

|항목|확인된 출처와 성격|다음 제안의 처리|
|---|---|---|
|실제 도로·장애물·유한 차체, 물리 action/domain, clock/visited/tracker/finish, 관측 경계|평가/물리 계약과 현재 사용자 유지 지시|그대로 유지, source 진단을 pixel 제출 성능으로 바꾸지 않음|
|force 물리1.25/불확실성.19/buffer.001, 내부1.059, tracking prefix clip≤10%, launch peak2.5/clip≤15%, body<100, model footprint≥.50/native≥.25|현재 유지 지시와541/551 채택 안전 인증. 모든 숫자의 최초 사용자 원문 기원까지 확인했다는 주장은 아님|엄격 유지, forecast/실행에 모두 적용|
|cap90|539: reference90=0.9×source body domain100으로 선택한 **설계값**. 물리적 최고속도 또는 자체 안전 증명이 아님|이번 후보는90 그대로, cap sweep 없음|
|고정551 path/reference/backup와533기하|539/549/551에서 고정한 **설계 identity**|새 line/profile 변경을 명시한 별도 계약 필요|
|path≤3m, reference 외부+5/내부+4.85m/s|551의 **채택 추종 인증 조건**. 사용자 원문의 직접 물리 요구라고 확인되지 않음. 현재586에서는 엄격한 원계약|숫자 유지. 새 사전고정 line/profile에 대한 판정으로 기준 객체가 바뀌므로 admissible set 변경을 명시. old551 편차도 병기|
|100/500ms, 상대 yaw/추가 margin gate|특정 실험의 비교·승격 설계|안전 법칙으로 쓰지 않으며 다음 소규모 시험에는 고정 성능 문턱을 가져오지 않음|

기존 숫자를 조용히 바꾸거나, 실제 주행 속도를 본 뒤 reference를 올려 실패를 합격으로 만들지 않는다. 새 문제 계약은 이전586의 합격을 소급 주장하지 않는다.

다음 단일 작은 반증 제안 — 한 line과 그 speed plan

[제안 계약](reselect587_next_contract.json)은 **PROPOSED_NOT_EXECUTED**다. 연구선은 하나다. 첫 코너의 방향 변화가 급격했던 s90..220 기하를 **단 하나의 tangent/curvature 연결 quintic Hermite line**으로 바꾸고, 그 기하에 대한549식 축별 힘 결합 speed profile을 source 결과를 보기 전에 계산·고정한다. cap90·537 feedback·540 launch 코드와 물리 안전은 유지한다. backup 입력의 기하·속도 배열도 새 경로에 맞춰 명시적으로 바꾸며 기존 backup 바이트 identity를 주장하지 않는다. 지금 새 line/profile조차 생성하지 않았다.

endpoint는 원551의 s90/s220이며 chord 길이L과 저장 tangent/curvature로 양 끝1·2차 미분을 지정한다. 정해진 closed-form basis와513개 고정 표본을 사용한다. 정적 기하가 뒤집히거나 자체 교차하거나 기존보다 peak curvature가 줄지 않거나 finite-body 여유를 만족하지 않으면, 다른 형상으로 바꾸지 않고 이 한 설계를 닫는다. 새 곡선의 실제 ds/arcs를 다시 계산하며 기존130m를 새 arc 길이로 재사용하지 않는다. 새 점의 parameter u에는 old station90+130u를 별도 보존한다. backup도 같은 새 기하/arcs를 쓰고, 그 속도 제곱은 각 점에서 새 candidate 값과 old station에 보간한 기존 backup 값의 최솟값으로 고정한다(periodic/launch 각각, 기존cap80 유지). 이 정의는 기존 backup 코드·입력을 모두 그대로 둔다는 뜻이 아니다. s300/s400 자격의 old progress는 원551 기하에 독립 projection해서 얻고, 동역학의 new progress와 구분한다. 보간·tie/wrap 산술은 후속 source 전에 구현과 함께 pin해야 한다. 정적 통과나 이 보수적 backup은 동역학 안전 증명이 아니다. 기존541에서 관측한 곡률 최대를 새 line의 reachability 증거로 복사하지 않으며, 새 profile의 곡률 입력을 바꾼 설계 가정도 명시한다.

후속 실행이 별도로 등록된다면, initial577 positive를 고정 world s400 crossing hold까지 최대416raw 정확 재현해 raw96 full checkpoint를 확보한다. 한 후보를 그 checkpoint에서 최대80holds/320raw만 수행하고, 새 기하가 s220에서 원기하로 돌아온 뒤 s300·s400까지 진행한다. teleport/factual pose 대입 없이 같은 state/history/clock을 이어 간다. 첫 엄격 위반에서 즉시 중단한다. 목표면은 설계 전에 원기하에 고정하며 s300/s400의 기존 진행±10·corridor3·첫 전진 교차·통과 hold 전체 안전을 유지한다. 내부 forecast/FINAL 계산도 전부 계측한다.

핵심 질문은 **곡률 전이를 바꾼 도달 가능한 주행이 첫 코너와 이후 복귀를 안전하게 수행하면서 s400을 더 일찍 통과하는가**다. s200/s300의 연속 시간·정수 bracket, early steering/pedal, yaw/slip/joint/rearω/force/clip/margin, s220 이후 상쇄를 모두 보고한다. 원551 path/reference 초과는 진단으로 병기한다. s400 연속 시간이32ULP보다 큰 폭으로 개선되고 전체 창이 안전할 때만 한 번 initial 고정 tape exact replay≤416raw를 한다.100/500ms gate는 없다. 같은 정수 bracket인 작은 이득도 사실대로 기록하며11초대나 전체랩 성능으로 외삽하지 않는다.

최악 실행 raw는 positive416+후보320+replay416=**1,152**다. 별도로 모든 내부 forecast·거절 trial까지 포함한 hard cap은 attempted/completed 각각60,000, external force260,000/internal240,000/total500,000, geometry65,000, profile 대수 경계평가100,000, **CPU900초/wall1,100초**다.551의166hold/73,065ticks·CPU748.556초에서80hold의 차수는 약35k ticks지만 이는 보장이 아니다. 실제 비용 상한을 먼저 만나면 예산 중단으로 기록한다. 586의 실행 raw 비용만 곱해 forecast를 숨기지 않는다. 매 단계 replay·audit 여유를 예약하고 승인 종료까지1,130초 미만이면 시작하지 않는다.

정적 실패·최초 strict 실패·미도달·비개선·exact replay 불일치면 후보를 닫고 새 형상/수치/solver/seed로 구조하지 않는다. 성공은 **전체랩 검증을 별도 제안할 자격**만 준다. whole/native/실제 incumbent 승격은 이번 제안에 포함하지 않는다. 현재587의 과학 실행 권한은0이며 이번에는 제안과 날짜 정정만 저장한다.

보존과 검증

586 원본 hash와 날짜 정정, source0 입력 hash, 실제 제안 집계가 재현 기록이다. 분석 도구는 JSON/NumPy 읽기·내적만 사용하고 동역학 모듈을 import하지 않는다. 원시 상태·명령·개인 원문·Jacobian은 저장소 밖 비공개에 둔다. main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`, Participants·기존 변경·실패·백업을 유지한다. 추가 유료 자원·다른 환경·HOLDOUT·SEALED는0이다. 586 source/과학 실패를 반복하지 않고 종료한다.
