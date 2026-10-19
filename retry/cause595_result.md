595 — 594 거절을 정확히 재현: path3m 초과, 초기 물리 상태 차이의 전파

**최초 실패는 source 예측 global raw204(hold51/raw4)의 PATH다.** path error3.011832519946m가 원 한계3m를11.832520mm 초과했다. projection delta1.727203518508m는허용[-.5,5] 안이고 footprint도 통과했다. 원594의192개 force/before·after tick hash·ratio/body와 거절 summary 전체가 정확히 일치했다.594를 소급 통과시키거나 threshold를 바꾼 결과가 아니다.

실제 native594는 raw156에서 끝났다. 이번204는 **새로 계산한 source 미래 예측 index**이며 실제 native path 초과를 관측한 것이 아니다.595는 단일48raw source 진단으로 종료했고 native/world/reset/행동·전체 cold source/native prefix 재실행은0이다. 연구 잔액22,548·reserve84,000/사용0,592 carry 종료·593 실패·594 인증 거절을 유지한다.

[checkpoint gate](cause595_checkpoint_gate.json), [동결 계약](cause595_contract.json), [실측 결과](cause595_result.json), [저장 증거 감사](cause595_audit.json), [계측 인증기](split595_certificate.py)를 보존했다.

정확한 입력 접근과 복제

594의 거절 파일에는 인증기에 전달된 full planar/root(roads 제외)·실제 tracker 전 필드·visited 전체 집합·launch/tracking 이력·clock이 남아 있었다. progress는 완료된 실제 raw156의 저장 station에서 가져왔다. 거절 당시 root/tracker/visited hash,실제 raw156의 COM/velocity/angle/yaw/contact·clock/tracker·visited 수·이력을 모두 대조했다. root dataclass roundtrip과 저장 progress/path error 재투영도 정확히 같았다.

roads는 추정하지 않고 원594가 사용한 pin된 immutable static 입력을 참조했다. 원594의 초기 full identity와 전 prefix material/effects 불변·오류0,현재 코드/입력/runtime hash를 확인했다. 복구 범위는 **594 source 인증기의 정확한 입력 checkpoint**이며 native Box2D solver 전체를 재생성한 것은 아니다. 새 world나 native prefix는 만들지 않았다.

checkpoint SHA256은 `033b7c9b15e1e151a24897c26bd9aa046c4fbcd93bc2e65c629c0163e0f85590`다. 원594의 마지막 hold40 인증에 해당하는48개의 force 입력/결과·tick 전후192event도 journal에서 읽어 고정했다. source 재현 중 매 이벤트의 action bytes·root SHA·힘 ratio·body를 순서대로 대조했고 모두 일치했다. 파일/필드 부재나 hash 불일치 시 임의 복원하지 않고 source0 blocker로 종료하도록 했다.

순수 검사 후 source 실행

원593 인증기의 동역학·명령·geometry/projection 의미와 판정 순서를 유지하고 per-raw 계측만 추가했다. 기존 복합 조건 `minimum<.50 or distance>3 or delta<−.5 or delta>limit`을 같은 순서의4개 flag로 분리했다. equality·양옆 ULP·다중 위반·원 short-circuit 우선순위의224개 조합을 포함한 순수 검사4개가 모두 통과한 뒤 검사 결과·코드·입력·dependency를 동결했다. 원 계약 status 문자열에는 이전 양식의 BEFORE_PURE_TESTS 라벨이 남았으나,실제 검사 완료 artifact를 등록 시 input hash로 포함했다. 원 snapshot은 수정하지 않았다.

hold40..51의 동일 float32 bytes를48raw 이하로 한 번만 실행했다. 각 raw의 path error/projection segment·delta/허용구간·현재 및 누적 footprint·force/누적clip/reference·tracker update 여부·최초 분기를 내구 기록했다. 첫47raw는 통과했고48번째의 PATH에서 즉시 physics 진행을 멈췄다. 그 뒤에는 저장 상태와 projection만 읽어 비교했고 다른 rollout·continuation·재시도는 없다.

|최초 실패 raw204 진단|값|원 기준|
|---|---:|---|
|path error|3.011832519946m|≤3m, **실패**|
|projection delta|1.727203518508m|−.5≤delta≤5m, 통과|
|그 raw footprint|2.239790246078m|≥.50m|
|창 전체 최소 footprint|0.512899591077m|≥.50m|
|그 raw force peak /창 peak|0.665980535216 /1.058822542727|≤1.059|
|그 raw 누적clip|29/432=6.712963%|≤10%|
|창 최대 누적clip|9.666667%|≤10%|
|그 raw reference excess|−0.665002912694m/s|≤4.85m/s|

모든 source body domain 검사도 통과했다. 실패 raw에서 tracker/visited/clock을 commit하기 전에 반환하는 원 인증기 순서도 유지했다.595가 tracker를 한 번 더 업데이트해 결과를 만든 것이 아니다. 원594의 footprint/projection 복합 표기를 이제 PATH로 분리할 수 있지만 기존594 원 기록은 그대로다.

같은 global index의 기존577 source와 읽기 비교

기존577 raw156..204의49개 저장 root·projection 결과를 읽었다. 각 저장 source projection을 원 path/hint로 다시 계산해 progress와distance가 정확히 일치함을 확인했다. 새595의 동일한49개 root에 기존577의 progress hint를 넣어 읽기 projection만 따로 검사했는데,모든 row에서 원595와 같은 progress/선분이 나왔다.49개 모두 저장577과도 같은 projection 선분을 선택했다. path나 projection 알고리즘을 교체한 비교가 아니다.

|같은 index의 차이|시작 raw156|실패 raw204|
|---|---:|---:|
|COM 위치 차이 norm|3.814956mm|25.827963mm|
|COM 속도 차이 norm|15.541414mm/s|30.320758mm/s|
|body angle 차이|−0.000308624rad|−0.000352301rad|
|새595 path error|0.504170724m|3.011832520m|
|저장577 path error|0.501032084m|2.986113603m|
|저장577 path 여유|2.498967916m|**13.886397mm**|
|projection hint를 저장577 값으로 바꿨을 때 결과|동일|동일|

0.96초 창에서 위치 차이 norm은 수치상6.770배로 커졌다. 그러나 시작 위치만 달랐던 실험은 아니다. 속도·angle/yaw·levers·inertia·joint/rate·wheel omega 등도 함께 달랐으므로,이를 위치-only perturbation gain이나 보편적인 Lipschitz/강건성 상수로 쓰지 않는다. native/model의 과거156raw에서 이 오차가 생긴 원인과 개별 물리 성분의 기여는 이번 실험만으로 분리하지 못한다.

실패점의 path 거리 차이는25.718917mm로 COM 위치 차이25.827963mm와 거의 같고,원 source의13.886397mm 여유보다 컸다. 두 trajectory 모두 같은 선분을 선택했다. 이 창에서49개 모두 mass/engine/마찰·contact membership도 같았다. **이미 존재하던 작은 실제/model 물리 root 차이가 동일 고정 명령 아래 전파되고,작은 path 여유를 소진했다는 설명을 지지한다.** 실제 native에서 raw204를 실행해 확인한 결과나 특정 수치 연산 하나를 원인으로 지목한 결과는 아니다.

tracker/projection 복제 차이와의 구분

actual tracker는 원594에 저장된 hash와 정확히 같았다. 저장577 tracker와 다른 필드는 `previous_longitudinal`, `previous_lateral`뿐이며,기하·departure/crossing·qualification/finish 상태는 같았다. visited 전체 집합도 같고 clock 차이는−2.6645e−15초다. 실제 running 이력15/240과 저장57716/240의 차이도 그대로 보존했다. 읽기 산술상 초기clip을 저장577처럼1개 더 넣어도 창 최대10%로 원 문턱을 넘지 않는다. 그 이력을 바꾼 physics rollout은 하지 않았다.

고정 명령의 source tick은 tracker/clock/visited/clip 이력에 따라 물리 상태를 바꾸지 않는다. projection은 이전 progress를 사용하지만49개 alternate-hint 조회가 같은 결과였다. 따라서 **이 재현에서 잘못된 tracker/progress 복제나 다른 projection branch 선택이 PATH 실패를 만들었다는 증거는 없다.** 반대로 root의 다중 성분 중 무엇이 지배적인지는 별도 반사실 실험 없이 단정하지 않는다. 여유13.9mm를 넘는 관측 거리 차이라는 유한 창의 결과이며,전체 경로·다른 초기화의 오차 bound는 아니다.

비용·감사·보존

|계수|실제595|사전 상한|
|---|---:|---:|
|source 시도 /완료tick|48 /48|각48|
|외부 /내부 force|192 /192|각192|
|force 총합|384|384|
|geometry 전체 조회|196|200|
|source CPU /wall|0.579954 /0.645399초|60 /90초|
|준비·테스트·등록·분석·감사 CPU /wall|14.183957 /13.382679초|60 /90초|
|전체 CPU /wall|14.763911 /14.028078초|120 /180초|

geometry196은 actual 시작 progress 검증1+current/post footprint49+source projection48+저장577 projection49+alternate-hint projection49다. projection 조회까지 보수적으로 모두 차감했고 physics 중 비교용98조회와 감사 시간을 예약했다. 새48raw는 원594의 비용을 재사용한 것으로 숨기지 않고 **별도 source 계산으로 전액 계수**했다. 원593/594의 비용·예약은 변경하지 않았다.

240event 새 journal chain과 모든 입력·코드·runtime pin,192개 원594 event/summary exact,최초 PATH와 기타 안전 분기,geometry/force/tick 계수·원장·native0을 확인한 source0 감사24개 모두 통과했다. 읽기 감사는 새 physics/force/geometry 조회0이다. runtime 전체12.522898CPU/11.784933wall(사전 checkpoint·검사 등 보수적 준비10초 charge 포함)에 읽기 감사0.241013CPU/0.243145wall와 보조2초를 더했다. 감사 이후 raw 재생산은 없다. 대화·문서·Git 대기를 source 시간으로 주장하지 않는다.

원문·checkpoint·명령·root/pose·매raw telemetry·journal·projection 비교는 지정 클라우드 Git 외부 비공개다. 공개는 기술 코드·hash·집계뿐이다. native/world/reset/행동·새 fullcold/FD/profile/solver·HOLDOUT/SEALED·유료 자원0이다. main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`,Participants·사용자 변경·기존 실패·백업·승인 종료2026-10-20 10:01:55UTC를 보존한다.

다음 하나의 미실행 제안

[단일 후속 제안](cause595_next_proposal.json)은 **같은 exact actual raw156에서 원537 feedback을12hold만 source로 시험**하는 것이다. 새 cold 정책은1..39의577 tape 뒤40부터 원537을 계속 사용하는 별도 정책으로 정의하고,이번 제안의 검사는40..51 구간만 한다. 기존551 paths/backup·안전·gain·cap·원537 finite trial/FINAL을 그대로 두며 형상·속도·threshold·solver sweep은 없다. 고정 tape가 수정된594 후보인 것처럼 소급하지 않는다.

질문은 현재 상태를 읽는 원 추종이 이 창에서 strict 국소 진행을 유지할 수 있는가다. 기존595/577 창은 저장 비교로만 재사용한다. 실제 source 적용48raw 외에도 최대12×32×48의 내부 예측을 모두 계수해 model 시도/완료18,480·force147,840·geometry40,000·총CPU480/wall645초의 **별도 미승인 상한**을 제안했다. 첫 no-safe-action/strict/domain/기술/비용 실패에 멈추고 다른 정책으로 구제하지 않는다. 통과해도 국소 source feasibility일 뿐 완주 시간·native·carry·incumbent 승격은 아니다. 이 제안의 source/native 실행은 모두0이며 자동 시작하지 않는다.
