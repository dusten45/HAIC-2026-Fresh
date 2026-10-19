598 — cold-only native 13.22초, fresh541 대비22raw/440ms 개선

**같은 지정 실행기에서 fresh541 baseline이 공식683raw/13.66초를 재현한 뒤,597 정책 하나가 native 공식661raw/13.22초에 안전 완주했다.** 두 world 모두 초기 full identity 일치·안전 flags 없음·close 후 body/joint0이다. 후보의 확인은662raw/13.24초이며,이 확인 시간을 공식 기록과 혼동하지 않는다. gain은 freshbaseline−candidate의 공식 integer raw22개,440ms다.500ms 문턱은 적용하지 않았다.

|검증 종류|정책|공식 integer raw|시간|
|---|---|---:|---:|
|이번 fresh native baseline|unchanged541|683|13.66초|
|이번 fresh native 후보|577 prefix39 뒤 원537 feedback|661|13.22초|
|기존 verified source|597 정책|661|13.22초|
|기존 verified source|고정577|660|13.20초|

반복 baseline은 새 개선으로 세지 않았다. source57713.20초는 native 완주 기록이 아니다. 이 결과는 **한 승인 초기화의 privileged full-state DEV cold-only 진단**이며 pixel 정책·Agent.act5초·다른 초기화·carry/combined/general 승격은 모두 닫혀 있다.11초대 목표는 아직 달성하지 못했다. 전체 정책 묶음의 비교이며 prefix/path/feedback 각 성분의 기여를 분리한 인과 실험은 아니다.

사전 동결과 전환 horizon

[계약](cold598_contract.json),[순수 검사19개](cold598_tests.json),정책·입력·runtime/code hash를 모든 world 전에 동결했다.593/594의 State→asdict 직렬화,fsynced hash journal,예약과 실제 dispatch의 분리,모든 기존 source/native 안전 기준을 재사용했다. main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`,Participants·기존 사용자 변경/백업·593~597 실패와 비용을 유지했다.

실제 후보는577의 정확한 float32 명령1..39 뒤40부터 매 hold 실제 native root·실제 이력에서 원537을 새로 선택했다.52 이후나166 이후 고정 tape 복귀는 없다. 원551 paths/backup/reference/cap·물리·finite31trial+새 FINAL은 바꾸지 않았다. 후보는 고정 prefix39회와 실제 feedback chooser127회를 실행했다.

prefix 인증의 미래 의미도 사전에 분리했다. 실제 현재 root/tracker/visited/clock/이력에서12개의 **outer hold**를 예측한다. 미래39까지는 정확한 고정577 명령이고,미래40에 닿으면 그 **예측 상태·예측 누적 이력**에서 원537을 한 번 선택하여 새 FINAL을 요구한다. 이후 outer 미래41+는 원537 인증기와 같은 backup continuation이다. 실제 native40+는 매 hold 다시 선택한다. 이 backup은 유한 admission witness이며 미래 실제 정책의 명령 전체가 같다는 주장이 아니다.

미래40의 내부 원537 인증은40..51까지 뻗을 수 있어 outer horizon보다 길 수 있다. 원537 내부 미래는 원래 backup이므로 recursive chooser는 없다. 전환 anchor는 prefix29..39에서 한 번씩,총11회였다. 실제40·52·166·167·294가 실제 root/history로 재선택하며40+ 고정 tape를 읽지 않는 순수 검사를 실행했다. 전환 구현/비용이 불명확한 채 world를 만들지 않았다.

매 실제 action 전에 새 인증과 원4raw constant-action 물리 예측을 계산하고,actual state hash 불변을 확인했다. prefix clone/anchor·모든 거절 trial/FINAL·4raw preview·native oracle/COM을 모두 새 비용으로 계수했다. tracking 계측5713개 summary가 원537의 수치/이유와 정확히 일치했다. launch는 원540의 buffered clip/phase-aware 인증과 새 FINAL을 유지했다. 매 실제 native raw에는 원 sensor/material/payload/observation/collision/damage/force/COM/예측오차/footprint/path/reference/projection/body 게이트를 적용했다. Detailed PATH/역방향·순방향 projection flags와 delta/양쪽 한계를 기록했다.

|실제 native 안전 집계|fresh baseline|후보|사전 native 기준|
|---|---:|---:|---|
|최소 footprint(m)|0.527154583|0.535201051|≥0.25|
|최대 path error(m)|1.509340762|1.606746942|≤3|
|tracking force peak|1.058899122|1.058950660|≤1.25|
|tracking prefix clip 최대|10.000000%|9.868421%|≤10%|
|launch force peak|2.403901738|2.403901738|≤2.5|
|launch24종료 clip|55/384=14.322917%|55/384=14.322917%|≤15%|
|reference excess 최대(m/s)|4.848802621|4.849682179|≤5|
|body 속도 최대(m/s)|95.756305295|96.927127713|<100|
|source force oracle vector 오차 최대(N)|0.000314494|0.000318391|≤0.05|
|COM impulse 오차 최대(m/s)|0.000024550|0.000024790|≤0.01|

후보4raw 예측 오차 최대는 position0.000036876m,speed0.000114399m/s,angle0.000032027rad,yaw0.000264703rad/s,force ratio0.000220425로 모두 원 한계 안이다. 런타임 flags뿐 아니라 저장 native 수치·누적 이력을 [읽기 산술 검토](cold598_review.json)에서도 다시 확인했다. 이 오차 집계는 해당 관측들의 최대이며 보편적인 model-error bound가 아니다.595의 고정 명령 forecast PATH 실패를 native 실제 PATH 실패로 바꾸거나 기존594를 소급 통과시키지 않았다.

비용·원장·감사

|계수|실제598|사전 전체 상한|
|---|---:|---:|
|world /reset /closed|2 /2 /2|각 world/reset2|
|native raw 예약 /dispatch /완료|1447 /1447 /1447|2450|
|native 행동 차감 /dispatch|337 /337|588|
|native wheel 예약 /관측|5788 /5788|9800|
|model 시도 /완료|133683 /131073|각180000|
|외부 /내부 force|540112 /524292|730000 /720000|
|force 합계|1064404|1450000|
|geometry margin/projection pack|383406|600000|
|실행 CPU /wall(초)|2792.694044 /3013.739498|3600 /4200|
|준비·검사·등록·분석·감사 CPU /wall(초)|67.943748 /67.182666|180 /240|
|전체 CPU /wall(초)|2860.637792 /3080.922164|3780 /4440|

baseline은171행동·683drive raw+51reset/warmup=734raw,후보는166행동·662drive raw+51=713raw다. 각각 source model69462시도/68108완료와64221시도/62965완료를 소비했다. baseline의 model 시도/완료는 기존594 baseline과 정확히 같고,실제683raw/안전/초기 identity를 새로 재현했다. 추가 baseline이나 후보 재시도는 없다.

총 model 구성은 원540/537 certificate 시도130463/완료127853,prefix outer1872/1872,4raw preview1348/1348이다. 시도−완료2610은 tick 전 거절이다. 원540의 filter443·full139,tracking5713 합계6295certificate와 고정 prefix39certificate를 모두 계수했다.4raw preview는 실제 마지막 action이 부분 종료해도 원래4틱을 계산하므로 driveraw1345보다3틱 많다. native oracle1345group×4=5380이 외부 force에 포함된다.

geometry383406에는 내부 nominal/steering111931회,source footprint136059회,tracking projection113882회,launch projection13971회,prefix projection1872회,4raw preview1348회,native/초기 projection2896회,native clearance1447회가 포함된다. 계약의 high-level pack 단위다. 모델/엔진 내부 contact 계산은 tick/raw 비용에 포함한다. [사후 읽기 검토](cold598_review.json)는 별도 native 입력 센서 contact 조회4×1447=5788회도 보수적으로 더해 **389194회**임을 확인했다. 두 arm도200313/188881회로 각300000 이내다. 이 추가 집계는 원 계약·원 결과를 수정하거나 새 gate를 만든 것이 아니다.

다음 hold는 전환 최대1588model(32×48anchor+48outer+4preview),일반 feedback1540,cheap prefix52를 선예약했다. native oracle/실제4raw/wheel,geometry5000(cheap300),hold60CPU/75wall+close5CPU/10wall와 종료감사30CPU/45wall를 예약했다. 위 센서 조회까지 포함한 보수적 geometry 최악4671+16=4687회도5000 안이다. 처음부터 두 arm90000model씩과CPU2000/1600,wall2300/1900을 확보했다. 원 kernel hardcap200000,TimeLimit1224·warmup50·reset 내부1틱·최대drive1174/294hold를 유지했다.

행동 호출 전에 연구22548에서337회를 차감했다. **잔액22211,reserve84000/사용0**이다. 예약/dispatch/완료가 분리되어 있으며 실패/부분 호출을 환불하거나 모델 예측을 native 호출로 세지 않는다. 원문·raw·명령·지도/seed·전체 상태/추적기/영상/journal은 지정 클라우드 Git 외부 비공개이고 공개는 기술 코드·hash·집계다. 다른 환경·추가 유료 자원·새 seed/HOLDOUT/SEALED/carry·FD/solver0이다.

[실측 결과](cold598_result.json),[읽기 감사](cold598_audit.json)를 보존했다.675921event chain,입력/코드/runtime pin,비용·전환·누적 이력·예약/dispatch·close·integer gain·보호 파일·미승격 등26개 감사가 모두 통과했다. 외부 감사19.261584CPU/19.278514wall과 보조5초가 위 합계에 포함된다. 사전 준비 보수적10초,모든 import/test/hash/IO/초기화/cleanup도 계수했다. 사후 저장값 산술0.097초는 보조5초 범위다. 문서/Git 대기를 simulation 시간으로 주장하지 않는다.

연결 알림과 남은 경계

09:42UTC 연결 알림 뒤에도 원래 PID36837이09:38:16UTC부터 실행 중이고 journal/비용/진행 파일이 증가함을 확인했다. 중단 문자·재실행·다른 환경 전환 없이 **그 단일 프로세스**의 결과를 회수했다. 두 번째 world는 원래 계약의 freshbaseline 게이트 후에만 열렸다. 모니터 회수 증거는 비공개에 보존하고 결과 hash에 포함했다. 마지막에는 과학 프로세스가 종료하고 두 world가 body/joint0임을 확인했다.

이 cold-only native 양성 결과와22raw gain을 보존한다. carry/combined/general 승격과 일반 incumbent 변경은 하지 않았다. 다음 판단 경계는 pixel 관측과실제 act5초 제약,11초대 병목이다. 추가 native·carry·새 초기화 실험은 시작하지 않았다. 승인 종료2026-10-20 19:01:55KST/10:01:55UTC를 유지하며 자동 연장은 없다.
