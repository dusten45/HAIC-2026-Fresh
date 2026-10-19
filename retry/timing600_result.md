600 — 저장 hold148의 단일 정책 계산은 5초 초과

**원537 한 호출의 core CPU 7.956916586초, wall 7.962848161초**다. 저장598 hold148의 float32 action bytes와 전체 report·trials·새 FINAL이 정확히 일치했고,906시도/888완료·외부force3624/내부3552·geometry2641도 모두 일치했다. 따라서 이 지정 클라우드의 **해당 구현·해당 관측 입력에서는 이 구성요소만으로5초를 넘었다**. 다른 구현/하드웨어의 보편적 불가능성,모든 입력의 지연,실제 pixel Agent.act 전체 지연을 판정한 결과는 아니다. lap time 개선 실험도 아니다.

[사전 동결 계약](timing600_contract.json)은 단일 choose 직전/직후 clock 경계를 고정했다. import·입력 복원·geometry context 준비·순수 검사는 core 밖,원 nominal/backup·finite trials·새 FINAL·report/action 계산·body/force/clip/geometry/비용 gate와 메모리 진단 기록은 core 안이다. 원kernel200000과598의choose max_ticks180000은 유지했고 단일 호출의1536 상한을 추가했다. 내부4raw preview/native/pixel/thread/marshalling은 없다.

598의 수치 meter 메서드를 상속하여 그대로 사용했다. short/asdict도 유지하되 진단 SHA/JSON/fsync는 뒤로 옮기고 core에서는 유한값·타입·signed zero를 보존하는 구조 키로 상태 동일성을 검사했다. 이는 원래 매 primitive 전 durable journal을 요구하던 방식과 구분되는,명시적인 오프라인 계산 경계 진단 프로토콜이다. 원문 입력은 호출 전에 fsync했고,종료 후 출력과4538개 진단 이벤트를 비공개 저장했다. 순수 synthetic 검사6개가 eager/deferred 기록 값·상태 동일성·원 force/body gate·상한·상속 메서드 불변성을 확인했다. 추가 실제 choose나 워밍업은 없었다.

|시간 범위|CPU|wall|
|---|---:|---:|
|호출 전 준비 합계(import·복원·pin·순수 검사,보수5초 포함)|6.213049s|5.419584s|
|단일 core|7.956917s|7.962848s|
|출력·deferred 진단 materialization/JSON/fsync·동등성 검사|0.813354s|0.816592s|
|읽기 전용 최종 감사|0.061716s|0.061717s|
|감사까지 전체(보수5초 포함)|15.053059s|14.268624s|

준비·감사 합계는CPU7.096142/wall6.305776초다. 최종 요약 쓰기용CPU/wall 각각1초를 더해도 전체CPU90/wall120·준비감사60/75·core30/45 상한 이내다. import와 입력 복원의 개별 세부 시간은 별도로 나누지 않았으며 위 준비 합계로 측정했다.

실제 choose **1회**,model906시도/888완료,외부force3624/내부3552/합7176,geometry2641회다. 새native/world/reset/행동/solver/FD/seed/HOLDOUT/SEALED는 모두0이다. [읽기 전용 감사](timing600_audit.json)22항목을 통과했다. [집계 원본](timing600_result.json),[순수 검사](timing600_tests.json),[실행 코드](timing600.py),[감사 코드](timing600_audit.py)를 보존한다. 입력과 raw/상태/명령/전체 report는 Git 밖 비공개다.

현재 최고 성과는 기존 단일 cold privileged DEV native13.22초이며 변경하지 않는다. 일반·carry·pixel/5초 정책 승격은 닫혀 있고,잔액22211·reserve84000/사용0·승인종료2026-10-20 19:01:55KST를 유지한다. 이번 진단은 종료했으며 재호출·후속 실험을 실행하지 않았다.
