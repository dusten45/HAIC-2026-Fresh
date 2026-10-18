# 506/507 — geometry 접촉 예측과 연속 두 hold의 국소 gate 통과

504 planar 응답에 **알려진 road polygon과 예측 wheel footprint**를 연결한 [후보](brake506_geometry.py)를 구현했다. 실제 source `VariablesContactDetector`가 Box2D road 센서 접촉으로 `wheel.tiles`를 갱신하며, 수동 접촉 제거는 없다. 이 시험은503~505의 숨은 외부 사건9조건과 **다른 검증 조건**이므로 그 수치와 같은조건 개선으로 비교하지 않는다.

## 완료된 확인 실행의 결과

| 지표 |접촉 고정504|geometry 후보|
|---|---:|---:|
|새6조건·1hold 목표속도 RMSE|0.262140m/s|0.003312m/s|
|새6조건 최대 절대 오차|0.624495m/s|0.008113m/s|
|그 force-time 접촉 불일치|20/96 wheel-ticks|0/96|
|선행 통과 후2조건×2hold RMSE|0.078526m/s|0.026711m/s|
|연속2hold 최대 절대 오차|0.144949m/s|0.052803m/s|
|그 force-time 접촉 불일치|14/64 wheel-ticks|0/64|

source timing·접촉 예측·속도·비용·실제 전환 coverage의 사전 gate를 모두 통과한 뒤에만 연속 두 hold를 실행했다. 경계 이탈·진입, 틈 이탈 후 재진입, 좌우 비대칭 접촉을 실제로 관측했다. 후보의1hold 최대 불필요 감속은0.0000527m/s였으며 interior 대조는 동일 명령/거리였다. 전체6조건에서504 대비 최대 투영 진행거리 지표 손실0.006980m, 두 hold 누적 최대0.011783m를 기록했다. 진입 조건에서는504의 과도한 감속을 줄여0.031158m 더 진행했다. 이 값들은 initial COM 방향에 투영한 post 속도 적분이며 lap time이 아니다.

## 접촉 timing과 남은 모델 오차

source는 `Car.step` 힘 계산 후 `World.Step`을 호출한다. 단일 wheel 센서 probe는 post-step 접촉이 **pre-step 위치의 geometry**와 일치함을 확인했다: prepose 불일치0, postpose 불일치2/4. 전체 차량 시험에서도 실제 pre-world pose의 footprint oracle과 source post-step 센서 membership 차이는0이었다. 따라서 예측기는 현재 force에 현재 관측 접촉을 쓰고, 현재 pre-world footprint의 접촉을 **다음 force**에 반영한다. 예측 post 위치로 즉시 마찰을 바꾸지 않는다.

footprint는 source wheel의0.56×1.08m 회전 사각형이며 convex polygon 사이 최소 거리와 양쪽 Box2D polygon skin 합으로 센서 overlap을 계산한다. 재진입과 road tile identity까지 비교했다. 차량 접촉 예측은160/160wheel-ticks가 일치했지만 비대칭 조향의 두 번째 hold 속도 오차는0.052803m/s로 남았다. 이 경우 접촉 예측 자체는 맞았으므로 잔여 오차를 timing 오류나 접촉 정답 누락으로 돌리지 않는다.504의 rigid joint/steering/yaw 근사와 더 긴 제어의 검증은 여전히 필요하다.

접촉 전환으로 brake response의 전역 단조성이 깨질 수 있어 고정33개 coarse 지점에서 첫 feasible bracket을 찾고 float32 경계를 확인한다. 결과 명령의 feasible prediction은 확인하되 전역 최소 제동·전역 최적성은 주장하지 않는다. geometry 후보는 현재 full body/wheel 상태·정확한 전체 도로 polygon/material이라는 **진단 privilege**를 사용하며, 미래 실제 접촉이나 사건 일정은 읽지 않는다.

## 기술 중단·확인 실행·비용

최초 [506 계약](brake506_contract.json)의 연속 hold 비용을 잘못 합산했다. 첫6조건 통과 분기를 거쳐 후속에 진입했지만 등록68positive ticks에서 guard가 멈췄다. 실제 필요한 후속은 `2fixtures×2arms×2holds×4ticks=32ticks`였고 전체는84였다. **원래 상한은 넘지 않았다.** 일괄 저장 전 종료되어 그 차량 상세 수치는 보존되지 않았다. [실패 기록](brake506_failure.json)의 최초 단계 통과와16world 종료는 고정 실행 경로/예외에서 추론한 사실로 표시하며, 그 시도의 상세 성능 수치를 재구성했다고 하지 않는다.

후보·6fixture·판정 기준을 바꾸지 않고 [507 확인 계약](brake507_contract.json)을 실행 전에 별도로 고정했다. 원래506 소스/계약/실패를 보존하고, 정확한84tick 예약 및 world별 즉시 저장·종료 receipt만 추가했다. **물리 확인 반복1회**이며 재실행0이라고 보고하지 않는다. 이 문서의 성능 수치는 완료된507 확인 실행에서만 가져왔다. [원시 fixture/실행 코드](brake507_confirm.py) · [집계](brake507_result.json) · [요약](brake507_summary.json).

순수4tests는 polygon 교차/거리·corner 거리·skin·중심점이 아닌 footprint·sensor phase·비단조 응답의 feasible float 경계를 검사했다. 완료 확인은17world/84positive ticks/17zero-dt contact primes, 모두 body/joint0으로 종료·live0. CPU0.575145s/wall0.575679s, 등록60/90s·private16MiB 이내다. 최초 실패68ticks와 합하면152positive ticks이며 최초16world(경로 추론)와 확인17world를 구분한다. 최초 시도 외부 shell wall0.470626s에 보수CPU/wall5s를 charge했다. 환경은box2d-py2.3.5/numpy1.26.0/gymnasium0.29.1이다.

native wrapper action/reset/seed·트랙/HOLDOUT/SEALED 접근0, 연구26027·예비84000/used0 유지. private raw·완료 world·closure 기록은 지정 cloud 로컬에만 보존하며 개인자료/과거 비공개seed/state·실측 raw를 공개하지 않는다. 사용자 대신 전송·첨부하지 않았다.

결론은 **정확한 geometry가 주어진 이 작은 물리 조건에서 접촉 예측과 두 hold 제어가 통과**했다는 것이다. 다음 검증은 이 관측 조건을 유지한 더 긴 곡선 corridor에서 누적 모델 오차와 경계 여유를 확인하는 범위다. 현재 결과를 pixel 정책·실제 트랙 안전/완주·whole-lap 개선이나 독립 일반화로 승격하지 않는다.
