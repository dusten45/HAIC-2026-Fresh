# 486 — 준비 실패의 기하 원인과 다음 최소 반증 설계

**485는 장애물 여유를 만족하지 못한 경로 계획 준비 실패다. margin-first 정책 실패나 물리적으로 통과할 경로가 없다는 증거는 아니다.** 486에서는 저장 snapshot·경로·solver/source만 분석했다. 새 reset/step/world·seed 선정·road solver·재최적화·속도 profile 평가는 모두0이다. 원래 초기 선형식을 재구성하고 저장 경로의 거리를 계산했으며, 대안 경로는 구성하지 않았다.

## −0.067586m가 의미하는 제약

258의 장애물 clearance는 각 장애물과 **경로의 모든 직선 segment** 사이 최소거리에서 `장애물 반경 + 차량 원형 envelope 2.9m + 추가 여유0.25m`를 뺀 값이다. 저장된 실제 반경을 적용한 요구 거리는 약4.350000048m이며, 가장 가까운 거리는4.282414070m였다.

| 저장 최종선의 성분 | 결과 |
|---|---:|
| 장애물 clearance 위반 |2개: −0.067585978m, −0.039437430m|
| 장애물 제곱 위반 합 |0.006123175333|
| 최대 절대 곡률 / 목표 한계 |0.129232961 / 0.130491734 m⁻¹|
| 최대 normal offset / 허용 bound |4.563231092 / 4.916666667m|
| 곡률·offset 위반 성분 |각각0|

최악의 −0.067586m는 segment 끝점에서도 같은 값이므로 보간만의 오류가 아니다. 다른 위반은 segment 내부에서 발생하며 vertex만 검사하면 −0.021952452m지만 segment 검사는 −0.039437430m다. 따라서 vertex-only 검사로 바꾸는 것은 안전 기준을 약화하는 변경이다.

추가0.25m를 **해석상 분리**하면 2.9m 차량 disk와 장애물 사이 최소 여유는 +0.182414022m다. 이는 여유 buffer 부족을 실제 차체 충돌과 동일시할 수 없다는 근거이며, buffer를 없애자는 제안이 아니다. 소스 hull 꼭짓점의 최대 원점 반경은 약2.864m로 2.9m inflation의 보수성도 확인된다. 다만 fixture skin·실제 자세·tracking 오차·도로 접촉·동역학은 이 분석으로 자격을 얻지 않는다.

도로 제약도 실제 차체가 모든 road polygon 안에 있는지 직접 검사하는 조건이 아니다. `half-width 40/6 −1.4 −0.35`로 정한 normal-offset proxy다. 차체는 장애물 쪽에서는 원형 envelope로, 도로 쪽에서는 이 별도 proxy로 반영된다. 곡률도 이산 경로의 기하 proxy이며 Box2D 주행 안전 증명이 아니다.

## 초기 경로와 solver가 실제로 한 일

원래 소스는 도로 vertex별 center/normal을 만들고 16계수 주기 cubic basis와 시작·종료10m taper를 사용한다. 각 장애물의 가까운 center vertex에서 반대쪽 회피 offset을 정한 뒤, 가중 선형식과 clipping으로 한 초기 계수 벡터를 만든다. 별도의 좌우 회피측 열거나 탐색 완전성 검사는 없다. 소스의 “one-homotopy” 주석도 모든 trial이 같은 위상에 머문다는 증명은 아니다.

이 초기 경로는 원본 중간 배열로 저장되지 않았다. 동결 source·snapshot에서 원래 초기식만 재구성했으며 반복 search나 profile 계산을 하지 않았다. 별도로 수행한 두 초기식 재구성의 계수·경로 hash는 일치했다.

| 경로 | 최소 clearance | 음수 장애물 | 위반 합 |
|---|---:|---:|---:|
| 재구성한 원래 초기선 |−0.452425596m|3|0.226220995179|
| 저장 최종선 |−0.067585978m|2|0.006123175333|

초기선도 부적격이었고 최종선에서 residual은 줄었다. **feasible 초기선을 버린 사례는 아니다.** 원래 초기 목적값·accepted-trial 기록·중간 경로는 없으므로 탐색 도중 feasible 선이 있었는지, 어떤 trial 교환에서 시간 이득과 위반이 경쟁했는지는 확인할 수 없다.

목적은 `추정 시간 +1000·위반 합 +0.001·주기 계수 차이 제곱합`이다. 저장 목적값은 정확히 다음과 같이 분해된다.

`28.546858505072 =22.198219469928 +6.123175333201 +0.225463701943`

즉 시간과 feasibility가 하나의 유한 가중 score에서 경쟁한다. 그래도 이번 실패가 그 경쟁 때문에 발생했다고 단정하지 않는다. 낮은 표현 차원, 초기 회피측, 고정 step·예산, 비매끄러운 최소 segment 제약도 가능한 원인이다.

194회는 first1 +6 passes×16 coordinates×2 directions +final1의 고정 일정이다. step은 `[2,2,1,1,0.4,0.4]`이고 매 후보는 scalar score가 엄격히 작을 때만 채택한다. 계수 bound는 clipping하며, basis가 비음수이고 row 합이 taper 이하라 offset bound도 구조적으로 제한된다. 실행 가능성을 확보한 뒤 시간을 개선하는 단계나 feasible incumbent 보관은 없다.

종료에는 gradient·stationarity·더 작은 step에서의 개선 부재·전역 하한·search completeness 검사가 없다. `solver_converged`도 실제 수렴 판정이 아니라 `free_feasible`과 같은 boolean이다. 원래 gate는 clearance≥−1e−6, 위반 합≤1e−8이며, 곡률 residual도 이 합으로 허용된다. 별도 수치 projection은 clearance≥−0.001 및 원래 곡률 한계 이내에서만 들어간다. 이번 residual은 그 범위 밖이므로 미진입이 맞다. 허용치를 확대하지 않았다.

## 전체 접근에서 258 의존성을 어떻게 볼 것인가

안전한 reference 자격 없이 모델 비교를 시작하지 않은 것은 타당하다. 하지만 “그 자격을 **이 특정258 휴리스틱이 반드시 찾아야 한다**”는 요구는 별개다. 이를 모든 새 조건의 필수 진입로로 고정하면 controller/ranking 연구가 planner의 coverage 실패로 계속 차단될 수 있다. 485는 그 준비 coverage에 대한 한 관측이다.

| 접근 | 제공하는 것 | 한계·현재 선택 |
|---|---|---|
| 기존258 시간+벌점 |작고 고정된 비용의 GT 경로·속도 후보|feasibility 우선 보장·불가능성 증명 없음|
| 동일 B16의 feasibility-first 순위 |표현·초기화·예산을 고정한 최소 원인 분리|같은 표현/회피측/step 한계는 남음. 다음 한 가설로 제안|
| centerline 기반 corridor/lattice + 명시적 장애물 회피 |도로 좌표에서 허용 offset 구간을 만들고 양쪽 회피 연결을 다룸|연속 segment·곡률·시작/종료 자격 필요. 새 방법으로 별도 설계해야 하며 이번에 구성·실행하지 않음|
| 연속 제약의 feasibility-first 구성 |feasible 단계와 시간 개선 단계를 분리|다른 solver의 국소 실패도 불가능성 증명이 아님. 다음 시험에 묶지 않음|

centerline은 기준 좌표로 유용하지만 저장된 centerline 자체의 같은 clearance는 −4.050283743m다. 그대로 사용하는 안전 fallback은 아니다. `profile(center,blocked)`의 중간 zero 노드도 현재 lap executor의 nonlaunch 양의 target 계약과 맞지 않는다. corridor 대안은 각 road/taper 구간에서 원래 inflated obstacles를 제외하고, 가능한 양쪽 연결을 유지하며, heading 또는 3점 상태로 곡률과 segment 전체를 검증한 뒤 속도를 계산하는 일반 구조다. discretization 실패와 연속 경로 부재도 구분해야 한다.

원래 최종 목표는 합법적인 `(4,84,84)` pixel 관측 정책의 실제 주행 성능이다. whole-map GT 경로와 근사 속도 시간은 진단 수단이며 픽셀 정책이나 공식 completion 성능을 대신하지 않는다. 경로 구성·tracking·pedal ranking·perception/배치 가능성을 구분해 각 gate가 무엇을 자격화했는지 유지해야 한다. 이번에는 과거 연구를 재개하거나 픽셀 기준선을 재평가하지 않았다.

## 다음 한 가설과 최소 반증 계약

**이미 노출된 첫485 DEV에서, 동일 B16·초기화·194회 일정의 후보 순위만 `(위반 합, 추정 시간+원래 평활 항)`으로 바꾸면 기존 geometry gate를 통과하기에 충분한가?** 시간과 평활 항 사이의 상대 가중치, 모든 거리·곡률·offset 기준, conditional projection은 그대로 둔다. 정확한 tuple 순서이며 새 epsilon·seed·방향 restart·차원·추가 archive는 없다. source의 초기 profile/center profile/조건부 repair 비용도 상한에 포함했다.

이것은 “순위 변경 하나로 충분하다”는 한 구조 가설이다. scalar 벌점이 이번 실패의 원인이라는 주장이나 모든 geometry 접근의 비교가 아니다. 실패한 조건을 보고 고른 사후 진단이므로 독립 DEV 검증으로 세지 않는다.

별도 승인 뒤 candidate solve1회/목적평가194회, 기존 조건부 projection 최대1회·clearance평가100회만 제안한다. baseline은 저장 결과로 고정하고 재실행하지 않는다. import·검증·기록·readback 포함 CPU60초/wall90초, 새 retained 출력8MiB/32파일, temp2MiB와 각 volume512MiB 예비를 강제한다. 새 actual/reset/world/model tick/seed는0이다.

기존 geometry gate를 통과하면 **별도 source 검증에 넣을 입력 후보**까지만 승격한다. 완결·정상 실행 후에도 부적격이면 이 조건·예산에서 순위 변경만으로 충분하다는 가설을 기각한다. 입력·수치·source·자원 실패는 기술적 미결이며 재시도·다른 조건·다른 solver로 구제하지 않는다. 원래 snapshot 유실 시 새 reset으로 복구하지 않는다.

486에서는 이 제안을 실행하지 않았다. 485의 실패·두 동결 조건·사용 이력과 원문을 보존했고, 연구 잔여26,175·예비84,000/사용0은 바뀌지 않았다. 새 분석 원시 배열·segment/장애물 식별 정보도 비공개다.

[수치 집계](geometry486_findings.json) · [상세 반증 계약](geometry486_contract.json) · [독립 접근 검토](alternative486_review.md) · [분석 소스](analyze486.py)
