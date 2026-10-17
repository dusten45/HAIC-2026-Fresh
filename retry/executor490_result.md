# 490 — 입력 후보 구성 완료, 투영 호환성 미자격

**489의 인증된 line bytes를 유지해 완전한 executor schema 입력 후보를 한 번 구성했다. 원래 시작점 투영에서 domain error가 발생했으므로 실행 호환성·동적 안전은 승격하지 않는다.** profile1회·frozen268 multipliers1회·P4 함수1회(정확히4패스)이며 새 경로 탐색·변환·보간·최적화와 actual/world/reset/step/seed·둘째 조건 접근은 모두0이다. 첫485의 이전 실패와 노출된 known DEV 지위는 그대로다.

## 구성과 비공개 입력

질량·effective mass·구동/제동/lateral 상수는485 저장 model 그대로이며 원래 mass 식과 일치한다. line과 curvature는489의 인증된 소유 파일을 참조한다. 새 private NPZ에는 speed·ds·pace·projected_nodes만 저장한다. 기존 line·명령·raw 전체를 복제하지 않았다. loader는 소유 파일 해시·정확한 line/node bytes·N/N+1 크기·ds와 원래 line 변 길이의 일치를 검사한다. 일반 SourceC의 paired417 policy 생성 뒤 P4를 직접 binding해 이중 pace 적용 없이 최종 소비 노드가 일치함을 확인했다.

| 정적 입력 항목 | 결과 |
|---|---:|
| launch 속도 target |0m/s|
| 그 외 최소 target |15.656694827508797m/s|
| 자유 finish target |79.38451066309376m/s|
| 최대 forward q 잔차 |1.3642420526593924e−12|
| 최대 backward q 잔차 |1.0231815394945443e−12|
| 두 잔차의1e−8 초과 |각0구간|

launch의 정확한0 target은 원래 finite nominal launch 예외로 처리하는 소스다. finish는 양수 자유 종료이며 같은 위치의 launch target과 같게 만드는 주기 속도 조건을 추가하지 않는다. 이번 phase act fixture는 투영 실패 뒤 실행하지 않았으므로 실제 launch/finish 동작 통과를 주장하지 않는다.

## 가감속·힘 대리량의 제한

P4 최종 이산 가감속 잔차는 통과했다. 그러나 source `segment_proxy`의 구간 내 보수적·가정적 대리량에는 다음 초과가 남았다. 추가 패스·속도 조정으로 수리하지 않았다.

| 구간 대리량 |1초과 구간 수|최대 비율|
|---|---:|---:|
| 상승 구간 endpoint engine 요구|35|1.0394473501365118|
| 병진 combined circle|17|1.050245977138826|
| equal-axle rear drive circle|33|1.2529585278788151|

이는 piecewise-linear squared speed·선형 보간 curvature·all-road/grip1·equal axle load를 둔 대리식이다. 실제 타이어 force·grip·steering lag·slip 검증이 아니다. 이산 구동 상한이 왼쪽 속도에서 통과해도 상승 구간 전체 engine 상한을 인증하지 않는다. pedal 함수의963개 순수 대수 query는 finite/범위/동시 gas-brake 부재 및 정지한 양수 target에서 양의 요청 검사를 끝냈다. clipped scalar acceleration과 실제 실현 가속도도 구분해야 한다.

## 투영 장애물과 진단 중단

모든321 vertex·midpoint와 midpoint normal shift ±0.25/1/3m를 원래 canonical projection에 질의하고, 현재 index 또는18개 stale index를 준 원래 nearest-vertex cursor와 비교하도록 등록했다. 이 유한 pose 검사 과정에서55건의 projection domain error를 잡았다. 이어 정확한 `line[0]`에 LAUNCH projection을 요구한 명시적 seam 검사도 `Distinct_or_nonadjacent_projection_ambiguity`로 실패했다. 이 두 종류의 원본 오류는 보존했다.

원래 함수는 `ds*ds`를 분모로 계산한 u가 정확히0/1일 때만 vertex tag를 부여하고, exact distance tie에 −1 interior tag가 섞이면 거부한다. 따라서 기하적으로 공유 끝점인 경우도 수치·태그 경계가 문제가 될 수 있다. 좌표를 반올림하거나 snapping/tolerance/fallback을 추가하지 않았다. 별도 대수 검사는 이 시작점의 다중 minimizer/비허용 tag 조합을 확인하는 지점까지 실행됐다.

원래 worker의 fatal seam 이후 sample별 cursor gap/불일치 배열은 저장되지 않았다. 따라서 그 비율·최악 gap·near-tie 통계를 복원했다고 주장하지 않는다. 별도 generic rectangle에서는 exact 비인접 tie 거부와 양쪽의 유일 최근접 arc 전환을 확인했다. 비자교·유일 최근접이라는 점별 성질도 off-reference tube 전체의 연속성을 보증하지 않는다. vertex에서는 tangent·sigma·f가 한쪽씩 바뀔 수 있고 shortest-period unwrap도 물리적 연속성 보증이 아니다.

첫 diagnostic worker는 technical stop으로 종료했다. 저장된 입력에서 **미실행 가감속 진단만** 남은 등록 한도 안에서 수행했으며 profile·P4·input/consumer 재구성 및 실패한 map projection 재질의는0이었다. 이 추가 단계도 최종 JSON 집계에서 NumPy int64 직렬화 오류가 났다. 그 시점까지 수치 검사·assertion은 완료됐고 segment 기록과 차감 journal이 남았다. 수치 함수를 다시 호출하지 않고 이 기록으로 위 집계를 만들었다. 최초/추가 오류·실행 source·이전 결과를 덮어쓰지 않았다. 전체 진단 gate 통과나 재현 성공으로 포장하지 않는다.

## 자원과 보존

사전 등록은 CPU30초/wall45초·RSS256MiB·retained8MiB/32파일·file/temp1MiB·volume별512MiB reserve였다. profile/multipliers/P4/consumer 각1회, canonical4096·cursor4096·경쟁거리4096 batch·proxy321·pedal1024의 hard cap을 두고 batch 전에 journal에 차감했다. 추가 진단도 같은 누적 cap을 유지했다. 원래 계산 worker의 실측은 CPU3.996121523초/wall3.968702910초·RSS34,439,168B다. 추가 단계 마지막 차감 checkpoint의 누적값은 CPU4.589697860초/wall4.544952583초다. 미실측 tail을 추가단계 전체1초의 보수적 allowance에 포함한 numeric 계상은 약CPU5.000초/active wall4.972초이며 완전 실측 합계로 부르지 않는다. 사람의 원인 진단·구현 간격은 active 계산 wall에 포함되지 않는다.

최종 원본 readback/해시와 전체 code/report/publication quota를 확인한다. main·Participants·backup·기존485~489 자료·연구 잔여26,175·예비84,000/사용0을 보존한다. 최신 종료2026-10-20 19:01:55 KST, 자동 연장 금지를 유지한다.

## 별도 미래 계약

[제안 계약](executor490_future_contract.json)은 **실행 승인 없는 설계**다. 동일 known DEV의 새 native world/reset1에서 자연 SourceC/P4로 첫 quarter 경계를 정하고, root 이전 witness1과 이어진 witness2를 관측하는129 action 상한을 제안한다. source3 world는 cold2개와 두 hold를 연속 실행하는 held/warm1개다. 그 뒤 원래 H6 margin 정책의 두 cold 반복+held-first를 비교하면 모델113 world/536 ticks이며 native raw는 reset 포함580 ticks 상한이다. 새로운 DEV 반복이나 일반화 증거로 세지 않는다.

현재 source-domain gate는 **차단/미자격**이다. 후속 reset 전에 별도 검토에서 변경 없는 source의 구체적인 launch/seam query gate를 충족하거나, 이 실패를 유지한 제한된 fail-closed 진단 범위를 사용자가 명시적으로 수락해야 한다. 전체 off-reference 연속성 보장은 약속하지 않는다. 이 계약은 source 수정·속도 조정·경로 수정·fallback을 승인하지 않는다.

비용은 현재 파일을 stat해 산출했다. 이전483의774파일42,420,812B(408 ticks/86 worlds), 최대 codec state368,379B, 첫485 full snapshot455,819B를 기준으로 새로운 전체 포맷 상한을 별도로 둔다. 모델192MiB·native256MiB·allocator/decision/temp 각8MiB·reserve512MiB를 포함한 `/tmp` 요구는984MiB이고 workspace는528MiB다. 실측 비율의536-tick×1.5 추정은83,593,954B지만 dedup/기록형식에 의존해 완료 보장으로 쓰지 않는다. 미래 full-state/header가 cap을 넘으면 필드 생략·기존 raw 삭제·cap 확대 없이 중단한다. 이번에는 물리 world를 만들지 않았다.

[집계](executor490_result.json) · [최초 등록](executor490_registration.json) · [남은 진단 등록](executor490_completion_registration.json) · [독립 정적 검토](executor490_review.md)
