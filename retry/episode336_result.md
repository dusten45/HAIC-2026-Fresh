336은 후보의 주행 실패가 아니라 평가기 진단 로그 오류로 1행동 뒤 강제 중단됐다. 제가 추가한 `info.damage_effects`의 DamageEffects dataclass를 JSON으로 변환하지 못했다. 실제 환경이 닫혀 무료 재개할 수 없으며, 이번 질문인 N2 episode 완주 여부는 아직 판정하지 못했다. 단일 새 B 계약을 지켜 두 번째 reset·재시드·재실행은 하지 않았다.

TimeLimit·wrapper·등록 실행 계약은 먼저 확인했다. 현재335의 `retry.diagnose.make_env`는 raw TimeLimit8200이며 reset 내부 첫 raw tick은 TimeLimit을 거치지 않고 warmup50은 counter에 들어간다. 실제 새 B reset 뒤 elapsed50·raw clock51tick을 확인해, 남은8150raw / skip4 = ceil2037.5 = **최대2038행동**을 등록했다. 마지막 행동은2raw tick이다. 물리 없는 counter double로 이 경계를 검증했고, 실제 reset counter로 재확인한 뒤 첫 정책 행동을 실행했다.

기본 CLI·등록 평가 loop의 max-steps2000과 이 연구 executor의 실제 TimeLimit2038은 다르다. 363은296의 과거 완주 행동 수일 뿐 종료 한도가 아니므로336에는363 cut을 넣지 않았다. 실제 source는 finish flag를 세우면서 `truncated=True`를 반환할 수 있다. finish-qualified 시각, 중심 통과 시각으로 소급한 finish_time, 종료를 확정한 clock을 분리하며 공식 lap time은 `(finish_time_s-postreset_start_time)×1000`으로 계산한다. 순수 FinishLineTracker 테스트에서도 중심 통과3초/확정4초일 때 finish_time3초임을 검증했다. 모든 truncated를 실패로 취급하지 않는다.

| 실제336에 보존된 결과 | 값 |
|---|---:|
| 등록 상한 / 실제 native | 2038 / 1 |
| 실제 재현 검증을 통과한335 prefix | 1/72행동 |
| 저장한 관측 stack / 명령 | 2 / 1 |
| elapsed raw counter | 50→54 |
| 실제 action raw / reset raw | 4 / 51 |
| terminated / truncated / finish flag | 모두 없음 |
| 분류 | 기술적 censoring; DNF 아님 |

첫 행동의 명령·관측·actor state·memory·수집 physics·접근 가능한 RNG는335와 비교를 통과했다. 그러나 풍부한 첫 trace 행을 JSON으로 쓰기 직전 예외가 발생해 trace 파일은 비어 있다. 실제 finish flag는 없고 lap time은 미관측이다. 첫 행동 후 unique tile·damage의 개별 row 값은 독립 저장되지 않았으므로 과거 GT를 복사해 새 측정처럼 채우지 않았다. 후보의 실패 최초 도로 구간이나 완주 성능을 이 결과에서 추정하지 않는다.

원래 실행 source·plan·오류 traceback·실제 raw frames/actions·초기 scene·종료 counter·비용을 그대로 보존했다. 공개 runner에는 dataclass를 `asdict`로 변환하는 JSON default 처리와 NumPy scalar/array 처리를 추가했다. native0 테스트에서 실제 DamageEffects의 손상0/.2/1.0 구조로 기존 오류를 재현한 뒤 수정 직렬화를 검증했다. 원래/수정 `run` AST는 JSON default 인자만 다름을 확인했다. 정책 archive·worker·제어·물리·시간 코드는 바꾸지 않았다. 수정 source는 이번 native에 실행하지 않았다.

기존335의72행동은 사전 저장 관측72회에서 모든 명령·features·tracker·직렬화 state·memory를 다시 재현했다. 이것은 cache qualification이며 새 native 검증으로 부르지 않는다. 실제336 전체72 prefix는 통과하지 못했다. 현재 환경은 닫혔고 snapshot 복원·teleport·이전 명령 강제·새 A를 통한 우회는 하지 않았다.

연구2038을 등록한 총 B는1,368,237이었다. 실제1 native를 차감해 누적native1,282,200·연구잔여2037·최종예비84,000이다. native wall0.947초/evaluator CPU0.608초/actor CPU0.269초, 실제 capture wall0.024초였다. cached actor72회는 wall1.587초/evaluator CPU0.968초/actor CPU0.832초다. 물리 없는 counter 테스트2038회는CPU0.142초, serializer 회귀검증은CPU0.0165초였다. 초기 hash/data 읽기·build·수정·보고 등 미계측 범위도 비용 기록에 명시했다. 새 학습·source physics rollout·유료 자원은 없다.

대체 실행을 한다면 이 실패 자료를 지우거나 같은 episode 재개로 위장하지 않고 별도 stage에서 동일 후보로 새 B 한 번을 시작해야 한다. 실제 한도2038을 모두 보장하려면 현재2037에 최소1 native의 추가 연구예산이 필요하며, 총 B는1,368,238이 된다. 단일 새 B 지시의 예외와 대체 episode 계약이 필요하므로 이번336에서는 추가1이나 새 reset을 등록하지 않았다. 수정 serializer의 native0 게이트와33572 prefix 자격을 먼저 통과한 뒤 실제 prefix를 재현하고 공식 종료까지 진행하는 방안을 제안했다. 일반 paired 다도로 검증은 실제 완주가 확인된 다음 단계다.

334의 전체 최근접 집계 악화와 사후 fixture 대응 subset 개선은 그대로 보존했다. 실제 가림은 여전히 미검증이다. champion296·TRAIN registry·사용자 변경·main·backup·Participants·DEV/HOLDOUT/SEALED를 보존했고 승격하지 않았다. 공개 파일에는 일반 코드와 집계 결과만 넣었으며 원문·회고·추출본·raw GT·pixels·모델·private seeds는 공개하지 않았다. 승인 종료는2026-10-17 19:01:55 KST다.
