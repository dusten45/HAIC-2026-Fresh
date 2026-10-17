# 442 — 동일 조건 fresh C0/P 실제 pair

결과 **FRESH_ACTUAL_PAIR_COMPLETED**. 유효 종료는 **2026년10월20일19:01:55 KST**다. 현재 승인 파일·v461·동결 plan·직접442 지시의 날짜를 실행 전에 대조했다. 440은 외부 SIGTERM 중단 그대로 보존하고, 그 미래 명령·미완료 결과를 이번 선택 입력이나 성능 추정으로 사용하지 않았다.

정적179개와 실제/model 적분 없는 통합 fixture가 통과했다. 실제 reset 전 저장 상태 재현·독립 repeat·현재 입력 복원·pending 게이트는 **1,137 ticks/35 worlds**로 통과했다. 439 기하 유도 비교 구간·goal-side/clock/age/deadline/DONE의 이산 정확 비교, 자기 charged ticket에서 native 사실 우선 commit, forecast 실패 후 다음 dispatch 차단을 유지했다. recipe·gain·H13/tail308·strict bracket·경로·조향·안전/진행 기준은 바꾸지 않았다.

| arm | 실제 행동 | prefix/suffix | 검증 suffix | 공식 lap | actual CPU초 |
|---|---:|---:|---:|---:|---:|
|C0|189|118/71|71|15.08초|73.816|
|P|173|118/55|55|13.76초|81.861|

새 pair의 양쪽 공식 완료 여부는 **True**다. 공식 event 차이 이득은 **1.320초**, raw tick bracket은 **[1.3, 1.34]초**다. 미완료 arm의 시간을 추정하지 않았다. 이 결과는 알려진 동일 시작 조건의 비교이며 픽셀 정책 승격·새 조건 일반화·공식 서버 성적·11초대 달성을 뜻하지 않는다.

C0: native 공식 event 16.100초, 확인 관측 16.120초. 실제 raw action ticks 755, reset ticks 51. damage 0.0, 전체 force ratio 최대 1.2319861938422425, clipped wheels 44/3020. progress 모델/실제 차이 최대 3.1413256692758296e-05m, 비교 구간 폭 최대 0.2637456063926038m. 클리핑 일치와 허용된 상태의 관측 후 검증을 범용 사전 안전 보장으로 확대하지 않는다.
P: native 공식 event 14.780초, 확인 관측 14.800초. 실제 raw action ticks 689, reset ticks 51. damage 0.0, 전체 force ratio 최대 2.0726140628591887, clipped wheels 145/2756. progress 모델/실제 차이 최대 1.9016656551684719e-06m, 비교 구간 폭 최대 0.21483157236457373m. 클리핑 일치와 허용된 상태의 관측 후 검증을 범용 사전 안전 보장으로 확대하지 않는다.

native fact·pre/post snapshot·ticket/clock·현재 query/context/memory/RNG 연결, 실제 ledger의 관측 유래와 모델 값 미commit을 저장 자료에서 다시 확인했다. 미래 모델 증거가 실제 DONE를 부여하지 않는다. 마지막 pending bridge와 guardian 증명2개를 저장 자료로 재검증했고, native 전에는 DONE=false이며 자기 native1tick 뒤에만 DONE=true가 된 것을 snapshot/ticket/ledger와 대조했다. 이 추가 저장 검사의 CPU0.442초는 별도이며 새 물리 적분은0이다. pending 경로 수와 own native 확인은 아래 JSON에 분리되어 있다. 저장436 비교는 실행 종료 후의 사후 진단이며 selection 입력이 아니다.

사전 상한은 실제 **416행동/reset2·exclusive CPU240초/wall480초**, 모델 **524,288 ticks/1,024 worlds·CPU1800초/wall2400초·순차1개**였다. 최악 모델 계산은 planner493,056 + guardian24,128 + qualification1,242 = **518,426 ticks/883 worlds**, 최악 실제 raw는 reset 포함1,766 ticks다. first error에서 전체 중단·추가 actual 재시도0을 유지했다.

실사용은 **362행동/reset2**, 실제 raw action1444 + reset102 = **1546 ticks**다. 모델은 **40269 ticks/461 worlds**, reserved40269와 대조했다. model observer 원문 40269 posts, 10224 action records가 원장과 일치한다. wrapper 행동·모델 tick·raw tick은 다른 단위다.

| worker 비용 범위 | CPU초 | wall초 |
|---|---:|---:|
|actual exclusive|155.690749|157.298604|
|model exclusive|691.388181|699.216399|
|그 밖 잔차|0.086782|0.080205|
|whole worker|847.165712|856.595208|

actual exclusive에는 제어·준비·전체 snapshot·native 물리/observer·사실 commit·forecast 검증·history·직렬화/hash/IO가 포함되고 model region은 빠진다. 모델에는 초기 import/source 검증과 qualification/query·restore·물리/observer·검증·receipt/barrier/readback·cleanup/IO가 포함된다. narrow step/tag·trace payload timer는 그 안의 부분집합이며 더하지 않는다. 실제 함수·observer·IO 각각의 독립 비용 분해나 순수 solver benchmark를 새로 수행하지 않았다. 정의와 한계는 [441 비용 분석](recovery441_result.md)을 따른다.

정적 별도 비용 CPU17.981초/wall18.017초, 저장 분석 CPU0.936초, 사후 연결 감사 CPU66.149초다. 준비·보고·Git·일부 import overhead를 포함한 전체 프로젝트 비용은 완전 계측하지 않았다.

v462는 이번 새 실제 호출 **362만** v461 잔여27,878에서 차감해 **27516**을 남긴다. 누적 실제 **1320548**, 예비 **84,000/사용0**이며 합계 operating cap1,432,064를 유지한다. 440 청구30,806 model ticks와 raw 원문30,762의44 차이·최종 CPU 하한 불확실성은 그대로다. 440/437/438 비용 재청구·환급·소급 성공 처리는 없다. HOLDOUT/SEALED·새 seed·학습·추가 유료 자원은0이다.

단일 worker PID와 시각·완료 행동·비용을 비공개 checkpoint에 매 검증 경계마다 저장했다. 별도 감시 관측은28회이며, 정적/선행 게이트/실제 시작/C0 완료/P 주요 진행을 보고했다. 감시 최대 관측 checkpoint 나이는 37.7초였다. 이 수치는 모든 시간의 최댓값 증명이 아니며 긴 model query 중에도 meter tick/파일/프로세스 생존을 함께 확인했다. 진행 없는10분 구간은 관측되지 않았다. 원본 상태·seed·명령은 공개하지 않았다.

**source manifest 정정:** 441의 “440 구현13개 모두 실행 전 plan hash 일치”는 과장이었다. 이전 glob은 파일명이440으로 끝나는8개만 포함했고 paired440_*5개가 빠졌다. 442 준비 단계에서 발견했고 최초 복사 오류·원인도 비공개 기록에 보존했다. 13개 원본은 f5e3909와 byte가 같은 것을 확인했지만, 과거 plan에 없던5개의 실행 당시 hash 보장을 소급 생성하지 않는다. 442는 새14개와 원본13개 모두 동결 manifest에 포함했으며 동결 후 변경하지 않았다. 이전441 보고서는 보존하고 여기서 그 주장을 정정한다.

prior 파일19059개와 보호 archive·이전 실패 보고서를 확인했다. main dfb7a2de2178825ca5c5ce20bab01ba67052ba31, Participants·사용자 변경·백업·개인 자료를 보존했다. [집계 JSON](paired442_result.json)에 실제 arm·검증·비용을 남겼고 raw 증거는 비공개다. Plan SHA256 `e0cfc05a5ee8471d67179b5b85a3fd0f5be301524762c683c99380ac60eab4a3`.
