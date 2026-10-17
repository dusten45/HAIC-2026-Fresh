# 473 — pre23 자연 reference 비교: 두 arm 모두 안전 실패, 승격하지 않음

**같은 저장 pre23에서 whole arm을 각각 한 번 실행했고, Original/P4 모두 자기 model finish 전에 경로오차3m 기준을 넘었다.** 앞 구간부터 P4 reference를 그대로 쓰는 현재 후보는 안전 게이트를 통과하지 못했다. 양쪽 완료가 없으므로 전체 finish 이득은 null이다. native13.640초와 과거13.760초는 알려진 조건의 저장 관측이며, 이번 결과는 새 native·fresh pair·픽셀·일반화 승격을 제공하지 않는다.

| whole 모델 관측 | Original reference | P4 reference |
|---|---:|---:|
| 종료 | UNSAFE | UNSAFE |
| 행동 / raw ticks |81 /324|51 /204|
| 첫 raw 안전 실패(root 이후) |321 /6.42초|202 /4.04초|
| 첫 실패의 진행(root 이후) |386.447805m|278.292773m|
| 실패가 포함된80ms 행동 종료 |6.48초|4.08초|
| 최대 raw 경로오차 |4.759864m|4.003376m|
| 최대 요구 force ratio |6.132524|3.958907|
| clipped /wheel samples |120 /1296|82 /816|
| 자기 finish |없음|없음|

실패를 포함한 원래80ms wrapper를 보존하고 다음 행동은 호출하지 않았다. 다른 위치·시간 길이의 종료값이나 clipping 총수를 속도/성능 순위로 바꾸지 않는다. 중립·guardian 구제, 새로운 root·후보 탐색, 추가 tail·whole 반복·학습은0이다.

| 공통 안전 공간 경계 | Original 시간 bracket | P4 시간 bracket | Original−P4 |
|---|---:|---:|---:|
|root+60m|[1.58,1.60]초|[1.20,1.22]초|[+0.36,+0.40]초|
|root+120m|[2.42,2.44]초|[2.00,2.02]초|[+0.40,+0.44]초|
|root+180m|[3.06,3.08]초|[2.62,2.64]초|[+0.42,+0.46]초|
|root+240m|[3.86,3.88]초|[3.38,3.40]초|[+0.46,+0.50]초|

공통 경계까지의 시간 이득은 관측됐지만 뒤의 안전 실패와 별개다. root+180m 첫 crossing post에서 speed는 양쪽 약100m/s, raw 경로오차0.049513→0.055482m, force ratio0.868515→0.937475다. 같은 Original 미래 reference 기준 감속부채 최대/B proxy는0.674562→0.692800, 최소 거리 여유18.605908→17.100882m다. root+240m에서는 경로오차1.094805→1.107147m, force ratio0.796329→0.948380이다. 모든 공통 경계의 양쪽 속도·힘·경로·common/own reference 및 감속부채를 JSON에 분리했다. 감속부채는 미래 낮은 node에 대한 근사 진단이며 exact tyre feasibility 인증이 아니다. 양쪽 서로 다른 endpoint의 proxy를 직접 순위로 쓰지 않았다. 자기 finish 이후에는 reference/감속부채가 N/A가 되는 정의역을 유지했다.

root는 새로 탐색하지 않고453 baseline/candidate의 공통 pre23 full native snapshot을 exact 대조했다. 같은 state·before memory·GoalLedger·RNG pickle/digest에서 readonly nodes만 바꾸며 고정 line·feedback1.5·steering·80ms·SourceC phase·자기 마지막 node/terminal tracker를 유지했다. 첫 명령도 자연 point-FF다: 같은 steering−0.0137075353에서 Original은 brake0.2686997652, P4는 gas0.7267574668이었다. 강제 fullgas pulse0이다. Original 첫3명령만 저장 native와 float32 exact한 연속 prefix였고,13행동 물리·geometry·ledger replay 허용범위 검증은 별도다. P4 native factual 범위는0이다. 양쪽 root H13 독립2+held가 통과했고, 각 whole의13행동이 자기 fresh qualification과 exact 일치해야14번째 행동을 허용했다.

source1137ticks/35worlds +root216/6=1353/41, whole324+204=528ticks/2worlds, 합계 **1881ticks/43worlds**였다. 숨은 auxiliary0, 계획3458/43·hard4096/43 안이며 source observer raw1881을 비용 원장과 전수 대조했다. whole worker **CPU39.329450초/wall38.886211초**, 상한300/600 안이다. actual/reset/차감0이고 v476 연구26175·예비84000사용0을 그대로 보존했다. 12.260초 reference clock은 진단 설계이며11.99초 목표를 낮추지 않았다.

등록 전 geometry 논리 digest를 파일로 오인한 준비 오류1건을 적분0에서 기록·수정했다. 첫 정적 시도는56번째 fixture의 synthetic profile SHA mock 누락으로 멈췄고 CPU8.150360초/wall8.132329초, 실제 적분0이었다. 실패 plan/소스/로그를 보존한 등록revision2에서 fixture만 수정해 **62검사+저장 감사**가 CPU12.963139초/wall13.062047초로 통과한 뒤 물리 실행은 한 번만 했다. 시작10분 이내 적분0 checkpoint도 남겼다.

공간은 최신 모델 비율 최대93191.314B/tick×1.25, 최신 header779344B+source manifest 증가3558B의3배·미래4KiB·16KiB/world, hard4096/43, plan2MiB·metadata16MiB·검증temp32MiB·reserve512MiB를 포함했다. 새 raw forecast531217567B, `/tmp` 필요1101642911B 대비 free2483167232B로 통과했다. workspace metadata64MiB+reserve512MiB 필요603979776B 대비 free862547968B도 통과했다. 기존 원본/raw/archive의 삭제·이동·변환0, 새 archive0이다.

새 plain raw **347파일/140364368B**를 지정 실행기 `/tmp/haic-retry-stage473-private`에 한 벌 유지했다. 모든 파일을 두 차례 재개방해 전체 bytes·SHA·finite JSON/JSONL·중복 key 금지·lossless bytes codec/UTF8 text 구조와 manifest 일치를 확인했다. 보존CPU4.084606초/wall4.107753초다. workspace 비공개 영역에는 전체 plan98165B·입력678550B·전수 manifest·코드·버전 pins·RNG/재현 조건을 보존했다. **`/tmp` 소실 시 exact raw 재검증은 불가능하고 hash로 raw를 복원할 수 없다.** 공유·영속성을 가정하지 않는다.

등록 source/input370개·보호18파일·v476·main dfb7a2de2178825ca5c5ce20bab01ba67052ba31·공식 Participants·기존 사용자 변경과 백업을 보존했다. DEV만 사용했고 HOLDOUT/SEALED·새 seed·별도 유료 자원 사용0이다. stage441의 명시적 연장 근거와 최신 종료 **2026-10-20 19:01:55KST**를 유지한다. 추가 실행 없이 현재 후보를 닫았다.

[상세 수치·공통 경계](compare473_result.json) · [최종 gate](compare473_gate.json) · [raw 보존 검증](compare473_retention.json)
