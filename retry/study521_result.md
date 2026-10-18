# 521 — 13hold 설명 후 경로 후보 선별: 큰 효과 근거가 없어 승격하지 않음

**새 물리 적분0, native action/reset/world0.** [사전 계약](study521_contract.json)에 따라 짧은 저장 분석과 하나의 경로 설계 절차를 수행했다. 520 gas 역산은 실제 검증으로 올리지 않았다. 경로 후보도 사전 scalar-clock 선별 기준에 미달해 cold/carry 물리 모델을 실행하지 않았다.

## gas1 미달은 무엇이며 큰 병목인가

[분석 코드](study521_analysis.py) · [집계](study521_analysis.json). 저장520의13hold/52raw 상태에서 source `wheel_response`를208회 계산해 저장된 힘 벡터와 오차0N으로 일치했다. 적분이나 반사실 주행은 하지 않았다. engine multiplier는 모두1, clipped wheel sample은0이었다.

|시작 후륜 gas 그룹|hold|직전 brake>0|평균 목표 가속|평균 실현4tick 가속|평균 종료속도 부족|
|---|---:|---:|---:|---:|---:|
|gas<0.4|10|3|34.7145m/s²|24.2288m/s²|0.8389m/s|
|gas>0.95|3|0|34.5410m/s²|33.5972m/s²|0.0755m/s|

첫 그룹의 평균 실제 후륜 gas는 첫tick0.1872→넷째tick0.4872였다. source는 후륜 gas를 tick당0.1 증가시키고, 현재 omega에 따라 `dt×40000×engine×gas/(1.6×(|omega|+5))`를 더한다. 그 뒤 `82×(omega_after×0.54−wheel_forward_velocity)`의 종방향 힘과 횡력을 합쳐 마찰로 clip하고, 힘의 반작용으로 omega를 줄인다. 시작 wheel slip·gas memory 및 엔진의 omega 의존성이 즉시 목표 가속과 다른 응답을 만든다. 낮은gas10hold 중 직전 brake는3개뿐이므로 모두 brake 직후라고 설명하지 않았다. 이미gas1인3hold의 작은 미달까지 ramp 탓으로 돌리지도 않았다.

13hold는1.04초로520 완주 추정20.22초의5.14%를 차지한다. 이는 **회수 가능 시간이나 개선의 인과적 상한이 아니다.** 단기 목표 불가능을 없애면 더 빠른 완주가 된다는 가정은 하지 않는다. 이번 설명에서20초대→11초대 격차를 줄일 큰 시간 이득의 근거는 나오지 않았고, 이미520 전체 모델의 효과는0.16초였다. 이에 미세 역산 분석을 더 늘리지 않고 경로 변경 한 가설로 옮겼다.

## 선택한 경로 가설과 선별 결과

[경로 구현](path521_control.py) · [고정 설계 절차](study521_design.py) · [설계 결과](study521_design.json) · [모델 gate 구현](study521_model.py) · [gate 결과](study521_model_result.json) · [순수 테스트](test_path521.py).

현재519 Gaussian 장애물 우회 경로에16계수 주기 cubic B-spline의 track-normal 변형을 더했다. 공개258의 저차원 spline 설계 아이디어를 현재 확인된 지도에 새로 적용했으며, 과거 pipeline 실행이나 유실 실험 재현은 하지 않았다. 가속은519 steady 방식, lateral100/top80/backward45/source-drive forward, gain2, 조향 규칙, 첫24gas0.32는 고정했다. 경로 변화에 따른 ds/곡률 및 **동일한 속도 생성 규칙**의 재계산만 허용했다. 별도 속도 상한이나 pedal 변환을 함께 최적화하지 않았다.

계수0에서 시작해6pass×16좌표×2방향, initial/final 포함 정확히194 objective 평가를 사용했다. 추가 start·homotopy·재시도는 없다. 전체 track-normal offset4.4m, segment-to-obstacle point clearance2.5m, 기하 곡률 조향 상한을 penalty/최종 feasibility로 검사했다. 동일519 scalar clock과 작은 계수 roughness가 목적함수다. 최종 기하 feasibility 및 clock 개선0.75초 이상이 물리 모델 선행 gate였고, 이후 cold/carry 모두 안전 및0.50초 이상 개선이 필요했다.

|지도 기반 결과|baseline519|spline 후보|
|---|---:|---:|
|scalar clock|19.848402s|19.720482s|
|경로 길이|995.445289m|993.265151m|
|최대 절대 곡률|0.103753/m|0.114531/m|

최종 기하 violation0, 최대 offset4.264816m, 최소 obstacle point clearance2.509161m였다. 그러나 clock 개선 **0.127921초<0.75초**로 선별 탈락했다. 따라서 새 모델 적분/cold/carry0이다. point clearance는 전체 차체 안전이 아니며 scalar clock은 실제 시간도 물리적 효과 상한도 아니다. 후보가 실제로0.128초 빨라졌다고 주장하지 않는다. 선택한 절차는 국소적이고 장애물 우회 homotopy·폭·16계수 제한을 가지므로 경로 설계 방법군 전체를 기각하지 않는다.

## 다음 실제 검증 후보에 대한 판단

**이번 단계에서 native 자격을 갖춘 새 후보는 없다.** 520 역산과521 spline 모두 실제 검증으로 보내지 않는다.

다음 모델 가설로는 경로를 그대로 두고 **상수 corner budget100을 현재 source 마찰 용량의70%로 바꾸는 한 변경**을 제안한다. 현재 저장 reset의 합계 wheel friction1600N/COM assembly mass7.30191997kg 기준153.384316m/s²다. top80·forward·backward·gas 변환·조향은 그대로 두고 곡률 속도 상한 생성의 lateral budget만 변경하는 구체적 후보다. source 용량 산식은 후보를 고르는 근거이며 yaw/steering/복합 힘/rolling 동역학을 포함한 실현 가능성 증명이 아니다. 70%도 보정 완료된 최적값이 아니다. 다음 단계에서 소스·입력·비용을 먼저 고정하고 같은 cold/carry 안전 및0.50초 효과 게이트를 통과할 때만 실제 짝 비교 후보로 올릴 수 있다. 여기서는 해당 후보의 새 계획/모델/native를 실행하지 않았다.

## 비용과 보존

저장 source force208회 CPU0.068873초/wall0.068874초, 설계194회 CPU0.517845초/wall0.370022초, gate/순수2tests CPU0.063621초/wall0.064017초. 합계 worker CPU0.650339초/wall0.502912초다. 준비·추가 단순 집계·publication allowance3CPU/3wall는 측정값과 별도다. 순수 테스트2개와 zero-deformation519 경로/profile 동일성 검사를 통과했다. 기존baseline1020ticks는 재적분하지 않았다.

연구24938, 예비84000/used0 유지. 지정 cloud·같은DEV identity만 사용했고 HOLDOUT/SEALED·새 seed·보호 평가·별도 유료 자원·옛 연구 실행0이다. 지도·상태·계수·원시 source 설명은 비공개로 보존했다. main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`, Participants, 사용자 변경과 백업을 보존한다. 승인 종료는 **2026-10-20 19:01:55 KST**다.
