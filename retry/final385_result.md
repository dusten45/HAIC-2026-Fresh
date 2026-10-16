385 — 최종 실행·보고 어댑터 연결 완료, 개봉은 비활성

**알려진 기술적 연결 장애물은 없다.** 실행·보고·원장·회계 경로를 구현했고 synthetic fixture 22개 항목과 현재 파일의 읽기 전용 metadata preflight를 통과했다. 실제 backend는 생성하지 않았다. 이 준비는 최종 개봉 권한을 포함하지 않으며, SEALED의 관측·성능·지형을 읽거나 평가를 시작하지 않았다.

최종 어댑터는 296 하나와 기존 절대 경로 `/workspace/HAIC-2026-Fresh/.venv/bin/python`을 사용한다. 382·384 계약 원본과 296·240 rollback을 보존했다. 기존 384의 ZIP·member·의존성·worker·native sandbox·SEALED manifest hash에 연결하고, 환경 core 소스·wrapper·damage·runner와 어댑터 소스도 준비 plan에 동결했다. 별도의 보존 receipt를 권한 파일에 묶어 current champion pointer·원래 manifest·query 초기 상태가 바뀌어도 진행하지 않는다.

공개 코드의 import는 inert하다. numpy·OpenCV·Agent·Gym·Box2D·core는 live backend의 reset 안에서만 import한다. 준비 검증 프로세스에는 이 모듈들이 로드되지 않았음을 확인했다. 실제 진입점은 다음 조건을 모두 만족하기 전 backend import나 조건 payload 해석을 하지 않는다.

- 명시적 최종 개봉 권한 파일, authorized=True, 사용자 승인 참조. 이번에 만든 파일은 **authorized=False·승인 참조 없음**인 비활성 template뿐이다. 로컬 권한 파일은 승인 근거를 기록하는 gate이며 암호학적 사용자 서명 인증이라고 주장하지 않는다.
- 382·384·385 plan과 보존 receipt, 어댑터·원래 manifest·296·의존성·환경 source hash가 일치해야 한다.
- Python 3.11.16의 고정 경로, 기존 예비 84,000 중 최소32,000 가용, 기존 query 사용0·현재 허용0·개봉 marker 없음, 승인 마감 이전이어야 한다.
- 최종 단계는 다른 연구 실행과 병행하지 않는 조건이다. adapter lock이 같은 어댑터의 동시 실행을 거부하고, 실행 중 공유 비용 원장 hash가 달라져도 중단한다. 이 lock이 모든 과거 도구나 외부 프로세스를 강제로 통제한다는 보장은 아니다.

metadata preflight는 비활성 template의 hash·runtime·초기 원장만 읽어 확인했다. live 진입점은 호출하지 않았고 조건 목록도 해석하지 않았다. 실제 query 원장은 여전히 **episodes_used=0, future_episode_queries_this_phase_max=0**이며, 실제 final 출력 디렉터리·개봉 marker·활성 권한 파일은 없다.

| 실행 단계 | 사전 기록·보존 |
|---|---|
| batch 개봉 | 새 출력 디렉터리·독점 lock·한 번만 생성 가능한 marker. 명시적 권한 뒤에만 query phase를 활성화한다. 준비 단계에서는 실행하지 않았다. |
| 조건 시작 | claim_intent를 fsync한 뒤 query 사용을 먼저 소비하고 case_claimed를 기록한다. 환경 reset 전에 claim하므로 reset/초기화 실패도 재시도하지 않는다. |
| reset | reset_intent → 정상 reset·actor reset → reset_committed. actor에는 관측만 보내며 seed·info·평가 로그를 보내지 않는다. |
| 각 행동 | act_intent → 원래 actor 반환 → exact shape3·finite·in-range 검사 → act_committed. clip·no-op 대체·commit 보정·정책 수정은 없다. |
| 환경 step | step_intent를 fsync한 다음 env.step을 한 번 실행하고 step_committed를 fsync한다. 정책 입력과 분리된 공식 종료·시간·damage·progress·raw tick 진단만 기록한다. 픽셀·지형·GT pose는 저장하지 않는다. |
| 종료·중단 | 첫 자격/timeout/IPC/무결성/마감 실패에 batch를 중단한다. cleanup과 부분 집계를 남기고 정상 종료·검열·미관측을 분리한다. 기존 출력이 있으면 재실행·resume을 거부한다. |

journal은 각 레코드의 seq·이전 hash·현재 hash와 fsync를 사용한다. 새 파일과 receipt는 부모 디렉터리도 fsync한다. hash chain은 손상 검출용이지 외부 공격자에 대한 인증 서명이 아니다. 디스크/OS 자체의 실패까지 무조건 기록 보존을 보장하지 않는다. 오류가 나면 기존 prefix를 덮어쓰거나 지우지 않는다.

특히 env.step이 적용된 뒤 commit 기록 전에 끊긴 경우, **확정 native 하한과 미해결 상한**을 분리한다. 확인된 step만 실제 비용에 차감하고 미해결 step은 예비에서 점유 상태로 남겨, 완료됐다고 가정하거나 다시 실행하지 않는다. 예컨대 confirmed0·pending1이면 실제 비용을 임의로0이나1로 확정하지 않는다. journal의 정상 prefix로 범위를 복원하며, root budget에도 UNRESOLVED_NO_RETRY와 점유량을 남긴다.

조건별 결과 파일을 모으는 방식 대신 journal에서 **처음부터16개 조건 행을 생성**한다. 정상 완주·DNF·기술/마감 검열·미관측을 모두 유지한다. finish_time_s를 truncated보다 먼저 판정하고 lap은 결승선 통과 시각에서 reset 후 시작 시각을 뺀다. step commit에 finish가 내구 기록됐으면 뒤의 분류 레코드가 누락돼도 그 완주를 보존한다. 정리 실패가 나더라도 이미 관측된 완주를 지우지 않으며 batch qualification 실패는 별도로 표시한다. 완주 시간은 완주 집합에서만 평균·중앙값을 계산하고 DNF에 시간을 채우지 않는다.

최종 회계는 immutable journal hash에 묶어 root의 `project-effective-budget-final385.json`과 별도 최종 receipt로 남기도록 연결했다. 확인된 step만 누적·예비 사용에 반영하고 연구 잔여는 건드리지 않는다. 같은 journal의 metadata 회계 복구는 멱등이며 FINAL385 비용 줄을 두 번 추가하지 않는다. query phase는 종료·중단 뒤 허용량0으로 닫고 이미 소비한 claim은 되돌리지 않는다. 예비 배분은 최대32,000·자동 retry0·240 비교0·미배정52,000을 유지한다.

`--recover-metadata`는 기존 marker와 같은 권한·source, 독점 lock 아래 journal 보고·회계만 복구한다. backend·actor·환경·reset·step을 만들지 않고 누락된 행동을 실행하지 않는다. 찢긴 journal의 정상 prefix는 읽되 손상 suffix를 자동 삭제하지 않는다. 실패 결과가 정상 반환돼 emitter까지 도달한 경우 CLI는 exit code2와 redacted JSON을 사용한다. 정산 예외가 다시 전파되는 실제 __main__ 경로는 emitter를 거치지 않으므로 JSON·exit2를 보장하지 않으며,원시 stderr traceback도 redacted public 파일과 구분한다. 이 범위는388 정정에서 명확히 했다. 공유 비용 원장 자체의 손상, 디스크 고갈, 유효 prefix까지의 소실은 자동 재주행으로 복구할 대상이 아니며, 독립 receipt를 보존한 metadata 회계 조정이 필요할 수 있다.

synthetic dry run의22개 검증에는 다음이 포함된다.

- finish/truncation 우선순위와 실제 통과 시각 lap, 정상 crash·외부 cap,16개 분모와 조건부 평균.
- timeout·invalid·reset 실패 시 native0·나머지 미관측, 엄격한 shape·finite·범위 검사.
- step 적용 후 commit 전 중단, pending 비용 점유, torn suffix, 분류 파일 없는 내구 finish 복원.
- 기존 디렉터리 재실행 거부, cleanup 실패 후 관측 완주 보존, claim 전 마감 시16개 미관측.
- 권한 없음/비활성 template의 live 진입 차단, query 중복 claim 거부, 중단 뒤 claim 보존·허용0, metadata 회계 중복 방지.
- 실제 정책·시뮬레이터 모듈이 import되지 않았고 실제 actor/env/native/SEALED 조회가0임을 확인.

개발 fixture에서 claim 전 마감을 검열로 세던 오류를 발견해 미관측으로 수정했다. 또한 검토 후 current champion/query/계약 보존 receipt도 권한 hash에 묶고 검증을 반복했다. 공개 요약의 예외 상세 제거를 추가한 최종22개 항목도 통과했다. 원래 구현·plan과 수정 receipt를 비공개로 보존했으며 실제 실험이나 정책은 반복하지 않았다. 첫 등록 fixture subprocess wall은0.185초, 첫 metadata preflight는2.283초였다. 이들은 최종22개 검증 전체의 wall로 대신하지 않는다. 개발·수정·게시 전체 시간이나 실제 주행 비용을 뜻하지 않는다.

**현재 상태는 코드 연결·synthetic 검증·metadata preflight 완료, 실제 개봉 대기다.** 남은 것은 명시적 최종 개봉 승인 참조를 가진 활성 권한과 실행 직전 최신 hash 확인이다. 현재 비활성 template을 자동 활성화하거나 평가를 예약하지 않았다. 실제 backend의 SEALED 실행·실제 전원/디스크 장애 시험·공식 서버/새 머신 동등성은 검증하지 않았으며 기존381 정상 actor 검증의 범위를 유지한다. 384의 예상 시간인 최대행동량 사용 시 약33–45분도 새로 benchmark하지 않았다.

새 native/actor/reset/env/model/학습/source physics/관측/성능/지형 조회/유료 자원은 모두0이다. 누적1,312,121·연구35,943·예비84,000·예비 사용0을 유지했고385 비용은v404·원장에 한 번만 기록했다. 원문·개인 회고·조건·seed는 공개하지 않았고 연구 전체 종료나 일정 취소는 없다.

[실행·보고·회계 어댑터](final385_adapter.py) · [synthetic 검증](final385_dryrun.py) · [비활성 준비 코드](final385_prepare.py) · [검증 집계](final385_result.json)
