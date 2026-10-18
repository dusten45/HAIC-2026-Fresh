# 510 — 실제 wrapper 연결 통과, 이번 prefix에는 제동 요청이 없어 효과 미검증

사용자가 지정한 초기 진단 커밋 `e0ac6effdf65b723f5467068c53f2133a4874050`의 코드·DEV 실행 설정만 좁게 확인했다. 첫 등록 case의 정확한 reset 쌍과 `split=DEV`, 초기 source 설정을 연결했고, 현재 core/wrapper 코드가 그때와 같은지도 확인했다. [조건 생성법](prepare510_case.py)은 그 고정 commit/path/case index만 읽으며 새 seed를 뽑지 않는다.509의 identity 장애물은 해소됐다. 보호 평가 집계/seed를 추가로 조회하지 않았으며509의 범위 오류 기록은 유지한다.

## 실제 native 결과

두 arm 모두32actions·128action rawticks를 완료했다. 각각 reset51ticks이며 옛 공개 도로/장애물 SHA와 일치했고, 두 새 reset의 등록한 body 관측/RNG/pixel fingerprint도 exact였다. fingerprint는 observed_state 필드·assembly 위치·hull angle·시각·RNG·관측 해시를 포함한다. 전체 solver warm-start나 모든 planar/joint checkpoint 동일성을 인증한 것은 아니다. 새 동결 참조는 `PixelAgent(adaptive=True)`이며 초기 starter나 과거 champion 복원이 아니다. 각 arm의 자기 현재 관측에서 reference를 한 번 호출하고, steering/gas와 갱신된 memory를 보존했다.

| 같은32action prefix |reference|adapter|
|---|---:|---:|
|종료 COM 속력|62.023435m/s|62.023435m/s|
|공식 타일 진행률|10.600707%|10.600707%|
|최소 sampled hull/wheel road 여유|4.720295m|4.720295m|
|nominal 제동 요청|0|0|
|실제 제동 교체|0|0|

32개 action/관측 해시·속도·진행·여유 행이 두 arm에서 모두 같았다. 실제 source 센서·payload·효과·여유 오류358raw rows에서0건이었다. 그러나 **reference가 제동을 요청하지 않았으므로 native 제동 성능과 미래 물리 예측 오차는 미검증(null)**이다. 이는 passthrough 연결 확인이며 제동 개선이나 기록·11초대·완주를 뜻하지 않는다. 구간은 arm당2.56초이고 서로 다른 길이의 종료 결과를 비교하지 않았다.

## 실제 물리 효과와 요청 해석을 분리한 작은 시험

508의 같은 혼합 curve 생성법에서 실제 기본 grass0.6을 사용했다. healthy와 damage0.4에 해당하는 현재 source 효과(grip0.8/engine0.9/steering0.9)를 고정한 두 조건이다. 각 arm은 동일한3개 nominal holds(가속0.25 한 번, 이후 brake0.03 두 번)를 받는다. 미래 효과를 주지 않았으며 가속·조향은 그대로였다.

| 두 제동 hold의 최대 오차 |healthy reference|healthy adapter|비단위 효과 reference|비단위 효과 adapter|
|---|---:|---:|---:|---:|
|실측−steady-torque로 해석한 목표|0.104862|0.002148|0.101350|0.002142|
|실측−해당 실제 명령의 물리 예측|0.002138|0.002148|0.002136|0.002142|

단위는m/s·절대값이다. 같은 brake 숫자의 steady 감속 해석과 실제4tick 응답의 차이가, 물리 예측 오차보다 컸다. adapter는 이 조건에서0.03보다 약한 brake를 선택해 과도한 감속을 줄였다. 이것이 모든 상태의 제동 의도를 인증하지는 않는다. 현재 계수로 scaling한 접촉 마찰 예측과 source actual-pose oracle 불일치0, 최소 여유2.799721m였다. 사전 물리 gate를 통과한 뒤 native로 넘어갔고 합성 조건을 추가하지 않았다.

## 비용·재현·다음 판단

[사전 계약](brake510_contract.json) · [실행](brake510_run.py) · [집계](brake510_result.json) · [요약](brake510_summary.json). 순수8tests가 full branch 예약식을 검사했다: 합성4world/48ticks/4zero-primes + native2world/2resets/**358ticks** =6world/406positive ticks다. 모두 닫혔다. 실제 native **64actions 전부**를 call 전에 immutable charge receipt로 기록하고64개를 전수 대조했다. reset 비용102ticks도 포함했다. 연구 **26027→25963**, 예비84000/used0. 실행CPU4.527347s/wall4.558412s(테스트 child 포함), 상한180/240s 이내. private562files/502,511B로32MiB/1024files 이내다. case 설정·실측 raw·action/관측 trace는 private에만 남겼고 사용자 대신 전송·첨부하지 않았다. 기술 재실행0이다.

이번64action 상한은 소진됐으며 추가 native 연장·reset은 하지 않았다. 다음 유효한 제동 비교는 **제동을 실제로 요청하는 명시적 물리 속도목표 reference**를 먼저 동결하는 것이다. 단순히 같은 prefix를 더 달리며 제동을 기다리거나, 사후에 제동을 주입한 결과를 이번 참조의 개선으로 섞지 않는다. steering/acceleration reference와 요청 정의·정지 규칙을 양 arm에 동일하게 사전 고정한 별도 진단이어야 한다. 새 실제 비용은 잔액25963에서 별도 등록해야 한다. 현재 결과만으로 native 제동 개선·whole-lap 이득·pixel 정책 자격을 주장하지 않는다.
