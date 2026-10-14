# 311 — 같은 goal row의 모든 다른 reachable terminal column 추가

**후보와 296 모두 5/6 완주였지만 공통 5개 평균이 0.664초 느려 screen gate를 탈락했다.** T2950은 off_track DNF가 남았다. 나머지 12 TRAIN은 미관측이며 DNF로 세지 않고 전체 18 성적을 만들지 않았다. 후보 수정·DEV·승격 없이 296과 rollback을 유지한다.

과거 163개 archived route_candidates body는 두 종류였다: 162개 original/left/right loop와 1개 continuity annotation. 모든 다른 terminal column을 한 predecessor tree로 추가한 동일 실험은 찾지 못했다. 134/135는 같은 goal column의 passing-side 대안, 171은 tie 기억, 304는 score anchor, 310은 비용 계수 변경이다. 이번 가설은 단일 terminal column 제한이 유효한 대안을 놓칠 수 있다는 것이며 최초 실패 원인으로 확정하지 않았다.

원래 start·가장 먼 connected goal row·allowed mask·장애물 여유·no-corner·edge 1+2/d·connection 1을 고정했다. 기존 original/left/right 후보를 모두 보존하고 **추가 Dijkstra predecessor tree 하나**로 같은 row의 다른 모든 reachable column의 최단 경로를 추가했다. 다른 goal row·GT 경로·새 margin·steering/lookahead/속도 계수·head·memory 변경은 없다. 원래 feasibility·shortest-route·기존 pool/scorer AST와 그 외 296 archive member는 그대로다. 그래프 가능성은 연속 차체 충돌 회피의 보장이 아니다.

확대 집합의 최소 cost를 gap 기준으로 썼다. 기존 후보의 gap·1e−9 근접 zero 규약에 공통 offset만 더해 기존 후보끼리의 순위를 보존했다. 정확한 동률은 기존 후보 우선, 추가 후보끼리는 column 순이다. 저장 입력과 실제 호출의 rank assert 및 간단한 exact-tie/column-order fixture를 native 없이 확인했다.

306의 exact296 저장 pixels 1,754개를 재사용했다. Additions-off의 행동·feature·memory·선택 경로가 모두 정확히 같았다. Additions-on은 자기 반환 memory를 순서대로 갱신하며 같은 저장 pixels를 봤고 1,676개 행동이 달랐다. 이는 새로운 closed-loop 궤적의 성공 대용이 아니다. 동일 현재 router 입력의 legacy 선택 대비 경로 변화와 지연도 기록했다.

| 저장 TRAIN | 입력 | 경로 변화 | 행동 변화 | 최대 후보 | on actor p95 ms |
|---|---:|---:|---:|---:|---:|
| T2950 | 315 | 205 | 297 | 62 | 27.71 |
| T2953 | 298 | 212 | 298 | 48 | 28.64 |
| T2956 | 292 | 201 | 275 | 46 | 28.43 |
| T2959 | 265 | 193 | 262 | 46 | 26.14 |
| O0 | 304 | 213 | 284 | 47 | 27.19 |
| O2 | 280 | 191 | 260 | 46 | 25.69 |

Preflight wall은 59.624초, 최대 on IPC는 66.269ms였다. 시간에는 baseline 진단 router도 포함되며 공식 서버 동등성의 증명은 아니다. 실제 변화 gate가 양성이어서 후보를 한 번 고정하고 지정 6 TRAIN을 각 한 번 공식 종료까지 실행했다. 완주 수 증가 또는 동률에서 공통 평균 시간의 엄격한 개선일 때만 12개를 확장하도록 결과 전에 정했다.

| Screen TRAIN | 저장 296 | 후보 | native |
|---|---|---|---:|
| T2950 | off_track DNF | off_track DNF | 296 |
| T2953 | 23.80초 | 24.36초 | 305 |
| T2956 | 23.32초 | 24.36초 | 305 |
| T2959 | 21.18초 | 22.10초 | 277 |
| O0 | 24.32초 | 25.02초 | 313 |
| O2 | 22.36초 | 22.46초 | 281 |

실제 1,777개 호출에서 후보 수는 0~49, 추가 tree는 1,771회였다. 추가 후보 선택·동일 현재 입력의 legacy 대비 경로 변화는 **1,491회**다. Column 수를 자르지 않았다. 기존 순위·tie·단일 tree·모델/controller/head 보존과 process 회수를 확인했다. 기술 오류·검열은 0, 실제 DNF는 1이다. 대안과 행동 변화가 생겼지만 이 6개 screen에서 완주·시간 개선으로 이어지지 않았다. Terminal 제한이 T2950 실패의 충분한 원인이라는 가설은 지지되지 않으며 모든 경로 확대 방법의 불가능성을 주장하지 않는다.

비용은 **1,777/5,657 native**, 확장 0, raw step 7,104 / reset 306 tick, native phase wall 66.643초다. Runner CPU 합계 73.642초·별도 actor CPU 35.282초였다. 저장 입력 preflight는 native/source physics 0이며 시간을 native elapsed에 더하지 않았다. Pixel Dijkstra·score 비용은 actor CPU에 포함된다. Source forecast physics·새 fit·유료 자원은 0이다.

종료 예산은 **누적 1,242,120 + 연구 잔여 3,880 + 최종 예비 84,000 = B1,330,000**이다. 296·240 rollback·main·Participants·사용자 변경·이전 결과·백업과 297 DEV12/HOLDOUT/SEALED·예비를 보존했다. 일반 코드·집계만 공개하며 model/ZIP·pixels·raw trace·등록 identity·개인 자료는 비공개다. 자동 후속 실험은 없다.
