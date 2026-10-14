# 310 — 기존 pixel route 비용 계수의 단일 변화 screen

**Screen winner clearance120은 전체18에서14/18로 기준296의17/18보다 완주가 적었다.** 추가 완주 T2950 하나,손실 N2/T2954/T2957/T29510 네 개다. 공통13개 평균 시간 차이는−0.003초로 전체 성능 개선의 근거가 아니다. Runner-up으로 교체하거나 계수·basis를 다시 조정하지 않았고 승격·DEV 개봉 없이 종료했다.

실제296의 edge cost `length*(1+2/max(distance,1.5))`와 후보 score `base_gap+connection_weight*connection`에서 **길이항1·clearance soft penalty2·connection weight1** 세 기존 비영 계수를 골랐다. 각각 하나만0.8/1.2배로 한 여섯 후보를 결과 전에 등록했다. Length는 기본거리,clearance는 낮은 distance-transform 여유의 soft penalty,connection은 nominal steering-transition proxy 비용이다. 실제 steering gain·smoothing을 바꾸지 않는다. Length/clearance는 edge ratio에서 일부 결합되지만 length는 basegap scale도 바꾸며, 여섯 독립 방향이라고 주장하지 않는다.

기존189 archive의 connected edge 구현은 모두1+2/d였다. 확인된134/135는 connection0/1 대조,171은 near-score tie 유지,123은 hard margin,304는 HUD wheel cost anchor,305는 소실 route 기억,294/297은 controller 계수,309는 final pedals였다. 동일0.8/1.2 계수 대조는 찾지 못했다. Source 변경은 후보마다 비용 한 줄뿐이며 원래 root·head·모델·controller/target/lookahead/속도 계수·perception/tracker를 보존했다. Hard mask·거리≥1.5·도로/장애물 배제·연결성·no-corner 조건을 해제하지 않았다. 관측 graph feasibility는 실제 연속 차체 충돌 회피의 보장이 아니다.

Screen은 새12 TRAIN의0·3·6·9 위치(T2950/T2953/T2956/T2959)와 기존여섯의앞두O0/O2였다. 여섯 후보를 각각6개 공식 종료까지 평가하고296은 캐시를 재사용했다. 순위는 완주 수→각자 성공 평균 시간→296 우선→등록 순서다. 비용 변경 없는 identity는304개 실제 저장 입력에서 행동·feature·memory·경로가 정확히 같았다. 실제 호출마다 동일 image/obstacles/speed/previous-steer의 원래 router를 읽기 전용으로 계산해 선택 경로를 비교했다. GT·teacher와 추가 detector/tracker update는 없으며 진단 routing CPU overhead는 actor 비용에 포함된다.

| Screen | 완주 | 자체 평균 초 | 추가/손실 vs296 | 공통 | 공통 평균 Δ초 |
|---|---:|---:|---:|---:|---:|
| 296 | 5/6 | 22.996 | 0/0 | 5 | +0.000 |
| length080 | 5/6 | 24.504 | 1/1 | 4 | -0.070 |
| length120 | 5/6 | 22.896 | 0/0 | 5 | -0.100 |
| clearance080 | 5/6 | 23.384 | 1/1 | 4 | -0.250 |
| clearance120 | 6/6 | 24.103 | 1/0 | 5 | +0.148 |
| connection080 | 5/6 | 22.996 | 0/0 | 5 | +0.000 |
| connection120 | 5/6 | 22.996 | 0/0 | 5 | +0.000 |

Clearance120(2→2.4)을6/6으로 한 번 동결한 뒤 **나머지12만** 추가했다. Own mean은 서로 다른 완주 집합에 조건부이고 전체도로 평균이 아니다. Screen 공통5개 평균+0.148초와 T2950 추가 완주를 함께 남겼다.

| Winner 전체 TRAIN | 공식 결과 | damage |
|---|---|---:|
| T2950 | 28.90초 | 0.2 |
| T2953 | 23.94초 | 0.4 |
| T2956 | 23.34초 | 0.0 |
| T2959 | 21.34초 | 0.0 |
| O0 | 24.24초 | 0.0 |
| O2 | 22.86초 | 0.2 |
| N0 | 23.98초 | 0.0 |
| N1 | 18.92초 | 0.4 |
| N2 | off_track DNF | 0.2 |
| N3 | 19.04초 | 0.0 |
| T2951 | 21.04초 | 0.0 |
| T2952 | 21.24초 | 0.0 |
| T2954 | off_track DNF | 0.0 |
| T2955 | 24.70초 | 0.4 |
| T2957 | off_track DNF | 0.4 |
| T2958 | 22.48초 | 0.0 |
| T29510 | off_track DNF | 0.4 |
| T29511 | 21.26초 | 0.0 |

동일 현재 입력의 원래 선택 대비 path 변화는 length080267/1,876행동,length120200/1,718,clearance080296/1,684,winner clearance120 **366/5,098**이다. 비용 변화가 실제 선택 경로로 이어졌다. Connection080/120은 각각0/1,754이며 두 후보의 전체6도로 행동·feature·memory·collision/종료 trace3,508개가296과 정확히 같다. Edge 변화는 candidate path pool 자체도 바꿔 selected-index만 비교하지 않았다. 새 경로 이후 head 입력·pedal·steering trajectory 변화는 같은 공식의 폐루프 효과이며 baseline stream까지 같다는 주장은 아니다.

36개 screen+12개 extension, **48개 공식 결과가 모두 완전 관측**됐다. Candidate 기술 오류·검열·미실행0이다. Extension12가 모두 저장된 뒤 반환 dict의 중복results 키로 집계 오류1건이 발생했다. 원래 source/계획/outcome과 오류를 보존하고 dictionary 집계만 고쳐 기존12 endpoint로 복구했다. 제어·선택·동결·결과 변경이나 native 재실행은 없었다.

비용 **13,884/16,000 native=screen10,597+extension3,287**, raw step55,490/reset2,448 tick이다. 전체 elapsed479.195초(약7.99분),runner CPU553.039초·별도 actor CPU187.693초,병렬 episode wall 합계803.798초다. Source forecast physics·새 fit·유료 자원0이다. Duplicate 조사·identity replay·정리 시간은 execution wall과 별도다.

종료 예산은 **누적1,240,343+연구 잔여5,657+최종 예비84,000=B1,330,000**이다. 296·240 rollback·main·Participants·사용자 변경·이전 결과·백업과 미개봉297 DEV12/HOLDOUT/SEALED·예비를 보존했다. 일반 코드·집계만 공개하며 모델·ZIP·raw trace/geometry·등록 identity·개인 문서는 비공개다. 이 후보의 전체TRAIN 완주 감소를 기록하고 자동 후속 실험은 없다.
