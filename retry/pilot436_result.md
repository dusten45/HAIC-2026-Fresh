# 436 현재 pending parent 분리 — 모델 pilot 완료

등록된 pending parent를 별도 타입으로 분리한 뒤 정적·복원 게이트와 동일 root 모델 pilot을 완료했다. P는 planner54회 후 guardian1회에서 자신의 공식 모델 finish를 확인했다. C0 대비 **root 이후 모델 잔여 완료 시간 이득은1.30–1.34초**다. 실제 픽셀 정책 완주·공식 제출 점수·전체 실제 lap 개선을 입증한 결과는 아니다.

`PendingParent436`은 현재 전체 physical/tracker snapshot, raw clock, nominal 전후 memory, RNG, forecast ledger와 관측 이력을 묶는다. 등록·qualification·departed/from-back·현재 corridor/velocity 조건을 검증하며 negative remaining path만으로 pending을 만들지 않는다. 일반 `Current.validate`는 그대로다. 이 타입은 planner 순위에 들어가지 않고 기존 FINISH_CONFIRM guardian만 호출한다. guardian의 AT_ROOT/BEFORE_ROOT 예측은 같은 current parent와 이벤트에 묶지만 parent DONE를 만들지 않는다. parent 자신의 다음 적분에서 공식 tracker 확인이 생겨야 model ledger가 완료된다. actual 실행/DONE 권한은 없다.

정적 **118개 통과**, model/environment 생성0회다. 다른 root/child/event, 완료·취소·교체·미등록 이벤트, phase 조작, unsafe history, RNG/source/ledger 변조와 기존54개 선택 불변을 검사했다. 첫 정적 실행은113개 중 튜플/JSON 배열 비교1개에서 실패했다. 원계획·원소스·실패 로그를 보존하고 기존 `json_ready` 직렬화로 비교만 수정했다. 정책·물리·임계값·예산 변경은 없고 모델 시작 이후 수정·재시도도 없다.

선행 저장423/427 재현·복원 및425 pending 게이트는 기존과 같은1,134 ticks/32 worlds였다. 추가로 저장435 pending에서 guardian 두 개와 held parent 자신의 한 전이를 확인했다. 두 guardian 예측 뒤 parent DONE는 false였고, 자신의1 raw tick 뒤에만 공식 확인·model DONE가 생겼다. 독립 반복·첫 전이의 body/wheel/hull/phase가 정확히 일치했다. 추가 실측 **3 ticks/3 worlds**, 선행 합계 **1,137 ticks/35 worlds**다. 이는 새 복원 모델의 독립 확인이며 **435의 중단이나 그 lap을 소급 인증하지 않는다**.

| 항목 | C0 모델 | P 모델 |
|---|---:|---:|
| parent 행동 |71|55|
| planner / guardian 선택 |0 /71|54 /1|
| 결과 |공식 모델 finish|공식 모델 finish|
| root 이후 event 구간 |5.62–5.64초|4.30–4.32초|
| 확인 step 종료 |5.66초|4.34초|
| parent raw ticks |283|217|
| 최대 post 경로 오차 |1.13470m|2.66505m|
| 최대 힘 비율 |1.11472|2.07261|
| clipped wheel samples |6 /1,132|107 /868|

P 질의55는 `REGISTERED_PENDING_GUARDIAN_ONLY`로 전환됐다. 두 guardian의 미래 확인과 parent 자신의 확인을 별도 저장했다. parent 공식 event bracket은[215,216], C0는[281,282] raw ticks다. **planner64 이후 guardian 전환은 도달하지 않아 관측되지 않았다.** 이번 guardian 전환은 등록 pending 때문이었다.

저장54개 planner 선택·receipt와126개 parent 첫 전이를 재검증했고 clipping 불일치는0이다. C0 전체71행동/P 첫54행동은435와 정확히 같았다. 463개 live world와 40,769개 post raw ticks, 10,350개 action records를 대조했다. H13 initial-boundary 192개와 별도 continuation-final 192개를 같은 child/source/봉인 key에 연결했다. unsafe/censored에는 완료 시간이나 승격 권한을 주지 않았다. 기존121개 FINISHED candidate witness는 중첩 모델 질의 집계이며 독립 parent 완주 수가 아니다.

사전 worst-case **519,146 ticks/885 worlds**는 추가 pending 게이트의 보수적108 ticks/3 worlds를 포함한다. cap은524,288 ticks/1,024 worlds/CPU1,800초/wall2,400초/순차 적분1개였다. 첫 모델 기술·정의역·복원·반복·안전 불명·비용 오류는 전체 중단하도록 동결했다.

실제 전체 모델 비용은 **40,769 ticks/463 worlds**, worker CPU **602.737초**, 모델 실행 wall **597.988초**다. 미확인 tick0, 최대 보유 world7개, 동시 적분1개다. 정적 두 실행 합계 CPU 23.032초/wall 23.286초, 저장 분석 CPU 11.088초, 보존·증거 정리 검증 CPU 28.593초를 별도로 기록했다. 모델 worker CPU에는 import/source 확인·controller·observer·hash·IO·검증·cleanup을 포함한다. 준비·보고·Git 시간은 완전 계측하지 않았으며 과거 비용은 다시 청구하지 않았다.

새 실제 행동/reset·actor·학습·HOLDOUT/SEALED·reserve·별도 유료 자원은 모두0이다. v456의 연구 잔여28,444, 누적 실제1,319,620, reserve84,000/사용0은 그대로다. 기존 기록 9,858개와 frozen source·보호 archive를 확인했다. 공식 Participants/main·기존 백업·선택 archive를 변경하지 않았다. 원문 지도/seed/state/RNG/명령/receipt와 개인 기록은 비공개로 보존한다.

현재 장애물은 **새 모델 상태의 실제 물리 충실도와 합법적 픽셀 정책 성능을 아직 검증하지 않았다는 점**이다. 저장된 알려진 상태의 재현은 새 상태의 실제 안전이나 일반화를 보장하지 않는다. 이 단계는 모델 pilot으로 종료하며 실제 주행·학습·보호 split·reserve로 자동 전환하지 않는다. 연장된 종료 시각은2026년10월20일19:01:55 KST이며 자동 연장은 없다.

최종 plan SHA256: `97fdac1083a515ad7f071a8db487cf1b9600a62843f91c084158bbe9bd58b259`.

[기계 판독 결과](pilot436_result.json) · [435 원중단](pilot435_result.md) · [평가기·관측·시간 계약](README.md).
