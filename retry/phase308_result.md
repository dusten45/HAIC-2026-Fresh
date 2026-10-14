# 308 — 실제 진행 속도로 spatial feedforward를 연결한 GT 진단

**후보 1/5, 저장 기준 3/5 완주로 사전 게이트를 탈락했다.** O0는 19.70→18.98초로 0.72초 빨라졌지만 N0·N3 완주를 잃었고 O2·N1은 구제하지 못했다. 추가 완주 0·손실 2이며 공통 완주 O0의 시간 개선을 전체 성능 개선으로 해석하지 않는다. 이 한 가설은 종료한다. 다른 factor·gain·pace·clamp·teacher·head를 시험하지 않았다.

258의 cached feasible reference와 constant1.5 profile, 기존265/269 follower를 고정했다. q>0이면 원래 `a_ff=(q_next²−q_here²)/(2ds)`에 현재 GT velocity의 선택 선분 unit tangent 투영 `v_parallel/q`를 곱했고, q==0이면 원래 feedforward를 유지했다. Norm-speed feedback1.5·양/음 acceleration clamp·pedal inverse·steering/cursor/memory·path/profile·lap-wrap branch는 그대로다. 다섯 TRAIN O0/N0/O2/N1/N3와 순서를 결과 전에 등록하고, 완주 수 증가 또는 동률에서 엄격한 공통 완주 평균 시간 개선을 기준으로 고정했다. N2의 cached solver-blocked 상태는 그대로 미실행이며 DNF로 세지 않았다. 새 solve·fit·source forecast는 없다.

| TRAIN | 저장 constant1.5 | 308 후보 | native | damage |
|---|---|---|---:|---:|
| O0 | 19.70초 완주 | **18.98초 완주** | 238 | 0 |
| N0 | 20.20초 완주 | off_track DNF | 248 | 0 |
| O2 | off_track DNF | off_track DNF | 323 | 0.4 |
| N1 | off_track DNF | off_track DNF | 180 | 0 |
| N3 | 17.66초 완주 | off_track DNF | 226 | 0.2 |

q·v_parallel·원래/적용 feedforward·feedback·clamped acceleration·실제 pedal·GT velocity/tangent·방문/counter를 모두 기록했다. 1,215개 행동의 지정 식과 pedal inverse를 확인했고, 같은 현재 상태의 원식 대비 **364개 pedal 변경**(34·24·224·44·38)이 있었다. q==0은 O2/N1/N3에서 각1회이며 원식을 유지했다. 원래 cursor/steering·profile/lap-wrap source block은 byte 동일하며 경로/profile hash도 유지했다. 이 동일 상태의 산술 비교는 저장 baseline 전체 궤적과의 상태 일치 대조가 아니다.

| TRAIN | 목표 아래 제동 행동: 기준→후보 | 속도≤1e−6 관측: 기준→후보 | 최장 새 타일 없음: 기준→후보 | 후보 negative v_parallel |
|---|---:|---:|---:|---:|
| O0 | 52→46 | 1→1 | 3→6 | 0 |
| N0 | 55→28 | 1→1 | 3→101 | 40 |
| O2 | 140→12 | 97→1 | 101→101 | 106 |
| N1 | 139→17 | 98→1 | 101→101 | 42 |
| N3 | 49→23 | 1→1 | 3→101 | 100 |

O2/N1의 오래 정지한 관측은 줄었지만 완주나 새 타일 진행은 회복되지 않았다. 마지막 pre-action 속도는 후보 O2/N1에서12.44/9.66m/s였으며 기준은 거의0이었다. 이 값은 terminal 뒤 GT 속도가 아니다. 후보 N0/N3도 새 타일 방문 없이101행동을 끝냈다. Negative v_parallel은 현재 선택된 참조 선분에 대한 부호이며 전역 트랙 역주행 판정으로 바꾸지 않는다. 기준 trace에는 v_parallel이 없어 미상으로 표시했다. O2/N1의 단순 제동 정체를 없애면 다섯 도로의 완주 우선 결과가 개선된다는 가설은 지지되지 않았다.

Tracking error 최대는 N0/O2/N1/N3 후보에서53.08/27.30/40.71/28.65m였다. Longitudinal 개입으로 실제 trajectory와 이후 steering/참조 선택 상태도 달라졌다. 이는 변경된 폐루프의 기술 통계이며 phase factor·controller coupling·reference alignment 중 하나만의 실패 원인으로 단정하지 않는다. O0의 양성 시간 변화와 다른 도로 실패를 함께 보존하며 진행 위상 제어 방법군 전체를 기각하지 않는다. 기존1.5 speed profile은 물리적 feasible profile로 인증된 것이 아니고, GT 정보가 있어도 이 개입의 성공을 보장하지 않았다.

첫 native 이전에265 legacy manifest의 geometry hash 키가 없는 연결 오류1건을 복구했다. 동일 seed/track/초기 이미지의 기존 TRAIN 등록 hash를 연결했으며 제어식·경로·비교 기준을 바꾸지 않았다. 원래 계획·source·오류·시작 기록을 보존했고 당시 native 소비·후보 결과는0이었다. 이후 다섯 후보는 각 한 번 공식 종료까지 실행했다. 후보 실행 기술 오류·검열은0, 네 실패는 실제 off_track이다.

비용은 **1,215/4,000 native**, 실제 raw step **4,858**, 다섯 후보 reset **255 tick**이다. Candidate phase wall40.523초·runner CPU40.187초이며, 별도 실패한 pre-native 초기화 wall0.586초를 기록했다. 그 reset51 tick은 source에서 도출한 값으로 후보의 측정값과 구분하고 해당 초기화 CPU는 미상이다. 알려진 reset 합계는306이다. 별도 source forecast physics·새 geometry solve·fit·유료 자원은0이다.

종료 예산은 **누적1,148,238 + 연구 잔여7,762 + 최종 예비84,000 = B1,240,000**이다. 예비·DEV·HOLDOUT·SEALED를 사용하지 않았다. 296·240 rollback·main·Participants·사용자 변경·기존 결과·백업을 보존했다. 공개는 일반 코드와 집계만 포함하고 raw GT trace·경로·profile·등록 identity는 비공개다. GT 진단이며 legal 제출 정책·승격 결과가 아니고, 자동 증류나 후속 실험은 없다.
