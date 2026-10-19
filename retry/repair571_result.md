# 571: 실제 성분 오차에 따른 strict footprint 복구

**소스상 공식 tracker가 candidate raw661·13.22초에서 raw660·13.20초로 20ms 개선됐다.** 선택된 새 명령열의 초기 source 상태부터 전체661raw를 독립 재생해 상태·힘·누적 이력·tracker와 최종 checkpoint가 정확히 일치했다. 확인 raw는661이며 점수로 혼동하지 않았다. Native 기록 개선은 주장하지 않는다.

출발점은 570의 세 번째 안전 작업점이다. 물리 시작은 같은565raw528/root/visited/tracker/clock, launch55/384와 tracking64/1728을 유지했고 이후 전체68변수 명령열 목적을 유지했다. Seed 복원을 위한 별도 prefix/whole 재생은 하지 않았으며, 최종 새 궤적의 독립 재생에는 원래565prefix528raw를 포함했다. 초기68FD와 geometry vertex 민감도는 동일 작업점의 저장570자료에서 재사용했다.

저장된 마지막 두570거절안의 raw577을 읽어 실제 활성 성분이 **도로 경계 segment250·차량 polygon6**임을 확인했다. 장애물 원이 아니었다. 차량 polygon의 모든 꼭짓점에 부호 있는 분리 halfspace를 적용해, 이전 최소 꼭짓점이 바뀌어도 같은 도로 성분을 분리하도록 했다. 초기 대상은 실패 hold145와 선행 hold144(raw573..580), 32개 꼭짓점 제약이다. 이는 고정 성분에 대한 충분조건이며 다른 성분이나 road-union coverage의 전역 증명은 아니다. 원 exact geometry validator는 변경하지 않았다.

오차 계수는 저장 calibration2개와 reject2개의 signed-vertex 예측 낙관 오차를 **실제 정규화 이동량**으로 나눈 최대값의 두 배, float32 ULP 전파와 binary64 항으로 정했다. 모든 여유는 `L*t`여서 이동0의 안전 seed를 포함한다. 계수 clip, 고정 buffer grid, 마이크로미터 위반 반올림은 하지 않았다. 도로·원 support, tied corner, 관측 오차 규칙의 단위검사4개를 소스 평가 전에 통과했다. 초기 데이터 설계는 소스0틱/CPU4.11초였다.

추가로 두 실제 strict 거절이 있었다. raw633과632의 도로 segment553·polygon7에서 margin이 각각0.499998174m, 0.499889078m였다. 실패한 상태를 채택하지 않았다. 현재 안전 incumbent에서 같은 성분의 분리 제약을 만들고, 실제 거절 방향의 오차/이동량을 동일한 규칙에 넣어 계수를 올린 두 복구가 각각 안전 완주로 이어졌다. Base support는 각 새 선형화에서 재선정하고, 관측된 추가 성분은 그 center 내에서 도입하며 성분별 계수 floor는 유지했다. 이 경험적 예산은 전 방향 오차 보증이 아니다. 모든 후보는 원 force/path/footprint/reference/count/finish를 다시 통과해야 했다.

| 새 안전 작업점 | 실제 전체 step gain(보간) | 570 작업점 대비 누적 gain | 공식 candidate / 확인 raw |
|---|---:|---:|---:|
| 1 | 1.3410ms | 1.3410ms | 661 / 661 |
| 2 | 0.0909ms | 1.4320ms | 661 / 661 |
| 3 | 1.4326ms | 2.8645ms | 661 / 661 |
| 4 | 1.1024ms | 3.9669ms | 660 / 661 |
| 5 | 1.6195ms | 5.5864ms | 660 / 661 |

전 구간 진단과 strict 실행은 같은 명령열에서 같은 도착 시간과 상태 prefix를 냈다. 최종 hull 도착 보간값은13.1973300700초다. 추가 보간 gain5.5864ms, 원565대비 누적 보간 gain16.2844ms와 공식 quantized gain20ms는 서로 다른 지표다. 13.20초 경계까지 약2.92ms라는 초기 진단을 성공 보장으로 쓰지 않았으며, 실제 tracker의 qualification·forward·width·half-depth 확인을 끝까지 검사했다.

선택된 궤적의 최소 footprint0.501723236m, 최대 path1.47239353m, force ratio1.05824899, reference overspeed4.849999403m/s, body96.9293547, 최종 tracking90/2260을 확인했다. 모든 원래 strict 허용치를 유지했다. Reference 경계는 여전히 가까우며, 이 결과가 추가 개선의 여유나 수렴을 보장하지 않는다. 최종 새 전체 source tape와 checkpoint는 비공개 `final-independent-tape-private.json`에 남겼다.

사전 5개 안전 작업점 수락 상한에서 종료했다. 이는 수렴·최적성·방향 불가능성 증명이 아니다. 실제 사용은 선형화5회, 새FD272열(기존68열 별도 재사용), 보정8회, 소스 제안/strict 검사7회, 관측 오차 복구2회, 안전 수락5회다. 비용은 독립 검증661틱을 포함해 **39,993소스틱, 힘159,972회, 기하39,993회, primitive 기하 질의44회, CPU1,040.23초, wall1,122.40초**였다. 전체 모델의 최고 body96.930453은100 아래이며 원자 비용 기록과 hash-chain journal을 감사했다. 이전570비용은 별도다.

실제 행동·reset·HOLDOUT·SEALED·새seed·유료 자원·예비 사용은0이다. 연구22,758/예비84,000을 유지했고 main/Participants/사용자 변경과 이전 실패 기록을 보존했다. 검증 대상은 결정론적 소스 모델의 전체 open-loop 명령열이다. Native 실행, 기존 feedback 전환·회복, 픽셀/지연/외란 강건성은 별개이며 아직 보장하지 않는다. 원문과 원시 상태·제어열은 공개 저장소로 전송하지 않았다.
