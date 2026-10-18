# 526 — 높은 참조 backward45→80: 공유-root 이득, cold 참조 초과로 탈락

**새 native action/reset/world0.** 525 실제18.40초를 고정 baseline으로 두고 high reference의 backward45만80으로 바꿨다. 작은 모델 반증은 같은2.56초에12.68m 추가 진행으로 통과했지만, cold는 hold75/raw4의 참조 초과5.497>5m/s로 중단했다. carry/실제 비교는 하지 않으며 새 완주 시간·0.50초 개선은 미검증이다.

[저장 분석 계약](audit526_contract.json) · [분석 코드](audit526.py) · [525 실제 집계](audit526_result.json) · [후보 계약](braking526_contract.json) · [후보](braking526_control.py) · [원 입력 오류 결과](braking526_model_result.json) · [초기화 수정 계약](braking526_execution_contract.json) · [사용 모델 실행](braking526_corrected_model.py) · [모델 결과](braking526_corrected_model_result.json) · [저장 감사](braking526_audit.py) · [최초 실패 분석](braking526_failure_analysis.json).

## 실제 궤적에서 비교한 병목 근거

525 governor의 source 공식18.40초 구간만 집계했다. raw20ms 경계에서 기준 profile/지형 label을 부여했고12arc bin은 raw 내 선형 분배했다. 각 표는 **서로 별개인 배타적 분류**로 각각18.40초이며 표 사이 시간을 겹쳐 더하지 않는다. 활성 시간은 인과적인 손실·회수 가능한 이득이 아니다.

|525 참조 활성 label|시간|평균 raw 힘 비율|clipping|
|---|---:|---:|---:|
|고정 launch|1.92s|0.590|기존 launch 조건|
|source forward|7.46s|0.609|0.268%|
|backward45|5.68s|0.279|0|
|top80|1.06s|0.068|0|
|곡률/전이|2.28s|0.537|2.632%|

별도 pedal 분류는 launch1.92/gas10.24/brake6.24/coast0초다. 제동 중 평균 source COM 투영 감속40.893m/s², 평균 raw 힘 비율0.293이었다. backward45 label의 평균 감속40.588m/s²/peak ratio0.850이었다. 제동을 더 강하게 할 가능성을 검토할 근거지만 모든 구간의 마찰 여유나 최대 제동 능력을 증명하지 않는다.

별도 geometry zone은 launch1.92/corner4.24/entry20m3.04/exit20m2.54/straight-transition6.66초다.12arc bin은1.113–2.260초 범위다. 참조 경로995.445m와 실제 COM chord 합986.336m는 다른 측정이다. 기존521의 제한된16계수 경로 탐색이 작았다는 사실을 모든 경로 설계의 한계로 쓰지 않았다. 더 짧고 완만한 경로도 후속 연구 가치가 있다. top80 활성1.06초/실측 최고79.835m/s는 현재 cap의 영향 근거지만 cap 변경의 효과 상한을 뜻하지 않는다.11초대 목표에서는 경로·상한도 중요하나, 현재 실제 증거에서 긴 제동 구간과 낮은 평균 힘 사용량을 이번 한 가설로 선택했다.

7개 governor BACKUP은 모두 `FORCE_PEAK` 거절에서 나왔고 예측1/5/9raw 후에 나타날 위험에 대한 가속 감소+제동 증가였다. 모두 clipping-history나 path 오류가 아니었다. 거절된 예측 peak는1.0735–1.1496, 실제 개입 hold peak는0.8601–1.0563이다. 개입 시간0.56초를 전체에서 회수할 수 있는 손실로 간주하지 않는다. scalar clock17.7835초도 실현 가능한 하한/최적값이 아니다.

## 한 변경과 사전 계층

525b의 Gaussian 경로·corner153.384316·top80·source-drive forward·steady gas map·조향·launch/tracking 구분·524 모델·현재 상태 governor/horizon12·여유0.19/예측1.06/물리1.25·누적 clipping 이력을 모두 유지했다. **높은 참조의 backward limit만45→80**으로 바꿨고, 공통 backup100의 backward45는 그대로다.80은 steady convention 최대91.1687보다 낮은 한 고정 후보이며 실현 가능/최적 제동값이 아니다. sweep/gain/미세gas 보정/정적v² cap 변경을 하지 않았다.

작은 반증은 저장525 실제 label에서 가장 긴 연속 backward45 run(38raw, 시작action145)을 결과 관측 전에 선택하고8hold 전 actual action137 직전 root에서 시작했다. 같은 root·현재까지의 clipping9/1792를 공유해 양쪽32holds/128raw를 시험했다. 완전한2.56초 안전과 진행 이득>=3m를 요구했다. cold 이후 carry는 같은 actual518 before47/visited ledger를 쓰고, 각각 안전 source-style finish·0.50초 개선·HIGH>=50%가 필요했다. 통과할 때만 native1000actions/2resets를 허용했다.

525b baseline cold/carry는 정책·경로·524 model·root·counter 이력이 같은 SHA-pinned 저장 모델을 재사용했다. body1668ticks+planning18915ticks=20583ticks는 재적분하지 않았다. baseline 실제18.40초는 불변이다.

## 입력 anchor 오류의 보존과 수정

원 driver가 늦은 probe에 예전 before47 carry anchor를 재사용했다. 잘못된 progress에서 두 governor가 action 이전에 거절되어 body0/잘못된forecast4ticks만 소비했다. 이는 후보의 과학적 반증으로 사용하지 않았다. 원 소스/계약/결과는 보존하고, 저장 root 직전의 **이미 관측한 actual progress**로 probe를 초기화하는 수정 계약을 새로 고정했다. 후보·안전/효과 기준·공유 상태·horizon은 바꾸지 않았다. 기존4ticks/16force 비용을 시작 counter에 포함했고 이전 잘못된 forecast를 유효 결과로 재사용하지 않았다.

## 작은 반증 통과, 전체 cold 실패

|공유 root137의2.56초 모델|baseline525|backward80|
|---|---:|---:|
|완료 raw|128|128|
|끝 progress 차이|기준|+12.675926m|
|tracking 힘 peak|0.888007|0.912526|
|최소 전체 차체·바퀴 여유|1.103412m|1.104652m|
|최대 path error|1.384492m|1.856362m|
|최대 참조 초과|0|3.407778m/s|

작은 반증은 통과했다. 같은 시간의 모델 진행 차이이며 실제/전체 lap 개선으로 환산하지 않았다.

cold는 **hold75/raw4, episode6.00초**의 `REFERENCE_OVERSPEED`에서 중단했다. 당시까지 최소 여유1.043465m, path1.411959m, tracking force peak1.052970<=1.06, clip4/816로 힘/기하 조건은 통과했지만 참조 초과 **5.497148m/s>5**였다. HIGH48/BACKUP3으로 정상 명령 유지94.1%였어도 전체 안전·finish gate는 실패다. carry/native는0이며 finish gain은null이다.

최초 실패 hold는 참조80m/s/feedforward0에서 시작해 **positive gas·brake0**을80ms 유지했다. 그 사이 backward80 segment를 넘어 참조는80→74.340170m/s(5.659830 감소), 실제 모델 속도는79.807050→79.837318m/s였다. raw별 참조 초과는0.7935/2.2247/3.7906/5.4971m/s다. governor가 본12hold 힘 peak는0.812277로 충분히 낮았으나 governor는 힘/path만 인증하고 reference overspeed는 검사하지 않는다.

따라서 이 최초 실패를 **물리 제동80의 능력 부족으로 단정할 수 없다.** 아직 다음 제어 갱신 전이며, 현재 위치의 gradient만 쓰는 action이 가파른 참조 하강을 hold 중에 만나는 시간 경계 문제다. 힘 안전성은 더 빠른 속도 참조의 추종 가능성을 보장하지 않았다. 다음 근거는 finite-hold reference 경계를 미리 반영하는 제동 결정/참조 추종 인증이다. 이번에 이를 추가 구현하거나5m/s 기준을 완화하지 않았고, backward 제동 방법군 전체를 기각하지 않는다.

## 비용·보존

새 모델 **6094ticks** = 유효 probe256 + cold300 + governor forecast5538(잘못된 anchor forecast4 포함). 적분 내 wheel force24376회와 별도 explicit force24388회는 별도다. 저장 분석/감사 적분·force0. baseline cached20583ticks는 새 비용이 아니다. source524 보정 기록도 읽기 재사용만 했다.

worker CPU: 실제 분석0.393025 +원입력오류0.068897 +수정모델13.347809 +저장감사0.165789 =**13.975519초**, wall13.846360초. 준비/publication allowance3CPU/3wall는 별도다. native/action/reset/world0, 연구 **24155**·예비 **84000/used0** 유지. SHA와 이미 관측한 prefix를 확인했다. raw state·지도·명령·case·RNG는 private, 코드/집계만 공개한다. 동일 지정 cloud/DEV/단일 작업, HOLDOUT/SEALED·새 seed·보호 평가·별도 유료 자원0.525/522/523 실패와524보정 보존, main·Participants·사용자 변경·백업 보존. 승인 종료 **2026-10-20 19:01:55 KST**다.
