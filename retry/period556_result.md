# 556 — source 이산 상대주기는 찾았으나 두 고정 속도 분기 모두 힘 게이트 미달

**같은 두555 합성 fixture에서 4raw 상대주기 기계 상태를 직접 찾았다.** wheel omega·gas 기억·joint/rate·heading·offset을 포함한 회전좌표계 fullstate 잔차는 float32 명령의 독립 전파에서도 기준 안이었다. 그러나 주기 힘 비율은 각각 **1.115358·1.062715로 전역1.059를 초과**했다. 주기 존재는 통과, 안전 게이트는 실패로 분리한다. 사전 조건에 따라 여러 주기/섭동 안정 검사와 최소 곡률 전환은 실행하지 않았다. 실제13.66초와551source13.22초를 유지하며 새 랩 이득 관측은 없다.

## 새 표현과 source 상태 경계

555의 연속 평형에 접선 힘만 더하지 않았다. 고정된 두 fixture의 속도·초기 yaw=`v*k`에서 **source 네 raw 전이를 shooting residual 안에서 직접 실행**하고, beta·joint target·gas·네 wheel omega를 함께 풀었다. constant steer/gas, brake0인 한 유한 분기다. 속도·곡률·gain sweep 또는555 반복 횟수 증액이 아니다.

source closure524가 쓰는 offset은 `yaw × 현재 lever`가 아니라 **한 raw 전 lever**를 이용한다. 초기 offset에 이 회전 지연을 반영했지만, 그 식만 믿지 않고 source 한 주기 뒤 offset 자체도 비교했다. joint·rate·gas 기억을 고정값으로 생략한 residual이 아니다. 모든 물리 상태 필드를 독립 검증했다.

SE(2)로 world 위치·방향을 분리하고 다음을 body 좌표계에서 비교한다: COM 속도, yaw·각운동량, joint/rate, wheel omega/gas/heading/offset/friction, lever, steer 및 질량·관성·engine/steering 계수·floor·skin. 실제 source tick에서 road contact 갱신을 그대로 실행했다. **고정 지도와 road tile ID는 SE(2) 대칭이 아니다.** 두 지점 모두 tile ID는 바뀌고 wheel friction은400으로 유지됐다. 따라서 결과는 이 국소 동일 마찰 조건의 **기계 fullstate 상대주기**이며, 전역 지도까지 포함한 root 전체의 주기나 무한히 안전한 원운동이 아니다.

이전555의 합성 pose·지도·분기 속도/곡률을 그대로 썼다. 도달 가능한 native 상태로 표시하지 않는다. 기존closure524의 rigid-body 근사 map을 검사했으며 native Box2D joint/contact solver 내부 상태 전체의 상대주기를 검증한 것도 아니다. 개인 원문은 parent가 완독해 전달한 필요한 내용과 승인 범위로 진행했으며, 이 실행기의 직접 원문 독해를 주장하거나 파일을 요청·전송하지 않았다.

## 계산 전 유한 기준

최대3개 상대주기 상태(원2개와 조건부 전환 목표1개), 각 solve `max_nfev60`·실제 residual 호출800회 이하, 4raw/호출, gtol 종료를 끄고 ftol/xtol1e−11로 등록했다. 원2개는 별도로 각각 float32 명령4raw를 다시 전파해 **모든 signature 잔차의 정규화 최대≤1**을 요구했다. 주요 허용치는 body 속도1e−4m/s·yaw1e−5rad/s·omega1e−4rad/s·gas/joint/heading1e−7이다. solver의 성공 플래그만으로 통과시키지 않았다.

안전 검증은 footprint≥.50m·preclip force≤1.059·모든 hull/wheel<100m/s·누적 wheel clipping≤10%·원 seed 경로 거리≤3m를 요구한다. 합성 분기의 목표 속도를 고정한 overspeed4.85 검사와 **원551 참조 대비 overspeed 별도 기록**을 구분했다. 이 기계 검사에 새 참가정책의 원551 준수나 실제 안전을 부여하지 않는다. solver의 부적합 forecast도 비용·상태·힘 위반을 보존하며 accepted validation으로 사용하지 않는다. 모든 새 적분에서 body domain을 검사한다.

두 원 fixture가 독립 한 주기 fullstate와 안전을 모두 통과해야 조건부 전환을 연다. 통과 상태에는 정확 상태8주기·사전 하나의 작은 속도/omega 섭동8주기를 별도로 검사한다. 섭동의 유한 시간 증폭은 진단값이며 물리 필요조건이나 점근 안정 증명이 아니다. 최소 전환은 **첫 fixture 다음 seed 지점의 기존 곡률**, 같은 속도의 상대주기를 한번 풀고4hold 제어 shooting·독립 float32 전파·후속3hold를 확인하도록 사전 등록했다. 다른 목표/기간 탐색은 없다.

전체 상한은 **model30,000틱·명시 휠 힘125,000회·geometry300회·CPU300초/wall360초**다. 전환은 residual 최대1,000호출·max_nfev60이며 전체 상한 안에 포함된다. deadline/body domain/비용 한도에서는 상태를 저장하고 중단한다. 실제cap0, 새seed/HOLDOUT/SEALED/다른환경/유료0으로 고정했다.

## 관측: 존재·안전·안정·전환의 분리

| 지표 |555 최대\|beta\| fixture|555 최대 힘 fixture|
|---|---:|---:|
| solver 최종 잔차 최대 |1.535e−14|1.421e−14|
| 독립 float32 한 주기 정규화 fullstate 잔차 최대 |.023105|.091871|
| body 속도 잔차 |1.361e−8m/s|3.985e−8m/s|
| yaw 잔차 |1.205e−8rad/s|4.792e−8rad/s|
| wheel omega 잔차 최대 |4.594e−8rad/s|7.540e−8rad/s|
| wheel offset 잔차 최대 |2.205e−8m/s|8.592e−8m/s|
| gas/joint/rate 잔차 |0|0|
| 독립 주기 preclip 힘 최고 |**1.115358**|**1.062715**|
| 주기 clipped wheel / samples |4/16=25%|8/16=50%|
| 안전 검증 첫 footprint |4.358366m|3.697269m|
| 최초 원551 참조 overspeed |−5.748130m/s|+5.557827m/s|
| 한 주기 기계 존재 |통과|통과|
| 전역 힘1.059 |실패|실패|

독립 기계 검사에서는 양쪽4raw를 모두 전파해 잔차와 힘/clip을 직접 얻었다. 이어 별도의 accepted safety validation은 둘 다 첫 힘 검사에서, 새 raw를 적분하기 전에 중단했다. 위 footprint는 최초 상태 값이며 전체 주기 footprint 최소라는 주장은 아니다. 첫 경로 거리는 둘 다0이었다. 두 번째는 원551 참조 대비도4.85를 넘으므로 원551 추종 정책의 합법적 대체로 표시할 수 없다.

힘 게이트 실패는555의 두 번째 clip-only 실패와 다르다. **이번에는 두 분기 모두1.059를 실제로 넘었으므로**, clipping0 같은 추가 조건으로만 멈춘 것이 아니다. 주기 동안 clipping25%/50%도 관측됐지만, 합성 fixture의 초기 누적 이력을 실제 주행 이력으로 바꾸지 않는다. 각 한 주기 비율과 장기간/전체 랩 누적 비율도 구분한다.

여러 주기 유지·섭동 증폭·다른 곡률로의 전환은 **미실행/미관측**이다. 한 주기 존재를 안정성·도달성·전환 가능성으로 바꾸지 않았다. 안전 게이트 실패를 주기 방정식의 해 부재로도 바꾸지 않는다. 고정 속도·동일한 초기 seed에서 찾은 한 분기의 결과이며 다른 안전한 상대주기의 부재를 증명하지 않는다.

## 비용·검증·다음 조건

총 residual88호출, source **360틱** = shooting352 + 독립 검증8이다. accepted safety validation은 힘 검사2회 후 적분0이었다. 명시 휠 힘 **1,448회**, 적분 내부 **1,440회**, body 검사360회·geometry2회, **CPU2.285942초/wall2.288437초**다. 최대 모든 model body 속도80.313801m/s로100 미만이었다. 부적합 solver forecast도 비용에 포함했고 최대 forecast 힘1.120345·힘 위반 raw352를 기록했다. 이는 실제 행동 또는 안전 통과 표본이 아니다.

읽기 전용 감사17항목이 소스/입력/STARTED hash·같은 합성 pose·전체 상태 schema·회전좌표계 잔차 재계산·float32·한 주기4raw·힘/clip 판정·road ID/마찰 경계·후속 미실행·모든 비용과 body domain·main을 확인했다. 감사의 새 source 힘/적분은0이다. 측정 CPU는 과학 실행 구간이며 편집·대화·Git 총비용 주장은 아니다.

**상대주기 표현 자체는 연속 평형보다 source 전이 일관성을 직접 확인할 수 있었다.** 다음에 열 수 있는 별도 가설은 period residual만 최소화한 뒤 안전을 거르는 방식 대신 **힘·clip 제약을 만족하는 상대주기 상태를 동시에 찾는 것**이다. 속도 여유와 전환 가능성을 독립 게이트로 두어야 한다. 이번 결과 뒤에 속도를 낮춰 재시험하거나 원 반복 수·목표를 바꿔 추가 실행하지 않았다.555의11.507초를 실제 랩 또는 이번 성능 보장으로 사용하지 않는다.

실제 행동/reset/world0, 연구 **22,758**·예비 **84,000/사용0**, main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`·공식Participants·사용자 변경·기존 실패·백업을 보존한다. 원시 지도·합성 fullstate·개별 분기/명령·solver JSONL·checkpoint는 저장소 밖 비공개다. 종료 **2026-10-20 19:01:55KST**, 자동 연장 없음이다.

[사전 계약](period556_contract.json) · [재현 코드](period556_model.py) · [기계/안전 분리 결과](period556_result.json) · [읽기 전용 감사](period556_audit.json)
