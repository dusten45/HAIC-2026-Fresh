# 531 — 1.25m 기하 feasibility는 복구, 성능 선별 실패로 물리 실험 중단

**531은 목표여유를 낮추지 않고 표본 기하상 feasible 초기 경로를 만들었다. 이것은 주행 성능 개선이 아니다.** 이후 고정한 매끄러운 성능 surrogate는 감소했지만 기존528의 scalar profile 시간은17.250→18.581초로 악화됐다. 사전 gate에 따라 위험구간·cold/carry·native를 실행하지 않았다. 실제 검증 기록18.40초, 연구24155·예비84000/used0 유지.

[사전 계약](feasible531_contract.json) · [530 기하 차이 분석](feasible531_analysis.json) · [정확 표본 기하](feasible531_geometry.py) · [두 단계 설계](feasible531_design.py) · [설계 결과](feasible531_design.json) · [잔차 감사](feasible531_audit.json) · [저장 endpoint profile 감사](feasible531_profile_audit.json).

## 530의 차이와 531의 고정 제약

530의 도로-normal support/최소 도로폭 근사는 저장 도로 경계에 대한 외곽 직사각형의 실제 거리와 같지 않았다. node의 central tangent와 실제 polygon segment tangent도 달랐다. 저장530 결과를25sample/segment로 읽기 감사했을 때 기존 Gaussian의 장애물 여유는 근사1.018903m/촘촘한 외곽0.946887m,530 종료 후보의 도로 여유는 근사1.204815m/외곽0.500722m였다. 이는530의 solver 실패만으로 경로군을 반증할 수 없는 이유다.

531은 같은 외곽 직사각형(halfwidth1.58m,앞2.681/뒤2.320m)을 사용하되, 각 실제 segment tangent에서 **저장 경계 segment와 box 사이 거리·경계 교차·저장 road union의 box vertex coverage·원형 장애물과 box의 signed distance**를 제약으로 직접 계산했다. 밖으로 나온 corner는 음의 경계 거리를 가져 복구 방향을 제공한다. nominal 전체 hull/wheel을 덮는 설계 외곽이며 동적 joint/추종 안전의 증명이 아니다.

구간당33개 일정 fraction 자세를 고정했다. 실제 최대 간격은0.218750m였다.±4m 횡변위/저장 최대 구간 길이/외곽 반경/목표여유에서 도출한 지역 기하 검색 필요 반경 상한11.863939m보다 큰12m를 고정했다. 최종에는 모든 저장 경계를 사용하는 기존530의 독립적인0.5m 이하 oracle도 별도 검사했다. 이는 표본 검사이고 연속시간/실제 동역학 안전 증명은 아니다.

**1.25m nominal 여유를 유지**하고 계산 제약은1.252m로 고정해0.002m 수치 buffer를 추가했다. segment≥2m,곡률≤tan(.4)/3.24,283지점 중273개 횡변위±4m·seam 양쪽20m의10지점 고정은 유지했다. 초기화는530 실패 후보가 아닌 원래528 Gaussian 한 개다. side/homotopy/multistart/방법/가중치 sweep는 없다.

## 사전 고정한 feasibility → 성능 절차

1. **feasibility:** SLSQP epigraph `min slack`, `각 정규화 제약+slack≥0`,slack≥0만 사용했다. 시작 slack은 최대 위반+0.001m다. 이 단계에서는 scalar time·성능 surrogate를 목적에 넣지 않았다. maxiter80/ftol1e-8,geometry local finite difference1e-5를 고정했다.
2. **feasibility gate:** 최대 정규화 위반≤1e-6,road union 밖0,33sample 및 독립530 oracle의 외곽 여유 모두≥1.25m,간격≤0.5m를 요구했다. optimizer 메시지 자체를 증거로 쓰지 않았다.
3. **성능:** 통과한 유일한 복구 endpoint에서 SLSQP 한 번만 실행했다. 목적은 `J=sum(ds*(h_i+h_next)/2)`, `h=sqrt(sqrt(k²+1e-8)/lateral+1/80²)`의 고정된 매끄러운 surrogate다. 곡률 smoothing1e-4/m·lateral153.384316은 사전 고정했다. 실제 forward/backward min/max profile을 최적화 중 미분하지 않았다. maxiter120/ftol1e-7/eps1e-5이며 추가 가중치가 없다.
4. **성능 gate:** solver success·동일1.25m feasibility·530 촘촘한 footprint gate≥0.75m·기존528 실제 scalar 생성식 개선≥0.50초를 모두 요구했다. endpoint 하나만 평가하고 다른 iterate를 골라 승격하지 않았다. surrogate/scalar는 실제 gain이나 실현 가능한 하한이 아니다.

두 단계 각각 CPU180초/wall240초,합계360/480초,geometry sample evaluation3000만·Jacobian205·constraint40000·성능 objective40000회로 사전 제한했다. local Jacobian 의존 범위는 미리 고정한3개 station에서 범위 밖 변화0으로 확인했다. Numpy1.26.0/SciPy1.14.1/BLAS1thread,기존 지정 cloud만 사용했다.

## 검증된 결과

feasibility는11회 반복에 성공했고 slack0,최대 정규화 위반3.09e-11이었다.33sample 외곽 최소1.25199999997m,독립530 oracle도 같은1.252m,road union 밖0으로 통과했다. 즉530에서 빠진 feasible 초기화 단계를 실제로 확보했지만 주행은 하지 않았다.

성능 단계는120회 상한에 도달해 `Iteration limit reached`로 끝났다. 종료 후보도 최대 정규화 위반6.19e-10,독립 oracle 최소1.25199999938m로 nominal1.25m를 만족했다. solver 수렴 조건과scalar 개선 조건은 모두 실패했으므로 추가 반복·재시작·새 목적을 시도하지 않았다.

|이미 저장된 endpoint 집계|기존528|feasibility 복구 후|성능 단계 종료|
|---|---:|---:|---:|
|경로 길이|995.445289m|995.636415m|993.971753m|
|고정 smooth surrogate|15.183206|15.363236|14.746595|
|기존528 scalar clock|17.250273s|17.372708s|18.580911s|
|최대 절대 곡률|0.103753/m|0.103753/m|0.127597/m|
|곡률 총변동|1.733868/m|2.408995/m|4.370935/m|
|periodic profile 최소 속도|38.449405m/s|38.449405m/s|34.671295m/s|

표의 복구 endpoint 성능값은 설계 종료 후 읽기 전용으로 설명한 값이며, 다른 후보로 선택하지 않았다. 끝 경로는 기존보다1.473536m 짧고 surrogate도 낮았지만, 곡률 peak·변동이 커지고 종방향 제약을 적용한 scalar profile은1.330638초 나빠졌다. **이번 smooth surrogate 개선이 기존 forward/backward profile 개선과 일치하지 않았다**는 것은 직접 확인했다. 곡률 지표만으로 모든 시간 악화의 인과를 증명하거나 새 가중치의 효과를 예측하지는 않는다.

## 중단·관측 경계와 남은 장애물

geometry/scalar 선별 실패로 사전선택 위험구간(530과 같은 저장528 장애물/최대곡률 진입 두 root,각24hold/96raw 짝),cold/carry,조건부 native 모두0이다. [조건부 모델 코드](feasible531_model.py)는 준비만 했으며 실행/동역학 검증하지 않았다. 기존 source-response governor/조향·top80/back80/source-drive forward/corner153·backup100/back45 법칙은 고정했고, 경로에 따른 동일 법칙의 profile 재생성만 허용했다. 공유528 함수 객체와 profile 재생성 수치 동일성을 감사했다.

후속 gate는 그대로다: 위험구간 모두 안전→cold 전체 force/추종/기하/source-style finish 및525실제18.40 대비모델≥0.50초·528모델대비≥0.10초/HIGH≥50%→동일actual518 before47 carry의 전 안전/finish·525carry대비≥0.50초·528carry 비악화→동일DEV fresh525 policy vs531 package 실제 official finish 짝만 허용했다. 실제528이 검증됐다고 주장하지 않는다.

불확실성0.19/예측1.06/물리1.25,참조초과5(528 내부4.85),누적tracking clipping10%,기존 geometry/launch/sourceTimeLimit/one-hold prediction/source-force oracle/관측·손상 경계를 유지했다. native1000actions/2resets/4102raw/2world 상한,actual wrapper attempt 사전 차감 및 finally world body/joint0 정리를 계약했다. 이번에는 world 생성0이다. DEV는 기존 저장 입력만 쓰고 HOLDOUT/SEALED·새 seed·보호 평가 호출0이다.

남은 장애물은 infeasibility가 아니라 **종방향 profile을 생략한 고정 smooth surrogate의 성능 불일치와 수치 수렴 미완료**다. feasible 표본 경로·원530 실패·531 두 endpoint와 이력을 모두 보존했다. 이 결과를 보고 방법/가중치/초기화/반복 상한을 바꾼 새 실험은 하지 않았으며 전체 경로 설계군이 무효라는 결론을 내리지 않는다.

## 비용·재현·보존

새 물리 적분/force/native action/reset/world0이다. geometry 설계는6,413,484 sample evaluation·131Jacobian·431constraint·33,180성능 objective 회였다. 저장 분석 CPU0.424193초,local 의존 확인0.417372초,두 단계 설계129.404621초,잔차 감사0.559280초,endpoint profile 감사0.008008초로 worker 합계 **CPU130.813474초/wall130.863289초**다. 준비·소스 확인·publication allowance5CPU/5wall는 실측 worker와 별도이며 추가 실험은 없다. 연구24155·예비84000/used0 유지.

사전 계약 SHA·소스/input pins·단일 `DESIGN_STARTED`·원 endpoint/잔차/비공개 위치를 보존했다. 공개물은 코드/계약/집계이며 지도·좌표·횡변위·root·raw 궤적·seed/RNG/case는 비공개다. main 지정SHA·Participants·사용자 변경·기존 백업은 보존한다. 승인 종료2026-10-20 19:01:55KST이며 자동 연장하지 않는다.
