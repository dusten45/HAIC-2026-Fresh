# 502 — 회전·슬립 응답을 반영한 제동 후보의 작은 물리 시험 통과

상수 가속도 제동 매핑 대신 **현재 휠 회전수에서 네20ms 응답을 계산해 목표 end-speed에 맞는 브레이크를 역산하는 후보 하나**를 구현했다. 새 합성 역학 벤치8쌍에서 사전 등록 기준을 통과했다. 과거501의35전이 raw는 복원하지 못했고, 이번 결과는 그 오차의 원인 분해가 아니다.

| 목표 속도 오차 | 기존 effective-mass 매핑 | 응답 기반 후보 |
|---|---:|---:|
| 전체8조건 RMSE |5.577712m/s|0.00001223m/s|
| 전체 최대 절대 오차 |8.978917m/s|0.00003204m/s|
| 초기 순수 구름4조건 RMSE |0.073583m/s|0.00001614m/s|
| 초기 휠 회전 초과4조건 RMSE |7.887733m/s|0.00000621m/s|

합성 직선·동일 마찰·고정 휠 방향 조건의 결과다. 응답 역산에 쓰는 휠 상태는 진단용 privileged 입력이다. 픽셀 제어기·원래501 root·실제 트랙·완주·독립DEV 일반화의 자격은 아니다. 큰 기존 매핑 오차는 이 의도적인 회전 초과 fixture에서 측정한 것이며, 과거501의 최대2.130529m/s와 같은 조건의 오차로 비교하지 않는다.

## 기전과 구현

[후보](brake502_response.py)는 원래 `Car.step` 순서대로 엔진 회전 증가→제동 회전 감소/lock→슬립 힘→2D 마찰 제한→휠 반작용을 계산한다. assembly mass에 합력을 적용하며4개의20ms 상태를 갱신한다. 현재 회전 에너지가 즉시 정상 구름으로 바뀐다는 가정을 쓰지 않는다. braking 후보의 gas0은 실제 source에서 즉시 감소한다.

역산은0.9 미만의 source 분기에서 수치 단조 검사를 한 뒤 float32 명령을 이분 탐색하고 인접 하위 float도 확인한다. `float32(0.9)<0.9`이므로 lock은 실제로0.9 이상인 첫 float32를 사용한다. 임의의 제동상한 축소나 안전 margin 추가는 없다. 이 수치 검사가 모든 상태에서의 연속 단조성 증명은 아니다. 도달 불가능·단조 검사 실패면 명시적으로 중단한다. 방향·회전/yaw·joint/접촉 변화를 네틱 동안 예측하지 못하는 한계가 남는다.

## 선행 검사와 실제 실행

[최종 실행 계약](brake502_final_contract.json)은 첫 world 전에 고정했다. source/candidate/test/runner SHA를 검증하고, 공개499·500·501 잔액이 모두 연구26027·예비84000/used0임을 대조했다. 비공개 원장이 복원됐다고 주장하지 않는다. 이 시험은 실제 wrapper action0이므로 새 원장 생성·차감도0이다.

순수3tests가 통과했다. 실제 소스에서 `Car.gas/brake/step`만 AST로 추출해 constructor/Box2D 없이 **576입력×4휠**의 힘과 omega를 후보와 대조했고, 각운동량 반작용과 상태에 따른 역산·float32 lock 경계를 검사했다. 준비 중 fixture의 road friction/grass 하한 혼동과 입력 수576을1152로 잘못 센 두 오류가 있었으며 둘 다 world0에서 수정했다. 후보 법칙은 바꾸지 않았다. [최초 계약](brake502_contract.json)·[중간 계약](brake502_execution_contract.json)과 private 실패 로그/수정 전 소스를 보존했다. 첫 world 후 코드·기준·조건 변경 및 물리 재시도0이다.

이어서 실제 Box2D `Car`로8조건×2arms, **16world/64rawticks**를 실행했다. track/seed/environment reset을 쓰지 않는 합성 DEV mechanics fixture이며, racing split을 추첨하거나 보호 정보를 읽지 않았다. 기존 비공개 splitter 집합의 복원이나 중복 배제·일반화 자격도 주장하지 않는다. solver는 원래 모델의 `.02,180,60`을 사용했다. 같은 초기 조건에서 목표 end-speed·원래 scalar 매핑과 응답 후보를 짝 비교했다.

실제 `Car.step` 반작용 직전의 force256행을 읽기 전용 trace로 포착하고 각 raw tick의 전후 휠 omega·hull/assembly COM 속도를 private에 남겼다. 같은 휠·같은 틱의 `I*delta_omega - I*delta_omega_brake + dt*F*R` 최대 절대 잔차는 **2.23e-14**였다. 서로 다른 휠/틱의 최대값을 더하지 않았다. 후보의 assembly-COM 예측 최대 오차는0.00003203m/s, hull 목표 속도 최대 오차는0.00003204m/s였다.

사전 gate는 후보 RMSE<=기존의0.5배, assembly/hull 최대 절대 오차<=0.15m/s였다. 이 **국소 gate만 PASS**이며 전체 방법이나 실제 참가 제어기로 승격하지 않는다. 과거501의 닫힌 exactEMPTY_SET 결과도 그대로다.

## 비용과 다음 조치

[실행 집계](brake502_result.json): 테스트 child와 준비 오류에 대한 보수2초 charge를 포함해 CPU2.557627s/wall2.558730s, 상한120/180초 이내다. 이는 worker 회계이며 대화 전체 경과시간이 아니다. native action/reset/새seed/HOLDOUT/SEALED0, 연구26027·예비84000/used0 유지.16world 모두 body/joint0으로 닫았고 live0이다. raw/실패 기록은 동일 cloud의 private 로컬에만 있으며 외부 전송·첨부0, 영속 보관을 보장하지 않는다. 공개 Git에는 raw state 배열이나 개인 원문을 넣지 않았다.

다음 연구선은 이 후보 하나로 제한한다. **조향과 비대칭 타이어 접촉에서 고정 방향·공유 COM 가정이 깨지는지** 작은 source 벤치로 반증하고, 통과한 경우에만 트랙 제어에 연결한다. 아직 해당 후속을 실행하거나 트랙 안전·finish·501 오차 원인을 검증하지 않았다. 과거 raw 부재는 원래35전이 사후분해의 한계이며 새 제어 연구 전체의 중단 사유로 삼지 않는다.
