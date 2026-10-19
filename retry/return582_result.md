# 582 — 원 feedback의 내부 forecast 때문에 source 전 중단

**결과: `BLOCKED_PREFLIGHT_NOT_EXECUTED`.** 변경 없는551/537 feedback에 계획에서 빠진 내부 rollout이 있다. 사용자가 명시한 “예상 밖 내부 rollout은 실행 전에 기술적 장애로 보고” 조건에 따라 **132raw prefix부터 새로 실행하지 않았다.** 이는 복귀 정책의 과학적 실패나 실행 도중 budget-censoring이 아니다. s200/s300의582 crossing·속도·yaw·wheel·clip·margin은 미관측이다.

## 확인한 원 코드와 비용

[원 certifier](structure537_control.py#L27)는 `HORIZON=12`와 hold당4raw로 **48틱**을 예측한다. 성공 보고는 이48틱 전체가 안전할 때만 나온다. [choose의 HIGH 성공 경로](structure537_control.py#L70)도 fresh `FINAL`48틱을 다시 실행한다. 다른 경로도 성공 sample48틱과 fresh FINAL48틱이 모두 필요하다. 따라서 accepted feedback action 하나에는 **최소96개의 forecast 완료틱**이 필요하다. 실제 행동4raw는 별도다.

candidate cache 최대31개와 fresh FINAL1개로, 결정당 인증은 최대32회다. 원 [backup](preview527_control.py#L13)은 예측된 변경 상태에서 high/low nominal을 다시 계산한다. 단순한 값 조회나 저장 명령 연결이 아니며, 이 예측과 FINAL을 생략하면 승인된 원 feedback이 달라진다.

| 성공 행동 한 번의 비용 | 최소 | 코드 상한 |
|---|---:|---:|
| 내부 forecast 틱/attempt |96|1,536|
| forecast 외부 wheel force 호출 |384|6,144|
| forecast 내부 적분 wheel 호출 |384|6,144|
| forecast geometry 검사 |98|1,568|
| 실제 source 행동 raw 추가 |4|4|

geometry는 인증마다 현재 root1회와 적분 후48회이므로 full 인증당49회다. force 실패의 pre-integration attempt와 내부 완료틱은 계속 별도 계수해야 한다. 이 계산은 코드·저장 입력을 읽은 정적 산술이며 새 force/적분 호출이 아니다.

## 600틱과 충돌하는 이유

주어진 `132+160+292=584`에는 feedback 내부 forecast가 없다. continuation을 안전한 full hold **D개** 진행하고 그 tape를 초기 상태부터 replay한다면 가장 싼 성공 경로도 다음과 같다.

- source 완료틱: **`264+104D`**
- geometry: **`264+106D`**
- 외부·내부 force 각각: **`1056+416D`**

따라서600틱으로는 성공 full hold3개까지이며,4개면680틱이다. 최대40hold를 모두 쓰는 경로는 최선에도4,424틱/geometry4,504회/외부·내부 force 각각17,696회다. 코드상 모든 인증 비용을 포함한40hold 상한은62,024attempt/geometry63,304회/외부·내부 force 각각248,096회다. 이것은 새로 허용하거나 실행한 예산이 아니다.

세 hold만으로 target에 닿을 가능성도 저장 geometry와 원 안전 한도로 배제된다. 원 reference profile 최대90m/s와 허용 초과4.85m/s에 따라 안전한 다음 COM 속도는≤94.85m/s다. source center의 raw당 이동은 `DT=.02` 곱이므로 고정 plane 방향 최대1.897m다. 저장581 endpoint에서의 signed plane 거리를 사용하면 다음은 **필요조건 하한**이다.

| 목적면 | 전방 signed 거리 부족 | 필요한 actual raw 최소 | crossing hold 완료 최소 | prefix·forecast·실행·replay 최소틱 |
|---|---:|---:|---:|---:|
|s200|63.354m|34|9holds|1,200|
|s300|163.812m|87|22holds|**2,552**|

이는 속도를 즉시 최대로 쓰고 plane 방향으로 직진한다고 보는 느슨한 하한이다. 가속·곡선·progress±10m/corridor 조건은 비용을 더 늘릴 수 있다. **s300의 하한만으로도** 외부 force10,208회·내부10,208회·geometry2,596회가 필요해 각각2,400/2,400/600 상한을 넘는다.

132prefix와 최대292replay를 먼저 예약하면600 중176틱이 남는다. 일부 짧은 호출이 들어갈 수 있다는 사실은 s300 복귀·독립 재현까지의 질문을 수행할 수 있다는 뜻이 아니다. 원 chooser의 단일 호출 상한도 실제 행동 포함1,540틱이어서 그 남은 공간에 통째로 예약할 수 없다.

## 등록·검증·실제 사용량

[582 계약](return582_contract.json)에 요청한600틱·force2,400각/합계4,800·geometry600·CPU50/wall70 및 단계 한도를 그대로 적고 상태를 **미실행 preflight 장애**로 등록했다. [읽기 전용 코드](return582_preflight.py)는 AST로12×4 horizon과 두 fresh FINAL 경로를 확인했다. 원537/backup/source kernel과 입력 hash, 이전581 source dependency closure의709개 파일이 그대로임을 확인했다. 현재 preflight 자체의 실제 import manifest도 고정했다. 실행하지 않은582 scientific runner의 실제 closure를 검증했다고 주장하지 않는다.

[집계 결과](return582_result.json)에 호출당 비용·D별 식·고정 plane 하한·원 입력 hash와 source 위치를 남겼다. 독립 읽기 검토도 최소96forecast틱 및 계산식에 동의했다. 준비의 CPU/wall은 마감·검증 보수 charge 포함 **0.578/0.581초**로10/15초 이내다. 새로운 과학 실행 비용은 없다.

| 항목 | 582 실제 |
|---|---:|
| 새132raw prefix 재구성 |0|
| feedback 선택/forecast 틱 |0 /0|
| continuation/replay |0 /0|
| 외부·내부 force 호출 |0 /0|
| native·FD·optimizer |모두0|
| HOLDOUT·SEALED |모두0|

기존581의8raw viability·정확 replay는 그대로 유효하다. 복귀 가능성·시간 이득은 이번에 검사하지 못했다. 내부 forecast를 예산에서 제외하거나 FINAL/horizon을 줄이거나 저장 action·factual pose로 대체하지 않았다. **원 feedback의 forecast를 포함하는 새 명시적 예산 계약이 선행되어야** 이 복귀 검사를 실행할 수 있다. 현재 계약이나 정책은 바꾸지 않았고 자동 후속도 없다.

source13.20/actual13.66초 incumbent, 연구잔여22,758, reserve84,000/사용0, main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`, Participants·사용자 변경·백업·이전 결과를 보존했다. 지정 클라우드만 사용했으며 별도 유료 자원0이다. 종료2026-10-20 10:01:55UTC를 연장하지 않았다. 공개물은 기술 코드·집계·계약이고 원문·원시 상태·명령·journal은 비공개로 남는다.
