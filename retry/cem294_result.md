# 294 — 여섯 제어 parameter의 고정 CEM과 독립 DEV 비교

**TRAIN 평균 시간을 0.490초 줄인 후보를 찾았지만, 새 DEV에서 baseline 완주 하나를 잃어 승격 근거는 탈락했다.** 고정 winner g3p4만 평가했으며 다른 archive 후보 재평가·재튜닝·챔피언 변경은 없다.

240을 출발점으로 gas scale, brake scale, steering curvature gain, route-target lookahead scale, lateral24/8 공통 배수, speed ceiling의 여섯 log parameter를 공동 탐색했다. 앞 다섯 상대 배수는 [.8,1.25], ceiling은 [40,50]이다. 기존 실제 scale은 [1.412502928638687,0.8138581028883641], 조향 계수는3.24, ceiling45, lateral24/8이다. perception·tracker·route-search cost·24/8 비율·smoothing.8·fallback·affine head는 고정했다.

lookahead는 원래 `4+.35*speed` 식과 [6,14] bound 모두에 배수를 적용했다. near-hazard eligibility의 원래 lookahead는 바꾸지 않았다. gain은 controller의 `atan(3.24*curvature*gain)` 위치에 적용했고 geometric curvature와 target/nominal/head feature는 후보의 실제 호출에서 재계산했다. gas/brake scale은 원래 head clip 뒤, 최종 clip 전 위치에서 바꿨으며 이미 clip된240 최종 페달을 다시 곱하지 않았다. 저장 관측12개에서 zero parameter의 행동·feature·nominal/state 정확 재현과 실제 조향 메모리를 짧게 확인했다.

RNG294, 4세대×8개 새 정책, initial sigma(.08,.08,.06,.06,.06,.04), floor.015를 고정했다. 매 정책은 여섯 TRAIN을 평가하며 DNF 후에도 다음 도로를 실행했다. 6/6 완주 후보와 정확한240을 archive에 보존하고 평균 공식시간·log parameter norm·등록 순서로 가장 빠른 최대3개를 elite로 썼다. mean과 diagonal population variance를 old.5/elite.5로 갱신했다. 모든32 draw와 네 번의 elite 갱신을 저장 기록으로 정확 재현했다.

**32개 정책 중31개는 여섯 도로 공식 결과를 확보했다.** 첫 g1p1의 O0/O2는 엄격한 실수 동등성 검사에서 각각87/40 native 뒤 기술 중단됐다. source와 같은 곱셈 표현 및1e−12 검사 tolerance로 최소 수정한 뒤 완료한/부분 실행을 재실행하지 않았다. 이 두 결과는 미확인으로 보존하고 DNF·elite에 넣지 않았다. g1p1의 나머지 네 도로와 나머지31개 정책은 실행했다. 원래 예외는 줄별 traceback이 없어 구체적 검사 원인은 추정이며, 이후 새 기술 오류는 없었다. budget censor0, native replay0이다.

확인된 새6/6 후보는4개다. 최종 archive winner g3p4를 학습 종료 뒤 동결했다. TRAIN 평균은240 **20.943333초→20.453333초(−0.490초,2.340%)**다. 모든 도로 개별 개선을 조건으로 삼지 않았고 N2의 악화도 보존했다.

| TRAIN | 240 | g3p4 | 변화 |
|---|---:|---:|---:|
| O0 | 23.66초 | 22.90초 | -0.76초 |
| O2 | 20.98초 | 20.40초 | -0.58초 |
| N0 | 23.62초 | 22.44초 | -1.18초 |
| N1 | 17.08초 | 17.04초 | -0.04초 |
| N2 | 21.56초 | 21.76초 | +0.20초 |
| N3 | 18.76초 | 18.18초 | -0.58초 |

첫 CEM draw 전에 unfiltered fresh DEV4 identity를 source-only 방식으로 고정하고 성능을 봉인했다. 같은 winner의 archive hash를 봉인한 뒤에만 평가를 열었다. 도로 순서는 AB/BA/AB/BA이며 A=240, B=winner다. 결과는 학습·후보 선택에 사용하지 않았다.

| 새 DEV | 순서 | 240 | g3p4 | 후보 변화 |
|---|---|---:|---:|---:|
| S2940 | AB | 21.72초 | 21.14초 | -0.58초 |
| S2941 | BA | 19.74초 | 18.26초 | -1.48초 |
| S2942 | AB | 22.06초 | 실제 crash DNF(83 native) | 완주 손실 |
| S2943 | BA | 23.98초 | 22.64초 | -1.34초 |

**baseline4/4, 후보3/4 완주.** 공통 완주3개 평균은21.813333→20.680000초(−1.133333초)지만 S2942의 baseline 완주를 보존하지 못했다. crash는83번째 native, damage1.0의 실제 종료이며 기술 오류·예산 검열이 아니다. 완주 feasibility를 우선하는 사전 gate는 탈락했다. 손상은 진단으로만 사용했다.

이 제한된 CEM은 공동 controller 조정으로 TRAIN 시간 개선을 실제 확보했고, 동결 winner의 새 DEV 완주 보존에는 실패했다. controller 최적화 방법군이나 목표 전체의 불가능성을 주장하지 않는다. 고정 후보 ZIP·여섯 parameter·raw trace·등록 identity는 비공개로 보존했다. 같은 호스트 pixel-only 실행 검증이며 공식 제출 qualification이나 새 경쟁 일반화의 확정은 아니다.

실제 비용 **48,412 native = TRAIN46,456/64,000 + 새 DEV1,956/16,000**. 200개 episode 시도 중198개 공식 종료,2개 기술 미확인; raw step193,449/reset10,200 tick, source model physics0. 전체 search wall2,014.687초, training wall1,909.430초(기술 복구 간격 포함)다. 별도 episode runner CPU 합계2,396.528초, 기록된 actor CPU 합계557.327초이며 기술 중단의 마지막 실패 호출 CPU는 별도 확인되지 않았다. episode wall 합계3,145.146초는 두 병렬 실행이 겹치므로 전체 경과시간으로 쓰지 않았다.

추가 배정76,000을 먼저 기록해 B1,140,000 / 연구80,976으로 시작했다. 종료 누적1,023,436 + 연구 잔여32,564 + 최종 예비84,000 = B1,140,000. 예비·HOLDOUT·SEALED·외부 유료 자원·다른 환경 사용0. champion240 archive와 manifest, main·Participants·백업·기존 사용자 변경을 보존했다. 공개는 일반 코드와 집계만 포함한다.
