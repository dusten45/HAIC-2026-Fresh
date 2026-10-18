# 558 — world pose·corridor·기계 주기·후속을 함께 제약했으나 단일 solve에서 feasible 해 미발견

**한 joint shooting solve가 사전40회 반복/status9로 종료했고,1,043개 고유 평가 중 feasible 해는0개였다.** 최종 iterate의 footprint1.544047m·원 경로 거리.608529m는 기존 .5m/3m 안이었다. 그러나 주 목표 pose·기계 endpoint·상대주기 잔차와 후속 목표를 동시에 만족하지 못했다. **이번 최종 실패를 PATH 이탈로 부르지 않는다.** 안전한 연결의 부재 증명도 아니다. 후보 독립 검증·후속 accepted 실행·실제 평가 모두0이며 실제13.66초·551source13.22초를 보존한다.

## 실행 전 고정한 한 문제

557의 첫 합성 안전 주기 상태를 그대로 초기 fullstate로 사용했다. 다른 fixture/지도/속도/시작점을 고르지 않았다. world 목표는 기존533 seed arc 위의 `s0+v0*T` 위치와 해당 segment의 tangent/곡률로 고정했다.

- 주 전환 **6hold=.48초**: 제어12변수로 기계 endpoint와 world pose를 함께 다루기 위한 사전 수치 문제 설계다. 이 기간이 물리적으로 필요하거나 충분하다는 주장이 아니다. 목표 거리는20.600867m 앞이다.
- 후속 **2hold=.16초**, 총.64초: 목표 거리는 시작에서27.467822m 앞이며 같은 최적화에 포함했다. 주 gate를 통과할 경우에만 독립 전파에서 이어 실행하도록 고정했다.
- 주 목표의 곡률은 해당 기존 seed segment값이며, 임의로557의 고정 곡률 원운동을 도로 위로 연장하지 않았다. 목표점/기간을 실행 뒤 바꾸거나 이전 PATH 기준을 완화하지 않았다.

변수는8hold의 steer/signed pedal16개와 주 목표의 상대주기 상태8개(v,beta,joint,gas,omega4), 총24개다. 주 목표는 world 위치에 놓고 body angle을 도로 tangent−beta로 둔다. 속도는[5,v0] 안에서 설계하며, source4raw의 body 속도/yaw/wheel omega 주기 잔차7개를 등식으로 제약했다. joint/rate/gas/heading/offset/lever 등 모든 기계 fullstate는 독립 검증 gate에 포함했다.

주 목표 pose 허용치는 위치 **.25m**·body angle **.02rad**, 기계 endpoint 허용치는557과 같다(속도.15m/s,yaw.05,omega.5,gas/joint.02 등). 후속 고정 시간에는 위치 **.35m**,속도방향.03rad,body방향.08rad,yaw오차.15rad/s,속도오차.5m/s를 요구했다. 이 오차들도 목적함수만이 아니라 **명시 부등식**에 넣었다.

원 지도에서 **주/후속32raw와 목표 주기4raw의 초기·모든 post-raw 상태**에 source 전체 footprint≥.5m·원 seed 경로 거리≤3m를 solver 제약으로 계산했다. 모든 raw force≤1.059,각 prefix clipping≤10%를 위한 기존.9999 order-statistic buffer,hull/wheel≤99.9,합성 목표 reference overspeed≤4.85도 함께 제약했다. 모든 model tick의 hard body domain100은 별도 유지했다. 거절 forecast도 비용에 포함하며 accepted 안전 표본으로 부르지 않는다.

목적은 정규화된 주 pose/기계·후속 pose/속도/yaw 오차 제곱합과 작은 목표 속도 유지 항이다. 초기화는 기존 seed 곡률의 `atan(3.24*k)` feedforward steer와557의 gas 하나뿐이다. 목표 beta/gas는 곡률 비율,omega는557 상태에서 초기화했다. PP·대체 시작점·후보/기간 sweep은 없다.

**SLSQP1회,maxiter40,ftol1e−8,eps1e−6,고유평가≤1,100**으로 고정했다. 동일 float64 변수의 중복 요청만 cache 재사용한다. feasible 판정은 scaled 주기 잔차≤1e−8·부등식 최소≥−1e−7이고, 발견한 feasible iterate 중 사전 목적이 가장 좋은 **한 후보만** 독립 float32 검증하도록 등록했다. 수렴 성공·feasible 발견·독립 검증을 분리한다.

전체 한도는 **model42,000틱·명시 휠 힘175,000회·geometry42,500회·CPU900초/wall1,000초**다. 목표 주기4raw의 독립 fullstate 검증 후, 주6hold와 목표 gate를 통과해야 후속2hold를 이어가며 clipping 이력은 분리 초기화하지 않는다. 비용/deadline/body domain에서는 상태를 보존하고 끝내며 재시도·자동 연장하지 않는다.

## 관측 결과와 판정

| 최종 solver iterate | 관측 | 사전 기준 |
|---|---:|---:|
| scaled 목표 주기 잔차 최대 |.006194712|≤1e−8|
| 전체 부등식 최소 |−3.463821|≥−1e−7|
| 최소 source footprint |1.544047m|≥.5m|
| 최대 원 경로 거리 |.608529m|≤3m|
| 주 목표 위치 오차 |.900326m|≤.25m|
| 주 목표 body 방향 오차 |.089276rad|≤.02rad|
| 주 기계 속도 오차/허용치 |2.457151|≤1|
| 주 기계 yaw 오차/허용치 |1.465202|≤1|
| 주 wheel omega 오차/허용치 |2.572742|≤1|
| 후속 위치 오차 |1.213537m|≤.35m|
| 후속 yaw 오차 |.279487rad/s|≤.15|
| 후속 속도 오차 |1.389217m/s|≤.5|

후속 속도방향/차체방향 오차는 각각.029946/.032594rad로 해당 허용치 안이었지만 다른 조건들이 남았다. 최종 corridor 수치를 전체 동시 feasible 또는 안전한 상태 연결로 승격하지 않았다. 이 iterate는 **거절된 최적화 forecast**이며 실제/accepted 실행이 아니다.

전체 평가에서 관측한 가장 작은 scaled 주기 잔차도.000198724로1e−8을 넘었다. 가장 좋은 부등식 최소도−3.403137로 미달이었다. 이 두 값은 서로 다른 iterate의 진단값이며 하나의 개선 후보로 조합하지 않는다. 모든 원시 iterate/목적/잔차/geometry와 최신 fullstate checkpoint를 비공개에 보존했다. 독립 후보 검증을 열 조건이 충족되지 않아 **새 float32 검증·accepted 후속 전파를 실행하지 않았다.**

SciPy의 bound projection 경고가 있었으나 실행 오류나 정책 수정으로 분류하지 않는다. 종료 원인은 사전40회 반복 한도다. 방정식의 안전 해 부재,목표의 물리적 불가능성,전체 상대주기 방법군 실패를 증명하지 않았다. **이번 단일 초기화·single-shooting 수치 문제에서 feasibility 회복에 실패**했다고 분류한다. 반복 수 증가·사후 기간 연장·다른 solver/시작점으로 재시험하지 않았다.

## 기전 가치와 남은 장애물

557에서는 기계 endpoint를 맞춰도 후속 PATH가 실패했다.558에서는 world geometry를 설계에 넣어 최종 iterate의 corridor는 안으로 들어왔지만, **도로상 위치/방향/시간과 기계 상대주기·후속 조건을 함께 만족하는 증인**은 얻지 못했다. 기계 주기 라이브러리만으로 주행을 보장할 수 없다는 기존 결론을 유지한다. 이 결과로 전체 랩이나 실제 평가를 확대할 근거는 없다.

남은 불확실성은 선언한 목표/시간의 feasibility와 단일 shooting의 초기화·conditioning을 구분하지 못한다는 것이다. 계속한다면 이 구분을 해소할 새 선행 근거가 먼저 필요하다. 단순 반복/계수/창 증액이 그 근거를 대신하지 않는다. 전체 랩1초 이득·실제 도달성·픽셀 정책 성능은 여전히 미검증이며,555의11.507을 실적으로 쓰지 않는다.

같은 합성 상태와 기존closure524 rigid-body 근사 source map의 검사다. native Box2D solver 내부 상태의 주기나 실제 도달 가능한 시작 상태로 부르지 않는다. 합성 목표 reference와 원551 참조 준수도 구분한다. 실제 정책 승격에는 참조의 명시·인증, 전체 도로·도달성과 실제 검증이 추가로 필요하다.

## 비용·감사·보존

총 **고유 평가1,043 ×36raw = model37,548틱**, 명시 휠 힘 **150,192회**·적분 내부150,192회, body검사37,548·geometry **39,634회**다. **CPU538.259478초/wall538.300428초**로 모든 등록 상한 안이다. 모든 비용에 거절 forecast를 포함했다. unsafe forecast raw2,638·preclip ratio최고48.779002도 기록했으며 실행/안전 통과로 표시하지 않는다. 모든 model body 최고62.341023m/s로100 미만이다. inherited residual_calls0은 미사용 필드이며 계산0이라는 의미가 아니다.

읽기 전용 감사15항목이 소스/입력/목표/STARTED hash·동일 초기 fullstate·고정시간 arc 목표·단일 solver/초기화·모든 feasible flag·검증 미실행 gate·모든 적분/힘/geometry/body 비용·한도·main을 확인했다. 감사 source/force/geometry 평가0이다. 측정 CPU는 과학 실행 구간이며 편집·대화·Git 총시간을 포함한 수치는 아니다.

실제 행동/reset/world·새seed/HOLDOUT/SEALED·다른환경·별도 유료0, 연구 **22,758**·예비 **84,000/사용0**이다. 원시 지도·합성 fullstate·목표 좌표·개별 제어/solver JSONL·checkpoint는 저장소 밖 비공개다. main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`·Participants·사용자 변경·기존 실패·백업을 보존했다. 개인 문서는 parent의 완독·허용된 필요 내용 전달 범위로 진행했으며 직접 원문 독해나 파일 요청/전송을 주장하지 않는다. 종료 **2026-10-20 19:01:55KST**, 자동 연장 없음이다.

[사전 계약](corridor558_contract.json) · [실행기](corridor558_model.py) · [원결과](corridor558_result.json) · [간결 집계](corridor558_summary.json) · [감사](corridor558_audit.json)
