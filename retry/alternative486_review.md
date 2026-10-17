# 저장된 첫 DEV의 경로 계획 선행 게이트 검토

486은 저장 자료와 소스 검토만 수행했다. 새 seed, geometry 생성, solve·재최적화, 환경·모델 constructor, reset·step은 실행하지 않았다. 아래 반증 실험은 다음 승인에 대한 제안이다.

첫 DEV의 485 결과는 경로 계획 준비 미자격이다. margin-first 비교나 source transition은 실행되지 않았으므로 그 정책의 독립 DEV 실패로 해석할 수 없다. 저장된 후보의 기존 inflated-obstacle clearance 최솟값은 −0.067586m이며 장애물 두 개에서 음수다. 최대 절대 곡률 0.129233/m는 기존 기하 한계 0.130492/m 이하다. 기존 수치 projection의 허용 조건인 clearance ≥−0.001m를 벗어나므로 projection이 실행되지 않은 것도 계약과 일치한다.

258의 16계수 주기 spline, 장애물 반대쪽으로 초기화하는 규칙, 고정 194회 평가와 `추정 시간 + 1000·위반량 + 평활 항`은 하나의 계획 휴리스틱이다. 명시적인 좌우 회피 분기 비교나 전역 최적성·불가능성 증명이 없다. 따라서 그 휴리스틱이 clearance를 충족하지 못했다는 결과는 회피 경로 자체가 없다는 증명이 아니다. 안전한 reference 없이 비교를 시작하지 않은 것은 타당하지만, 이 특정 solver의 성공을 모든 후속 정책 연구의 필수 조건으로 삼으면 정책 효과보다 계획기의 적용 범위를 먼저 시험하게 된다.

일반적인 대안은 centerline을 도로 좌표의 기준으로 사용하고, 도로 내부·장애물 여유·곡률의 실행 가능성을 먼저 확보한 뒤 속도와 시간을 평가하는 구조다. centerline을 그대로 달리는 대안은 아니다. 저장된 centerline의 같은 clearance 최솟값도 −4.050284m다. 또한 기존 `profile(center, blocked)`의 중간 정지 노드를 SourceC에 그대로 넣는 것은 nonlaunch 정지와 양의 reference-node 계약에 맞지 않으므로, 별도 STOP 정책 승인 없이 fallback으로 사용할 수 없다. 명시적 장애물 회피 corridor와 회피 측 선택은 가능한 후속 구조지만, 현재 자료만으로 새 경로나 어느 측이 좋은지 선택하지 않는다.

다음 하나의 구조 가설은 **같은 표현과 평가 예산 안에서 실행 가능성을 시간보다 먼저 순위화하는 것만으로 이 저장 사례의 기존 경로 게이트를 통과할 수 있다**는 것이다. 첫 반증은 이 가설의 충분성만 시험한다. 새 case를 뽑거나 spline 차원·회피 초기 방향·step 크기·clearance·곡률 한계를 동시에 바꾸지 않는다.

승인 후 한 번만, 이미 저장된 동일 첫 DEV snapshot·질량 모델·초기 계수와 같은 pass·coordinate·direction 일정으로 194회 평가한다. 후보 선택 순위만 `(기존 위반량, 기존 추정 시간 + 기존 평활 항)`의 정확한 사전식 순위로 바꾼다. 시간과 평활 항 사이의 원래 상대 가중치는 유지한다. 선택 이후의 trial 계수는 이 변경에 따라 달라질 수 있다. 기존 near-feasible projection은 원래 조건과 최대 100회 clearance 평가를 그대로 유지하고, 사용 여부를 별도로 기록한다. 계수·경로·trial 기록은 비공개로 보존한다. 이 시험은 사후 선정된 실패 사례의 원인 분리이며 독립 DEV 검증은 아니다.

승격 기준은 기존 `free_feasible` 조건(clearance ≥−1e−6m, 위반량 ≤1e−8)을 그대로 충족하거나 기존 조건부 projection의 원래 exit 검사를 통과하는 것이다. 곡률·offset 잔차도 별도 기록하되 기존 허용잔차는 변경하지 않는다. 이 경우에도 물리 안전이나 tracking 성공을 주장하지 않고, 별도 승인된 source fidelity 검증의 입력 후보로만 삼는다. 게이트를 충족하지 못하면 이 예산에서 순위 변경 하나만으로 충분하다는 가설을 기각한다. 다른 차원·방향·가중치 탐색이나 재시도는 하지 않는다. 비유한 값·schema·source hash·자원 실패는 기술적 미결로 보존한다.

제안 상한은 solve 1회/목적함수 평가 194회와 기존 조건부 projection ≤100회, 전체 CPU 60초·wall 90초, 새 비공개 출력 8MiB다. import·검증·기록·종료를 포함하며 각 volume의 512MiB 잔여 공간과 기존 종료 시각을 지킨다. 새 geometry draw·physics world·reset·actual·모델 적분은 모두 0이다. 이 시험 뒤의 자동 실행은 없다.

근거 소스: `retry/racing258_plan.py`의 `geometry`, `basis`, `solve`, `obstacle_clearance`, `profile`; `retry/racing258_feasibility.py`의 `project`; `retry/bootstrap485.py`의 기존 준비 게이트. 수치는 비공개 485 첫 DEV의 저장된 미자격 후보에서만 읽었다.
