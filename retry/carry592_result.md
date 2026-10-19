592 — 고정577 legacy carry source 선행 검증 실패

**SOURCE_CARRY_FAILED**다. actual-stored legacy before47에서 고정577 tape47..166을 그대로 적용한 한 번의 source 시험은 **hold48/raw4, global raw192 직전 force 검사**에서 ratio1.103131920309>strict1.059로 멈췄다.8raw를 시도해7tick만 완료했고 거절된 여덟 번째 tick은 적분하지 않았다. 공식 완주·episode≤14.46초·exact replay 게이트를 충족하지 못했으므로 replay는0회다. native 행동/reset/world도0이다. 정책을 재정렬·수정하거나 다른 후보로 구제하지 않았다.

이 carry 실패는 기존 **cold source13.20초 관측을 취소하지 않는다.** 다만 동일 유한 global-hold 정책의 combined cold+legacy-carry 선행 승격은 닫힌다.541 actual13.66초는 그대로이고577의 native 성능은 여전히 미측정이다.14.46초는541 source carry 관측이며 native carry 결과로 옮기지 않는다.500ms 문턱은 이번 게이트에 사용하지 않았다.

[실행 전 동결 계약](carry592_contract.json), [실측 결과](carry592_result.json), [저장 증거 감사](carry592_audit.json), [실행기](carry592_model.py)를 보존했다. source 시작 전 코드·runtime dependency·입력·전체 handoff를 hash로 고정했고 지정 클라우드에서 단일 실행만 했다. 이후 원 실행기·테스트·계약은 변경하지 않았다.

cold 증거 재확인과 handoff

577 tape SHA256 `bc432812cdd71702ec030edda72a9aa63ca79e61dceb1f970891a659f20cd5a6`을 직접 다시 확인했다.661raw/166commands·원 strict 실패 flag 부재·full8필드 checkpoint·저장 행에서 재구성한 최종 CP/명령 일치·현재 source 코드/입력 pin·STARTED 등록의 contract hash를 읽기로 검사했다. 기존577 journal 전체71,713event chain도 새로 읽어 검증해 기존 head·event·kind와 정확히 같았다. **중복 cold source는0tick**이다. 이는 기존 독립 cold 재현 증거를 재사용한 것이며 native 검증이 아니다.

legacy before47 root와46 after root가 정확히 같고 checkpoint SHA는 `f214ec85a254121a332a5c4347b61efda6fb00cdbbed2bd9a716038dcca701b0`이다. old518 close80의 누적1,149raw 뒤 둘째 reset51raw+drive184raw로 실제 raw1384를 식별했다.591에 고정한 실제 raw hash도 일치했다. 옛184개 실제 raw에서 contact로 visited를 누적하고 force ratio>1로 이력을 읽어 계산해 ledger와 대조했다. 새 물리·기하 질의는 이 단계에 없다.

시작은global raw184/다음hold47, visited43, tracking[0,352], 원 launch[46,384]다. 실제 저장 tracker의 모든 필드와 실제 clock4.699999999999988초를 사용했다. elapsed는 `actualclock−1.02 = 3.6799999999999877`초로 고정했고3.68로 반올림하지 않았다. replay에도 같은 시작값을 복제하도록 구현했다. 기존541 source의 `tracker_for(carry=True)` departure 재구성을 호출하지 않았으며 실제 저장 tracker를 기준으로 한 별도 carry 질문이다. frozen complete handoff SHA256은 `bb557b163aac370e78e4b9c42d01c64d5bcbf2dcb0ac116cc6b3b051c648f0fd`다.

global hold index47..166만 반환하는 유한 float32 정책으로 고정했다. tape1 재시작,progress 정렬,feedback/chooser,조향·pedal 보정,마지막 명령 연장,167번째 명령은 없다. 시작 metadata의 progress는 등록551 reference로 한 번 projection하되 물리 root·실제 tracker·clock·visited·두 이력은 바꾸지 않았다. 초기 root 자체의 footprint/path/reference/body도 먼저 검사했다.

|초기 current root 진단|관측|
|---|---:|
|footprint margin|2.965300764m|
|path error|0.299295979m|
|reference excess|−16.551677086m/s|
|body speed|38.843039002m/s|

원 strict evaluator와 첫 실패

기존 `late568.Study.raw`를 변경 없이 사용했다. carry는hold47부터이므로 tracking force≤1.059, 모든 누적 prefix clipping≤10%, footprint≥.50m,path≤3m,reference excess≤4.85m/s,body<100,원 projection·visited·공식 FinishLineTracker를 적용했다. ratio>1과 clipping identity를 그대로 판정했다. source wheel response 외부·내부 호출을 별도로 계측하고 force verdict를 내구 기록한 다음에만 tick하도록 했다.

|항목|결과|
|---|---|
|첫 거절|hold48/raw4, global raw192의 pre-force|
|거절 force peak / 허용치|1.103131920309 /1.059|
|거절 raw의 proposed tracking|2/384|
|실제 commit된 마지막 tracking|1/380|
|완료된 마지막 global raw|191|
|마지막 완료 episode 시각|3.819999999999988s|
|공식 finish timestamp|미관측|
|조건부 replay|0회|

거절된 force는 계산·차감했지만 tick·현재 상태·누적 history를 commit하지 않았다. proposed2/384는 거절 진단이며 실제 committed history는1/380이다. 실제로 실행한7raw의 최대 force ratio는1.009789999785,최소 footprint margin1.675898929m,최대 path error0.486258374m,최대 reference excess−13.503722961m/s,최대 body40.448720734m/s다.1.10313을 실행한 궤적의 힘으로 보고하지 않는다. 원시 vectors/actions/root는 공개하지 않는다.

이번 결과는 finite tape가 이 특정 legacy handoff에서 원 source 안전을 유지하지 못한다는 증거다. 실패 뒤 continuation,완주 시간 추정,carry 전용 feedback 패치 또는 native 시도는 없다. cold 전용 명령열의 일반 carry 적응성·방법군 전체의 가능성·불가능성으로 확대하지 않는다. strict source 한계1.059보다 크지만 실제 physical1.25보다 작다는 이유로 거절을 통과시키지 않았다.

비용·예약·감사

실행 전에 carry 최대480raw와 replay 최대480raw,각 case30CPU/45wall,source 합60CPU/90wall을 고정했다. carry 동안 replay480raw/481geometry/30CPU45wall을 예약했고 준비·검사·등록·감사는 별도60CPU/90wall,그 안에서 마지막 감사5CPU/10wall을 예약했다. 전체120CPU/180wall 및 승인 종료2026-10-20 10:01:55UTC를 유지했다. 상한 변경이나 자동 연장은 없다.

|계수|실제|전체 상한|
|---|---:|---:|
|source raw 시도 / 완료tick|8 /7|960 /960|
|외부 / 내부 wheel response|32 /28|3,840 /3,840|
|force 총합|60|7,680|
|geometry pack|8 = current root1 + 완료 후7|962|
|source CPU /wall|0.217302 /0.241042초|60 /90초|
|준비·테스트·등록·감사 CPU /wall|17.433946 /16.924472초|60 /90초|
|전체 CPU /wall|17.651248 /17.165514초|120 /180초|

준비·감사에는 시작 전 읽기 작업의 보수적10초 charge,import·사전 순수 검사·등록·cold journal 전체 읽기·pin/legacy 검증·최종 runtime chain 검사와 source0 후처리를 포함했다. runtime 전체15.477619CPU/14.991881wall에 후처리 감사0.173629CPU/0.173633wall과 보수적 보조2초를 합산했다. 대형 입력·journal hash도 측정 종료 전에 포함했다. 문서·대화·Git 대기 시간을 과학 계산 비용으로 주장하지 않는다.

63event runtime journal chain과 모든 pin이 맞았다. BEFORE_FORCE/FORCE_VERDICT/RAW_ATTEMPT8,BEFORE/AFTER_TICK/RAW_VERDICT7,current/post geometry8을 실제 호출 수와 대조했다. pre-force 거절1개가 attempt−completed1과 일치하고32=4×8,28=4×7이다. source domain이나 기술/비용 검열이 아닌 **정상 strict force 실패**다. 순수 정책 범위·clone/clock 격리·replay 게이트 검사4개,최종 source0 감사21개 모두 통과했다. 감사 중 새 source/force/geometry는0이다.

새 FD/profile/feedback/solver,native actions/reset/world,HOLDOUT/SEALED/새 조건/별도 유료 자원은0이다. 연구22,758·reserve84,000/사용0과 cold source13.20·actual13.66을 유지한다. 다음 native 네 world 비교는 선행 carry 게이트 실패로 진행하지 않는다. 별도 새 정책이나 실험 제안을 자동 생성하지 않는다.

원시 명령·state·tracker·legacy raw·journal·frozen handoff는 Git 외부 비공개에 보존했다. 공개는 기술 코드·계약·해시·집계·이 보고서뿐이다. main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`,Participants·사용자 변경·기존 실패·백업·590 종료 판정을 보존했다.
