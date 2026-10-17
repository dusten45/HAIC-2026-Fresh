# 489 — 고정 lattice 단일 실행 결과

**첫485의 이미 노출된 저장 지도에서 geometry 후보 하나가 독립 gate를 통과했다.** 새 조건·profile·P4·native·reset·step·world·seed는 모두0이며 후속 실행을 시작하지 않는다. DEV 노출 이력을 유지했고 둘째 조건·HOLDOUT·SEALED를 사용하지 않았다.

488의21 offset/0.5m·양쪽 회피·pair-state·고정 초기 pair·canonical tie·첫 terminal 하나를 그대로 구현했다. 선분 전체와 여섯 장애물의 원래 inflation, 원래 곡률 proxy, 모든 closed-seam triple, 강화된 exact-rational tube와 positive-dot 조건을 유지했다. 다른 goal·해상도·후처리·solver 구제는 없었다.

## gate와 결과

원본 geometry/arc 재구성, 양쪽 회피, 선분 내부 충돌, incoming 방향 곡률, 역방향 dot,21-rank/6-obstacle broadcast, taper/midlap/closing boundary, actual float64 displacement, signed zero/alias, canonical predecessor/terminal, root/last/closing edge, nonlocal compatibility 분리 및 출력 quota의 **synthetic15개 검사가 통과한 뒤 map 탐색을 정확히1회** 실행했다.

독립 구현은 모든 node/edge/triple mask, edge margin, 층별 reachability·parent·terminal을 재계산해 일치를 확인했다. 복원한 최종 경로 한 개를 원래 source 함수의 전체 선분 clearance·모든 corner curvature·offset V로 다시 검사했다.

| 항목 | 결과 |
|---|---:|
| 최소 inflated clearance |0.011543096325152824m|
| 원래 source V |0|
| 최대 absolute curvature proxy |0.1302938656808264|
| 원래 target |0.13049173417844498|
| 강화 tube certificate |통과|
| source/checker 불일치 |0|

이는 원래 geometry gate와 추가 tube/dot 조건을 만족한 **기하 후보**다. Polyline corner의 고전적 C² 곡률, 실제 road-body containment, 동적 안전·완주 성능을 증명하지 않는다. 여러 구조 변경을 함께 적용한 방법군이며 한 요소의 인과효과로 해석하지 않는다.

## executor 경계

정확한 최종 polyline에서 finite schema·양의 segment length·중복점 부재를 확인했고 인접 backtracking·비인접 intersection/overlap은 검출되지 않았다. 따라서 현재 판정은 `ON_REFERENCE_COMPATIBLE_ONLY`다. Off-reference cursor projection/추종, speed(M+1)·model을 포함한 완전한 executor 입력, P4/native/pixel 자격은 미확보다. 속도나 주행으로 자동 승격하지 않는다.

## 비용과 보존

전체 단일 worker는 import·source/input 검사·synthetic·구성·탐색·독립 감사·원래 최종 gate·compatibility·직렬화·전체 readback을 포함해 **CPU4.341745832초 / wall4.557455315초 / 최대 RSS39,141,376B**였다. 제한60/90초·256MiB 안에서 끝났다. 중단 margin55/82초, preimport thread1 및 추가적인 AS256MiB 제한을 적용했다. synthetic의 아주 짧은 vectorized microbatch는 process_time 해상도에서0으로 기록됐으며, 비용이0이라는 뜻이나 전체 비용 보장으로 사용하지 않는다.

producer와 독립 audit 각각 node6,848 / edge142,011 / triple2,982,048회를 선차감했다. 여기에는 synthetic 비용도 포함된다. source full-path gate1회, compatibility segment-pair 선차감51,366회다. 모두 고정 hard workcap 이내다. 각 batch 이전 차감·fsync journal을 남겼고, 종료2파일·64KiB를 예약했다.

비공개 raw는2,137,228B이며 좌표·rank·mask·부모·후보·rational witness·certificate를 보존한다. 전체 code/report/publication 동반 파일도16MiB/40파일의 global quota에 포함해 최종 확인한다. 파일·temp2MiB, 양쪽 volume512MiB reserve를 유지했고 이전 raw를 복사하거나 삭제하지 않았다. 공개물에는 좌표가 없다.

기존 main·Participants·backup·485~488 자료와 연구 잔여26,175·예비84,000/사용0을 보존한다. 최신 종료2026-10-20 19:01:55 KST와 자동 연장 금지를 유지한다. 다음 기술 경계는 완전한 executor 입력과 off-reference 추종 자격이며 이번 작업에서는 진행하지 않았다.

[실행 등록](lattice489_registration.json) · [집계](lattice489_result.json) · [기존 설계 계약](corridor488_contract.json)
