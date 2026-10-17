# 429 조기 물리 unsafe 정적 프로토콜 — 모델·실제 실행 없음

저장 기록만 사용한 정적 검사 56개가 통과했다. 이 단계에서 모델 tick/world, 실제 행동/reset, actor 호출, 학습, SEALED, reserve, 별도 유료 자원 사용은 모두 0이다. 정적 통과는 모델 정확도나 실제 전이의 승격 근거가 아니다. 승인 기간 종료에 따라 결과를 정리하며 새 실험을 시작하지 않는다. 과거 계획에 기록된 다른 종료 시각은 이번 정리에서 실행 권한으로 사용하지 않는다.

## 계약과 결과

`early429.py`는 요청 H13보다 먼저 물리적 unsafe로 멈춘 1–12행동 기록을 별도 `EarlyPhysicalIneligible` 타입으로 보존한다. 관측 길이, 명시적 물리 중단 이유, 유한한 마지막 상태·memory·raw trace, 확인된 비용을 유지한다. H13까지 패딩하거나 완료 시간을 추정하지 않는다. `end13`, 순위 자격, 완료 witness, 실제 실행·DONE·승격 권한을 부여하지 않는다.

물리 중단은 경로 오차, 손상 증가, 충돌/장애물, road loss/grass의 확인된 사유로 제한한다. 기술 예외, NaN/Inf, reverse/정의역, restore/repeat, parent/RNG, phase·clock 불일치는 계속 전역 `ProtocolStop`이다. 인증에는 원래 root state/memory/clock/RNG, ledger, policy와 검증된 선행 게이트가 모두 필요하다. 미확인 값은 통과로 간주하지 않는다. wire 변환에도 이 구분과 불변 bytes를 보존하고 추가 finish/DONE 필드를 거부한다.

기존 `planner419.choose`의 H13, 세 recipe, gain·strict bracket, 동일 child의 initial+tail, memory·actual ledger·DONE 분리는 그대로다. nominal이 부적격이면 검증된 neutral guardian이 필요하고, 둘 다 부적격이면 STOP한다. gas가 이를 구제하지 않는다. 저장된 정상 35개 receipt의 선택은 기존 chooser와 같았다. unsafe tail 4개에는 완료 시간이 생기지 않았다. 공식 partial finish와 실제 dispatch에 필요한 DONE 권한도 기존 통제를 유지했다.

## 확인할 수 없는 부분

428 질의 36의 fullgas는 독립 반복 모두 8행동/32 raw ticks에서 `path_error_over3m`으로 멈췄다. 합계 64 ticks/2 worlds는 **428의 기지출**이며 이번 비용으로 재청구하지 않는다. 관측 상태·memory와 중단 이유는 비공개 원문에 보존했다. branch 전체 CPU/wall은 저장되지 않아 `null`이다.

원래 질의 36의 context/RNG stamp와 일부 parent/restore/fidelity 인증은 저장되지 않았다. 따라서 기록은 **UNBOUND**이며 실제 chooser에 넣으면 거부된다. 합성 context를 사용하는 정적 대조는 타입·선택 규칙 검사에만 사용했다. 원래 선택 36이나 실행되지 않은 nominal/neutral tail 결과를 복원했다고 주장하지 않는다.

## 실패 보존과 비용

첫 정적 실행은 테스트의 `TickBracket` import 누락으로 2개 검사 중 error 1개에서 멈췄다. 원계획·원소스 사본·실패 결과·로그를 그대로 보존했다. 테스트 import 한 줄만 추가하고 별도 동결 계획에서 같은 assertions를 검사하여 56개 통과했다. 모델/environment 생성자를 차단했고 호출 수도 0임을 검사했다.

두 정적 실행 합계 CPU 2.149336초, wall 2.165733초, whole-process CPU 5.757785초다. 준비·수정·보고·Git 시간은 완전 계측하지 않았다. 원래 계획 SHA256은 `b9eb2942ac14a0adc94fa366ee4a5aee205c64a3d34f88afbf6b9cef723cb90b`, 수정 정적 계획은 `6c83cc6b72e0a81cd4a2ba19ca6a89a5941e337ca583eb3caa4322b4439ea326`이다.

420–428단계의 2,018개 보존 파일 및 보호 해시를 대조했다. 기존 코드·실패·비용·공식 Participants·main·백업은 변경하지 않았다. v449 잔액은 연구 28,444행동, 누적 실제 1,319,620행동, reserve 84,000/사용 0으로 동일하다. 비공개 원문·상태·RNG·receipt는 공개 저장소에 포함하지 않는다.

## 미실행 범위 제안

아래는 순수 상한 계산이며 실행 계획의 승인이나 새 실험 결과가 아니다.

| 항목 | 제안 범위/최악 비용 |
|---|---:|
| C0 suffix | 최대 80행동 |
| P planner | eligible FIRST_LAP 최대 64결정 |
| P 전체 suffix | planner 이후 guardian만 사용, 총 최대 100행동 |
| planner initial+tail 및 반복 | 493,056 ticks |
| guardian 및 반복, 최악 116질의 | 24,128 ticks |
| 두 model parent, 총 180행동 | 720 ticks |
| 재현/restore/pending guardian 자격 여유 | 1,134 ticks / 32 worlds |
| 총 상한 계산 | **519,038 ticks / 882 worlds** |
| 제안 cap | 524,288 ticks / 1,024 worlds / CPU 1,800초 / wall 2,400초 / 순차 1개 |

P의 100행동 cap에는 planner와 FINISH_CONFIRM/guardian을 모두 포함한다. cap 뒤에 tail을 숨겨 더하지 않는다. C0의 80행동 제안은 이전 64행동 censored 결과를 완주로 바꾸지 않는다. 후속 실행을 별도로 승인받더라도 integration 전에 원래 context/RNG/root와 게이트 증거를 먼저 저장해야 한다. 동일 root·ledger·policy 인증 없는 재사용, 조기 unsafe의 H13 패딩, 기술 오류의 물리 unsafe 전환은 허용하지 않는다. 현재 actual gate는 닫혀 있다.

기계 판독 요약: [protocol429_result.json](protocol429_result.json). 직전 결과: [428 initial8 중단](pilot428_result.md).
