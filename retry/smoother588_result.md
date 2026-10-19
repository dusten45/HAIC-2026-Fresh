588 — 한 quintic line의 정적 설계 gate 실패, source0 종료

승인된 s90..220의 단일 quintic Hermite 형상을 등록·구현·순수 검사한 뒤 정적 평가했다. **최대 곡률 감소와 finite-body 여유 gate를 통과하지 못해 이 한 설계를 닫았다.** 후보 속도 profile/backup 생성, positive control, source pilot, replay는 모두0이다. 형상·endpoint·숫자·표본·gate를 결과에 맞춰 수정하거나 다른 형상을 시험하지 않았다. 586의 실패나 이전 incumbent 판정은 바뀌지 않는다.

[실행 전 계약](smoother588_contract.json) · [구현](smoother588_math.py) · [등록·정적 실행기](smoother588_design.py) · [결과](smoother588_result.json) · [저장 감사](smoother588_audit.json)

고정한 정의와 순수 검사

기존551 path/reference identity를 바꾸는 별도588 계약이다. 물리 안전과 path3/reference4.85 숫자는 유지하고, 통과할 경우 raw97부터 사전 고정한 새 line/profile을 기준으로 판정하도록 명시했다. 첫96raw는 원래577 계약을 유지하며 전체 prefix를 새 reference로 소급 평가하지 않는다. 실제 실행은 정적 단계에서 종료되어 이 전환을 동역학으로 시험하지 않았다.

기하 프레임은 world xy·CCW 양수 곡률·left normal(−ty,tx)이고 source body angle은 atan2(−tx,ty)다. s90/220 endpoint는 end_arc≥s인 첫 segment의 선형 위치/저장 signed curvature 보간과 그 segment tangent를 사용했다. L은 두 endpoint의 Euclidean chord이며 미분L·t, 이차미분L²·k·n을 지정한 고유 quintic을 closed form으로 만들었다. u=k/512의513개 표본과 endpoint 위치의 직접 대입을 고정했다. 저장 polyline 자체를 실제 C² 곡선이라고 주장하지 않는다.

외부 원래 점은 유지하고 true ds/arcs를 재계산했다. 곡률 gate는513개 해석 곡률과 새 sampled path의 접합부 바깥 한 node까지의 이산 곡률 최댓값을 함께 검사한다. 비교 old도 같은 signed atan2/평균 인접 ds 정의와 join 이웃을 포함한다. 비인접 sampled segment 쌍 전체를 검사해 새 구간과 원래 바깥 구간의 교차도 포함했다. 단순 oldstation 증가와 chord 방향 단조성을 별도로 고정했다.

정적 배치는 원래 source COM-relative levers를 rigid 회전해 hull origin shift를 보존하고, 기존 hull4개·wheel rectangle4개를 사용했다. 모든 wheel joint는 정적0이며 wheel heading은 body heading이다. 새513점은 해석 tangent, 기존 외부 점은 outgoing segment 방향을 사용했다. 기존 road-union/finite boundary/obstacle-circle polygon 판정을 그대로 적용했으며 중심점 여유·531의 추가1.252m floor·최소1m ds 규칙으로 대체하지 않았다. 이 정적 자세가 실제 도달 가능한 wheel/joint 상태라는 주장은 없다.

6개 순수 검사는 endpoint 위치/미분·signed curvature, left-segment tie와 launch/periodic 보간·projection wrap, 자기 교차, truearc/oldstation mapping, COM 회전·finite-body/obstacle 판정, synthetic retiming/backup 최소 profile을 확인했고 모두 통과했다. 후보 생성 전에 계약과 코드·입력 SHA를 고정했다. 후보 endpoint 자료의 독립 다항식 검산 최대 성분 오차는2.0641e−12, signed curvature 오차는1.0430e−16이었다.

정적 결과와 해석

|항목|고정된 한 형상의 결과|
|---|---:|
|기존 교체 구간 arc|130.000m|
|endpoint chord|70.166829m|
|새 sampled arc|88.194153m|
|old 최대 절대 곡률|0.0839059578/m|
|new 최대 절대 곡률(해석/이산·join 합)|0.1670307254/m|
|new 이산·join 최대 곡률|0.1670201491/m|
|derivative norm 최소|50.310810|
|chord 방향 derivative 최소|−24.230603|
|sampled-chain 자기 교차|0|
|새513개 정적 배치 중 margin<0.50m|224개|
|새513개 최소 signed margin|−9.964293m|
|보존된 외부246개 최소 margin|1.568353m|

최악 배치는 새 표본227, oldstation label147.63671875m다. 감사의 한 번 추가 geometry 평가에서 road margin−9.964292813761283m, obstacle margin+12.879832274218593m로 원래 combined minimum과 정확히 일치했다. 실패는 이 정적 배치의 **도로 여유**에서 왔다. 음수 값은 등록된 signed finite-polygon 지표이며 실제 차량 충돌·그 깊이의 penetration 관측이 아니다. 실제 주행은 없었다.

등록 순서상 첫 실패는 chord-forward다. 시작 endpoint tangent의 chord 방향 성분부터−24.20225036이므로, 지정한 endpoint와 이 단조 선별 조건이 양립하지 않는다. 이는 실제 역주행이나 모든 가능한 matching 경로의 실패를 뜻하지 않는다. **그 조건을 제외해 해석하더라도**, 이 형상은 peak curvature가 약1.991배로 늘었고224개 margin 미달이 있어 승인된 smoother-line gate를 통과하지 못한다. 곡률 감소 gate 역시 이 가설의 설계 조건이지 물리 필요조건이 아니다.

길이가 약41.81m 짧아진 것은 안전한 경로 또는 시간 개선의 증거가 아니다. sampled self-intersection0도 연속 곡선 전체나 동역학의 보장이 아니다. 578/555의 낙관 proxy를 성능 근거로 사용하지 않았다. 도달 가능한 경로와 속도를 함께 바꾸는 방법군 전체를 기각한 결과도 아니다.

전환·profile·source 경계

저장된577 raw96 checkpoint 위치의 old/new progress를 각각 독립 projection한 값은 둘 다81.08792499028122m로 s90 이전에 일치했다. 상태·시계·history·visited/tracker를 이동하거나 새 source를 실행하지 않은 순수 mapping 확인이다. s300/s400는 old551 기하에 별도 projection하고 기존 corridor/forward crossing을 유지한다는 계약도 고정했다.

549식 retiming의 cap90, 축별 힘·질량 구분, backward→forward 순서·40회 bisection·정확한 반복 종료, 새 discrete curvature만 사용, backup의 동일 새 기하/truearc와 oldstation 보간 min-profile/cap80을 구현·등록했다. 다만 **실제 후보 retiming 분기로 진입하지 않았으므로 새 reference/backup artifact는 없다.** 실제 속도를 보고 reference를 바꾼 일도 없다. 88회의 대수 force-bound 평가와80회 bisection은6개 순수 검사 중 synthetic fixture에서만 발생했으며 실제 wheel force 호출은0이다.

정적 gate 실패에 따라 사용자 계약의 source 선행 조건이 성립하지 않았다. positive control0, candidate0, replay0이며, source pilot 실행기를 추가로 구축·실행할 필요도 발생하지 않았다. 전체랩/native·새 world·HOLDOUT·SEALED·FD·solver·추가 유료 자원도 모두0이다. 비용 검열이나 기술 오류로 인한 미관측 실패가 아닌 **이 단일 형상의 정적 설계 가설 실패**다.

계수·비용·보존

|집계|실제|승인 상한|
|---|---:|---:|
|actual / attempted / completed source raw|0 / 0 / 0|1,152 / 60,000 / 60,000|
|external / internal / total physical force|0 / 0 / 0|260,000 / 240,000 / 500,000|
|full-body geometry pack|762|65,000|
|profile 대수 bound 평가(전부 synthetic test)|88|100,000|
|CPU(준비·검사·정적·감사·보수적 보조 비용 포함)|24.242167초|900초|
|wall(같은 계산 단계 누적)|23.468980초|1,100초|

geometry762는 실제 정적 배치759=새513+외부246, synthetic 검사2, 원인 분해 감사1이다. 원래 정적 배치의 fixture polygon은6,072개였다. 실제 후보의 position513/derivative1026 평가와 별도로 synthetic 검사에서도513점 구성 한 번이 있었다. 이들 순수 계산은 CPU에 포함되며 실제 raw나 force kernel로 세지 않는다. segment AABB 후보쌍286,906은 실제 closed chain286,902+synthetic4이며, exact segment 교차검사1은 synthetic bow-tie fixture에서 발생했다. 이 순수 broadphase/교차 계수와 full-body geometry pack 계수를 구별한다.

원본 결과는 준비/등록 예비10초와 실제 프로세스 수입·검사·정적 계산을 포함해 CPU21.638368초/wall21.231874초다. source0 감사CPU0.603798초/wall0.237106초와 보수적 보조 비용2초를 더했다. 대화·편집 대기 전체를 과학 실행 wall로 주장하지 않는다. 최종 감사 여유CPU15/wall25 및 모든 aggregate 상한 안이며, 실패·검사 비용을 버리지 않았다.

감사는 입력/코드/계약·비공개 geometry/events SHA,6개 검사,실제 표본/geometry 수,endpoint 수식,최악 margin 성분,raw96 mapping,후보 profile 부재·source0,incumbent/원장/main 보존을 확인했다. 모두 통과했다. 원시 기하·다항식·정적 pose polygon·events·stdout는 지정 클라우드의 저장소 밖 비공개에 보존했다. 공개하는 것은 기술 코드·계약·집계뿐이다.

실제13.66초/source13.20초,연구22,758·reserve84,000/사용0을 유지한다. main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`,Participants·사용자 변경·586/587·기존 실패와 백업은 변경하지 않았다. 승인 종료는2026-10-20T10:01:55UTC다. 이 한 설계를 닫고 다른 형상이나 새 실험을 자동으로 시작하지 않는다.
