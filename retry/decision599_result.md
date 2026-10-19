599 — 실제 act 시간은 미측정, 다음은 한 입력의 정책 계산 시간 반증

현재 실제 성과는 **한 cold 조건의 privileged DEV native13.22초/661raw**다. 공식11초대 진입은20ms 격자상 **599raw/11.98초 이하**이므로62raw/1.24초 단축이 필요하다.11.99까지1.23초는 연속값 차이다. 일반/carry 승격은 닫혀 있고 잔액22211·reserve84000/사용0을 유지한다.

598 timing에서 확인한 범위

실제 Agent.act 경계는 `local_runner.safe_act`의 별도 thread에서 Agent.act와 배열 변환을 마치기까지의5초이며,env.step/native/render는 반환 뒤다.598은 직접 privileged chooser→actual-state hash→4raw preview→fsynced ACTION_CHARGED→env.step(oracle/COM/trace/render) 순서다. 두 호출 경계가 다르다.

저장 기록에는 chooser/trial 전후 perf/CPU timestamp,fsync·oracle별 소요 시간이 **없다**. HOLD_RESERVE의60CPU/75wall은 예약 상한이고 raw의clock/time은 simulation 시간이다. 전체 arm CPU/wall과 마지막 누적 checkpoint,회수 시 보존한 sparse baseline34hold 누적 checkpoint는 모두 혼합 시간이다. 후보1425.27CPU/1535.44wall을166으로 나누거나 임의 IO 시간을 빼서act 지연이라고 할 수 없다.5초 통과·실패를 아직 판정하지 않는다.

127개 실제 feedback 결정의 저장 호출 수만 분리했다. ACTION_CHARGED−HOLD_RESERVE에서4raw 진단 예측을 제외하면 원 chooser는96~906model attempt다. 최대 작업량은 **hold148:906시도/888완료,geometry2641회**다. 이것은 최대 latency 순위가 아니다. 이 결정의 root·실제 이력·progress·예상 action/report를 비공개 입력으로 준비했으며 새 choose는 호출하지 않았다.

578과 같은 저장값 분류의 시간 배분

|배타적 분류|578의577source|598 fresh baseline|598 native 후보|
|---|---:|---:|---:|
|launch1..24hold|1.92s|1.92s|1.92s|
|직선 가속/주행/감속|2.76s|2.78s|2.74s|
|고정 경로 곡률 코너|4.58s|4.78s|4.60s|
|장애물 근접|1.34s|1.38s|1.34s|
|코너/근접 후35m 회복|2.60s|2.80s|2.62s|

원578 분류·거리·중앙 속도·제약 근접 집계를 저장577에서 재현한 뒤 같은 규칙을 적용했다. 공식 candidate raw까지만 세고 확인 raw는 제외했다. 이 표는 점유 시간이며 회수 가능한 손실이 아니다. 같은 고정 geometry/progress 횡단의 보간 진단에서 baseline 대비 이득은s0..300 약44.60ms,s300..600 약232.96ms였다. 전체 정책 묶음의 차이이며 성분별 인과 효과는 아니다. 이미 얻은440ms를 남은1.24초 기회로 다시 더하지 않는다.

코너·근접·회복8.56초가 주요 검토 구간이지만,1.24초 회수 가능성은 관측되지 않았다. 현재 거리에서 평균 속도 약10.26% 상승이 필요하다는 조건부 산술도 도달 가능성 증명이 아니다. 현재 sample을 reference+4.85로 즉시 포화시키는578식 비물리 proxy는 후보0.73997초(577은0.73624초)다. 가속·yaw·접지·미래 경로를 무시한 값이므로 이득 예측이나 상한으로 쓰지 않는다. 단순한 reference gap 소진으로 목표를 설명할 증거도 없다.

남은 물리 가설은 더 넓은 도달 가능한 코너 준비/회복 상태와 종횡 제어·속도 계획의 결합이다. 고정path/reference/cap90·PP 구조·초기 control 고정은 설계 선택이다. 현재COM도94.84968m/s이므로90은 물리 최고속도가 아니다. 그러나 기존force/누적clip/footprint/path/reference buffer/body domain·평가 tracker/TimeLimit는 현재 인증 계약으로 유지한다. 경로/reference를 바꾸려면 새 identity와 old-reference 진단을 명시해야 하며 기준을 소급 완화할 수 없다. launch24의control 고정과1..24/25+의 서로 다른 안전 phase 규칙도 구분한다. launch96raw는 모두 가속 중이고clip55/384로 여유가 작다.1.92초를 공짜 slack으로 보거나 permissive phase를 늘려서 해결하지 않는다.

579~590이 실제 배제한 범위

|기록|배제한 것 / 남긴 것|
|---|---|
|579·580|13행동 이하·폭4·진행도 ranking의52safe terminal이100ms 게이트를 못 넘었다. 상태 다양성은 있었다. 버린 느린 준비 상태의 미래와 다른 joint program은 미검증이다.|
|581·582·583·584·585|슬립 정렬8raw viability는 통과했다.582는 내부 rollout 비용 누락으로source0였다. 특정 변경 상태에서537복귀21개는force 실패,한 cone/pursuit 법칙은8번째raw에서footprint/path 실패했다. 상태의 보편적 회복 불가능성은 입증하지 않았다.|
|586·587|50시간별 좌표의 국소 결과12.782μs는 같은raw bracket이고 full raw312REFERENCE 실패였다. 실패penalty/terminal/절단 residual이FD를 오염시켰고 수렴도 안 됐다. 전체 joint control 공간을 기각한 결과가 아니다.|
|588|한 chord-quintic 정적 설계 gate 실패다. 모든 경로 변경의 실패가 아니다.|
|589·590|35법선변위의 한 정적 개선은 통과했으나,그 형상+cap90 retiming+기존 controller는safe s400에서29.0685ms 느렸다. 정적J 개선을 시간으로 환산하는 접근과 이 한 조합은 닫되,모든 결합 path/speed 정책을 기각하지 않는다.|

독립 검토의6계수안은 state-dependent spatial correction·joint program 완주·s400 비교라는 점에서579의greedy beam이나586의실패FD와 **완전히 같지 않다**. 다만 여전히 PP target/pedal 주변의 작은 표현이며1.24초 재고의 근거는 아니다. adaptive597을base로 쓸지 저장tape를base로 쓸지,수정 action의 새 FINAL이 future residual program을 무엇으로 인증하는지 미정이다. 원 action의FINAL을 수정 명령에 재사용할 수 없고,backup witness는 준비 상태를 다시 보수적으로 거절할 수 있다. whole-program 직접strict source 검사/replay는 별도 명시할 인증 프로토콜이다.

250000model은 원kernel200000보다 커서 채택하지 않았다. 저장598 h40..76의 원 chooser 합13174를9개에 복사하고 수정48raw 인증을 더한 명목 가격도 실제 변경 상태의 상한이 아니다. 원 chooser만37×32×48×9=511488까지 갈 수 있다. 전체200000 이하 budget을 두면 미완료 program은 비용 검열로 남으며 family 반증으로 셀 수 없다. 지금 같은 offset/형상/FD sweep을 재실행하지 않는다.

다음 단일 제안 — 미실행

[제안](decision599_next_proposal.json)은 **저장 hold148 입력에서 원537 한 번의 clean 정책 계산 시간**이다. 원 path/reference/backup/물리·수치 gate·finite trial·새 FINAL을 유지하고,input 복원/import/context 준비와 결과 JSON/fsync를 별도로 잰다. timed call 안에는 정책·보고값 계산과 필수 body/비용 gate를 포함하며 per-primitive 진단 IO만 밖으로 옮기는 오프라인 프로토콜을 명시한다. 저장 action bytes·전체 reports/FINAL 및906/888 호출 수가 일치하지 않으면 시간 해석을 중단한다.

최대 **1536model시도/완료,외부6144·내부6144·총12288force,geometry5000,전체CPU90초/wall120초**다. 원kernel200000은 유지한다. native/world/reset/action/solver/FD/새 seed/HOLDOUT/SEALED0이다. input 현재 접근과 준비는 확인했으며,별도 실행 범위를 승인받기 전에는 이 호출도 시작하지 않는다.

동일 의미의 core wall≥5초면 그 관측 입력의 필수 구성요소가 deadline에 들어가지 못했다는 반증이다. CPU/wall을 함께 기록하고 단일 관측을 모든 구현의 불가능성으로 일반화하지 않는다.5초 미만이어도 pixel 추론·상태추정·thread/marshalling·모든 다른 입력의 실제act 통과를 증명하지 않는다. **이 실험은1.24초 lap gain을 만드는 실험이 아니라,현재 미측정인 필수 계산 경계를 가르는 더 저렴한 게이트**다.6계수안을 비용/의미 미정인 채 자동 실행하는 대신 이를 하나만 제안한다.

[읽기 결과](decision599_analysis.json),[실패 범위·설계 검토](decision599_review.json),[읽기 코드](decision599_read.py)를 보존했다. 신규rollout/native/chooser/force/geometry evaluator/solver/정책 평가0이며 읽기CPU6.13초/wall6.13초(보수 준비5초 포함)다.11:00UTC 연결 알림 후에도 비공개 입력과598 native 원본 파일을 실제로 다시 읽어 접근을 확인했다. 새 실행은 없고 기존 과학 프로세스도 종료 상태다. 원문/raw/명령/좌표는 Git 외부 비공개,main·Participants·기존 결과와 원장 보존,승인 종료2026-10-20 19:01:55KST를 유지한다.
