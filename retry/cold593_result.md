593 cold-only native 진단 — baseline 초기화 중 기록 구현 오류로 종료

**BASELINE_TECHNICAL_FAILURE_CANDIDATE_NOT_STARTED**다. 첫 baseline world의 reset 내부 첫 raw 진입에서, 내구 기록의 `before_state=plain(before)`가 dataclass `State`를 직렬화하지 못해 `TypeError:UNSUPPORTED_JSON:State`로 종료했다. 실행기 구현 오류이며 native 안전 위반이나577 성능 실패가 아니다. **541 baseline의683raw/13.66초 재현도,577 native 효과도 이번에 검증하지 못했다.**

world/reset은 이미 시작됐고 STARTED가 있으므로 이번 계약의 import-only 복구 예외에 해당하지 않는다. 원 코드·계약·등록·실패·부분 counter를 보존했고 수정 후 재실행이나 새 world 시도는 하지 않았다. candidate·carry는 시작하지 않았다. 592의 carry strict 실패와 combined 승격 종료를 유지한다. 이 좁은 cold-only 질문은 기술 blocker로 미해결 상태다.

[사전 동결 계약](cold593_contract.json), [원 실행 결과](cold593_result.json), [기술 종료 감사](cold593_closeout.json), [동결 실행기](cold593_native.py), [고정 미래 tape 인증기](cold593_certificate.py)를 남겼다. 공개 결과의 최상위 `error:null`은 성공을 뜻하지 않는다. arm의 `stop=TECHNICAL_FAILURE`, `error=TypeError:UNSUPPORTED_JSON:State`가 실제 종료 원인이다. arm의 maximum 값0·빈 flags도 안전 통과 측정값이 아니라 초기화 기본값이다.

동결한 질문·절차와 실행 전 확인

이번 요청은 기존 DEV의 privileged full-state cold-only 진단이었다. 기존541 cold baseline 한 번을 안전하게 공식683raw 및 완료drive683raw로 재현할 때만 고정577 cold 명령1..166을 한 번 실행하도록 했다. 양의 actual 개선은 fresh baseline보다 작은 공식 finish integer raw만 인정하고500ms 문턱이나 source 보간 시간을 쓰지 않도록 고정했다. 결과가 좋아도 general/carry/combined incumbent으로 승격하지 않는 별도 질문이었다.

baseline은 원541 cap90 paths·backup,540 launch 및537 tracking/FINAL을 유지했다. wrapper/환경/core/control 코드와 approved case·기하·입력 pin,Python·Box2D·NumPy/OpenCV/Pygame 및 로드된 runtime/dependency binary·font hash,headless SDL 설정을 첫 source/native 생성 전에 등록했다. 후보는 원577 float32 bytes 그대로이며 reindex·fallback·feedback·167번째 명령 경로가 없다.

candidate 인증기는 actual root·실제 두 clipping history·전체 visited 집합·실제 tracker 전 필드·clock의 독립 복제에서 다음12hold의 **서로 다른 고정 미래 명령**을 순서대로 평가하도록 작성했다. launch1..24는2.5·15%(hold24 완료 때)·reference 진단,tracking25+는1.059·prefix10%·reference4.85,전 단계 footprint.50/path3/body<100을 적용한다. 경계를 걸치는 예측도 global index로 구분한다. 가상 official confirmation에서 인증을 닫되 현재 명령4raw의 동역학 비교 자료는 별도로 확보하며 live 종료는 실제 tracker만 따르도록 했다. 이 구현은 정적 검토·순수 검사만 했으며 실제 후보 인증 성공으로 보고하지 않는다.

실행 전577의 유효661raw/166commands·exact/full CP artifact·입력/source pin·기존 journal71,713event chain·STARTED 계약 등록을 읽기로 확인했다. tape hash는 `bc432812cdd71702ec030edda72a9aa63ca79e61dceb1f970891a659f20cd5a6`이다. 중복 cold source는0이다. legacy592 carry 실패가 닫힌 상태도 확인했다. 순수 payload/horizon/launch→tracking/official integer clock 검사4개는 통과했으나, 이 검사들은 실제 dataclass 로그 직렬화 경로를 다루지 않아 이번 구현 오류를 잡지 못했다. 사전 읽기 검토도 이를 놓쳤다.

오류 위치와 실행되지 않은 연산

`env.reset`→원 `CarRacing.reset`→내부 `self.step(None)`의 감시 wrapper 순으로 진입했다. wrapper가 raw 의도1·wheel 최악 예약4를 메모리 counter에 반영한 뒤 `BEFORE_NATIVE_RAW` 이벤트의 인자를 만들다가 실패했다. `plain`은 dict/list/tuple/NumPy 등을 처리하지만 dataclass 자체는 지원하지 않는다. 그 결과 **이 BEFORE 이벤트는 fsync되지 않았고 `original_step(action)`과 native physics/force trace는 호출하지 않았다.** 기록 전 실패가 실제 raw 실행으로 이어지지 않았다는 점을 코드 순서·traceback·journal로 대조했다.

|단위|시도/예약|실제 완료·호출|
|---|---:|---:|
|world|1|생성1,close1|
|reset|1|완료0|
|native raw|precharge1|original step 호출0,완료0|
|native wheel|최악 예약4|관측된 실제 계산0|
|env.step 행동|0|0|
|model raw 시도/완료|0|0|
|외부/내부 model force|0 /0|0 /0|
|source/native geometry pack|0|0|
|candidate/carry|0|0|

reset51raw 조건·initial full identity 확인 지점에는 도달하지 못했다. 따라서 초기 identity 불일치를 관측한 것도 아니다. nativewheel 예약4를 실제 계산4로 바꾸거나 raw precharge1을 삭제/환불하지 않는다. 실패 후 `finally close`를 수행했고 body=0/joint=0을 확인했다.

journal에는 WORLD_RESERVE·WORLD_CHARGED·RESET_CHARGED·WORLD_CLOSED의4event가 있고 chain/head와 최종 counters가 맞는다. raw precharge counter는 실패·최종 world 기록에 보존돼 있다. BEFORE_NATIVE_RAW 부재가 이번 직렬화 실패 위치와 일치한다. 완료 행동이 없으므로 연구 잔액22,758·reserve84,000/사용0은 변하지 않았다. 이는 환불이 아니라 `env.step` 시도 자체가0인 결과다.

기술 감사·비용·복구 금지

실행 뒤 별도 source0 감사에서 작은 synthetic `State` dataclass만 만들어 `plain(State)`의 같은 오류를 재현했다. `plain(asdict(State))`는 JSON roundtrip을 통과했다. 이는 직렬화 원인 확인이며 world/force/tick/geometry를 실행한 검사가 아니다. 수정 식은 감사에 기록했지만 **동결된 실패 실행기에는 적용하지 않았다.** STARTED/world/reset 이후 실패였으므로 같은 arm 또는 새 world를 재실행할 권한은 이번 계약에 없다. 별도 복구 실험이나 대체 후보를 만들지 않았다.

원 계약·모든 입력·구현/runtime hash,부분 journal4event,실제 raw 미호출 위치,counter/cleanup/원장·candidate 미시작·no retry·성과 미주장·보호 범위를 확인한 읽기 감사18개는 통과했다. 이는 실패 기록 감사의 통과이지 baseline 또는 후보 과학 게이트 통과가 아니다.

|비용|실제 합계|사전 상한|
|---|---:|---:|
|과학 실행 CPU /wall|0.013936 /0.015444초|3,000 /3,300초|
|준비·테스트·등록·감사 CPU /wall|18.740957 /17.578320초|120 /180초|
|전체 CPU /wall|18.754894 /17.593764초|3,120 /3,480초|

runtime 전체16.050078CPU/15.302740wall에는 import·등록·테스트·cold 증거 읽기·실패·cleanup과 보수적 준비10초 charge가 포함돼 있다. 이후 source0 감사0.704816CPU/0.291024wall 및 보수적 보조2초를 더했다. 모든 대형 hash 계산 후 감사 측정을 마쳤다. 대화·문서·Git 대기를 시뮬레이션 시간으로 주장하지 않는다.

사전 자원 상한은2world/2reset·raw2,450·행동666·model 시도/완료각100,000·외부450,000/내부400,000/총850,000·실제 native wheel9,800·geometry110,000이었다. baseline과 candidate를90k/10k model 및2,400/600CPU로 나눠 예약하고 각 hold의 최대 인증·4raw·oracle·기하·cleanup/audit도 예약했다. 기존 kernel hard cap200,000은 변경하지 않았다. 예산 부족이나 안전 실패가 아니라 첫 초기화의 직렬화 구현 오류로 중단했다.

결론·보존

기존 source57713.20초와 actual54113.66초는 서로 다른 기존 관측으로 유지한다. 이번에는 새 native 완주·gain·pixel 성능·일반화·carry 안전·combined 승격 결과가 없다.593 cold-only 진단은 미완료이며 재시도 없이 닫았다.

new condition/HOLDOUT/SEALED/profile/FD/solver/유료 자원0이다. 원문·raw state·seed/map/commands·영상/RNG·traceback·journal은 지정 클라우드의 Git 외부 비공개에 보존했다. 공개는 기술 코드·계약·hash·집계·이 보고서뿐이다. main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`,Participants·사용자 변경·기존 백업·실패·592 판정을 보존하고 승인 종료2026-10-20 10:01:55UTC를 연장하지 않았다.
