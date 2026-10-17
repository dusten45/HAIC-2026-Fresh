# 456 — 모델 생성 전 runner 이름 연결 오류로 중단

**상태 `PREMODEL_RUNNER_BINDING_STOP`. fresh qualification과 네 부모 비교는 시작되지 않았다. 새 model ticks/worlds·실제 행동/reset·새 seed·학습은 모두0이다.** 완료 시간·이득·실제 승격 결과는 없다. 455 가설의 성능이나 기존419 planner에 대한 반증 실험 결과로 해석하지 않는다.

구현·동결 plan과 정적253개+저장 감사는 통과했고 `436ba1a`로 일반 commit/push했다. 정적 비용은 CPU24.429초/wall24.643초다. 실제 runner를 한 번 실행하자 Meter 생성에서 아래 오류로 exit1했다.

```text
TypeError: Meter.__init__() got an unexpected keyword argument 'start_wall'
```

원인은 `compare456.py`에서 budget adapter를 import한 뒤 backend wildcard import를 하면서 `Meter` 이름이 `retry.pilot420_backend.Meter(d)`로 덮인 것이다. 의도한 클래스는 `retry.budget456.Meter(d,start_wall=None)`다. 동결 소스의 읽기 전용 사후 확인에서 두 클래스가 다른 것을 확인했다.253개 정적 검사는 budget adapter 자체와 planner AST·scope·권위·상한을 검사했지만 **runner의 최상위 Meter 이름 연결을 놓쳤다**.

실패는 `opening.json`·meter/budget·fresh qualification·model world 생성 이전이다. 해당 opening/budget/constructor/observer receipt도0개이고, source의 예외 위치에서 모델 생성 전임을 확인했다. 저장 root113의 state/memory/ledger/RNG 및 nominal13 자료 연결 확인은 통과했지만 이것을 새 모델 qualification 성공으로 쓰지 않는다. 실패한 worker의 source hash 확인·import·준비 CPU/wall 전체는 별도 계측하지 못했으며, 새 모델 소비0과 worker overhead0을 혼동하지 않는다.

계약은 candidate native113 직전 동일 root, C0-1/P-1/C0-2/P-2, 각 부모100행동, P 기존419 적격 planner8회 후 같은 guardian이었다. 사전 계산206,194 ticks/1,677 worlds, hard212,992/1,792·CPU6,000초/wall9,000초·순차1이었다. 이 예산을 실행 완료나 유보된 추가 실행 권한으로 쓰지 않는다.

**전역 오류 중단 규칙에 따라 동결 소스를 고치거나 모델 실행을 재시도하지 않았다.** 최초 로그·plan/hash·정적 결과·준비 단계 오류 기록·저장 사후 진단은 비공개에 보존했다. 원문 state/seed/명령/RNG·개인 문서는 공개하지 않았다. [집계 JSON](compare456_result.json)은 종료 후 저장 자료로 작성한 postmortem이며 worker meter가 생성한 결과가 아님을 표시한다. [실행 코드](compare456.py)·[예산 adapter](budget456.py)·[사전 게이트](compare456_gate.json)도 실패 당시 상태로 보존한다.

다음 수정은 분명한 budget class alias 또는 명시적 backend import와 최상위 runner binding 정적 fixture다. 이는 별도 실행을 준비할 때 적용할 수정 제안이며456에서 수행하지 않았다. 추가 simulation·미세 gate·새 seed·실제 승격을 자동으로 진행하지 않는다.

v473 원장은 변경하지 않았다. **연구 잔여27,059, 누적 실제1,321,005, 예비84,000/사용0**이다. HOLDOUT/SEALED·추가 유료 자원0, main dfb7a2de2178825ca5c5ce20bab01ba67052ba31·Participants·보호 ZIP·기존 사용자 변경·백업과451 censor를 보존했다. 유효 종료2026년10월20일19:01:55 KST를 유지한다.
