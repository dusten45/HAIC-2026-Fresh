# 433 runner 수정·모델 전용 pilot — 질의42 계약 중단

432의 클래스 참조를 고쳐 정적 74개와 선행 재현·복원 게이트를 통과한 뒤 모델을 실행했다. C0는 71행동에서 공식 finish를 확인했다. P는 41행동 뒤 질의42의 `invalid_terminal_vector` 오류에서 즉시 중단했다. **P parent 완료가 없어 전체 완료 시간 이득은 `null`**이다. 모델 적분 뒤 계약 수정·재시도는 하지 않았다.

## 수정 범위와 동결 계약

433 runner는 정의된 `test_pilot433.Scope433`을 참조한다. 단계 이름을 정규화해 비교하면 모델 실행 로직은 432와 같고, 정적 harness 변경은 클래스 참조 수정뿐이다. 432 원계획·코드·실패·비용·보고서는 그대로 보존했다. 모델 적분 전 명백한 import/이름/runner 연결 오류의 비의미적 복구는 이번 사용자 승인에 포함되지만 물리·안전·정의역 계약 완화는 포함되지 않는다.

같은 알려진 423 pre119 root에서 새 context로 C0≤80행동, P 적격 FIRST_LAP planner≤64결정 뒤 guardian만 사용해 P 전체 suffix≤100행동으로 동결했다. H13·recipe·gain·동일 child tail≤추가308·엄격 bracket·guardian·memory/actual ledger/DONE 분리를 유지했다. 최악 비용은 **519,038 ticks / 882 worlds**로 재확인했다. cap은 **524,288 ticks / 1,024 worlds / CPU1,800초 / wall2,400초 / 순차 적분1개**다. 종료는 **2026년 10월 20일 19:01:55 KST**이며 자동 연장은 없다.

동결 계획 SHA256: `17e5670bb688a5097368843c010b8c38c57b9dc18d74d40467541276e1026573`.

## 선행 게이트와 복합 사유 처리

정적 **74개 모두 통과**했다. 431의 정확한 물리 사유 집합 감사, 15개 허용 조합/64개 순서 및 오류·변조 거부와 기존 receipt 선택 유지, scope·적분 전 저장 검사를 포함한다. 이어 저장된 423 C0 71행동/427 P 59행동을 각각 두 번 전체 재현하고, 427의 실제 상태12개를 각각 두 번 복원해 첫 전이를 확인했다. body/wheel/raw hull·phase·clipping·공식 finish와 held parent/memory/RNG/actual ledger 불변 검사를 통과했다. pending root의 nominal 독립2회도 통과했고 실제 DONE 권한은 부여하지 않았다. 선행 비용은 **1,134 ticks / 32 worlds**다.

각 질의의 원 context·root state/memory/ledger·전체 global RNG·gate를 적분 전에 비공개 receipt로 저장했다. 생성 전 입력과 복원 게이트/첫 적분 snapshot, 선택한 parent 전이 전 증거도 연결했다. 캐시나 428 UNBOUND receipt를 사용하지 않았다. 이 자격은 저장된 실제 상태·명령에 한정되며 새 모델 상태의 실제 정확도·안전·일반화를 인증하지 않는다. 알려진 DEV root만 사용했고 새 HOLDOUT/SEALED 평가는 없다.

430에서 멈췄던 새 질의38의 `path_error_over3m,road_loss_or_grass`는 정상적으로 인증된 부적격 후보가 되어 nominal을 선택했다. 질의39·40의 같은 복합 사유도 처리했다. 41개 완료된 선택 receipt에서 early 부적격9개를 확인했고, 실패한 질의42에도 neutral3행동/fullgas4행동의 early 기록2개가 인증·저장됐다. 모두 관측 길이·유한 stop state·비용을 유지하고 완료 시간·H13 패딩·순위 자격·실제 실행/DONE 권한을 부여하지 않았다.

## 최초 모델 오류의 정확한 조건

질의42 nominal의 독립 두 모델은 같은 결과였다. initial13의 terminal vector는 유한했고 speed/path error/힘 비율에 별도 위반은 없었지만 `remaining_path_m = -0.1803092504 m`였다. 13번째 row의 phase는 `FIRST_LAP`, official `finished`는 false였다. 추가 tail1행동의 raw1 tick에서 official finish가 확인됐고, 그 raw 이벤트 시각은 initial13 마지막 시각과 같았다.

기존 `planner419.Evidence.authenticate`는 terminal vector의 음수 remaining path를 `FINISHED && official_finish_qualified && tail_actions_integrated==0`인 경우에만 허용한다. 이 후보는 **tail_actions_integrated=1**이므로 조건이 false이고 `TerminalVector.validate`가 `ContractError: invalid_terminal_vector`를 냈다. 이 실패를 물리 unsafe나 guardian 둘 다 불가로 바꾸지 않았다. 음수를 0으로 자르거나, epsilon을 넣거나, 이후 finish를 근거로 initial13 계약을 소급 통과시키지 않았다.

**선택42·parent 행동42는 생성하지 않았다.** raw child의 finish 관측은 P parent 완료나 유효한 순위 증명으로 사용하지 않으며, 이 부적격 candidate의 planner 시간은 `null`이다. 질의42 전체 지출은 **162 ticks / 6 worlds**로 총비용에 포함된다. 실패 이후 추가 모델 재시도·실제 주행은 없다.

증거 한계도 있다. initial13 때의 dump가 continuation 최종 dump로 덮어써져 H13의 별도 전체 finish-tracker snapshot은 남아 있지 않다. raw13 rows와 end13 vector/state digest는 보존되어 있지만, 이것만으로 원래 H13의 등록된 pending/crossing 인증을 보충했다고 주장할 수 없다. 다음 설계 검토는 이 전체 snapshot과 공식 이벤트/확인 경계를 보존하는 표현을 먼저 다뤄야 한다. 일반적인 음수 허용이나 계약 우회는 근거가 아니다.

## 관측 결과와 비교 한계

| 항목 | C0 | P |
|---|---:|---:|
| parent 행동 | 71 | 41 |
| planner / guardian 완료 선택 | 0 / 71 | 41 / 0 |
| 결과 | 모델 공식 finish | 계약 중단으로 검열 |
| root 이후 공식 이벤트 구간 | 5.62–5.64초 | 미관측 |
| parent raw ticks | 283 | 164 |
| 최대 post 경로 오차 | 1.13470 m | 1.27252 m |
| 최대 힘 비율 | 1.11472 | 1.58883 |
| clipped wheel samples | 6 / 1,132 | 41 / 656 |

C0의 확인 step 종료는5.66초이며 공식 이벤트 시각과 구분했다. P는 planner 질의42개를 시도했고41개 선택·parent 전이만 완료했다. **64결정 이후 guardian 전환에는 도달하지 않았다**. 그 범위 로직의 정적 검사는 통과했지만 이번 모델 실행에서 전환을 관측한 것은 아니다.

선택한 parent 첫 전이112개는 child 첫 전이와 허용 오차 내에서 일치했고 clipping 불일치는0이었다. C0 첫71행동과 P 첫37행동은430 저장 rows와 정확히 같았다. 41개 완료 receipt의 선택·digest·원 context 연결을 저장 자료로 재검사했다. 집계는 유효한 모델 FINISHED witness91개, unsafe tail4개, early 부적격9개이며 중첩 질의의 witness 수를 독립 완주 수로 해석하지 않는다. 실패한42의 nominal 후보는 이 유효 집계에 포함하지 않는다.

공통 arc70/75/80/85/90%의 P 시간 이득 구간은 각각0.18–0.22 /0.36–0.40 /0.70–0.74 /0.88–0.92 /0.98–1.02초이고95%는 미관측이다. 이를 합산하거나 전체 완료 이득·11초대 성과로 바꾸지 않는다. actual gate는 닫혀 있다.

## 비용·보존·남은 장애물

실제 모델 지출은 **39,065 ticks / 390 worlds**, worker 계측 CPU **261.000초**, 실행 wall **259.255초**다. cap 이내이며 미확인 적분 tick은0, 최대 보유 world7개·동시 적분1개다. 정적 CPU5.775초, 저장 분석 CPU5.427초는 별도다. 준비·보고·Git 시간은 완전 계측하지 않았다. 과거432/430 비용을 다시 청구하지 않았다.

새 실제 행동/reset·actor·학습·SEALED·reserve·유료 자원은 모두 **0**이다. v453 연구 잔여 **28,444**, 누적 실제 **1,319,620**, reserve **84,000/사용0**을 유지했다. 기존420–432 기록3,763개와 동결 source·보호 archive를 대조했다. 생성 전 입력390개, 첫 적분 복원389개, 질의 전113개, parent 전이 전112개의 증거 연결을 확인했다. 원문 state·RNG·지도·seed·receipt는 비공개 공간에 유지했다. 공식 Participants/main과 기존 백업은 수정하지 않았다.

남은 장애물은 planner terminal-vector의 음수 remaining path 정의역과 뒤늦은 공식 finish 확인 사이의 표현 계약이다. 전체 H13 snapshot·등록 이벤트·phase를 보존한 별도 정적 설계/반증 검토가 필요하다. 현재 실행과 원계약은 그대로 보존하며, 이 과업의 권한으로 안전/물리 계약을 완화하거나 모델/실제로 재시도하지 않는다.

[기계 판독 결과](pilot433_result.json) · [432 원실패](pilot432_result.md) · [431 감사 수정](audit431_result.md).
