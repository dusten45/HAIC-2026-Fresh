# 466 — H2A 수치 분석과 미래 압축 기록 조사 완료

**새 physics/native 적분·world/reset·seed·학습·HOLDOUT·SEALED·예비·유료 사용0이다. 압축 writer 구현/실행·기존 파일 삭제/이동/변환도0이다.** 465의 승격 조건 미통과와 감속 부채 trade-off를 유지하고 전체 secant 불가능성으로 확대하지 않았다.

[H2A 분석·다음 계약](design466_next.md)에서 같은segment위치의 병진 접촉력·후륜/equal-axle·엔진 등가 요구를 분리했다. q·κ의 곱 내부 극값도 검사했다. 고정4회 원래 A/B 재투영은239nodes 중222개와238gradient 중230개를 바꾸고, reference clock을10.027245→12.260072초로 늘렸다. 이산 A/B squared-speed 잔차는 roundoff 범위로 없어졌지만 총 접촉력 proxy 초과8개·후륜 proxy34개·continuous engine proxy94개는 남았다. 실제 tyre feasibility 인증은 아니다.

pre126 현재81.032m/s는 새target89.547와 backward join ceiling91.152보다 낮아 근사 접합은 배제되지 않았다. 같은 point-FF 식의 root gradient는−210.662→+29.917m/s²로 바뀌어, target을 낮췄음에도 첫 명령은 brake에서 fullgas가 된다. 이것은 reference 구조가 제어 신호에 미치는 효과를 판별할 근거이며 새 시간 이득 계산은 아니다.

제안한 단 한 반증은 **공통 첫 fullgas 뒤 Original-reference point-FF 대 Projected4-reference point-FF**다. 첫 pulse를 같게 해야 이미 확인한0.220초를 새 reference의 지속 효과로 다시 세지 않는다. 이후 저장 상태에서 추가 명령 변화가 있다. 각H13 독립2+held첫전이1, old source 포함 **1458ticks/41worlds**, hard2048/64·CPU180/wall300·actual/reset0의 설계만 제안했다. root+60m strict 시간 이득과1.04초 종료 진행 이득을 함께 요구하며, 낮아진 target에 대한 tracking오차·clipping감소만으로 승격하지 않는다.11초대 목표는 유지하고12.260초 profile을 champion이나 실제 시간 하한으로 채택하지 않는다.

[압축 호환성 조사](compression466_review.md)는 새 파일 첫 출력부터 lossless gzip으로 쓰고 실물파일을 재개방해 schema·stored/logical SHA·기존receipt digest를 확인하는 명시적 IO adapter를 제안한다. 기존codec의 모든 field/배열/bytes 복원을 유지한다. 현재 plain read_text/glob/hash 경로에는 연결 수정이 필요하고, source→constructor→runtime link→H13/pending barrier의 실제 readback 순서를 유지해야 한다. 기록을 생략하거나 hash만 남기는 방법은 제안하지 않았다.

기존 archive에서 model gzip 비율은약12.1–12.7%였다. 미래 파일별 writer 성능/압축률 보장은 아니다. serialization·gzip·fsync·전수readback/schema/hash·임시파일·workspace복사를 모두 비용에 넣어야 한다. 작은 H13 비용을 크게 줄일 여지는 있지만, 최신비율의 전체guarded 최악 plain payload약8.42GB는25% 압축 가정에서도workspace 전수복사가 안들어간다. 이미gzip인자료의복사에압축률을두번곱하지 않았다. 따라서 공간 문제의 개선 가능성과 미해결 부분을 분리했다.

순수 산식4개와 저장 분석은 physics constructor/step/native 금지 상태에서 통과했다. 첫 저장은NumPy scalar JSON 타입 오류로 중단됐고 실패folder·[gate](structural466_attempt1_gate.json)를 유지했다. 타입 정규화만 고친 별도 recovery에서 분석CPU0.603초/wall0.604초, 이를포함한 [통합gate](structural466_gate.json)0.611/0.612초였다. 최초 실패gate0.626/0.631초는 별도이며 중첩시간을 합산하지 않는다. 개발·읽기·Git 전체 overhead 완전 계측은 아니다. 압축 구현 benchmark는 실행하지 않았다.

[수치 집계](structural466_result.json)·[설계 JSON](design466_next.json)·[checkpoint](structural466_progress.json), private node/segment와 입력SHA를 보존했다. v475·연구26346·예비84000사용0·보호18파일·main dfb7a2de2178825ca5c5ce20bab01ba67052ba31·Participants·원본/백업을 유지했다. 현재 /tmp 약3.542GB/workspace 약903MB이며 다음시작전source증가·전체raw보존몫을다시검사해야 한다. 이번에는후속실행0이다. 최신종료2026-10-20 19:01:55 KST 이후 새 실험·자동연장 없음이다.
