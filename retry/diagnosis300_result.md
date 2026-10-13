# 300 — 저장 trace와 최소 신호 보강으로 좁힌 실패 진단

**현재 기록은 단순한 gain 부족이나 일괄적인 도로 인식 오류보다, 장애물 접근 시 목표·최종 페달의 불일치와 충돌 후 복구/진행 방향 문제를 지지한다.** 이는 관측된 메커니즘이며 고유 원인의 인과 증명은 아니다. 다음 한 개입으로 near-hazard의 nominal-zero gas 일관성 guard를 제안한다. 이번에는 제어를 바꾸거나 그 개입을 실행하지 않았다.

기존 240·296·298 steering 원복·299 중점의 다섯 TRAIN 도로 trace 20개를 먼저 읽었다. 행동·target·곡률·HUD 속도·memory·충돌은 있으나 GT 위치/진행·전체 경로·실제 wheel/접지 상태가 없어 시간만으로 상태를 맞추지 않았다. 사전 등록 후 **T2950의 240/296, T2954의 296/298** 네 주행만 새 신호를 수집했다. archive/정책 코드는 그대로이고, 관측 adapter와 평가기만 읽기 전용 신호를 기록했다. 모든 1,073개 행동·feature·memory·충돌·종료가 기존 trace와 정확히 일치했다.

| 저장된 TRAIN 결과 | 240 | 296 | 298 steering 원복 | 299 중점 |
|---|---|---|---|---|
| T2950 | 26.36초 완주 / 접촉 179 | off_track / 접촉 184 | 26.84초 완주 / 접촉 없음 | 25.40초 완주 / 접촉 없음 |
| T2954 | off_track / 접촉 162 | 27.44초 완주 / 접촉 없음 | crash / 접촉 80 | off_track / 접촉 없음 |
| T2955 | 23.50초 완주 / 접촉 189 | 23.86초 완주 / 접촉 없음 | crash / 접촉 146 | 24.10초 완주 / 접촉 없음 |
| T29510 | 18.98초 완주 / 접촉 없음 | 18.94초 완주 / 접촉 179 | 19.06초 완주 / 접촉 없음 | off_track / 접촉 202 |
| T29511 | 19.88초 완주 / 접촉 없음 | 21.30초 완주 / 접촉 없음 | 20.90초 완주 / 접촉 없음 | crash / 접촉 176 |

접촉 숫자는 첫 native 충돌 구간이다. `off_track`은 공식 종료 label이며 휠이 잔디에 닿은 순간과 동일하지 않다. 기존 자료만 있는 299·T2955/T29510/T29511의 실제 첫 궤적 이탈이나 actuator 상태를 복원했다고 주장하지 않는다. 특히 T2954/299는 접촉 기록 없이 off_track, 298은 반복 접촉 crash이므로 같은 원인으로 묶지 않는다.

**공간 정렬:** 실제 centerline의 인접 segment 연결을 유지한 signed arc를 계산했다. 역행하면 좌표가 감소한다. 5m bin의 첫 순방향 통과를 bracket으로 잡고 실제 native snapshot 중 arc 오차≤2.5m인 것만 비교했다. 나중에 같은 위치로 되돌아온 상태를 대신 넣지 않았고, 같은 진행 위치도 동일 상태라는 뜻은 아니다. 1m를 넘는 최초 coarse lateral 차이는 T2950 약255m, T2954 약105m에서 관측됐다. 이는 이산 진단 기준이며 연속시간의 최초 숫자 차이나 실패 원인을 확정하는 값이 아니다.

**T2950 — 충돌과 복구/역진행을 분리했다.** 240은 native179, arc688.21m에서 충돌한 뒤 완주했다. 296은 native184, arc688.74m에서 충돌했고 이후 off_track으로 끝났다. 최초 raw wheel road-contact loss는 각각 native182/tick1(arc690.63m), native185/tick2(arc691.68m)로 충돌 이후였다. 두 정책 모두 첫 충돌 행동의 사전 관측에서 target이 이미 없었다. target loss를 충돌의 사후 결과로만 단정하지 않았다.

296은 충돌 후 steering 반전에서 post-native joint lag가 약0.362rad까지 커졌다. 실제 motor rate 제한이 걸리는 복구 지연은 관측됐지만 최초 충돌의 유일한 원인은 아니다. 마지막 새 타일은214, 종료는315로 101개 행동 동안 새 타일이 없었다. 진단 arc는 최대721.29→336.49m로 감소했고 종료 속도는39.19m/s였다. 정지 실패가 아니라 이미 방문한 도로를 움직이며 역진행하는 양상이다. reward/off-track counter 자체는 따로 기록하지 않았으며 visited·pose와 원본 종료 로직에 일치하는 설명이다.

**T2954 — 298의 최초 충돌은 접지 상태에서 발생했다.** 원복 정책은 native80, arc285.50m에서 처음 충돌하고80~84의 다섯 충돌로 crash가 됐다. 모든 wheel은 첫 충돌 전에 road contact가 있었고 종료까지 최초 road-contact loss는 관측되지 않았다. 296은 충돌 없이 완주했고 road-contact loss는 나중인 native84/tick1(arc293.11m)에 있었다. 잔디 이탈이나 road contact 감소 자체가 이 crash의 필요조건은 아니다.

298의 충돌 전20m 구간은 target 6/6과 경로 점이 실제 road polygon 위에 있었다. 가장 가까운 관측 장애물의 GT 위치 오차는 최대0.280m였다. unsmoothed steering clip은0회, 충돌 전 post-native joint 오차는 최대4.12×10⁻⁶rad로 wheel은 명령을 따라갔다. 따라서 이 구간의 주원인을 steering command 한계나 지속적인 actuator 추종 실패로 단정할 근거는 없다. 도로 위의 경로가 충돌 가능한 차량 궤적이라는 보증은 아니며, 일부 tracker ghost와 경로 선택의 인과 역할도 미확인이다.

진행 약275m에서 296은 curvature0.019·steering0.109인 반면 298은0.104·0.320이었다. 약285.5m에서는 296은 target 없음/steering−0.146, 298은 target 있음/steering+0.346으로 참조 전환과 실제 회피 궤적이 달랐다. 이때 상태·이력은 서로 다르므로 같은 상태의 순수 gain 효과로 해석하지 않는다.

**검증된 페달 신호:** T2954/298의 충돌 전 유효 target 구간에서 GT 속도45.56~50.69m/s, HUD feedback46.25~51.25m/s, 목표8.21~15.93m/s였다. nominal gas는6행 모두0인데 최종 gas는0.548~0.616이었다. T2950/296에서도 유효 target5행의 nominal gas는 모두0이고 최종 gas0.282~0.502가 남았다. affine head와 최종 scale이 nominal-zero 출력을 양의 gas로 바꾸는 관계는 source와 실행 기록으로 확인했다. HUD가 속도를 크게 놓친 것만으로 설명되지 않는다.

**아직 가설인 부분:** 높은 속도와 양의 gas가 제동·회피 여유를 줄였을 수 있으나 성공한 정책에도 비슷한 목표 초과가 있어 고유 원인으로 확정할 수 없다. pure-pursuit target curvature는 GT 도로 곡률이나 물리적 필수 yaw가 아니다. tire force/friction clipping은 직접 수집하지 않았다. 충돌 후 도로 방향/phase 관측 부재가 역진행을 허용하는지도 독립적으로 분리하지 못했다.

**다음 한 가지 반증 개입 — 미실행:** 정확한296에서 legal near flag(feature8)==1이고 같은 호출의 nominal gas(feature14)==0이면 반환 gas만0으로 둔다. steering·brake·경로·head 계수·actual memory는 유지한다. 기존 nominal-zero 결정을 hazard 구간에서 일관되게 실행하는 한 gate이며 계수·중간값 탐색이 아니다. T2950/T2954의 이번 matched296 기준을 재사용하고, 후보의 완주·접촉·첫 통과 arc와 속도/복구 신호를 사전에 고정해 비교한다. 접촉/무진행이 그대로이거나 기준 완주를 잃으면 이 guard가 메커니즘을 고쳤다고 주장하지 않는다. 진행 방향 문제 전체의 해결책으로 보지 않는다.

실제 비용 **1,073/2,500 native, 사전 고정한4개 공식 주행**이다. 원래 결과 재확인만을 위한 호출은 없었다. raw step4,288/reset204 tick, collection wall165.505초·runner CPU155.950초·별도 actor CPU9.409초다. 저장 분석은 wall0.933초/CPU0.917초였다. 마지막 console의 NumPy 정수 직렬화 오류는 데이터·비용·원장 저장 후 발생했고, 추가 분석 실행이나 native 호출 없이 출력 변환만 수정했다.

누적 **1,136,567 + 연구 잔여9,433 + 최종 예비84,000 = B1,230,000**이다. GT는 진단에만 사용했으며 정책 입력·코드는 변경하지 않았다. 297 DEV12·HOLDOUT·SEALED·예비·다른 환경·유료 자원은 미사용이다. champion296과240 rollback, main·Participants·사용자 변경·기존 백업을 보존했다. 공개는 일반 분석 코드와 집계만 포함하고 pose/path·geometry·seed·raw trace·모델 값은 비공개로 보관한다.
