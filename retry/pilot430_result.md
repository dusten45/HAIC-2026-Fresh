# 430 모델 전용 pilot — 최초 기술 오류에서 중단

C0 모델은 71행동에서 공식 finish를 확인했다. P 모델은 37행동 뒤 질의 38의 **복합 물리 사유 감사 오류**로 중단했다. P 완료는 관측되지 않아 검열이며, 전체 완료 시간 이득은 `null`이다. P가 64결정에 도달하지 않아 이후 guardian 전환은 이번 모델 실행에서 관측되지 않았고 범위 로직만 정적 검사했다. 오류 이후 코드 수정·모델 재시도·추가 실제 실행은 하지 않았다.

## 승인 기간 정정

429에서 승인 기간이 끝났다고 한 판단은 잘못이었다. 최신 사용자 지시는 10월 16일의 3일 연장과 자율 진행이며, 적용 종료는 **2026년 10월 20일 19:01:55 KST**다. [기간 정정](authorization430_correction.md)에 기록했다. [429 원보고서](protocol429_result.md)와 당시 비용·실패는 그대로 보존했다. 자동 연장은 없다.

## 동결 계약과 선행 게이트

같은 알려진 423 pre119 root에서 두 model parent를 새로 시작했다. C0는 최대 80행동, P는 적격 FIRST_LAP planner 최대 64결정 후 guardian만 사용하며 전체 suffix 최대 100행동으로 동결했다. H13, 세 recipe·gain·엄격 bracket, 같은 child의 initial+추가 tail≤308, nominal/neutral guardian, memory·actual ledger·DONE 분리는 바꾸지 않았다. cap 뒤 tail이나 완료 시간 추정을 허용하지 않았다.

시작 전 최악 비용을 **519,038 ticks / 882 worlds**로 재확인했다. 구성은 planner 493,056 + guardian 24,128 + parent 720 + 자격 여유 1,134 ticks다. cap은 524,288 ticks / 1,024 worlds / CPU 1,800초 / wall 2,400초 / 순차 적분 1개다. 최초 기술·정의역·재현·복원·수치·parent/RNG 오류, guardian 불가, 비용/기간 초과에 전역 중단하도록 정했다.

동결 정적 검사 **64개가 모두 통과**했다. 이어 아래 게이트를 모두 통과한 뒤에만 pilot을 진행했다.

- 저장된 423 C0 71행동과 427 P 59행동의 전체 실제 명령을 각각 독립 모델 2개에서 재현: body/wheel/raw hull, phase·clipping·공식 finish 검사.
- 실제 427의 12개 상태를 각각 두 번 복원해 첫 전이 검증. held parent 첫 전이 및 parent·memory·RNG·actual ledger 불변 확인.
- 저장된 425 pending root에서 nominal 2회: `AT_ROOT_CONFIRMED_IN_MODEL`, 실제 DONE 권한 없음.

게이트 비용은 **1,134 ticks / 32 worlds**로 동결 계산과 같았다. 이 자격은 저장된 실제 상태·명령에 한정된다. 이후 새로운 상태·넓어진 힘 영역의 실제 정확도나 실제 안전을 인증하지 않는다. 알려진 DEV root만 사용했으며 새 HOLDOUT·SEALED 평가나 일반화 주장은 없다.

## 적분 전 기록과 조기 unsafe

각 질의의 원래 context·root state/memory/ledger·global RNG 전체 bytes·gate를 child 생성 전에 비공개 원자적 receipt로 저장하고 readback digest를 확인했다. world 입력과 복원 게이트·첫 적분 snapshot도 적분 전에 저장했다. 선택한 첫 행동을 model parent에 적용하기 전에 원 context와 parent/RNG/ledger 불변 증거를 다시 기록했다. 캐시나 428 UNBOUND receipt는 입력으로 사용하지 않았다.

| 새 430 질의의 fullgas | 관측 행동: required/repeat | raw ticks: required/repeat | 결과 |
|---|---:|---:|---|
| 36 | 8 / 8 | 32 / 32 | 인증된 조기 물리 부적격, nominal 선택 |
| 37 | 7 / 7 | 28 / 28 | 인증된 조기 물리 부적격, nominal 선택 |
| 38 | 7 / 7 | 28 / 28 | 복합 사유 감사 오류, 선택·parent 전이 없음 |

36·37은 `path_error_over3m`이며 `LIVE_BEFORE_QUERY_CAPTURE` 인증을 통과했다. 관측된 유한 stop state·memory·trace·비용을 보존하고 H13 패딩, 완료 시간, 순위 자격, 실제 실행/DONE/승격 권한을 부여하지 않았다. 이는 **새 430 질의의 독립 실행 결과**다. 원래 428 질의 36의 선택을 복원한 것이 아니며 그 인증 부족은 그대로다.

## 최초 오류와 관측 한계

38의 required/repeat는 모두 7행동에서 `path_error_over3m,road_loss_or_grass`로 멈췄다. 저장 수치는 유한하고 telemetry를 제외한 독립 반복은 정확히 같았다. 원래 context/RNG와 복원 증거도 저장되어 있다. 하지만 `audit429.py:18`은 `error` 전체 문자열이 단일 사유 whitelist의 원소인지 검사한다. 각 사유가 허용 목록에 있어도 쉼표로 연결된 문자열은 거부되어 `ProtocolStop: only_explicit_physical_stop_can_be_ineligible`가 발생했다.

이는 **복합 물리 중단 사유를 놓친 구현 공백**이다. 정적 64개는 이 조합을 다루지 못했다. 정상·물리 부적격·기술 오류를 구분한다는 의도만으로 이를 통과 처리하지 않았다. 최초 오류 규칙에 따라 전역 중단했으며, typed 인증·선택 38·parent 행동 38을 만들지 않았다. P planner 질의는 38개를 시도했고 선택·parent 전이가 완료된 것은 37개다. 질의 38 전체 initial 지출은 264 ticks/6 worlds이며 그중 fullgas 부분은 56 ticks/2 worlds다. nominal/neutral은 initial13까지 안전했지만 tail은 실행하지 않아 그 후속 결과를 알 수 없다. 이 오류를 guardian 불가나 parent 물리 실패로 해석하지 않는다.

## 모델 관측 결과

| 항목 | C0 | P |
|---|---:|---:|
| parent 행동 | 71 | 37 |
| planner / guardian 결정 | 0 / 71 | 37 / 0 |
| 상태 | 모델 공식 finish | 기술 중단으로 검열 |
| root 이후 공식 이벤트 구간 | 5.62–5.64초 | 미관측 |
| 확인한 raw ticks | 283 | 148 |
| 최대 post 경로 오차 | 1.13470 m | 1.06691 m |
| 최대 힘 비율 | 1.11472 | 1.40734 |
| clipped wheel samples | 6 / 1,132 | 31 / 592 |

C0의 이벤트 시각과 확인 step 종료 시각 5.66초는 구분했다. P의 실제·모델 완료 시간을 추정하지 않았다. parent 첫 전이 108개는 선택한 child 첫 전이와 허용 오차 내에서 일치했고 clipping 불일치는 0이었다. C0 첫 64행동과 P 첫 35행동은 428 저장 rows와 정확히 같았다.

37개 완료된 planner receipt의 선택·digest·root 연결을 재검사했다. candidate 집계는 FINISHED witness 86개, unsafe tail 4개, 인증된 early 부적격 2개다. 이는 중첩 질의의 모델 witness 수이며 독립 완주 수가 아니다. 안전하지 않거나 미완료인 후보의 시간은 모두 `null`이다. 공통 관측 arc 70/75/80/85%의 P 시간 이득 구간은 각각 0.18–0.22 / 0.36–0.40 / 0.70–0.74 / 0.88–0.92초였고 90/95%는 미관측이다. 이를 합산하거나 전체 완료 이득·11초대 성과로 바꾸지 않는다.

## 비용·보존·다음 조치

실제 지출은 **38,213 model ticks / 366 worlds**, whole-worker CPU **245.642초**, model 실행 wall **245.286초**다. 모두 cap 이내이며 미확인 적분 tick은 0이다. 최대 보유 world는 7개, 동시에 적분한 world는 1개다. 정적 CPU 2.532초와 저장 분석 CPU 3.454초는 별도다. 준비·보고·Git 시간은 완전 계측하지 않았다. 36–38의 부분 지출은 위 총비용에 포함되며 과거 비용은 다시 청구하지 않았다.

새 실제 행동/reset·actor 호출·학습·SEALED·reserve·유료 자원은 모두 **0**이다. v450은 연구 잔액 28,444행동, 누적 실제 1,319,620행동, reserve 84,000/사용 0으로 같다. 원 계획 SHA256은 `9611d49e63b085cbe9174e65e02d0e70f29bd2285eb2cee217edbdd73c47c37d`다.

기존 420–429 파일 2,038개, 보호 archive·manifest, 원래 429 보고서, 동결 코드 해시를 확인했다. 생성 전 입력 증거 366개, 첫 적분 복원 증거 365개, 질의 전 증거 109개, parent 전이 전 증거 108개의 연결을 대조했다. 원문 state·RNG·지도·seed·명령 trace·receipt는 비공개 공간에 유지한다. 공식 Participants/main과 기존 백업은 수정하지 않았다.

다음 유용한 작업은 복합 사유를 정확한 비어 있지 않은 token 집합으로 감사하는 **별도 정적 수정**이다. 마지막 raw flags와 사유 집합 일치, 허용 조합, unknown/reverse/domain/technical token 거부, 수치·반복·복원·비용 변조 거부를 먼저 검증해야 한다. 현재 실패와 코드는 보존하며 이 실행을 수선해 재시도하지 않는다. 새 모델 범위는 선행 정적 게이트 뒤에 따로 정해야 한다. 실제 실행 gate는 닫혀 있다.

기계 판독 요약: [pilot430_result.json](pilot430_result.json).
