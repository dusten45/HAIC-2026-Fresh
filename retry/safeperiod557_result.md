# 557 — 안전 상대주기와 짧은 상태 전환은 확인, 후속 도로 경로 게이트 실패

**속도·source 이산 주기·힘/clip 제약을 함께 풀어 같은 두 합성 곡률에서 안전한 주기를 찾았다.** 유한 로컬 속도 최대 해는 **42.918473·75.550515m/s**, 최소 해는 둘 다 검색 하한5m/s였다. 모든 endpoint가 독립 float32 주기 검증을 통과했다. 이는 전역 속도 범위나 모든 중간 속도의 가능성 증명이 아니다.

사전 최소 전환도 실행했다. 다음 고정 곡률의 안전 주기로 **16raw 동안 clipping0·힘/도로 안전을 지키며 목표 fullstate 허용치에 도달**했다. 전환 solver는60회 반복 한도/status9로 종료했으므로 최적 수렴으로 표시하지 않는다. 사전 규칙으로 보존한 feasible iterate의 독립 검증 결과다. 그 뒤 target 제어 유지 중4raw 후 원 경로 거리3.204985m로3m를 넘어 전체 전환 후속 게이트는 실패했다. **실제cap0, 새 랩 성능 관측0**, 실제 기준13.66초·551source13.22초 유지다.

## 새 제약 문제와 계산 전 기준

556은 속도를 고정한 period residual만 풀어 주기는 찾았지만 두 해의 힘이1.059를 넘었다.557은 속도를 변수로 추가하고 같은 source4raw map 안에서 다음을 **동시에 제약**했다.

- 변수: 속도, beta, joint target, gas, wheel omega4개. constant steer/gas·brake0인 한 상대주기 분기다. 속도[5,90], beta±.6, joint±.4, gas[0,1], omega[0,500]은 유한 검색 영역이며 물리 필요조건으로 주장하지 않는다.
- 주기 등식: body 좌표계 속도2·yaw1·wheel omega4의 source 한 주기 차이0. gas/joint/rate/heading/offset/lever와 모든 기계 상수도 **독립 fullstate 검증**한다. 한 raw lever 지연 offset을 포함한다.
- 힘/clip/속도 부등식: 모든 raw preclip force≤1.059, 모든 hull/wheel≤99.9m/s. 각 raw prefix의 `floor(.1*N)+1`번째 큰 ratio를 주기 설계에서는.9998, 전환에서는.9999 이하로 제약해 누적 clipping≤10%와 float32 여유를 확보한다. 이 buffer는 충분조건이며 물리적으로 필요한 유일한 조건이 아니다. 최종 평균만 맞추는 clipping 해를 허용하지 않는다.
- 목적: 각 동일 feasible set에서 속도 최대와 최소를 각각 한 번 최적화한다. 최대 초기값은556 해의 속도/omega만.9배, 나머지 beta/joint/gas는556 해다. 최소는 선택된 최대 해에서 시작한다. 다른 시작점·속도 grid/sweep·재시도는 없다.

SLSQP `maxiter60,ftol1e−10,eps1e−7`, objective당 source unique evaluation≤700으로 고정했다. 동일 float64 변수의 objective/constraint/Jacobian 요청은 cache로 재사용한다. 계산된 feasible iterate 중 사전 목적에 가장 좋은 것을 보존하며, **solver 수렴·feasible 해 발견·독립 검증을 별도 판정**한다. scaled period 잔차≤1e−8·부등식≥−1e−8이 수치 gate이며, 이후 float32 한 주기 fullstate 정규화 잔차≤1과 기존 안전 검증을 통과해야 admitted다. feasible iterate를 찾지 못하면 미수렴/유한 분기 미발견이지 안전 주기 부재 증명이 아니다.

두 최대 해가 admitted일 때 exact8주기·사전 작은 body-vx/omega 섭동8주기를 각자 검사하고, 첫 fixture 다음 seed 곡률로 최소 전환한다. 전환 target은 source 최대 속도를 상한으로 같은 안전 상대주기 문제를 한 번 풀며 곡률/목표를 바꾸지 않는다. 전환은4hold 제어8변수·fullstate endpoint 오차 제곱합 최소화,16raw 내 힘/prefix clip/body/target overspeed 부등식, SLSQP60회·unique rollout≤1,000이다. 독립 endpoint 통과 시 target3hold를 추가한다. geometry/path 검증은 실제 알려진 지도에서 독립 수행하며 위반 시 즉시 해당 검증을 멈춘다.

전체 사전 상한은 **source38,000틱·명시 휠 힘160,000회·geometry300회·CPU480초/wall540초**, 극값 solve 최대5개+전환1개다. 비용/deadline/body domain 중단과 상태/실패 보존, 실제cap0·새seed/보호평가/다른환경/유료0을 동결했다.556의 코드·기록은 변경하지 않고 새 실행의 저장 위치만557 비공개 디렉터리로 분리했다.

## 안전한 주기와 속도 증인

| 항목 |첫 합성 곡률|둘째 합성 곡률|
|---|---:|---:|
|556 고정 속도(힘 게이트 실패)|44.283203|76.810791|
|557 admitted 최대 속도|**42.918473**|**75.550515**|
|최대 해 속도 변화|−1.364730|−1.260276|
|admitted 최소 속도|5.000000|5.000000|
|최대/최소 로컬 solver 반복|6/6|5/8|
|최대/최소 독립 주기 fullstate·안전|모두 통과|모두 통과|

두 최소는 **검색 하한**에 닿았으며 물리적 최소 속도가 아니다. 최대도 로컬 solver와 이 분기/영역의 수치 해다. 두 endpoint 사이 전체의 연속 가능성·전역 최대·다른 제어 분기의 부재는 미검증이다. 조건부 전환 목표까지 포함한5개 극값 solve는 모두 solver 성공, 독립 float32 fullstate/힘/clip/geometry gate를 통과했다. 원556 해를 사후 필터로 다시 사용한 결과가 아니다.

검사는556과 동일한 합성 pose·지도·곡률을 사용했다. 실제 도달 가능한 snapshot이나 native Box2D joint/contact solver 내부 상태의 주기가 아니다. 기존closure524 rigid-body 근사 map에서 SE(2) pose를 분리한 기계 fullstate 상대주기다. world 도로 tile ID와 지도는 SE(2) 대칭이 아니며, source contact 갱신과 friction·실제 지도 geometry는 계속 검사했다.

## 여러 주기와 섭동: 기계 상태와 도로 유지의 차이

8주기를 요청한 네 rollout은 모두 **원 seed 경로 거리3m**에서 먼저 멈췄다. 첫 곡률 exact/perturbed는17raw, 둘째는25raw까지 실행했다. 힘 한계나 clipping이 최초 실패가 아니었다. 따라서8주기 안정 통과나 점근 안정이라고 표시하지 않는다.

이미 저장된 마지막 **완료된 주기 phase**끼리 비교하면 첫 fixture는4주기, 둘째는6주기를 확인할 수 있다. exact의 fullstate 정규화 오차는 각각.06422/.05044로 작았다. 작은 섭동의 동일 phase 오차는 초기 대비 **1.78265배/ .64546배**였다. 첫 상태는 이 유한 구간에서 오차가 증폭했고 둘째는 줄었다. 두 수치를 점근 안정/불안정의 증명이나 물리적 필요조건으로 바꾸지 않는다. 저장 상태의 phase 정렬 계산이며 추가 적분은0이다.

일정 곡률 주기 상태를 계속 돌리는 것만으로 곡률이 달라지는 원 도로를 따라갈 수 없다는 제한이 드러났다. `PATH`는 사전3m 설계 envelope의 실패이며 그 위치에서 실제 충돌했다고 주장하지 않는다.

## 최소 전환: feasible endpoint와 최적 수렴을 분리

고정된 다음 seed 곡률 target의 안전 상대주기는 source와 같은42.918473m/s 상한에서 찾았다.4hold transition shooting은60회 반복/status9로 종료했다.1,000 상한 안의574 unique rollout 중 사전 목적에 따른 feasible iterate를 선택했고, 독립 float32 전파로 다음을 확인했다.

| 독립 전환 지표 | 결과 |
|---|---:|
|실행 raw |16|
|endpoint fullstate 정규화 잔차 최대|.000197316 (허용1)|
|힘 최고|.999799976 (한계1.059)|
|clipped wheel|0|
|최소 footprint|4.358366m|
|최대 경로 거리|2.144755m|

**유한 source 안에서 짧은 안전 상태 연결의 feasible 증인**은 얻었다. 최적 비용/최적 제어 수렴은 미확인이다. 후속 target3hold 중4raw 이후 다음 검사에서 경로 거리 **3.204985m**로 중단했다. 이때 목표 기계 상태 오차는 여전히 허용 안이었고 후속 힘 최고.914426이었다. 즉 최종 실패는 기계 endpoint mismatch/힘/clip이 아니라 **후속 도로 경로 envelope**다. 후속 포함 전환 gate를 통과로 바꾸지 않았다.

## 계속 가치·비용·보존

이 접근은 **안전 상대주기 상태와 짧은 기계 전환을 PP 없이 source에서 직접 검사하는 표현**으로는 계속 가치가 있다.556의 unsafe 고정 속도 해와 다른 안전 해를 얻었고, 속도와 안전을 함께 풀어야 한다는 기전 근거가 생겼다. 다만 일정 곡률 상태의 연결만으로 전체 도로/도달성/시간 목적이 해결되지 않는다. 첫 fixture의 섭동 증폭과 후속 path 실패도 남는다. **전체 랩1초 개선을 지지하는 후보는 아직 없다.** 다음 별도 가설의 핵심은 상태 전환과 실제 corridor/pose 제약을 함께 다루는 것이며, 이번 해의 반복 수 증액·창/속도 sweep이나 바로 전체 랩 평가로 넘어갈 근거는 아니다.

원551 참조 대비 overspeed는 모든 accepted 검증에서 별도로 기록했다. 합성 목표 속도는 기계 검사 reference이고 원551 준수·전체 도로 안전·실제 도달성·픽셀 관측 정책 검증을 대체하지 않는다. 실제 정책 승격에는 이 경계 전체가 남는다.555의 낙관11.507을 실적이나 보장으로 사용하지 않았다.

총 **source10,388틱** = 주기 최적화1,060 + endpoint 독립40 + exact/perturbed84 + 전환 최적화9,184 + 전환 독립16 + 후속4다. 명시 휠 힘 **41,572회**, 적분 내부41,552회, body 검사10,388·geometry135, **CPU57.092993초/wall57.109503초**다. period unique265·transition unique574=**839회**이며 inherited `residual_calls=0`은 미사용 필드로 계산0을 의미하지 않는다. 거절 solver forecast의 힘 위반43raw·최대9.821543도 저장·계상했다. 실제/accepted 안전 표본으로 부르지 않는다. 모든 model body 최고79.132967m/s로100 미만이다.

읽기 전용 감사16항목이 hash/STARTED·사전 feasible iterate 선택·5개 독립 fullstate·동시 제약·phase 정렬·전환 미수렴 보존·안전 endpoint/후속 실패 분리·모든 source/force/geometry 비용·body domain·main을 확인했다. 감사 force/적분0이며 편집·대화·Git을 측정 과학 CPU에 포함했다고 주장하지 않는다.

실제 행동/reset/world·새seed/HOLDOUT/SEALED·다른환경·별도 유료0, 연구 **22,758**·예비 **84,000/사용0**이다. 원시 지도·상태/명령·분기/개별 solver JSONL·checkpoint는 저장소 밖 비공개다. main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`·Participants·사용자 변경·기존 실패·백업을 보존한다. 개인 문서는 parent의 완독·필요 내용 전달 범위로 진행했으며 직접 원문 독해나 파일 요청/전송을 주장하지 않는다. 종료 **2026-10-20 19:01:55KST**, 자동 연장 없음이다.

[사전 계약](safeperiod557_contract.json) · [실행기](safeperiod557_model.py) · [원결과](safeperiod557_result.json) · [간결 집계](safeperiod557_summary.json) · [감사](safeperiod557_audit.json)
