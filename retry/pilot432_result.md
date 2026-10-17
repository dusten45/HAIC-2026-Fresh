# 432 정적 게이트 오류 — 모델 미시작

432는 모델 실행 전 정적 suite 구성에서 중단했다. `static432.py`가 `test_pilot432.Scope430`을 참조했으나, 복사된 테스트에 정의한 클래스는 `Scope432`였다. 오류는 `AttributeError: module 'retry.test_pilot432' has no attribute 'Scope430'`이다. **테스트 클래스를 복사하며 참조 이름을 놓친 구현 오류**이며 시뮬레이터나 복합 물리 감사 실패가 아니다.

이 실행의 정적 검사 수는 **0**이다. suite 구성 전 모듈 import까지 진행됐고, 모델 qualification/pilot의 opening·budget·result는 생성되지 않았다. 새 모델 ticks/worlds·실제 행동/reset·actor·학습·SEALED·reserve·유료 자원 사용은 모두 **0**이다. 최초 새 오류에서 중단하라는 지시에 따라 계획·원코드·실패 결과를 보존하고 수정·재시도하지 않았다.

앞선 [431](audit431_result.md)은 별도 계획에서 정적 **74개를 통과**했으며 `5020e4c`로 커밋·push하고 원격을 확인했다. 허용 조합 15개, token 순서 64가지, 저장된 430 질의 38과 오류/변조 거부, 기존 37개 receipt 선택 유지가 그 결과다. 432의 로딩 오류는 이 검증 결과를 취소하거나 새로운 모델 결과로 바꾸지 않는다.

432 계획은 431 통과 후 별도로 동결했다. 같은 알려진 root에서 C0≤80행동, P FIRST_LAP planner≤64결정 뒤 guardian만 사용하고 P 전체 suffix≤100행동으로 정했다. 기존 H13·recipe·gain·동일 child tail·엄격 bracket·권한 분리를 유지했다. 새 context/RNG/root의 적분 전 저장 및 423/427 재현·복원/pending 선행 게이트도 유지했다. 최악 비용을 **519,038 ticks / 882 worlds**로 재확인했고 cap은 **524,288 ticks / 1,024 worlds / CPU1,800초 / wall2,400초 / 순차 적분1개**였다. 이 모델 범위는 실행되지 않았다.

따라서 완료 parent의 시간 비교, candidate 완료 시간, 64결정 뒤 guardian 전환 관측은 새로 없다. 430의 P 검열과 전체 gain `null`은 그대로다. 430 원실패·코드·비용을 변경하지 않았다.

실패한 정적 run의 측정 비용은 CPU **1.672346초**, wall **1.671639초**다. 준비·보고·Git 시간은 완전 계측하지 않았다. v452는 연구 잔액 **28,444**, 누적 실제 **1,319,620**, reserve **84,000/사용0**을 유지한다. 종료는 **2026년 10월 20일 19:01:55 KST**이며 자동 연장은 없다.

원 계획 SHA256: `32882fd79be56b7a4bd5b0778f07631b0febb8887effe15bde0357b8ebe9e6d9`. 동결 source·기존 기록·보호 archive 해시를 대조했고 원문 state·RNG·지도·seed·receipt는 비공개 공간에 유지한다. 공식 Participants/main 및 기존 백업은 변경하지 않았다.

남은 장애물은 runner의 클래스 참조 한 곳이다. 이를 `Scope432`로 정정하는 별도 정적 복구와 게이트 검증이 다음 조치다. 현재 432 실행을 고쳐 재실행하거나 추가 모델 재시도·실제 주행으로 자동 전환하지 않는다.

[기계 판독 결과](pilot432_result.json) · [431 정적 수정](audit431_result.md) · [430 원실패](pilot430_result.md).
