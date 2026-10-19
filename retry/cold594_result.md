594 — 직렬화 복구 후 baseline 재현, 고정577 cold 후보는 미래 인증 거절

**baseline은 안전하게 공식683raw/13.66초를 재현했고, 후보는39행동·156raw 후 다음 행동의 미래12hold 인증에서 거절됐다.** 최종 상태는 `CANDIDATE_CERTIFICATE_REJECTED`다. 후보40번째 행동은 실행하지 않았다. 후보의 native 공식 완주 시간·양의 개선은 관측하지 못했으므로 source57713.20초를 native 성과로 옮기지 않는다. 실제 실행한 후보 prefix는 안전했으며, 이번 중단은 실제 물리 안전 위반·직렬화 오류·비용 검열이 아닌 **사전 source 미래 인증 실패**다.

592 carry 실패와 combined/general 승격 종료를 그대로 유지한다.594 안의 재시도·feedback/fallback·재정렬·tape 연장·추가 실험은 없다. [사전 계약](cold594_contract.json), [원 결과](cold594_result.json), [감사](cold594_audit.json), [거절 해석](cold594_rejection_review.json)을 남겼다.

수정 범위·시작 전 검사

593의 실패 실행기·계약·결과·비용은 변경하지 않았다. 새594는 승인된 별도 복구 실행이다. 실제 `State` dataclass를 먼저 `asdict`로 바꾼 뒤 기존 `plain`을 적용하도록 [입력 로그 직렬화](cold594_logging.py)만 수정했다. 정상 행동과 reset의 `action=None` payload 전달은 기존 값 그대로다. AST 비교에서 native arm은 이 직렬화 호출만 달랐고 정책·물리·안전·meter·예약 메서드는 동일했다.12개 미래 명령 인증기는 기존593 파일을 그대로 재사용했다. [변경 범위 증거](cold594_change_review.json)에 원·새 runner hash와 원593 비용을 따로 보존했다.

world 없이 실제 State/Wheel dataclass·중첩 NumPy 값을 사용해 JSON roundtrip,reset None/정상 행동 로그,직렬화 예외·fsync 실패 시 physics stub 미호출,raw 예약/완료 분리,내구 기록 이후에만 stub 실행을 검사했다. 기존 payload/horizon·launch/tracking·official integer clock 검사까지 **9개 모두 통과**했다. [검사 결과](cold594_tests.json)는 실제 source/native/world/force/geometry 호출0인 순수 회귀 결과다. 이후 구현·입력·runtime/dependency binary·font 및 검사 hash를 새 계약으로 동결했다.

577 cold의 기존661raw/166commands·full checkpoint·exact 독립 검증·코드/입력 pin·STARTED 계약·71,713-event journal chain을 읽기로 확인했고 중복 cold source는0이다. 고정 tape SHA256은 `bc432812cdd71702ec030edda72a9aa63ca79e61dceb1f970891a659f20cd5a6`이다. 최초594 시작 뒤 원 runner/helper/입력·runtime pin을 바꾸지 않았다.

native 절차와 결과

동일 승인 DEV 초기화에서 원541 paths/backup·540 launch·537 tracking 및 새 FINAL을 유지한 baseline을 먼저 한 번 실행했다. 초기 full identity·기하/장애물·51raw reset을 확인했고 공식 finish683raw와 실제 drive683raw 모두 일치했다. 그 뒤 같은 기존 실행 프로세스의 사전 조건부 흐름으로 고정577 후보 한 번만 실행했다.

후보는 실제 root·launch/tracking 이력·전체 visited·실제 tracker·clock의 독립 복제에서 다음12hold의 서로 다른 고정 tape 명령을 새 인증했다. launch1..24는force2.5/clip15%(24 완료 때)/reference 진단,25+는force1.059/누적clip10%/reference4.85이며 모든 단계 source footprint.50/path3/body<100과 원 projection을 유지했다. 현재 행동의4raw 예측과 실제 native 오차도 비교했다. 가상 confirmation과 live 종료는 분리했고,actual physical1.25/reference5/footprint.25·collision/damage·oracle/COM·모든 예측 오차 문턱을 완화하지 않았다.

|실제 native 관측|fresh541 baseline|고정577 후보|
|---|---:|---:|
|초기 identity / reset raw|통과 /51|통과 /51|
|행동 시도·완료|171|39|
|drive raw|683|156|
|공식 finish integer raw /시간|683 /13.66초|미관측|
|마지막 실제 episode 시각|13.66초|3.12초|
|최소 footprint margin|0.527154583m|0.953029038m|
|최대 body speed|95.756305295m/s|83.548017952m/s|
|최대 path error|1.509340762m|1.606746942m|
|최대 tracking reference excess|4.848802621m/s|4.596446074m/s|
|launch force peak /clip|2.403901738 /55/384|2.403901738 /55/384|
|tracking force peak /최종clip|1.058899122 /65/2348|1.058766732 /15/240|
|최대 tracking 누적clip 비율|10.0%|6.25%|
|oracle vector /COM impulse 최대오차|0.000314494N /0.000024550m/s|0.000188487N /0.000017252m/s|
|최대4raw position /speed 예측 오차|0.000040221m /0.000110103m/s|0.000036876m /0.000062646m/s|
|최대 angle /yaw /force-ratio 오차|0.000028487rad /0.000243561rad/s /0.000179066|0.000032027rad /0.000264703rad/s /0.000220425|
|실제 raw flag /최종 body,joint|0 /0,0|0 /0,0|

baseline의 모드 횟수·힘·여유·오차도 기존541 관측 집계와 같다. 후보는 완주하지 않았으므로3.12초를 랩 시간·DNF 시간이나 절감량으로 쓰지 않는다.500ms 조건은 없었지만 양의 공식 integer finish gain 자체를 측정하지 못했다. incumbent은 바꾸지 않았다.

40번째 행동의 인증 거절과 기록 한계

실제156raw 완료 상태에서 global hold40..51의 고정 명령12개를48model tick 예측했다. 마지막 미래 raw는 인덱스 산술상 global204다. 인증은 `GEOMETRY_PATH_PROJECTION`으로 반환돼 hold40의 `env.step` 전에 멈췄다. 실제 prefix의 running history15/240은 유지됐으며 예측29/432를 실제 이력으로 commit하지 않았다.

예측 tracking peak1.058822543≤1.059,예측 clip29/432≤10%,최소 예측 footprint0.512899591m≥0.50m였다. 코드의 해당 복합 조건은 footprint/path/projection을 묶지만 **이번 저장된 최솟값으로 footprint 위반은 제외된다.** 따라서 path error>3m 또는 progress delta가 `[-.5,max(5,2×COM step distance)]`를 벗어난 분기다. 세부 실패 distance/delta는 원 인증 summary에 저장되지 않아 어느 하나로 단정할 수 없다. compact model journal은 state hash를 저장하므로 새로운 physics/geometry/replay 없이 그 세부값을 복원할 근거도 없다. 이 한계를 숨기거나 새 계산으로 구제하지 않았다.

이것은39행동 실제 prefix에서 물리 안전 위반을 관측한 결과가 아니며,테이프 전체 native 완주가 물리적으로 불가능하다는 증명도 아니다. 정해진 **실제 상태 기반 미래 인증 게이트를 통과하지 못해** cold-only 비교가 완결되지 않은 결과다. 순수 source full cold 안전13.20초와 native에서의 fresh 미래 인증은 다른 질문이다. source 시간·보간 시간·안전한 짧은 prefix를 완주 개선으로 환산하지 않았다.

연결 장애와 기존 실행 회수

모니터 도구에 `exec-server transport disconnected`가 발생했고 parent도07:57UTC 연결 끊김을 알렸다. 마지막 확인 baseline39행동/156raw 이후,연결 복구 시 **기존 native Python PID34847**이 살아 있고66행동/264raw의 내구 진행 기록이 이어짐을 확인했다. 새 runner·재시작·복제 arm을 호출하지 않고 기존 프로세스 결과만 회수했다.

장애 중 기존 세션에 보낸 중단 문자의 전달 방식은 확정할 수 없다. 원 명령 세션은 이후130을 반환했지만 Python PID는 계속 진행했다. 이후 프로세스는 원래 동결된 순서대로 baseline을 완료하고 조건부 후보를 실행한 뒤 인증 거절에서 종료했다. 최종 journal·모든 입력/runtime pin·연속 counters·두 world cleanup을 회수했고 프로세스 종료도 확인했다. 세션 종료코드를 native 과학 실행 종료로 잘못 해석하지 않았다. [연결 회수 증거](cold594_transport_review.json)에 prefix snapshot과 최종 결과 hash를 구분해 보존했다.

비용·원장·감사

|계수|실제594|사전 상한|
|---|---:|---:|
|world /reset /close|2 /2 /2|각2|
|native raw 시도·완료|941 =683+156+51×2|2,450|
|행동 시도·완료|210 =171+39|666|
|model raw 시도 /완료tick|71,538 /70,184|각100,000|
|외부 /내부 model wheel force|289,508 /280,736|450,000 /400,000|
|model force 총합|570,244|850,000|
|실제 native wheel|3,764|9,800|
|geometry pack|73,600|110,000|
|과학 실행 CPU /wall|1,327.024303 /1,406.957614초|3,000 /3,300초|
|준비·검사·등록·감사 CPU /wall|22.556207 /21.809792초|120 /180초|
|전체 CPU /wall|1,349.580509 /1,428.767406초|3,120 /3,480초|

모든 실제 `env.step`210시도를 호출 전에 fsync 차감해 **연구22,758→22,548**이다. 실패·부분·terminal 행동을 환불하지 않았다. 거절된 hold40은 인증 계산만 했고 `env.step` 시도가 없어 행동 charge는 없다. reserve84,000/사용0을 유지한다. 원593의world/reset 시도 각1·raw 예약1/wheel 예약4·actual raw/행동0·기존 전체CPU18.754894/wall17.593764초는 별도 그대로 보존하며594의 성공이나환불로 바꾸지 않는다. 승인된 복구의594 world2와 합쳐 과거 world 시도를 지우지 않는다.

model 시도−완료1,354는 baseline의 pre-force 거절이다. 외부289,508=4×(model 시도71,538+native oracle839),내부280,736=4×완료70,184,실제 native wheel3,764=4×941이다. geometry73,600은 model 완료70,184−현재 행동4raw 예측840+baseline 인증 current roots3,275+후보 인증 current roots40+native raw941로 대조했다. 후보40인증×48future raw+39행동×4현재 예측=2,076model tick이며 거절된 미래48tick도 모두 포함한다.

286,804-event runtime journal chain을 검증했고,후속 읽기 감사34개에서 sequence/kind/head·코드/입력/runtime pin·State 회귀·명령 bytes·원장·native flags/힘 이력·호출/기하 계수·cleanup·상한·원593 보존·중복 arm 부재가 모두 통과했다. 모니터 장애 구간의 비용이나 호출을 추정으로 채우지 않았다. source0 감사는 새 source/native/force/geometry 호출0이다. runtime 전체CPU1,346.303745/wall1,425.486735초(보수적 시작 준비10초 포함)에 읽기 감사1.276765CPU/1.280671wall와 보수적 보조2초를 합산했다. 대화·편집·Git 대기는 과학 비용으로 주장하지 않는다. 기존 kernel hard cap200,000은 변경하지 않았다.

추가 carry/native 재시도·새 condition/HOLDOUT/SEALED/profile/FD/solver/유료 자원0이다. 일반·pixel·carry 안전이나 combined 승격 주장은 없다. 원문·case/seed·state·명령 bytes·관측/RNG·raw journal은 지정 클라우드 Git 외부 비공개이며 다른 Codex 작업으로 전송하지 않았다. 공개는 기술 코드·계약·hash·집계·이 보고서다. main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`,Participants·사용자 변경·기존 실패/백업·592/593 기록을 보존했고 승인 종료2026-10-20 19:01:55KST를 연장하지 않았다. 다음 실험이나 정책 수정은 시작하지 않는다.
